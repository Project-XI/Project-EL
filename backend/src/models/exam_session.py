from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field


class ExamSessionState(str, Enum):
    DRAFT = "DRAFT"
    CONFIGURED = "CONFIGURED"
    READY = "READY"
    LIVE = "LIVE"
    ACTIVE_VIVA = "ACTIVE_VIVA"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class SessionTimingWindow(BaseModel):
    opens_at: Optional[datetime] = None
    closes_at: Optional[datetime] = None
    viva_duration_minutes: int = Field(default=15, ge=1, le=240)
    check_in_grace_minutes: int = Field(default=5, ge=0, le=60)


class RubricCriterion(BaseModel):
    name: str
    description: Optional[str] = None
    max_score: int = Field(default=10, ge=1, le=100)


class ExamRubric(BaseModel):
    title: str = "Default Viva Rubric"
    criteria: List[RubricCriterion] = Field(default_factory=list)


class StudentSubmission(BaseModel):
    roll_number: str
    repository_url: Optional[str] = None
    document_paths: List[str] = Field(default_factory=list)
    batch_label: Optional[str] = None
    assignment_state: str = "assigned"


class ExamSessionConfig(BaseModel):
    subject: str
    course: str
    semester: str
    subject_code: Optional[str] = None
    academic_year: Optional[str] = None
    department: Optional[str] = None
    instructor_name: Optional[str] = None
    exam_coordinator: Optional[str] = None
    timing_window: SessionTimingWindow = Field(default_factory=SessionTimingWindow)
    rubric: ExamRubric = Field(default_factory=ExamRubric)
    notes: Optional[str] = None


class SessionAuditEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: str
    event_type: str
    actor: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class GatekeeperAdmissionDecision(BaseModel):
    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: str
    student_roll_number: str
    admitted: bool
    reason: Optional[str] = None
    session_state: ExamSessionState
    timing_valid: bool = False
    submission_present: bool = False
    duplicate_join: bool = False
    suspicious: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExamSession(BaseModel):
    session_id: str
    admin_id: str
    title: str = "Untitled Viva Session"
    state: ExamSessionState = ExamSessionState.DRAFT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    activated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    config: Optional[ExamSessionConfig] = None
    assigned_students: List[StudentSubmission] = Field(default_factory=list)
    gatekeeper_decisions: List[GatekeeperAdmissionDecision] = Field(default_factory=list)
    analysis_artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    audit_events: List[SessionAuditEvent] = Field(default_factory=list)
    admitted_roll_numbers: List[str] = Field(default_factory=list)
    active_student_roll_number: Optional[str] = None
    oracle_started_at: Optional[datetime] = None
    oracle_completed_at: Optional[datetime] = None
    oracle_status: str = "not_started"

    def touch(self) -> None:
        self.updated_at = datetime.utcnow()
