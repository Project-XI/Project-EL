from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone
import hashlib


class AccessDecision(str, Enum):
    ACCESS_GRANTED = "ACCESS_GRANTED"
    ACCESS_DENIED = "ACCESS_DENIED"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"
    TEMPORARY_BLOCK = "TEMPORARY_BLOCK"


@dataclass
class VerificationOutput:
    verified: bool
    roll_number: str
    confidence: float
    timestamp: datetime


@dataclass
class IdentityConflictResult:
    has_conflict: bool
    conflict_id: Optional[str]
    matched_rolls: List[str]
    status: str


@dataclass
class SafetyCheck:
    name: str
    passed: bool
    message: str


@dataclass
class AccessDecisionResult:
    decision: AccessDecision
    reason: str
    confidence: float
    evidence: Dict[str, Any]
    decision_id: str
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason": self.reason,
            "confidence": round(self.confidence, 4),
            "evidence": self.evidence,
            "decision_id": self.decision_id,
            "timestamp": self.timestamp.isoformat(),
        }


class ExaminationAccessDecision:
    def __init__(self):
        self._decisions: Dict[str, AccessDecisionResult] = {}

    def _generate_decision_id(
        self, roll_number: str, decision: AccessDecision, timestamp: datetime
    ) -> str:
        raw = f"{timestamp.isoformat()}:{roll_number}:{decision.value}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def decide(
        self,
        roll_number: str,
        verification: Optional[VerificationOutput] = None,
        conflict: Optional[IdentityConflictResult] = None,
        safety_checks: Optional[List[SafetyCheck]] = None,
        session_id: Optional[str] = None,
    ) -> AccessDecisionResult:
        timestamp = datetime.now(timezone.utc)
        evidence: Dict[str, Any] = {
            "session_id": session_id,
            "verification": None,
            "conflict": None,
            "safety_checks": [],
        }

        if verification:
            evidence["verification"] = {
                "verified": verification.verified,
                "confidence": verification.confidence,
                "timestamp": verification.timestamp.isoformat(),
            }

        if conflict:
            evidence["conflict"] = {
                "has_conflict": conflict.has_conflict,
                "conflict_id": conflict.conflict_id,
                "matched_rolls": conflict.matched_rolls,
                "status": conflict.status,
            }

        if safety_checks:
            evidence["safety_checks"] = [
                {"name": sc.name, "passed": sc.passed, "message": sc.message}
                for sc in safety_checks
            ]

        if not verification or not verification.verified:
            decision = AccessDecision.ACCESS_DENIED
            reason = "Identity verification failed or missing"
            confidence = 0.0
        elif conflict and conflict.has_conflict:
            if conflict.status == "pending_review":
                decision = AccessDecision.MANUAL_REVIEW_REQUIRED
                reason = f"Identity conflict pending review: {conflict.conflict_id}"
            else:
                decision = AccessDecision.ACCESS_DENIED
                reason = f"Identity conflict detected with: {', '.join(conflict.matched_rolls)}"
            confidence = 0.5
        elif safety_checks:
            failed_checks = [sc for sc in safety_checks if not sc.passed]
            if failed_checks:
                if any("block" in sc.message.lower() for sc in failed_checks):
                    decision = AccessDecision.TEMPORARY_BLOCK
                    reason = f"Safety violation: {failed_checks[0].message}"
                else:
                    decision = AccessDecision.ACCESS_DENIED
                    reason = f"Safety check failed: {failed_checks[0].message}"
                confidence = 0.3
            else:
                decision = AccessDecision.ACCESS_GRANTED
                reason = "All checks passed"
                confidence = 0.95
        else:
            decision = AccessDecision.ACCESS_GRANTED
            reason = "All verification checks passed"
            confidence = 0.95

        decision_id = self._generate_decision_id(roll_number, decision, timestamp)
        result = AccessDecisionResult(
            decision=decision,
            reason=reason,
            confidence=confidence,
            evidence=evidence,
            decision_id=decision_id,
            timestamp=timestamp,
        )

        self._decisions[decision_id] = result
        return result

    def get_decision(self, decision_id: str) -> Optional[AccessDecisionResult]:
        return self._decisions.get(decision_id)

    def get_decisions_for_roll(self, roll_number: str) -> List[AccessDecisionResult]:
        return [
            d for d in self._decisions.values()
            if roll_number in str(d.evidence.get("verification", {}))
        ]

    def clear(self):
        self._decisions.clear()