from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class WorkflowStateBase(BaseModel):
    name: str
    description: Optional[str] = None

class WorkflowStateCreate(WorkflowStateBase):
    pass

class WorkflowState(WorkflowStateBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

class WorkflowTransitionBase(BaseModel):
    name: Optional[str] = "Unnamed Transition"
    from_state_id: str
    to_state_id: str

class WorkflowTransitionCreate(WorkflowTransitionBase):
    pass

class WorkflowTransition(WorkflowTransitionBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
