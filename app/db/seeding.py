from app.db.session import SessionLocal
from app.models.workflow import WorkflowState, WorkflowTransition
from app.models.setting import Setting
import logging
import uuid

logger = logging.getLogger("oms-service")

def seed_data():
    db = SessionLocal()
    try:
        # 1. Seed Workflow States
        if db.query(WorkflowState).count() == 0:
            logger.info("Seeding initial workflow states...")
            states_data = [
                {"name": "created", "description": "Order has been created"},
                {"name": "pending", "description": "Order is pending approval"},
                {"name": "approved", "description": "Order has been approved"},
                {"name": "processing", "description": "Order is being processed"},
                {"name": "shipped", "description": "Order has been shipped"},
                {"name": "delivered", "description": "Order has been delivered"},
                {"name": "cancelled", "description": "Order has been cancelled"},
                {"name": "refunded", "description": "Order has been refunded"},
            ]

            state_objs = {}
            for data in states_data:
                state = WorkflowState(id=str(uuid.uuid4()), **data)
                db.add(state)
                state_objs[data["name"]] = state
            
            db.flush() # Flush to get IDs

            # 2. Seed Transitions
            logger.info("Seeding workflow transitions...")
            transitions = [
                ("created", "processing", "Start Processing"),
                ("created", "cancelled", "Cancel Order"),
                ("processing", "shipped", "Ship Order"),
                ("processing", "cancelled", "Cancel Order"),
                ("shipped", "delivered", "Mark as Delivered"),
                ("shipped", "cancelled", "Cancel Order (Return)"),
                ("delivered", "refunded", "Refund Order"),
            ]

            for from_name, to_name, trans_name in transitions:
                if from_name in state_objs and to_name in state_objs:
                    trans = WorkflowTransition(
                        id=str(uuid.uuid4()),
                        name=trans_name,
                        from_state_id=state_objs[from_name].id,
                        to_state_id=state_objs[to_name].id
                    )
                    db.add(trans)
            
            db.commit()
            logger.info("Workflow states and transitions seeding complete.")

        # 3. Seed Default Settings
        if db.query(Setting).filter(Setting.key == "global_order_processing_enabled").count() == 0:
            logger.info("Seeding global order processing setting...")
            new_setting = Setting(
                key="global_order_processing_enabled",
                value="true"
            )
            db.add(new_setting)
            db.commit()
            logger.info("Settings seeding complete.")
            
    except Exception as e:
        logger.error(f"Error seeding data: {e}")
        db.rollback() 
    finally:
        db.close()
