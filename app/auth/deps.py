from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.application import Application
from app.auth.security import verify_secret, decode_access_token
import os
from typing import Optional

def get_current_app(
    db: Session = Depends(get_db),
    x_api_key: str = Header(None),
    x_api_secret: str = Header(None)
) -> Application:
    if not x_api_key or not x_api_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key and Secret are required"
        )
    
    app = db.query(Application).filter(Application.api_key == x_api_key, Application.is_active == True).first()
    if not app or not verify_secret(x_api_secret, app.api_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key or Secret"
        )
    
    return app

def verify_dashboard_auth(
    authorization: str = Header(None),
    # Backward compat: still accept header-based auth during transition
    x_dashboard_email: str = Header(None),
    x_dashboard_password: str = Header(None)
):
    # Try JWT Bearer token first (preferred)
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        payload = decode_access_token(token)
        if payload and payload.get("sub"):
            return True
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Fallback: legacy header-based auth
    if x_dashboard_email and x_dashboard_password:
        expected_email = os.getenv("DASHBOARD_EMAIL", "admin@example.com")
        expected_pass = os.getenv("DASHBOARD_PASSWORD", "password123")
        
        if x_dashboard_email == expected_email and x_dashboard_password == expected_pass:
            return True
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Valid Bearer token or Dashboard credentials required"
    )

def get_order_context_app(
    db: Session = Depends(get_db),
    authorization: str = Header(None),
    x_api_key: str = Header(None),
    x_api_secret: str = Header(None),
    x_dashboard_email: str = Header(None),
    x_dashboard_password: str = Header(None),
    x_app_id: str = Header(None)
) -> Optional[Application]:
    # Try API Key/Secret (Standard Client)
    if x_api_key and x_api_secret:
        app = db.query(Application).filter(Application.api_key == x_api_key, Application.is_active == True).first()
        if app and verify_secret(x_api_secret, app.api_secret):
            return app

    # Try JWT Bearer token (Dashboard)
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        payload = decode_access_token(token)
        if payload and payload.get("sub"):
            if x_app_id:
                app = db.query(Application).filter(Application.id == x_app_id).first()
                if app:
                    return app
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Selected Application was not found or has been revoked"
                )
            return None  # Admin context, no specific app

    # Fallback: legacy header-based auth
    if x_dashboard_email and x_dashboard_password:
        expected_email = os.getenv("DASHBOARD_EMAIL", "admin@example.com")
        expected_pass = os.getenv("DASHBOARD_PASSWORD", "password123")
        if x_dashboard_email == expected_email and x_dashboard_password == expected_pass:
            if x_app_id:
                app = db.query(Application).filter(Application.id == x_app_id).first()
                if app:
                    return app
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Selected Application was not found or has been revoked"
                )
            return None

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Valid API Key/Secret or Bearer token required"
    )
