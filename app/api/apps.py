from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.application import (
    ApplicationCreate,
    Application as ApplicationSchema,
    AppStatusUpdate,
    AppModeUpdate,
    AppDomainsUpdate,
)
from app.models.application import Application as ApplicationModel
from app.auth.security import get_secret_hash, generate_api_key, generate_api_secret
from app.auth.deps import verify_dashboard_auth
from typing import List
from datetime import datetime, timezone
import uuid
import secrets

router = APIRouter()

@router.post("", response_model=ApplicationSchema)
def create_app(
    app: ApplicationCreate, 
    db: Session = Depends(get_db),
    _ = Depends(verify_dashboard_auth)
):
    app_data = app.model_dump()
    
    # Generate keys if not provided
    if not app_data.get("api_key"):
        app_data["api_key"] = generate_api_key()
    
    plain_secret = app_data.get("api_secret")
    if not plain_secret:
        plain_secret = generate_api_secret()
        app_data["api_secret"] = plain_secret
    
    # Store hashed secret
    app_data["api_secret"] = get_secret_hash(app_data["api_secret"])
    
    # Create DB model instance
    db_app = ApplicationModel(**app_data)
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    
    # Prepare response with plain secret
    response_data = {
        "id": db_app.id,
        "name": db_app.name,
        "api_key": db_app.api_key,
        "api_secret": plain_secret,
        "is_active": db_app.is_active,
        "created_at": db_app.created_at,
        "updated_at": db_app.updated_at
    }
    
    return response_data

@router.get("", response_model=List[ApplicationSchema])
def read_apps(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    _ = Depends(verify_dashboard_auth)
):
    return db.query(ApplicationModel).filter(ApplicationModel.deleted_at == None).offset(skip).limit(limit).all()

@router.delete("/{app_id}")
def delete_app(
    app_id: str, 
    db: Session = Depends(get_db),
    _ = Depends(verify_dashboard_auth)
):
    db_app = db.query(ApplicationModel).filter(ApplicationModel.id == app_id).first()
    if not db_app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Soft delete
    db_app.deleted_at = datetime.now(timezone.utc)
    db_app.is_active = False # Also deactivate for safety
    db.commit()
    return {"message": "Application revoked successfully"}

@router.put("/{app_id}/status")
def update_app_status(app_id: str, update: AppStatusUpdate, db: Session = Depends(get_db), _ = Depends(verify_dashboard_auth)):
    db_app = db.query(ApplicationModel).filter(ApplicationModel.id == app_id).first()
    if not db_app or db_app.deleted_at:
        raise HTTPException(status_code=404, detail="App not found")
    db_app.is_active = update.is_active
    db.commit()
    return {"status": "success"}

@router.put("/{app_id}/mode")
def update_app_mode(app_id: str, update: AppModeUpdate, db: Session = Depends(get_db), _ = Depends(verify_dashboard_auth)):
    db_app = db.query(ApplicationModel).filter(ApplicationModel.id == app_id).first()
    if not db_app or db_app.deleted_at:
        raise HTTPException(status_code=404, detail="App not found")
    db_app.is_live_mode = update.is_live_mode
    db.commit()
    return {"status": "success"}

@router.put("/{app_id}/domains")
def update_app_domains(app_id: str, update: AppDomainsUpdate, db: Session = Depends(get_db), _ = Depends(verify_dashboard_auth)):
    db_app = db.query(ApplicationModel).filter(ApplicationModel.id == app_id).first()
    if not db_app or db_app.deleted_at:
        raise HTTPException(status_code=404, detail="App not found")
    db_app.allowed_domains = update.allowed_domains
    db.commit()
    return {"status": "success"}
