from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.order import Order
from app.models.application import Application
from app.auth.deps import verify_dashboard_auth
from sqlalchemy import func, text

router = APIRouter()

from datetime import datetime, timedelta

@router.get("/stats", dependencies=[Depends(verify_dashboard_auth)])
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_orders = db.query(Order).filter(Order.deleted_at == None).count()
    pending_orders = db.query(Order).filter(Order.status == "pending", Order.deleted_at == None).count()
    total_amount = db.query(func.sum(Order.total_amount)).filter(Order.deleted_at == None).scalar() or 0
    active_apps = db.query(Application).filter(Application.is_active == True).count()
    
    # Growth Calculation (Last 30 days vs previous 30 days)
    now = datetime.utcnow()
    last_30 = now - timedelta(days=30)
    prev_30 = now - timedelta(days=60)
    
    current_count = db.query(Order).filter(Order.created_at >= last_30, Order.deleted_at == None).count()
    previous_count = db.query(Order).filter(Order.created_at >= prev_30, Order.created_at < last_30, Order.deleted_at == None).count()
    
    growth = 0
    if previous_count > 0:
        growth = ((current_count - previous_count) / previous_count) * 100
    elif current_count > 0:
        growth = 100
        
    recent_orders = db.query(Order).filter(Order.deleted_at == None).order_by(Order.created_at.desc()).limit(5).all()
    
    return {
        "total": total_orders,
        "pending": pending_orders,
        "amount": total_amount,
        "active_apps": active_apps,
        "growth": f"{growth:+.1f}%",
        "recent": recent_orders
    }

@router.get("/health", dependencies=[Depends(verify_dashboard_auth)])
def get_system_health(db: Session = Depends(get_db)):
    db_status = "online"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "offline"
        
    return {
        "api": "online",
        "database": db_status,
        "relay": "online"
    }
