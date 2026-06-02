from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

from src.agents.gatekeeper.registry.lookup import RegistryLookup
from src.agents.gatekeeper.registry.registry_store import StudentRegistry
from src.agents.oracle.agent import OracleAgent
from src.core.events import EventEmitter
from src.models.events import EventType
from src.models.exam_session import (
    ExamRubric,
    ExamSession,
    ExamSessionConfig,
    ExamSessionState,
    GatekeeperAdmissionDecision,
    SessionAuditEvent,
    SessionTimingWindow,
    StudentSubmission,
)


ALLOWED_TRANSITIONS = {
    ExamSessionState.DRAFT: {ExamSessionState.CONFIGURED},
    ExamSessionState.CONFIGURED: {ExamSessionState.READY},
    ExamSessionState.READY: {ExamSessionState.LIVE},
    ExamSessionState.LIVE: {ExamSessionState.ACTIVE_VIVA, ExamSessionState.COMPLETED},
    ExamSessionState.ACTIVE_VIVA: {ExamSessionState.COMPLETED},
    ExamSessionState.COMPLETED: {ExamSessionState.ARCHIVED},
    ExamSessionState.ARCHIVED: set(),
}


class SessionTransitionError(ValueError):
    pass


class ExamSessionService:
    def __init__(self, storage_dir: Optional[str] = None, registry: Optional[StudentRegistry] = None) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        default_dir = repo_root / "data" / "exam_sessions"
        self.storage_dir = Path(storage_dir) if storage_dir else default_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.registry = registry or StudentRegistry()
        self.lookup = RegistryLookup(self.registry)
        self.oracle = OracleAgent()

    def create_session(
        self,
        admin_id: str,
        title: str,
        config: Optional[ExamSessionConfig] = None,
    ) -> ExamSession:
        session = ExamSession(
            session_id=f"ES-{uuid4().hex[:10].upper()}",
            admin_id=admin_id,
            title=title,
            config=config,
            state=ExamSessionState.CONFIGURED if config else ExamSessionState.DRAFT,
        )
        self._append_audit(session, "session_created", "admin", {"admin_id": admin_id, "title": title})
        self._emit(session.session_id, EventType.SESSION_CREATED, {"state": session.state.value, "title": title})
        if config:
            self._emit(session.session_id, EventType.SESSION_CONFIGURED, {"state": session.state.value})
        self._save(session)
        return session

    def list_sessions(self) -> List[ExamSession]:
        sessions: List[ExamSession] = []
        for path in sorted(self.storage_dir.glob("*.json")):
            loaded = self._load(path.stem)
            if loaded is not None:
                sessions.append(loaded)
        return sessions

    def get_session(self, session_id: str) -> Optional[ExamSession]:
        return self._load(session_id)

    def configure_session(self, session_id: str, config: ExamSessionConfig) -> ExamSession:
        session = self._require(session_id)
        if session.state not in {ExamSessionState.DRAFT, ExamSessionState.CONFIGURED}:
            raise SessionTransitionError(f"Cannot configure session in state {session.state.value}")
        session.config = config
        session.state = ExamSessionState.CONFIGURED
        session.touch()
        self._append_audit(session, "session_configured", "admin", config.model_dump(mode="json"))
        self._emit(session.session_id, EventType.SESSION_CONFIGURED, {"state": session.state.value, "title": session.title})
        self._save(session)
        return session

    def assign_students(self, session_id: str, submissions: Iterable[StudentSubmission]) -> ExamSession:
        session = self._require(session_id)
        session.assigned_students = list(submissions)
        session.touch()
        self._append_audit(session, "students_assigned", "admin", {"count": len(session.assigned_students)})
        self._save(session)
        return session

    def set_ready(self, session_id: str) -> ExamSession:
        session = self._require(session_id)
        if not session.config:
            raise SessionTransitionError("Session must be configured before it can be marked ready.")
        if not session.assigned_students:
            raise SessionTransitionError("Session must have assigned students before it can be marked ready.")
        self._transition(session, ExamSessionState.READY, actor="admin", event_type=EventType.SESSION_READY)
        self._save(session)
        return session

    def activate_session(self, session_id: str, actor: str = "admin") -> ExamSession:
        session = self._require(session_id)
        if session.state != ExamSessionState.READY:
            raise SessionTransitionError("Only READY sessions can be activated.")
        session.activated_at = session.activated_at or datetime.utcnow()
        self._transition(session, ExamSessionState.LIVE, actor=actor, event_type=EventType.SESSION_LIVE)
        self._save(session)
        return session

    def gatekeeper_precheck(self, session_id: str, roll_number: str, actor: str = "gatekeeper") -> GatekeeperAdmissionDecision:
        session = self._require(session_id)
        normalized_roll = roll_number.strip().upper()
        lookup_result = self.lookup.by_roll_number(normalized_roll)
        submission = next((item for item in session.assigned_students if item.roll_number == lookup_result.roll_number), None)
        duplicate_join = lookup_result.roll_number in session.admitted_roll_numbers
        timing_valid = self._is_within_timing_window(session)
        session_live = session.state in {ExamSessionState.LIVE, ExamSessionState.ACTIVE_VIVA}
        submission_present = submission is not None

        admitted = all([session_live, lookup_result.success, timing_valid, submission_present, not duplicate_join])
        reason = None
        if not session_live:
            reason = f"session_not_live:{session.state.value}"
        elif not lookup_result.success:
            reason = f"student_lookup_failed:{lookup_result.failure_reason.value if lookup_result.failure_reason else 'unknown'}"
        elif not timing_valid:
            reason = "outside_allowed_timing_window"
        elif not submission_present:
            reason = "required_submission_missing"
        elif duplicate_join:
            reason = "duplicate_session_join"

        decision = GatekeeperAdmissionDecision(
            session_id=session_id,
            student_roll_number=lookup_result.roll_number or normalized_roll,
            admitted=admitted,
            reason=reason,
            session_state=session.state,
            timing_valid=timing_valid,
            submission_present=submission_present,
            duplicate_join=duplicate_join,
            suspicious=not admitted,
            metadata={
                "student_found": lookup_result.success,
                "student_name": lookup_result.profile.full_name if lookup_result.profile else None,
                "submission_repository_url": submission.repository_url if submission else None,
            },
        )
        session.gatekeeper_decisions.append(decision)
        self._append_audit(
            session,
            "student_admitted" if admitted else "student_rejected",
            actor,
            decision.model_dump(mode="json"),
        )
        self._emit(
            session_id,
            EventType.STUDENT_ADMITTED if admitted else EventType.STUDENT_REJECTED,
            decision.model_dump(mode="json"),
        )
        if admitted:
            session.admitted_roll_numbers.append(decision.student_roll_number)
            session.active_student_roll_number = decision.student_roll_number
            if session.state == ExamSessionState.LIVE:
                self._transition(session, ExamSessionState.ACTIVE_VIVA, actor=actor, event_type=EventType.SESSION_ACTIVE_VIVA)
        self._save(session)
        return decision

    async def start_oracle_analysis(self, session_id: str, roll_number: str, actor: str = "oracle") -> ExamSession:
        session = self._require(session_id)
        if session.state not in {ExamSessionState.LIVE, ExamSessionState.ACTIVE_VIVA}:
            raise SessionTransitionError("ORACLE analysis can only start after the session is live and the student is admitted.")

        normalized_roll = roll_number.strip().upper()
        decision = next((item for item in reversed(session.gatekeeper_decisions) if item.student_roll_number == normalized_roll), None)
        if decision is None or not decision.admitted:
            raise SessionTransitionError("Gatekeeper admission is required before ORACLE analysis can begin.")

        session.oracle_status = "running"
        session.oracle_started_at = session.oracle_started_at or datetime.utcnow()
        self._append_audit(session, "oracle_analysis_started", actor, {"roll_number": normalized_roll})
        self._emit(session_id, EventType.ORACLE_ANALYSIS_STARTED, {"roll_number": normalized_roll})

        submission = next((item for item in session.assigned_students if item.roll_number == normalized_roll), None)
        payload = {
            "repo_url": submission.repository_url if submission else None,
            "report_path": submission.document_paths[0] if submission and submission.document_paths else None,
            "roll_number": normalized_roll,
        }
        context = await self.oracle.process(session_id, payload)
        artifacts = context.model_dump() if hasattr(context, "model_dump") else context.dict()
        session.analysis_artifacts.append({
            "artifact_type": "oracle_context",
            "payload": artifacts,
        })
        session.oracle_completed_at = datetime.utcnow()
        session.oracle_status = "completed"
        self._append_audit(session, "oracle_analysis_completed", actor, {"roll_number": normalized_roll})
        self._emit(session_id, EventType.ORACLE_ANALYSIS_COMPLETED, {"roll_number": normalized_roll})
        self._save(session)
        return session

    def complete_session(self, session_id: str, actor: str = "admin") -> ExamSession:
        session = self._require(session_id)
        if session.state not in {ExamSessionState.ACTIVE_VIVA, ExamSessionState.LIVE, ExamSessionState.READY}:
            raise SessionTransitionError(f"Cannot complete session in state {session.state.value}")
        session.completed_at = session.completed_at or datetime.utcnow()
        self._transition(session, ExamSessionState.COMPLETED, actor=actor, event_type=EventType.SESSION_COMPLETED)
        self._save(session)
        return session

    def archive_session(self, session_id: str, actor: str = "admin") -> ExamSession:
        session = self._require(session_id)
        if session.state != ExamSessionState.COMPLETED:
            raise SessionTransitionError("Only completed sessions can be archived.")
        session.archived_at = session.archived_at or datetime.utcnow()
        self._transition(session, ExamSessionState.ARCHIVED, actor=actor, event_type=EventType.SESSION_ARCHIVED)
        self._save(session)
        return session

    def _is_within_timing_window(self, session: ExamSession) -> bool:
        config = session.config
        if not config or not config.timing_window.opens_at or not config.timing_window.closes_at:
            return True
        now = datetime.utcnow()
        return config.timing_window.opens_at <= now <= config.timing_window.closes_at

    def _transition(self, session: ExamSession, new_state: ExamSessionState, actor: str, event_type: EventType) -> None:
        allowed = ALLOWED_TRANSITIONS.get(session.state, set())
        if new_state not in allowed:
            raise SessionTransitionError(f"Invalid transition from {session.state.value} to {new_state.value}")
        previous_state = session.state
        session.state = new_state
        session.touch()
        self._append_audit(session, f"transition:{new_state.value.lower()}", actor, {"from": previous_state.value, "to": new_state.value})
        self._emit(session.session_id, event_type, {"state": new_state.value, "previous_state": previous_state.value, "actor": actor})

    def _append_audit(self, session: ExamSession, event_type: str, actor: str, payload: Dict[str, Any]) -> None:
        session.audit_events.append(
            SessionAuditEvent(
                session_id=session.session_id,
                event_type=event_type,
                actor=actor,
                payload=payload,
            )
        )
        session.touch()

    def _emit(self, session_id: str, event_type: EventType, payload: Dict[str, Any]) -> None:
        try:
            EventEmitter.emit(
                session_id=session_id,
                agent_name="ExamSession",
                event_type=event_type,
                payload=payload,
            )
        except Exception:
            pass

    def _session_path(self, session_id: str) -> Path:
        return self.storage_dir / f"{session_id}.json"

    def _save(self, session: ExamSession) -> None:
        with self._session_path(session.session_id).open("w", encoding="utf-8") as handle:
            json.dump(session.model_dump(mode="json"), handle, indent=2, sort_keys=True, default=str)

    def _load(self, session_id: str) -> Optional[ExamSession]:
        path = self._session_path(session_id)
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as handle:
            return ExamSession.model_validate(json.load(handle))

    def _require(self, session_id: str) -> ExamSession:
        session = self._load(session_id)
        if session is None:
            raise SessionTransitionError(f"Unknown exam session: {session_id}")
        return session
