"""
TransitionManager — explicit finite-state machine for viva session lifecycle.

Valid transitions are declared up front.  Any attempt to move between
states that are not connected by an edge raises ``InvalidTransitionError``
rather than silently falling through.

Allowed transitions
-------------------
IDLE         → INITIALIZED
INITIALIZED → IN_PROGRESS
IN_PROGRESS → PAUSED
IN_PROGRESS → COMPLETED
IN_PROGRESS → ERROR
PAUSED      → IN_PROGRESS
PAUSED      → COMPLETED
PAUSED      → TERMINATED
ERROR       → TERMINATED
ERROR       → IN_PROGRESS   (retry after recovery)

Terminal (no outgoing edges)
COMPLETED
TERMINATED
"""

from __future__ import annotations

from typing import Set

from ..models.session_state import SessionLifecycleStage
from .history import SessionHistory


class InvalidTransitionError(Exception):
    """Raised when an illegal state transition is attempted."""

    def __init__(self, from_stage: str, to_stage: str) -> None:
        super().__init__(f"Invalid session transition: {from_stage!r} → {to_stage!r}")
        self.from_stage = from_stage
        self.to_stage = to_stage


# Valid edges keyed by *from* stage
_VALID_EDGES: dict[str, Set[str]] = {
    SessionLifecycleStage.IDLE.value: {
        SessionLifecycleStage.INITIALIZED.value,
    },
    SessionLifecycleStage.INITIALIZED.value: {
        SessionLifecycleStage.IN_PROGRESS.value,
    },
    SessionLifecycleStage.IN_PROGRESS.value: {
        SessionLifecycleStage.PAUSED.value,
        SessionLifecycleStage.COMPLETED.value,
        SessionLifecycleStage.ERROR.value,
    },
    SessionLifecycleStage.PAUSED.value: {
        SessionLifecycleStage.IN_PROGRESS.value,
        SessionLifecycleStage.COMPLETED.value,
        SessionLifecycleStage.TERMINATED.value,
    },
    SessionLifecycleStage.ERROR.value: {
        SessionLifecycleStage.TERMINATED.value,
        SessionLifecycleStage.IN_PROGRESS.value,
    },
    # Terminal stages — no outgoing edges
    SessionLifecycleStage.COMPLETED.value: set(),
    SessionLifecycleStage.TERMINATED.value: set(),
}


class TransitionManager:
    """
    Enforces explicit state transitions for a viva session.

    Parameters
    ----------
    history:
        Linked :class:`SessionHistory` instance.
    """

    def __init__(self, history: SessionHistory) -> None:
        self.history = history

    def is_valid(self, from_stage: str, to_stage: str) -> bool:
        """Return True iff *from_stage → to_stage* is a defined edge."""
        return to_stage in _VALID_EDGES.get(from_stage, set())

    def can_transition(self, to_stage: str, current_stage: str) -> bool:
        return self.is_valid(current_stage, to_stage)

    def validate_transition(self, from_stage: str, to_stage: str) -> None:
        """Raise ``InvalidTransitionError`` if edge is not defined."""
        if not self.is_valid(from_stage, to_stage):
            raise InvalidTransitionError(from_stage, to_stage)

    def get_allowed_transitions(self, current_stage: str) -> Set[str]:
        return set(_VALID_EDGES.get(current_stage, set()))


def is_terminal(stage: str) -> bool:
    return stage in {
        SessionLifecycleStage.COMPLETED.value,
        SessionLifecycleStage.TERMINATED.value,
    }
