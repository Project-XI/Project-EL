"""
Stage 7-9 Runtime Models

Deterministic, evidence-grounded models for:
- Stage 7 SENTINEL integrity oversight
- Stage 8 MAIN evaluation loop artifacts
- Stage 9 curriculum-linked questioning
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class IntegritySignalType(str, Enum):
    PROLONGED_OFFSCREEN_FOCUS = "prolonged_offscreen_focus"
    REPEATED_GAZE_SHIFT = "repeated_gaze_shift"
    SESSION_INTERRUPTION = "session_interruption"
    SUSPICIOUS_AUDIO_PATTERN = "suspicious_audio_pattern"
    LOW_VISIBILITY_WARNING = "low_visibility_warning"
    CONTRADICTION_ESCALATION = "contradiction_escalation"
    CONFIDENCE_INSTABILITY = "confidence_instability"
    EXCESSIVE_SILENCE_PATTERN = "excessive_silence_pattern"
    ENVIRONMENT_CHANGE = "environment_change"


class IntegritySeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class SentinelIntegrityEvent(BaseModel):
    event_id: str
    session_id: str
    signal_type: IntegritySignalType
    severity: IntegritySeverity
    observed_at: datetime = Field(default_factory=datetime.utcnow)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    explanation: str
    replay_metadata: Dict[str, Any] = Field(default_factory=dict)


class SentinelAlert(BaseModel):
    alert_id: str
    session_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    event_ids: List[str] = Field(default_factory=list)
    manual_review_recommended: bool = False
    reason: str


class ContradictionChainEntry(BaseModel):
    chain_id: str
    target_id: str
    previous_claim: str
    current_claim: str
    severity: str
    turn_index: int
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class EvaluationArtifact(BaseModel):
    session_id: str
    turn_index: int
    target_id: str
    implementation_specificity: float
    runtime_understanding: float
    operational_reasoning: float
    architectural_understanding: float
    failure_path_awareness: float
    tradeoff_understanding: float
    consistency_score: float
    implementation_familiarity: float
    topic_coverage: Dict[str, float] = Field(default_factory=dict)
    weak_areas: List[str] = Field(default_factory=list)
    follow_up_chain: List[str] = Field(default_factory=list)
    contradiction_chain: List[ContradictionChainEntry] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CoreSubject(str, Enum):
    DSA = "DSA"
    DBMS = "DBMS"
    OPERATING_SYSTEMS = "OPERATING_SYSTEMS"
    COMPUTER_NETWORKS = "COMPUTER_NETWORKS"
    OOP = "OOP"
    SOFTWARE_ENGINEERING = "SOFTWARE_ENGINEERING"
    SYSTEM_DESIGN = "SYSTEM_DESIGN"
    CLOUD_DEVOPS = "CLOUD_DEVOPS"


class CurriculumQuestion(BaseModel):
    question_id: str
    subject: CoreSubject
    prompt: str
    linked_implementation_signal: str
    difficulty: str
    expected_coverage: List[str] = Field(default_factory=list)


class CurriculumTransitionState(BaseModel):
    session_id: str
    transition_started_at: datetime = Field(default_factory=datetime.utcnow)
    started: bool = False
    completed_subjects: List[CoreSubject] = Field(default_factory=list)
    asked_questions: List[str] = Field(default_factory=list)
