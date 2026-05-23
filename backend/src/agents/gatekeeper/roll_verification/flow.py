"""
flow.py
───────
Roll Number Verification Flow for the GATEKEEPER agent.

Responsibilities
────────────────
- Accept raw roll-number input from any source (API, CLI, staff terminal).
- Normalize, validate, and lookup the student in the registry.
- Return a typed VerificationFlowResult with full audit trail.
- Generate a StudentDisplayCard for manual staff verification.
- Support both single-lookup and batch-verification modes.

Rules
─────
- Stateless class — registry injected at construction.
- Deterministic: same roll number → same result for the same registry state.
- Never raises — all errors captured in VerificationFlowResult.
- No ORACLE logic, no face verification logic — identity layer only.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from src.agents.gatekeeper.registry.lookup import (
    LookupFailureReason,
    LookupResult,
    RegistryLookup,
)
from src.agents.gatekeeper.registry.registry_store import StudentRegistry
from .display import StudentDisplayCard, format_display_card, format_not_found, format_inactive
from .fixtures import build_fixture_registry

logger = logging.getLogger(__name__)


# ── Flow status ───────────────────────────────────────────────────────────────

class FlowStatus(str, Enum):
    VERIFIED     = "verified"      # Roll number found and student is active
    NOT_FOUND    = "not_found"     # Roll number not in registry
    INVALID      = "invalid"       # Bad format or empty input
    INACTIVE     = "inactive"      # Found but student account is inactive
    MANUAL_CHECK = "manual_check"  # Passed to staff for visual confirmation


# ── Flow result ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class VerificationFlowResult:
    """
    Complete output of a single roll-number verification flow run.

    Consumed by GATEKEEPER to decide session admission.
    """
    roll_number:   str
    status:        FlowStatus
    display_card:  Optional[StudentDisplayCard]   # Set on VERIFIED / INACTIVE
    message:       str
    lookup_result: LookupResult                   # Raw lookup for audit trail
    requires_manual: bool = False                 # True → staff must visually confirm

    @property
    def is_verified(self) -> bool:
        return self.status == FlowStatus.VERIFIED

    @property
    def is_rejected(self) -> bool:
        return self.status in (FlowStatus.NOT_FOUND, FlowStatus.INVALID, FlowStatus.INACTIVE)

    def to_dict(self) -> dict:
        return {
            "roll_number":    self.roll_number,
            "status":         self.status.value,
            "is_verified":    self.is_verified,
            "is_rejected":    self.is_rejected,
            "requires_manual":self.requires_manual,
            "message":        self.message,
            "display_card":   self.display_card.to_dict() if self.display_card else None,
        }


# ── Verification Flow ─────────────────────────────────────────────────────────

class RollVerificationFlow:
    """
    Stateless roll number verification flow.

    Usage
    ─────
        flow   = RollVerificationFlow()          # Uses real fixture registry
        result = flow.verify("150096725066")     # Raj Rasal → VERIFIED
        result = flow.verify("BADROLLNUM")       # → INVALID
        result = flow.verify("150096799999")     # → NOT_FOUND

        print(result.display_card.pretty())      # Staff identity card
        print(result.is_verified)                # True / False

    Batch usage:
        results = flow.verify_batch(["150096725002", "150096725066"])
    """

    def __init__(
        self,
        registry: Optional[StudentRegistry] = None,
        require_manual_confirmation: bool = False,
    ) -> None:
        """
        Parameters
        ──────────
        registry                 : StudentRegistry to use. Defaults to fixture registry.
        require_manual_confirmation: If True, VERIFIED results are flagged for staff check.
        """
        self._registry  = registry or build_fixture_registry()
        self._lookup    = RegistryLookup(self._registry)
        self._manual    = require_manual_confirmation

    # ── Single verification ───────────────────────────────────────────────────

    def verify(self, raw_roll_number: str) -> VerificationFlowResult:
        """
        Run the full roll number verification flow for one input.

        Pipeline:
        1. Lookup (normalize → validate → store → active check)
        2. Map LookupResult → FlowStatus
        3. Build display card (if found)
        4. Return VerificationFlowResult
        """
        lookup = self._lookup.by_roll_number(raw_roll_number)

        # ── Success ────────────────────────────────────────────────────────────
        if lookup.success:
            card = format_display_card(lookup.profile)
            logger.info("[RollVerification] VERIFIED: %s", card.one_line())
            return VerificationFlowResult(
                roll_number    = lookup.roll_number,
                status         = FlowStatus.VERIFIED,
                display_card   = card,
                message        = f"✅ Identity confirmed: {lookup.profile.full_name} ({lookup.roll_number})",
                lookup_result  = lookup,
                requires_manual= self._manual,
            )

        # ── Failure → map reason to FlowStatus ────────────────────────────────
        reason  = lookup.failure_reason
        roll    = lookup.roll_number or str(raw_roll_number)

        if reason == LookupFailureReason.INVALID_FORMAT:
            return VerificationFlowResult(
                roll_number    = roll,
                status         = FlowStatus.INVALID,
                display_card   = None,
                message        = f"❌ Invalid roll number format: '{roll}'. Expected 4-15 alphanumeric characters.",
                lookup_result  = lookup,
            )

        if reason == LookupFailureReason.EMPTY_INPUT:
            return VerificationFlowResult(
                roll_number    = "",
                status         = FlowStatus.INVALID,
                display_card   = None,
                message        = "❌ Roll number cannot be empty.",
                lookup_result  = lookup,
            )

        if reason == LookupFailureReason.STUDENT_INACTIVE:
            # Fetch the profile directly (get_safe bypasses active check)
            profile = self._registry.get(roll)
            card    = format_display_card(profile) if profile else None
            return VerificationFlowResult(
                roll_number    = roll,
                status         = FlowStatus.INACTIVE,
                display_card   = card,
                message        = format_inactive(card) if card else f"⚠️ Student {roll} is inactive.",
                lookup_result  = lookup,
            )

        # NOT_FOUND
        return VerificationFlowResult(
            roll_number    = roll,
            status         = FlowStatus.NOT_FOUND,
            display_card   = None,
            message        = format_not_found(roll),
            lookup_result  = lookup,
        )

    # ── Batch verification ────────────────────────────────────────────────────

    def verify_batch(
        self,
        roll_numbers: List[str],
    ) -> Dict[str, VerificationFlowResult]:
        """
        Verify multiple roll numbers in one call.

        Returns dict[roll_number → VerificationFlowResult].
        Preserves input order.
        """
        results = {}
        for roll in roll_numbers:
            results[roll] = self.verify(roll)
        return results

    def verified_count(self, batch_results: Dict[str, VerificationFlowResult]) -> int:
        """Count verified students in a batch result."""
        return sum(1 for r in batch_results.values() if r.is_verified)

    def rejected_count(self, batch_results: Dict[str, VerificationFlowResult]) -> int:
        """Count rejected students in a batch result."""
        return sum(1 for r in batch_results.values() if r.is_rejected)

    # ── Registry info ─────────────────────────────────────────────────────────

    @property
    def registry_size(self) -> int:
        return self._registry.count
