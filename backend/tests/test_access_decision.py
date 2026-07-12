import pytest
from datetime import datetime, timezone
from backend.src.services.access_decision import (
    ExaminationAccessDecision,
    AccessDecision,
    VerificationOutput,
    IdentityConflictResult,
    SafetyCheck,
    AccessDecisionResult,
)


class TestExaminationAccessDecision:
    def test_decide_access_granted_verified_no_conflict(self):
        decider = ExaminationAccessDecision()
        verification = VerificationOutput(
            verified=True,
            roll_number="R001",
            confidence=0.95,
            timestamp=datetime.now(timezone.utc),
        )

        result = decider.decide(roll_number="R001", verification=verification)

        assert result.decision == AccessDecision.ACCESS_GRANTED
        assert result.reason == "All verification checks passed"
        assert result.confidence == 0.95

    def test_decide_access_denied_verification_failed(self):
        decider = ExaminationAccessDecision()
        verification = VerificationOutput(
            verified=False,
            roll_number="R001",
            confidence=0.30,
            timestamp=datetime.now(timezone.utc),
        )

        result = decider.decide(roll_number="R001", verification=verification)

        assert result.decision == AccessDecision.ACCESS_DENIED
        assert "verification failed" in result.reason.lower()

    def test_decide_manual_review_required_conflict_pending(self):
        decider = ExaminationAccessDecision()
        verification = VerificationOutput(
            verified=True,
            roll_number="R001",
            confidence=0.95,
            timestamp=datetime.now(timezone.utc),
        )
        conflict = IdentityConflictResult(
            has_conflict=True,
            conflict_id="conflict-123",
            matched_rolls=["R002"],
            status="pending_review",
        )

        result = decider.decide(
            roll_number="R001",
            verification=verification,
            conflict=conflict,
        )

        assert result.decision == AccessDecision.MANUAL_REVIEW_REQUIRED
        assert "pending review" in result.reason

    def test_decide_access_denied_conflict_approved(self):
        decider = ExaminationAccessDecision()
        verification = VerificationOutput(
            verified=True,
            roll_number="R001",
            confidence=0.95,
            timestamp=datetime.now(timezone.utc),
        )
        conflict = IdentityConflictResult(
            has_conflict=True,
            conflict_id="conflict-123",
            matched_rolls=["R002"],
            status="approved",
        )

        result = decider.decide(
            roll_number="R001",
            verification=verification,
            conflict=conflict,
        )

        assert result.decision == AccessDecision.ACCESS_DENIED

    def test_decide_access_denied_safety_check_failed(self):
        decider = ExaminationAccessDecision()
        verification = VerificationOutput(
            verified=True,
            roll_number="R001",
            confidence=0.95,
            timestamp=datetime.now(timezone.utc),
        )
        safety_checks = [
            SafetyCheck(name="face_quality", passed=True, message="OK"),
            SafetyCheck(name="environment", passed=False, message="Multiple faces detected"),
        ]

        result = decider.decide(
            roll_number="R001",
            verification=verification,
            safety_checks=safety_checks,
        )

        assert result.decision == AccessDecision.ACCESS_DENIED
        assert "Safety check failed" in result.reason

    def test_decide_temporary_block_blocking_violation(self):
        decider = ExaminationAccessDecision()
        verification = VerificationOutput(
            verified=True,
            roll_number="R001",
            confidence=0.95,
            timestamp=datetime.now(timezone.utc),
        )
        safety_checks = [
            SafetyCheck(name="face_quality", passed=True, message="OK"),
            SafetyCheck(name="block_check", passed=False, message="Temporary block violation"),
        ]

        result = decider.decide(
            roll_number="R001",
            verification=verification,
            safety_checks=safety_checks,
        )

        assert result.decision == AccessDecision.TEMPORARY_BLOCK

    def test_decide_no_verification(self):
        decider = ExaminationAccessDecision()
        result = decider.decide(roll_number="R001")

        assert result.decision == AccessDecision.ACCESS_DENIED
        assert "missing" in result.reason.lower()

    def test_decision_is_deterministic(self):
        decider = ExaminationAccessDecision()
        verification = VerificationOutput(
            verified=True,
            roll_number="R001",
            confidence=0.95,
            timestamp=datetime.now(timezone.utc),
        )

        result1 = decider.decide(roll_number="R001", verification=verification)
        result2 = decider.decide(roll_number="R001", verification=verification)

        assert result1.decision == result2.decision
        assert result1.reason == result2.reason

    def test_decision_has_explainable_evidence(self):
        decider = ExaminationAccessDecision()
        verification = VerificationOutput(
            verified=True,
            roll_number="R001",
            confidence=0.95,
            timestamp=datetime.now(timezone.utc),
        )
        conflict = IdentityConflictResult(
            has_conflict=True,
            conflict_id="conflict-123",
            matched_rolls=["R002"],
            status="pending_review",
        )

        result = decider.decide(
            roll_number="R001",
            verification=verification,
            conflict=conflict,
            session_id="session-1",
        )

        assert "verification" in result.evidence
        assert result.evidence["verification"]["verified"] is True
        assert result.evidence["conflict"]["has_conflict"] is True
        assert result.evidence["session_id"] == "session-1"

    def test_access_decision_result_to_dict(self):
        decider = ExaminationAccessDecision()
        verification = VerificationOutput(
            verified=True,
            roll_number="R001",
            confidence=0.95,
            timestamp=datetime.now(timezone.utc),
        )
        result = decider.decide(roll_number="R001", verification=verification)

        d = result.to_dict()

        assert "decision" in d
        assert "reason" in d
        assert "confidence" in d
        assert "evidence" in d
        assert "decision_id" in d
        assert "timestamp" in d

    def test_get_decision_by_id(self):
        decider = ExaminationAccessDecision()
        verification = VerificationOutput(
            verified=True,
            roll_number="R001",
            confidence=0.95,
            timestamp=datetime.now(timezone.utc),
        )
        result = decider.decide(roll_number="R001", verification=verification)

        found = decider.get_decision(result.decision_id)

        assert found == result
        assert decider.get_decision("nonexistent") is None

    def test_full_approval_flow(self):
        decider = ExaminationAccessDecision()
        verification = VerificationOutput(
            verified=True,
            roll_number="R001",
            confidence=0.95,
            timestamp=datetime.now(timezone.utc),
        )
        safety_checks = [
            SafetyCheck(name="face_quality", passed=True, message="OK"),
            SafetyCheck(name="environment", passed=True, message="Clear"),
        ]

        result = decider.decide(
            roll_number="R001",
            verification=verification,
            safety_checks=safety_checks,
            session_id="exam-123",
        )

        assert result.decision == AccessDecision.ACCESS_GRANTED
        assert result.confidence == 0.95
        assert "exam-123" in str(result.evidence)