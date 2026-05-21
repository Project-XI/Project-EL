from typing import Dict, Set

from src.agents.main_agent.models import SessionLifecycle


ALLOWED_TRANSITIONS: Dict[SessionLifecycle, Set[SessionLifecycle]] = {
    SessionLifecycle.INITIALIZED: {
        SessionLifecycle.ACTIVE,
        SessionLifecycle.TERMINATED,
    },
    SessionLifecycle.ACTIVE: {
        SessionLifecycle.INTERRUPTED,
        SessionLifecycle.COMPLETED,
        SessionLifecycle.TERMINATED,
    },
    SessionLifecycle.INTERRUPTED: {
        SessionLifecycle.ACTIVE,
        SessionLifecycle.TERMINATED,
    },
    SessionLifecycle.COMPLETED: set(),
    SessionLifecycle.TERMINATED: set(),
}


def validate_transition(from_stage: SessionLifecycle, to_stage: SessionLifecycle) -> None:
    if from_stage == to_stage:
        return
    if to_stage not in ALLOWED_TRANSITIONS[from_stage]:
        raise ValueError(f"Invalid session transition from {from_stage} to {to_stage}")

