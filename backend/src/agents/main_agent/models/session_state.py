from enum import Enum
from typing import Dict, List

from pydantic import BaseModel, Field

from .coverage_state import CoverageState
from .transcript_entry import CandidateResponse, TranscriptEntry


class SessionLifecycle(str, Enum):
    INITIALIZED = "initialized"
    ACTIVE = "active"
    INTERRUPTED = "interrupted"
    COMPLETED = "completed"
    TERMINATED = "terminated"


class ContradictionEntry(BaseModel):
    turn_id: int
    detail: str


class SessionTransition(BaseModel):
    from_stage: SessionLifecycle
    to_stage: SessionLifecycle


class SessionState(BaseModel):
    schema_version: int = 1
    session_id: str
    lifecycle_stage: SessionLifecycle = SessionLifecycle.INITIALIZED
    next_turn_id: int = 1
    question_history: List[TranscriptEntry] = Field(default_factory=list)
    response_history: List[CandidateResponse] = Field(default_factory=list)
    contradiction_history: List[ContradictionEntry] = Field(default_factory=list)
    weak_areas: Dict[str, int] = Field(default_factory=dict)
    coverage_state: CoverageState = Field(default_factory=CoverageState)
    follow_up_chains: Dict[str, List[int]] = Field(default_factory=dict)
    transitions: List[SessionTransition] = Field(default_factory=list)
