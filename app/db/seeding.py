from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.workflow import WorkflowState
import logging

logger = logging.getLogger("oms-service")

def seed_data():
    db = SessionLocal()
    try:
        # Check if states already exist
        if db.query(WorkflowState).count() > 0:
            return

        logger.info("Seeding initial data...")
        # Default states
        states = [
            {"name": "created", "description": "Order has been created"},
            {"name": "pending", "description": "Order is pending approval"},
            {"name": "approved", "description": "Order has been approved"},
            {"name": "processing", "description": "Order is being processed"},
            {"name": "shipped", "description": "Order has been shipped"},
            {"name": "delivered", "description": "Order has been delivered"},
            {"name": "cancelled", "description": "Order has been cancelled"},
            {"name": "refunded", "description": "Order has been refunded"},
        ]

        for state_data in states:
            state = WorkflowState(**state_data)
            db.add(state)
        
        db.commit()
        logger.info("Seeding complete.")
    except Exception as e:
        logger.error(f"Error seeding data: {e}")
        db.rollback() 
    finally:
        db.close()
