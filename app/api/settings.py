from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.setting import Setting
from app.schemas.setting import SettingUpdate
from app.auth.deps import verify_dashboard_auth

router = APIRouter()

@router.get("/admin")
def get_settings(db: Session = Depends(get_db), _ = Depends(verify_dashboard_auth)):
    settings = db.query(Setting).all()
    
    # Ensure defaults exist
    defaults = {
        'global_order_processing_enabled': 'true',
        'global_currency': 'USD'
    }
    
    current_keys = {s.key for s in settings}
    for key, value in defaults.items():
        if key not in current_keys:
            default_setting = Setting(key=key, value=value)
            db.add(default_setting)
            db.commit()
            settings.append(default_setting)
            
    return {s.key: s.value for s in settings}

@router.post("/admin")
def update_settings(update: SettingUpdate, db: Session = Depends(get_db), _ = Depends(verify_dashboard_auth)):
    response_data = {"status": "success"}
    
    if update.global_order_processing_enabled is not None:
        setting = db.query(Setting).filter(Setting.key == 'global_order_processing_enabled').first()
        if not setting:
            setting = Setting(key='global_order_processing_enabled', value=update.global_order_processing_enabled)
            db.add(setting)
        else:
            setting.value = update.global_order_processing_enabled
        response_data['global_order_processing_enabled'] = update.global_order_processing_enabled

    if update.global_currency is not None:
        setting = db.query(Setting).filter(Setting.key == 'global_currency').first()
        if not setting:
            setting = Setting(key='global_currency', value=update.global_currency)
            db.add(setting)
        else:
            setting.value = update.global_currency
        response_data['global_currency'] = update.global_currency
        
    db.commit()
    return response_data
