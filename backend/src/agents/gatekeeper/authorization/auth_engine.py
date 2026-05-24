"""
auth_engine.py
──────────────
Authorization Engine for the GATEKEEPER pipeline.

Responsibilities
────────────────
- Consume the results of all prior pipeline stages (Roll verification, Face verification, Conflict detection).
- Apply final business rules to determine if the session should be GRANTED, DENIED, or PENDING_ADMIN_REVIEW.
- Compile the final AccessDecision with a complete audit trail.

Rules
─────
- Pure logic — evaluates inputs and emits a decision.
- Deterministic and auditable.
- Never raises.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from src.agents.gatekeeper.conflict_detection.conflict_detector import ConflictReport, ConflictSeverity
from src.agents.gatekeeper.face_verification.face_result import FaceVerificationResult
from src.agents.gatekeeper.roll_verification.flow import VerificationFlowResult
from .access_decision import AccessDecision, DecisionStatus

logger = logging.getLogger(__name__)


class AuthorizationEngine:
    """
    Final decision maker for the GATEKEEPER pipeline.

    Rules:
    1. If roll verification failed (invalid, not found, inactive) -> DENIED.
    2. If conflict severity is CRITICAL (face clone) -> DENIED.
    3. If conflict severity is HIGH (face swap) -> DENIED.
    4. If face verification failed -> PENDING_ADMIN_REVIEW (or DENIED based on strictness).
       * We use DENIED for NO_PHOTO or UNVERIFIABLE, but PENDING_ADMIN_REVIEW for MISMATCH if we want staff to verify.
       * For this implementation, we will DENY hard on MISMATCH to be strict, but leave a path for admin override.
    5. If admin flagged required -> PENDING_ADMIN_REVIEW.
    6. Else -> GRANTED.
    """

    def evaluate(
        self,
        roll_result: VerificationFlowResult,
        face_result: FaceVerificationResult,
        conflict_report: ConflictReport,
    ) -> AccessDecision:
        """
        Evaluate all stage outputs and return a final AccessDecision.
        """
        reasons = []
        roll_number = roll_result.roll_number
        student_name = roll_result.display_card.full_name if roll_result.display_card else "Unknown"
        
        # Build audit trail
        audit_trail: Dict[str, Any] = {
            "roll_verification": roll_result.to_dict(),
            "face_verification": face_result.to_dict(),
            "conflict_detection": conflict_report.to_dict(),
        }

        # ── Rule 1: Roll Verification Failure ─────────────────────────────────
        if roll_result.is_rejected:
            reasons.append(roll_result.message)
            return AccessDecision(
                decision=DecisionStatus.DENIED,
                roll_number=roll_number,
                student_name=student_name,
                reasons=reasons,
                audit_trail=audit_trail,
            )

        # ── Rule 2: Manual Review Flag ────────────────────────────────────────
        if roll_result.requires_manual:
            reasons.append("Manual staff verification requested.")
            return AccessDecision(
                decision=DecisionStatus.PENDING_ADMIN_REVIEW,
                roll_number=roll_number,
                student_name=student_name,
                reasons=reasons,
                requires_admin_review=True,
                audit_trail=audit_trail,
            )

        # ── Rule 3: Identity Conflicts ────────────────────────────────────────
        if conflict_report.has_conflict:
            reasons.append(conflict_report.reason)
            if conflict_report.severity in (ConflictSeverity.CRITICAL, ConflictSeverity.HIGH):
                # Hard block for severe conflicts
                return AccessDecision(
                    decision=DecisionStatus.DENIED,
                    roll_number=roll_number,
                    student_name=student_name,
                    reasons=reasons,
                    audit_trail=audit_trail,
                )
            elif conflict_report.severity == ConflictSeverity.MEDIUM:
                # Soft block for suspicious but not guaranteed fraud
                return AccessDecision(
                    decision=DecisionStatus.PENDING_ADMIN_REVIEW,
                    roll_number=roll_number,
                    student_name=student_name,
                    reasons=reasons,
                    requires_admin_review=True,
                    audit_trail=audit_trail,
                )

        # ── Rule 4: Face Verification Failure ─────────────────────────────────
        if not face_result.matched:
            reasons.append(face_result.reason)
            # If it's a mismatch but no fraud detected, we might want admin review
            # For strictness, if confidence is 0, we deny. But let's route mismatch to admin review.
            if face_result.status.value == "mismatch":
                return AccessDecision(
                    decision=DecisionStatus.PENDING_ADMIN_REVIEW,
                    roll_number=roll_number,
                    student_name=student_name,
                    reasons=reasons,
                    requires_admin_review=True,
                    audit_trail=audit_trail,
                )
            else:
                # NO_PHOTO or UNVERIFIABLE
                return AccessDecision(
                    decision=DecisionStatus.DENIED,
                    roll_number=roll_number,
                    student_name=student_name,
                    reasons=reasons,
                    audit_trail=audit_trail,
                )

        # ── Success ───────────────────────────────────────────────────────────
        reasons.append(f"Identity fully verified for {student_name}.")
        return AccessDecision(
            decision=DecisionStatus.GRANTED,
            roll_number=roll_number,
            student_name=student_name,
            reasons=reasons,
            audit_trail=audit_trail,
        )
