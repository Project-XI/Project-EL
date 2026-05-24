"""
lookup.py
─────────
Registry lookup engine for the GATEKEEPER roll number verification flow.

Responsibilities
────────────────
- Normalize raw roll number input (strip whitespace, uppercase).
- Validate format (4–15 alphanumeric characters).
- Query the StudentRegistry.
- Return a typed LookupResult with full failure reasoning.

Rules
─────
- Never raises — all failure paths captured in LookupResult.
- Stateless — registry is injected at construction.
- No pipeline decisions here — only data retrieval + validation.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .registry_store import StudentRegistry
from .student_schema import StudentProfile

logger = logging.getLogger(__name__)

# Roll number validation: 4–15 alphanumeric characters (no spaces, no symbols)
_ROLL_PATTERN = re.compile(r"^[A-Z0-9]{4,15}$")


# ── Failure reason ────────────────────────────────────────────────────────────

class LookupFailureReason(str, Enum):
    EMPTY_INPUT      = "empty_input"
    INVALID_FORMAT   = "invalid_format"
    NOT_FOUND        = "not_found"
    STUDENT_INACTIVE = "student_inactive"


# ── Lookup result ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class LookupResult:
    """
    Complete output of a single registry lookup.

    Fields
    ──────
    success         : True only when the student is found AND active.
    roll_number     : Normalized roll number (or raw input on early failure).
    profile         : Populated on success; None on failure.
    failure_reason  : Set when success is False.
    """
    success:        bool
    roll_number:    Optional[str]
    profile:        Optional[StudentProfile]
    failure_reason: Optional[LookupFailureReason]

    def to_dict(self) -> dict:
        return {
            "success":        self.success,
            "roll_number":    self.roll_number,
            "failure_reason": self.failure_reason.value if self.failure_reason else None,
            "profile":        self.profile.to_dict() if self.profile else None,
        }


# ── Registry lookup ───────────────────────────────────────────────────────────

class RegistryLookup:
    """
    Stateless roll number lookup engine.

    Pipeline
    ────────
    1. Normalize input (strip, uppercase)
    2. Validate format (regex)
    3. Query registry
    4. Check active status
    5. Return LookupResult

    Usage
    ─────
        lookup = RegistryLookup(registry)
        result = lookup.by_roll_number("150096725066")
        if result.success:
            print(result.profile.full_name)
    """

    def __init__(self, registry: StudentRegistry) -> None:
        self._registry = registry

    def by_roll_number(self, raw: object) -> LookupResult:
        """
        Run the full lookup pipeline for a raw roll number input.
        Accepts any type — will reject non-string / invalid input gracefully.
        """

        # ── Step 1: Empty / non-string guard ─────────────────────────────────
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            logger.debug("[Lookup] Empty or None input rejected.")
            return LookupResult(
                success=False,
                roll_number=None,
                profile=None,
                failure_reason=LookupFailureReason.EMPTY_INPUT,
            )

        if not isinstance(raw, str):
            # Coerce numeric types gracefully, reject collections
            try:
                raw = str(int(raw))
            except (TypeError, ValueError):
                logger.debug("[Lookup] Non-string, non-numeric input rejected: %r", raw)
                return LookupResult(
                    success=False,
                    roll_number=None,
                    profile=None,
                    failure_reason=LookupFailureReason.INVALID_FORMAT,
                )

        # ── Step 2: Normalize ─────────────────────────────────────────────────
        normalized = raw.strip().upper()

        # ── Step 3: Format validation ─────────────────────────────────────────
        if not _ROLL_PATTERN.match(normalized):
            logger.debug("[Lookup] Invalid format: %r → normalized %r", raw, normalized)
            return LookupResult(
                success=False,
                roll_number=normalized,
                profile=None,
                failure_reason=LookupFailureReason.INVALID_FORMAT,
            )

        # ── Step 4: Registry query ────────────────────────────────────────────
        profile = self._registry.get(normalized)

        if profile is None:
            logger.debug("[Lookup] Not found in registry: %s", normalized)
            return LookupResult(
                success=False,
                roll_number=normalized,
                profile=None,
                failure_reason=LookupFailureReason.NOT_FOUND,
            )

        # ── Step 5: Active check ──────────────────────────────────────────────
        if not profile.is_active:
            logger.info("[Lookup] Inactive student: %s (%s)", profile.full_name, normalized)
            return LookupResult(
                success=False,
                roll_number=normalized,
                profile=profile,
                failure_reason=LookupFailureReason.STUDENT_INACTIVE,
            )

        # ── Success ───────────────────────────────────────────────────────────
        logger.info("[Lookup] Verified: %s (%s)", profile.full_name, normalized)
        return LookupResult(
            success=True,
            roll_number=normalized,
            profile=profile,
            failure_reason=None,
        )
