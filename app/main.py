import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app.db.session import engine, Base
from app.api import health as health_api, orders as orders_api, apps as apps_api, workflow as workflow_api, dashboard as dashboard_api, auth as auth_api, settings as settings_api
from app.models import application, order, order_item, workflow, history, setting
from app.db.seeding import seed_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("oms-service")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    Base.metadata.create_all(bind=engine)
    # Auto-seed data
    seed_data()
    yield
 
app = FastAPI(title="OMS Microservice", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "*"
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
    logger.error(f"Bad Request on {request.url}: {exc}")
    return JSONResponse(
        status_code=400,
        content={"error": "Bad Request", "detail": str(exc), "code": 400}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation Error on {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"error": "Unprocessable Entity", "detail": exc.errors(), "code": 422}
    )

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "detail": str(exc), "code": 404}
    )

# Include routers
API_V1_STR = "/api/v1"
app.include_router(health_api.router, prefix=f"{API_V1_STR}", tags=["Health"])
app.include_router(auth_api.router, prefix=f"{API_V1_STR}/auth", tags=["Authentication"])
app.include_router(apps_api.router, prefix=f"{API_V1_STR}/apps", tags=["Applications"])
app.include_router(orders_api.router, prefix=f"{API_V1_STR}/orders", tags=["Orders"])
app.include_router(workflow_api.router, prefix=f"{API_V1_STR}/workflow", tags=["Workflow"])
app.include_router(dashboard_api.router, prefix=f"{API_V1_STR}/dashboard", tags=["Dashboard"])
app.include_router(settings_api.router, prefix=f"{API_V1_STR}/settings", tags=["Settings Admin"])

@app.get("/")
def root():
    return {"message": "Welcome to the Order Management System (OMS) Microservice"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8003, reload=True)
