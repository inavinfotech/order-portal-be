from sqlalchemy.orm import Session
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.history import OrderStatusHistory
from app.models.setting import Setting
from app.models.application import Application as ApplicationModel
from app.schemas.order import OrderCreate, OrderUpdate
from app.exceptions import (
    OrderValidationError,
    TransitionError,
    ApplicationNotFoundError,
    ProcessingDisabledError,
)
from typing import List, Optional
from datetime import datetime, timezone
import uuid


class OrderService:
    @staticmethod
    def get_order(db: Session, order_id: str, application_id: Optional[str] = None) -> Optional[Order]:
        query = db.query(Order).filter(
            Order.id == order_id, 
            Order.deleted_at == None
        )
        if application_id:
            query = query.filter(Order.application_id == application_id)
        return query.first()

    @staticmethod
    def get_orders(db: Session, application_id: Optional[str] = None, user_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Order]:
        query = db.query(Order).filter(Order.deleted_at == None)
        if application_id:
            query = query.filter(Order.application_id == application_id)
        if user_id:
            query = query.filter(Order.user_id == user_id)
        return query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_orders_count(db: Session, application_id: Optional[str] = None, user_id: Optional[str] = None) -> int:
        query = db.query(Order).filter(Order.deleted_at == None)
        if application_id:
            query = query.filter(Order.application_id == application_id)
        if user_id:
            query = query.filter(Order.user_id == user_id)
        return query.count()

    @staticmethod
    def create_order(db: Session, order: OrderCreate) -> Order:
        # Check global processing setting
        processing_setting = db.query(Setting).filter(Setting.key == "global_order_processing_enabled").first()
        if processing_setting and processing_setting.value == "false":
            raise ProcessingDisabledError("Order processing is currently disabled globally. No new orders can be created.")

        # Validate application exists
        app = db.query(ApplicationModel).filter(ApplicationModel.id == order.application_id).first()
        if not app:
            raise ApplicationNotFoundError(f"Application with ID {order.application_id} does not exist")
            
        # Idempotency check
        if order.idempotency_key:
            existing_order = db.query(Order).filter(
                Order.application_id == order.application_id,
                Order.idempotency_key == order.idempotency_key
            ).first()
            if existing_order:
                return existing_order

        try:
            # Create order object (items will be added later)
            order_dict = order.model_dump(exclude={"items"})
            
            # Sum up total_amount if items are provided and total_amount is not set
            if "total_amount" not in order_dict or order_dict["total_amount"] is None:
                if order.items:
                    order_dict["total_amount"] = sum(item.quantity * item.unit_price for item in order.items)
                else:
                    order_dict["total_amount"] = 0

            db_order = Order(**order_dict)
            db.add(db_order)
            db.flush()  # Get the ID without committing yet

            # Create order items
            if order.items:
                for item in order.items:
                    db_item = OrderItem(**item.model_dump(), order_id=db_order.id)
                    db.add(db_item)
            
            db.commit()
            db.refresh(db_order)
            return db_order
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def update_order(db: Session, order_id: str, application_id: Optional[str], order: OrderUpdate) -> Optional[Order]:
        db_order = OrderService.get_order(db, order_id, application_id)
        if not db_order:
            return None
            
        update_data = order.model_dump(exclude_unset=True)
        if "status" in update_data and update_data["status"] != db_order.status:
            from app.services.workflow_service import WorkflowService
            if not WorkflowService.validate_transition(db, db_order.status, update_data["status"]):
                raise TransitionError(f"Invalid transition from {db_order.status} to {update_data['status']}")
            
        for key, value in update_data.items():
            setattr(db_order, key, value)
            
        db.commit()
        db.refresh(db_order)
        return db_order

    @staticmethod
    def transition_order(db: Session, order_id: str, application_id: Optional[str], to_status: str, changed_by: str, notes: Optional[str] = None, force: bool = False) -> Optional[Order]:
        db_order = OrderService.get_order(db, order_id, application_id)
        if not db_order:
            return None
            
        from_status = db_order.status
        if from_status == to_status:
            return db_order
            
        if not force:
            from app.services.workflow_service import WorkflowService
            if not WorkflowService.validate_transition(db, from_status, to_status):
                raise TransitionError(f"Invalid transition from {from_status} to {to_status}")
            
        try:
            # Update order status
            db_order.status = to_status
            
            # Log history
            history_entry = OrderStatusHistory(
                id=str(uuid.uuid4()),
                order_id=order_id,
                from_status=from_status,
                to_status=to_status,
                changed_by=changed_by,
                notes=notes
            )
            db.add(history_entry)
            
            db.commit()
            db.refresh(db_order)
            return db_order
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def delete_order(db: Session, order_id: str, application_id: Optional[str]) -> Optional[Order]:
        db_order = OrderService.get_order(db, order_id, application_id)
        if db_order:
            db_order.deleted_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(db_order)
        return db_order
