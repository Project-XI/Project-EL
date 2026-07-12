from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class AuditEvent:
    event_id: str
    timestamp: datetime
    event_type: str
    roll_number: str
    session_id: Optional[str]
    payload: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "roll_number": self.roll_number,
            "session_id": self.session_id,
            "payload": self.payload,
            "metadata": self.metadata,
        }


class AuditLogService:
    def __init__(self):
        self._logs: List[AuditEvent] = []

    def _generate_event_id(self, roll_number: str, event_type: str, timestamp: datetime) -> str:
        raw = f"{timestamp.isoformat()}:{roll_number}:{event_type}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def log_verification_attempt(
        self,
        roll_number: str,
        session_id: Optional[str],
        capture_info: Dict[str, Any],
        result: str,
        confidence: float,
    ) -> AuditEvent:
        event = AuditEvent(
            event_id=self._generate_event_id(roll_number, "verification_attempt", datetime.now(timezone.utc)),
            timestamp=datetime.now(timezone.utc),
            event_type="verification_attempt",
            roll_number=roll_number,
            session_id=session_id,
            payload={
                "result": result,
                "confidence": confidence,
                "capture": capture_info,
            },
        )
        self._logs.append(event)
        return event

    def log_match(
        self,
        roll_number: str,
        session_id: Optional[str],
        similarity: float,
        confidence: float,
    ) -> AuditEvent:
        event = AuditEvent(
            event_id=self._generate_event_id(roll_number, "face_match", datetime.now(timezone.utc)),
            timestamp=datetime.now(timezone.utc),
            event_type="face_match",
            roll_number=roll_number,
            session_id=session_id,
            payload={
                "similarity": similarity,
                "confidence": confidence,
            },
        )
        self._logs.append(event)
        return event

    def log_mismatch(
        self,
        roll_number: str,
        session_id: Optional[str],
        similarity: float,
        confidence: float,
        threshold: float,
    ) -> AuditEvent:
        event = AuditEvent(
            event_id=self._generate_event_id(roll_number, "face_mismatch", datetime.now(timezone.utc)),
            timestamp=datetime.now(timezone.utc),
            event_type="face_mismatch",
            roll_number=roll_number,
            session_id=session_id,
            payload={
                "similarity": similarity,
                "confidence": confidence,
                "threshold": threshold,
            },
        )
        self._logs.append(event)
        return event

    def log_suspicious_event(
        self,
        roll_number: str,
        session_id: Optional[str],
        reason: str,
        conflict_id: Optional[str] = None,
        matched_rolls: Optional[List[str]] = None,
    ) -> AuditEvent:
        event = AuditEvent(
            event_id=self._generate_event_id(roll_number, "suspicious_identity", datetime.now(timezone.utc)),
            timestamp=datetime.now(timezone.utc),
            event_type="suspicious_identity",
            roll_number=roll_number,
            session_id=session_id,
            payload={
                "reason": reason,
                "conflict_id": conflict_id,
                "matched_rolls": matched_rolls or [],
            },
        )
        self._logs.append(event)
        return event

    def log_admin_override(
        self,
        roll_number: str,
        session_id: Optional[str],
        conflict_id: str,
        reviewer_id: str,
        approved: bool,
        reason: str,
    ) -> AuditEvent:
        event = AuditEvent(
            event_id=self._generate_event_id(roll_number, "admin_override", datetime.now(timezone.utc)),
            timestamp=datetime.now(timezone.utc),
            event_type="admin_override",
            roll_number=roll_number,
            session_id=session_id,
            payload={
                "conflict_id": conflict_id,
                "reviewer_id": reviewer_id,
                "approved": approved,
                "reason": reason,
            },
        )
        self._logs.append(event)
        return event

    def log_examination_access(
        self,
        roll_number: str,
        session_id: str,
        granted: bool,
        reason: Optional[str] = None,
    ) -> AuditEvent:
        event = AuditEvent(
            event_id=self._generate_event_id(roll_number, "examination_access", datetime.now(timezone.utc)),
            timestamp=datetime.now(timezone.utc),
            event_type="examination_access",
            roll_number=roll_number,
            session_id=session_id,
            payload={
                "granted": granted,
                "reason": reason,
            },
        )
        self._logs.append(event)
        return event

    def get_timeline(self, roll_number: Optional[str] = None) -> List[Dict[str, Any]]:
        events = self._logs
        if roll_number:
            events = [e for e in events if e.roll_number == roll_number]
        return [e.to_dict() for e in sorted(events, key=lambda x: x.timestamp)]

    def get_events_by_type(self, event_type: str) -> List[Dict[str, Any]]:
        events = [e for e in self._logs if e.event_type == event_type]
        return [e.to_dict() for e in sorted(events, key=lambda x: x.timestamp)]

    def get_session_timeline(self, session_id: str) -> List[Dict[str, Any]]:
        events = [e for e in self._logs if e.session_id == session_id]
        return [e.to_dict() for e in sorted(events, key=lambda x: x.timestamp)]

    def search(self, query: str) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        results = []
        for event in self._logs:
            payload_str = json.dumps(event.payload).lower()
            if query_lower in payload_str or query_lower in event.roll_number.lower():
                results.append(event.to_dict())
        return results

    def clear(self):
        self._logs.clear()

    def count(self) -> int:
        return len(self._logs)