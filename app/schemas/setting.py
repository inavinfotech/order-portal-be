from pydantic import BaseModel

from typing import Optional

class SettingUpdate(BaseModel):
    global_order_processing_enabled: Optional[str] = None
    global_currency: Optional[str] = None
