from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import uuid

class WorkflowState(Base):
    __tablename__ = "workflow_states"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, index=True)
    description = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    outgoing_transitions = relationship("WorkflowTransition", foreign_keys="[WorkflowTransition.from_state_id]", back_populates="from_state")
    incoming_transitions = relationship("WorkflowTransition", foreign_keys="[WorkflowTransition.to_state_id]", back_populates="to_state")

class WorkflowTransition(Base):
    __tablename__ = "workflow_transitions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    from_state_id = Column(String, ForeignKey("workflow_states.id"), nullable=False)
    to_state_id = Column(String, ForeignKey("workflow_states.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    from_state = relationship("WorkflowState", foreign_keys=[from_state_id], back_populates="outgoing_transitions")
    to_state = relationship("WorkflowState", foreign_keys=[to_state_id], back_populates="incoming_transitions")
