from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.workflow import WorkflowState
from app.models.application import Application
from app.auth.security import get_secret_hash
import logging

logger = logging.getLogger("oms-service")

def seed_data():
    db = SessionLocal()
    try:
        # 1. Seed Workflow States
        if db.query(WorkflowState).count() == 0:
            logger.info("Seeding initial workflow states...")
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
            logger.info("Workflow states seeding complete.")

        # 2. Seed Website Application
        # We use the credentials defined in website/backend/.env
        # website_api_key = "app_c0e41c8423a83e1bff7dfb88"
        # website_api_secret = "wjyVuQav2YYD4171WAfOhibn2PyCmPI84SjFJ9mx1kQ"
        
        # existing_app = db.query(Application).filter(Application.api_key == website_api_key).first()
        # if not existing_app:
        #     logger.info("Seeding website application...")
        #     new_app = Application(
        #         name="TianaLuxora Website",
        #         api_key=website_api_key,
        #         api_secret=get_secret_hash(website_api_secret),
        #         is_active=True,
        #         is_live_mode=False,
        #         allowed_domains="*"
        #     )
        #     db.add(new_app)
        #     db.commit()
        #     logger.info("Website application seeding complete.")
            
    except Exception as e:
        logger.error(f"Error seeding data: {e}")
        db.rollback() 
    finally:
        db.close()
