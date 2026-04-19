from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List
import uuid

class OrderItemBase(BaseModel):
    product_id: str
    product_name: Optional[str] = None
    sku: Optional[str] = None
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)

class OrderItemCreate(OrderItemBase):
    pass

class OrderItem(OrderItemBase):
    id: str
    order_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    application_id: Optional[str] = None
    user_id: str
    customer_name: str
    product_name: str
    quantity: int
    total_amount: float
    currency: str = "USD"
    status: Optional[str] = "created"
    idempotency_key: Optional[str] = None

class OrderCreate(OrderBase):
    items: List[OrderItemCreate]

    @field_validator('items')
    @classmethod
    def items_not_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError('Order must have at least one item')
        return v

class OrderUpdate(BaseModel):
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    quantity: Optional[int] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None
    currency: Optional[str] = None

class OrderTransition(BaseModel):
    to_status: str
    notes: Optional[str] = None
    force: bool = False

class OrderStatusHistory(BaseModel):
    id: str
    order_id: str
    from_status: str
    to_status: str
    changed_at: datetime
    changed_by: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True

class Order(OrderBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    items: List[OrderItem] = []
    history: List[OrderStatusHistory] = []

    class Config:
        from_attributes = True
