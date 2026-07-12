from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib

from backend.src.services.audit_log import AuditLogService
from backend.src.services.identity_history import IdentityHistoryStore


@dataclass
class ReviewConflict:
    conflict_id: str
    roll_number: str
    session_id: Optional[str]
    matched_roll_numbers: List[str]
    confidence_scores: List[float]
    timestamp: datetime
    status: str = "pending_review"
    reviewer_id: Optional[str] = None
    review_timestamp: Optional[datetime] = None
    review_reason: Optional[str] = None
    prior_face_history: Optional[List[Dict[str, Any]]] = None
    new_face_history: Optional[List[Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "roll_number": self.roll_number,
            "session_id": self.session_id,
            "matched_roll_numbers": self.matched_roll_numbers,
            "confidence_scores": self.confidence_scores,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
            "reviewer_id": self.reviewer_id,
            "review_timestamp": self.review_timestamp.isoformat() if self.review_timestamp else None,
            "review_reason": self.review_reason,
            "prior_face_history": self.prior_face_history,
            "new_face_history": self.new_face_history,
        }


class AdminReviewWorkflow:
    def __init__(
        self,
        audit_log: Optional[AuditLogService] = None,
        identity_history: Optional[IdentityHistoryStore] = None,
    ):
        self._conflicts: Dict[str, ReviewConflict] = {}
        self._audit_log = audit_log or AuditLogService()
        self._identity_history = identity_history or IdentityHistoryStore()

    def _generate_conflict_id(self, roll_number: str, matched_rolls: List[str], timestamp: datetime) -> str:
        sorted_rolls = sorted([roll_number] + matched_rolls)
        raw = f"{timestamp.isoformat()}:{','.join(sorted_rolls)}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]

    def flag_conflict(
        self,
        roll_number: str,
        matched_roll_numbers: List[str],
        confidence_scores: List[float],
        session_id: Optional[str] = None,
    ) -> ReviewConflict:
        timestamp = datetime.now(timezone.utc)
        conflict_id = self._generate_conflict_id(roll_number, matched_roll_numbers, timestamp)

        prior_history = []
        for matched_roll in matched_roll_numbers:
            records = self._identity_history.get_history_for_roll(matched_roll)
            prior_history.extend([r.to_dict() for r in records])

        conflict = ReviewConflict(
            conflict_id=conflict_id,
            roll_number=roll_number,
            session_id=session_id,
            matched_roll_numbers=matched_roll_numbers,
            confidence_scores=confidence_scores,
            timestamp=timestamp,
            prior_face_history=prior_history if prior_history else None,
        )
        self._conflicts[conflict_id] = conflict

        self._audit_log.log_suspicious_event(
            roll_number=roll_number,
            session_id=session_id,
            reason=f"Identity conflict with {matched_roll_numbers}",
            conflict_id=conflict_id,
            matched_rolls=matched_roll_numbers,
        )

        return conflict

    def get_pending_conflicts(self) -> List[ReviewConflict]:
        return [c for c in self._conflicts.values() if c.status == "pending_review"]

    def get_conflict_details(self, conflict_id: str) -> Optional[Dict[str, Any]]:
        conflict = self._conflicts.get(conflict_id)
        if not conflict:
            return None

        prior_history = []
        for matched_roll in conflict.matched_roll_numbers:
            records = self._identity_history.get_history_for_roll(matched_roll)
            prior_history.extend([r.to_dict() for r in records])

        new_history = self._identity_history.get_history_for_roll(conflict.roll_number)

        return {
            "conflict": conflict.to_dict(),
            "prior_embeddings": prior_history,
            "new_embedding_history": [r.to_dict() for r in new_history],
        }

    def approve_conflict(
        self,
        conflict_id: str,
        reviewer_id: str,
        reason: str,
        session_id: Optional[str] = None,
    ) -> bool:
        conflict = self._conflicts.get(conflict_id)
        if not conflict:
            return False

        conflict.status = "approved"
        conflict.reviewer_id = reviewer_id
        conflict.review_timestamp = datetime.now(timezone.utc)
        conflict.review_reason = reason

        self._audit_log.log_admin_override(
            roll_number=conflict.roll_number,
            session_id=session_id or conflict.session_id,
            conflict_id=conflict_id,
            reviewer_id=reviewer_id,
            approved=True,
            reason=reason,
        )

        self._audit_log.log_examination_access(
            roll_number=conflict.roll_number,
            session_id=session_id or conflict.session_id or "unknown",
            granted=True,
            reason=f"Admin approved after review: {reason}",
        )

        return True

    def reject_conflict(
        self,
        conflict_id: str,
        reviewer_id: str,
        reason: str,
        session_id: Optional[str] = None,
    ) -> bool:
        conflict = self._conflicts.get(conflict_id)
        if not conflict:
            return False

        conflict.status = "rejected"
        conflict.reviewer_id = reviewer_id
        conflict.review_timestamp = datetime.now(timezone.utc)
        conflict.review_reason = reason

        self._audit_log.log_admin_override(
            roll_number=conflict.roll_number,
            session_id=session_id or conflict.session_id,
            conflict_id=conflict_id,
            reviewer_id=reviewer_id,
            approved=False,
            reason=reason,
        )

        self._audit_log.log_examination_access(
            roll_number=conflict.roll_number,
            session_id=session_id or conflict.session_id or "unknown",
            granted=False,
            reason=f"Admin rejected after review: {reason}",
        )

        return True

    def get_override_actions(self) -> List[Dict[str, Any]]:
        return [c.to_dict() for c in self._conflicts.values() if c.status in ("approved", "rejected")]

    def get_conflict_by_id(self, conflict_id: str) -> Optional[ReviewConflict]:
        return self._conflicts.get(conflict_id)

    def clear_resolved(self):
        self._conflicts = {k: v for k, v in self._conflicts.items() if v.status == "pending_review"}