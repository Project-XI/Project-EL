"""
access_decision.py
──────────────────
Final output of the GATEKEEPER Authorization Engine.

Rules
─────
- Frozen dataclass — immutable after creation.
- Fully serializable.
- Contains the final go/no-go decision and the audit trail explaining why.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class DecisionStatus(str, Enum):
    GRANTED              = "granted"
    DENIED               = "denied"
    PENDING_ADMIN_REVIEW = "pending_admin_review"


@dataclass(frozen=True)
class AccessDecision:
    """
    Final authorization decision for a viva session request.

    Fields
    ──────
    decision              : GRANTED, DENIED, or PENDING_ADMIN_REVIEW.
    roll_number           : The requested roll number (or raw input if invalid).
    student_name          : The resolved student name (if available).
    reasons               : List of human-readable explanations for the decision.
    requires_admin_review : True if the session is halted pending staff override.
    audit_trail           : Dump of all pipeline stage results for logging.
    """
    decision:              DecisionStatus
    roll_number:           str
    student_name:          str
    reasons:               List[str]       = field(default_factory=list)
    requires_admin_review: bool            = False
    audit_trail:           Dict[str, Any]  = field(default_factory=dict)

    @property
    def is_granted(self) -> bool:
        return self.decision == DecisionStatus.GRANTED

    @property
    def is_denied(self) -> bool:
        return self.decision == DecisionStatus.DENIED

    def to_dict(self) -> dict:
        return {
            "decision":              self.decision.value,
            "roll_number":           self.roll_number,
            "student_name":          self.student_name,
            "reasons":               self.reasons,
            "requires_admin_review": self.requires_admin_review,
            "is_granted":            self.is_granted,
            "audit_trail":           self.audit_trail,
        }
