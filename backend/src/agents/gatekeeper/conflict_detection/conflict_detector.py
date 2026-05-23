"""
conflict_detector.py
────────────────────
Identity conflict detection engine for the GATEKEEPER pipeline.

Responsibilities
────────────────
- Consume HistoryCheckResult from the face history stage.
- Classify conflicts into severe categories (clone vs swap).
- Produce a structured ConflictReport that the Authorization Engine will use.

Rules
─────
- Pure logic — reads the HistoryCheckResult and decides conflict level.
- Deterministic and rule-based.
- No DB calls or state mutation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List

from src.agents.gatekeeper.face_history.history_checker import HistoryCheckResult

logger = logging.getLogger(__name__)


class ConflictSeverity(str, Enum):
    NONE     = "none"
    LOW      = "low"       # Minor anomaly, log only
    MEDIUM   = "medium"    # Suspicious, maybe flag for later review
    HIGH     = "high"      # Likely fraud (e.g. face swap attempt on same roll), block access
    CRITICAL = "critical"  # Severe fraud (e.g. proxy test taker / face clone), block immediately


class ConflictType(str, Enum):
    NO_CONFLICT = "no_conflict"
    FACE_SWAP   = "face_swap"    # Same roll number, different faces presented over time
    FACE_CLONE  = "face_clone"   # Same face presented under multiple different roll numbers


@dataclass(frozen=True)
class ConflictReport:
    """
    Final output of the conflict detection stage.
    """
    has_conflict:   bool
    conflict_type:  ConflictType
    severity:       ConflictSeverity
    involved_rolls: List[str] = field(default_factory=list)
    involved_faces: List[str] = field(default_factory=list)
    reason:         str       = ""

    def to_dict(self) -> dict:
        return {
            "has_conflict":   self.has_conflict,
            "conflict_type":  self.conflict_type.value,
            "severity":       self.severity.value,
            "involved_rolls": self.involved_rolls,
            "involved_faces": self.involved_faces,
            "reason":         self.reason,
        }


class IdentityConflictDetector:
    """
    Rules engine that categorizes face history anomalies into actionable conflicts.

    Rules:
    - is_cloned_face (same face, multiple rolls) -> CRITICAL / FACE_CLONE
    - conflict_face_ids (same roll, multiple faces) -> HIGH / FACE_SWAP
    - neither -> NONE / NO_CONFLICT
    """

    def analyze(self, history_result: HistoryCheckResult) -> ConflictReport:
        """
        Analyze the history check result and emit a ConflictReport.
        """
        # Rule 1: Face Clone (Proxy Test Taker)
        # If the same face ID is associated with other roll numbers, this is a critical security breach.
        if history_result.is_cloned_face:
            all_involved_rolls = [history_result.roll_number] + history_result.clone_roll_numbers
            reason = (
                f"CRITICAL: Identity Clone detected. The presented face '{history_result.face_id}' "
                f"has been used by multiple roll numbers: {all_involved_rolls}."
            )
            logger.error("[ConflictDetector] %s", reason)
            return ConflictReport(
                has_conflict=True,
                conflict_type=ConflictType.FACE_CLONE,
                severity=ConflictSeverity.CRITICAL,
                involved_rolls=all_involved_rolls,
                involved_faces=[history_result.face_id],
                reason=reason,
            )

        # Rule 2: Face Swap (Account Sharing / Mid-exam swap)
        # If this roll number has previously used different face IDs, flag it as high severity.
        if history_result.conflict_face_ids:
            all_involved_faces = [history_result.face_id] + history_result.conflict_face_ids
            reason = (
                f"HIGH: Face Swap detected. Roll number '{history_result.roll_number}' "
                f"has presented multiple distinct faces: {all_involved_faces}."
            )
            logger.warning("[ConflictDetector] %s", reason)
            return ConflictReport(
                has_conflict=True,
                conflict_type=ConflictType.FACE_SWAP,
                severity=ConflictSeverity.HIGH,
                involved_rolls=[history_result.roll_number],
                involved_faces=all_involved_faces,
                reason=reason,
            )

        # No conflict
        return ConflictReport(
            has_conflict=False,
            conflict_type=ConflictType.NO_CONFLICT,
            severity=ConflictSeverity.NONE,
            reason="No identity conflicts detected.",
        )
