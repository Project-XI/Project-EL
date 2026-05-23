from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TranscriptEventKind(str, Enum):
    QUESTION = "question"
    ANSWER = "answer"
    EVALUATION = "evaluation"
    CONTRADICTION = "contradiction"
    FAIRNESS = "fairness"
    FOLLOW_UP = "follow_up"
    STATE_TRANSITION = "state_transition"
    TOPIC_COVERAGE = "topic_coverage"
    SESSION_NOTE = "session_note"


class TranscriptEventRecord(BaseModel):
    event_id: str
    session_id: str
    step_id: str
    order_index: int
    kind: TranscriptEventKind
    payload: Dict[str, Any] = Field(default_factory=dict)
    evidence_links: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TranscriptTurnRecord(BaseModel):
    turn_id: str
    session_id: str
    step_id: str
    order_index: int
    question_text: str
    answer_text: Optional[str] = None
    normalized_answer_text: Optional[str] = None
    evaluation: Optional[Dict[str, Any]] = None
    contradiction_events: List[Dict[str, Any]] = Field(default_factory=list)
    fairness_events: List[Dict[str, Any]] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    evidence_links: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TranscriptRecord(BaseModel):
    schema_version: str = "1.0"
    session_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    turns: List[TranscriptTurnRecord] = Field(default_factory=list)
    events: List[TranscriptEventRecord] = Field(default_factory=list)
    session_state: Dict[str, Any] = Field(default_factory=dict)
    export_metadata: Dict[str, Any] = Field(default_factory=dict)
