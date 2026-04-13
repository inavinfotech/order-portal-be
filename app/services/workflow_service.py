from sqlalchemy.orm import Session, aliased
from app.models.workflow import WorkflowState, WorkflowTransition
from app.schemas.workflow import WorkflowStateCreate, WorkflowTransitionCreate
from typing import List, Optional
import uuid

class WorkflowService:
    @staticmethod
    def get_states(db: Session) -> List[WorkflowState]:
        return db.query(WorkflowState).all()

    @staticmethod
    def get_transitions(db: Session) -> List[WorkflowTransition]:
        return db.query(WorkflowTransition).all()

    @staticmethod
    def create_state(db: Session, state: WorkflowStateCreate) -> WorkflowState:
        db_state = WorkflowState(
            id=str(uuid.uuid4()),
            name=state.name,
            description=state.description
        )
        db.add(db_state)
        db.commit()
        db.refresh(db_state)
        return db_state

    @staticmethod
    def delete_state(db: Session, state_id: str) -> bool:
        db_state = db.query(WorkflowState).filter(WorkflowState.id == state_id).first()
        if db_state:
            # Note: Transitions dependent on this state will be handled by the user or DB constraints.
            # In our case, we might want to check if transitions exist.
            db.delete(db_state)
            db.commit()
            return True
        return False

    @staticmethod
    def create_transition(db: Session, transition: WorkflowTransitionCreate) -> WorkflowTransition:
        db_transition = WorkflowTransition(
            id=str(uuid.uuid4()),
            name=transition.name,
            from_state_id=transition.from_state_id,
            to_state_id=transition.to_state_id
        )
        db.add(db_transition)
        db.commit()
        db.refresh(db_transition)
        return db_transition

    @staticmethod
    def delete_transition(db: Session, transition_id: str) -> bool:
        db_transition = db.query(WorkflowTransition).filter(WorkflowTransition.id == transition_id).first()
        if db_transition:
            db.delete(db_transition)
            db.commit()
            return True
        return False

    @staticmethod
    def validate_transition(db: Session, from_state_name: str, to_state_name: str) -> bool:
        from_st = aliased(WorkflowState)
        to_st = aliased(WorkflowState)
        
        transition = db.query(WorkflowTransition).select_from(WorkflowTransition).join(
            from_st, WorkflowTransition.from_state_id == from_st.id
        ).filter(
            from_st.name == from_state_name
        ).join(
            to_st, WorkflowTransition.to_state_id == to_st.id
        ).filter(
            to_st.name == to_state_name
        ).first()
        
        return transition is not None

    @staticmethod
    def get_state_by_name(db: Session, name: str) -> Optional[WorkflowState]:
        return db.query(WorkflowState).filter(WorkflowState.name == name).first()
