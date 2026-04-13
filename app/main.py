import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api import health as health_api, orders as orders_api, apps as apps_api, workflow as workflow_api, dashboard as dashboard_api, auth as auth_api, settings as settings_api
from app.db.session import engine, Base
from app.models import application, order, order_item, workflow, history, setting

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("oms-service")

# Create database tables manually (no Alembic)
Base.metadata.create_all(bind=engine)

def seed_data():
    from sqlalchemy.orm import Session
    from app.db.session import SessionLocal
    from app.models.workflow import WorkflowState
    from app.models.application import Application
    
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

seed_data()

app = FastAPI(title="OMS Microservice", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": str(exc), "code": 500}
    )

@app.exception_handler(400)
async def bad_request_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=400,
        content={"error": "Bad Request", "detail": str(exc), "code": 400}
    )

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "detail": str(exc), "code": 404}
    )

# Include routers
app.include_router(health_api.router, tags=["Health"])
app.include_router(auth_api.router, prefix="/auth", tags=["Authentication"])
app.include_router(apps_api.router, prefix="/apps", tags=["Applications"])
app.include_router(orders_api.router, prefix="/orders", tags=["Orders"])
app.include_router(workflow_api.router, prefix="/workflow", tags=["Workflow"])
app.include_router(dashboard_api.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(settings_api.router, prefix="/settings/admin", tags=["Settings Admin"])

@app.get("/")
def root():
    return {"message": "Welcome to the Order Management System (OMS) Microservice"}
