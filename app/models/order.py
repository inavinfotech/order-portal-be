from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import uuid

class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = Column(String, ForeignKey("applications.id"), nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    customer_name = Column(String, index=True)
    product_name = Column(String)
    quantity = Column(Integer)
    total_amount = Column(Numeric(12, 2))
    currency = Column(String, default="USD")
    status = Column(String, ForeignKey("workflow_states.name"), default="created", index=True)
    idempotency_key = Column(String, nullable=True, index=True)
    image = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    application = relationship("Application", back_populates="orders")
    history = relationship("OrderStatusHistory", back_populates="order", cascade="all, delete-orphan")
    workflow_state = relationship("WorkflowState", foreign_keys=[status], primaryjoin="Order.status == WorkflowState.name")
