"""
VivaSessionManager — persistent, replay-safe session state layer for the
MAIN Agent.

Public API
----------
VivaSessionState
    Top-level coordinator owned exclusively by MAIN.
SessionHistory
    Ordinal Q&A history with guaranteed ordering.
CoverageState
    Topic coverage tracker.
SessionLifecycleStage
    Enum of valid session lifecycle stages.
TransitionManager
    FSM-based state-transition validator.
SessionPersistence
    Storage-adapter factory / interface.
"""

# Models
from .models.session_state import (
    SessionLifecycleStage,
    SessionState,
    WeakAreaRecord,
    ContradictionEntry,
    FollowUpRecord,
    RecordedQuestion,
    RecordedResponse,
)
from .models.transcript_entry import TranscriptEntry
from .models.coverage_state import CoverageState, TopicCoverage

# Session layer
from .session.history import SessionHistory
from .session.transitions import TransitionManager, InvalidTransitionError, is_terminal
from .session.state import VivaSessionState
from .session.persistence import (
    SessionPersistence,
    in_memory_persistence,
    file_system_persistence,
)

__all__ = [
    # Enums / constants
    "SessionLifecycleStage",
    # Durable state
    "SessionState",
    "TranscriptEntry",
    "CoverageState",
    "TopicCoverage",
    "WeakAreaRecord",
    "ContradictionEntry",
    "FollowUpRecord",
    "RecordedQuestion",
    "RecordedResponse",
    # Session layer
    "SessionHistory",
    "TransitionManager",
    "VivaSessionState",
    "SessionPersistence",
    "in_memory_persistence",
    "file_system_persistence",
]
