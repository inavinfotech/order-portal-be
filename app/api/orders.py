from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.order import OrderCreate, OrderUpdate, Order, OrderTransition
from app.services.order_service import OrderService
from app.auth.deps import get_current_app, verify_dashboard_auth, get_order_context_app
from app.models.application import Application
from app.exceptions import (
    OrderValidationError,
    TransitionError,
    ApplicationNotFoundError,
    ProcessingDisabledError,
)
from typing import List, Optional

router = APIRouter()

def _handle_service_error(e: Exception):
    """Convert domain exceptions to HTTP responses."""
    if isinstance(e, ProcessingDisabledError):
        raise HTTPException(status_code=503, detail=e.message)
    elif isinstance(e, ApplicationNotFoundError):
        raise HTTPException(status_code=400, detail=e.message)
    elif isinstance(e, TransitionError):
        raise HTTPException(status_code=400, detail=e.message)
    elif isinstance(e, OrderValidationError):
        raise HTTPException(status_code=422, detail=e.message)
    raise e

@router.post("/{order_id}/transition", response_model=Order)
def transition_order(
    order_id: str, 
    transition: OrderTransition, 
    db: Session = Depends(get_db),
    current_app: Optional[Application] = Depends(get_order_context_app)
):
    app_id = current_app.id if current_app else None
    changed_by = current_app.name if current_app else "Admin Dashboard"
    try:
        order = OrderService.transition_order(
            db=db, 
            order_id=order_id, 
            application_id=app_id,
            to_status=transition.to_status, 
            changed_by=changed_by, 
            notes=transition.notes,
            force=transition.force
        )
    except Exception as e:
        _handle_service_error(e)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.post("/", response_model=Order)
def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_app: Application = Depends(get_current_app),
    x_idempotency_key: Optional[str] = Header(None)
):
    # Enforce app ownership
    order.application_id = current_app.id
    if x_idempotency_key:
        order.idempotency_key = x_idempotency_key
    
    try:
        return OrderService.create_order(db=db, order=order)
    except Exception as e:
        _handle_service_error(e)

@router.post("/admin", response_model=Order)
def create_admin_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    _ = Depends(verify_dashboard_auth)
):
    try:
        return OrderService.create_order(db=db, order=order)
    except Exception as e:
        _handle_service_error(e)

@router.get("/", response_model=List[Order])
def read_orders(
    skip: int = 0, 
    limit: int = 100, 
    user_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_app: Optional[Application] = Depends(get_order_context_app)
):
    app_id = current_app.id if current_app else None
    return OrderService.get_orders(db, application_id=app_id, user_id=user_id, skip=skip, limit=limit)

@router.get("/count")
def read_orders_count(
    user_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_app: Optional[Application] = Depends(get_order_context_app)
):
    app_id = current_app.id if current_app else None
    return {"count": OrderService.get_orders_count(db, application_id=app_id, user_id=user_id)}

@router.get("/{order_id}", response_model=Order)
def read_order(
    order_id: str, 
    db: Session = Depends(get_db),
    current_app: Optional[Application] = Depends(get_order_context_app)
):
    app_id = current_app.id if current_app else None
    db_order = OrderService.get_order(db, order_id=order_id, application_id=app_id)
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order

@router.put("/{order_id}", response_model=Order)
def update_order(
    order_id: str, 
    order: OrderUpdate, 
    db: Session = Depends(get_db),
    current_app: Optional[Application] = Depends(get_order_context_app)
):
    app_id = current_app.id if current_app else None
    try:
        db_order = OrderService.update_order(db, order_id=order_id, application_id=app_id, order=order)
    except Exception as e:
        _handle_service_error(e)
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order

@router.delete("/{order_id}", response_model=Order)
def delete_order(
    order_id: str, 
    db: Session = Depends(get_db),
    current_app: Optional[Application] = Depends(get_order_context_app)
):
    app_id = current_app.id if current_app else None
    db_order = OrderService.delete_order(db, order_id=order_id, application_id=app_id)
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order
