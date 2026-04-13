from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.workflow import WorkflowState, WorkflowTransition, WorkflowStateCreate, WorkflowTransitionCreate
from app.services.workflow_service import WorkflowService
from app.auth.deps import verify_dashboard_auth
from typing import List

router = APIRouter()

@router.get("/states", response_model=List[WorkflowState], dependencies=[Depends(verify_dashboard_auth)])
def read_workflow_states(db: Session = Depends(get_db)):
    return WorkflowService.get_states(db)

@router.post("/states", response_model=WorkflowState, dependencies=[Depends(verify_dashboard_auth)])
def create_workflow_state(state: WorkflowStateCreate, db: Session = Depends(get_db)):
    # Check if name already exists
    existing = WorkflowService.get_state_by_name(db, state.name)
    if existing:
        raise HTTPException(status_code=400, detail="State with this name already exists")
    return WorkflowService.create_state(db, state)

@router.delete("/states/{state_id}", dependencies=[Depends(verify_dashboard_auth)])
def delete_workflow_state(state_id: str, db: Session = Depends(get_db)):
    success = WorkflowService.delete_state(db, state_id)
    if not success:
        raise HTTPException(status_code=404, detail="State not found")
    return {"status": "success", "message": "State deleted"}

@router.get("/transitions", response_model=List[WorkflowTransition], dependencies=[Depends(verify_dashboard_auth)])
def read_workflow_transitions(db: Session = Depends(get_db)):
    return WorkflowService.get_transitions(db)

@router.post("/transitions", response_model=WorkflowTransition, dependencies=[Depends(verify_dashboard_auth)])
def create_workflow_transition(transition: WorkflowTransitionCreate, db: Session = Depends(get_db)):
    return WorkflowService.create_transition(db, transition)

@router.delete("/transitions/{transition_id}", dependencies=[Depends(verify_dashboard_auth)])
def delete_workflow_transition(transition_id: str, db: Session = Depends(get_db)):
    success = WorkflowService.delete_transition(db, transition_id)
    if not success:
        raise HTTPException(status_code=404, detail="Transition not found")
    return {"status": "success", "message": "Transition deleted"}
