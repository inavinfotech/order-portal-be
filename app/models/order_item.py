from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import uuid

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String, ForeignKey("orders.id"), nullable=False, index=True)
    product_id = Column(String, index=True)
    variant_id = Column(String, index=True, nullable=True)
    variant_name = Column(String, nullable=True)
    product_name = Column(String)
    sku = Column(String)
    quantity = Column(Integer)
    unit_price = Column(Numeric(12, 2))
    image = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    order = relationship("Order", back_populates="items")
