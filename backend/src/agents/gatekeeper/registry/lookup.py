"""
lookup.py
─────────
Roll-number lookup service for the GATEKEEPER Student Registry.

Responsibilities
────────────────
- Accept raw roll-number input (possibly dirty/user-provided).
- Normalize and validate the format before hitting the store.
- Return a typed LookupResult with clear success/failure distinction.
- Surface the reason for failure so GATEKEEPER can respond appropriately.
- Never raises — all errors are captured in LookupResult.

Rules
─────
- Pure service functions + a stateless class.
- All lookups go through validate → normalize → store.get().
- Deterministic: same input → same result for the same registry state.
- No UI logic, no session logic, no ORACLE imports.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .student_schema import ROLL_NUMBER_PATTERN, StudentProfile
from .registry_store import StudentRegistry


# ── Lookup failure reasons ────────────────────────────────────────────────────

class LookupFailureReason(str, Enum):
    NOT_FOUND         = "not_found"          # Valid format, not in registry
    INVALID_FORMAT    = "invalid_format"     # Roll number fails regex
    EMPTY_INPUT       = "empty_input"        # Blank or None input
    STUDENT_INACTIVE  = "student_inactive"   # Found but account deactivated
    UNKNOWN_ERROR     = "unknown_error"      # Unexpected exception


# ── Lookup result ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class LookupResult:
    """
    Result of a roll-number lookup operation.

    Always check `success` before accessing `profile`.
    `failure_reason` is set when `success` is False.
    """
    success: bool
    roll_number: str                         # The normalized input (or raw if invalid)
    profile: Optional[StudentProfile]        # Set only when success=True
    failure_reason: Optional[LookupFailureReason] = None
    message: str = ""

    @staticmethod
    def ok(profile: StudentProfile) -> "LookupResult":
        return LookupResult(
            success       = True,
            roll_number   = profile.roll_number,
            profile       = profile,
            failure_reason= None,
            message       = f"Student '{profile.full_name}' found.",
        )

    @staticmethod
    def fail(
        roll_number: str,
        reason: LookupFailureReason,
        message: str = "",
    ) -> "LookupResult":
        return LookupResult(
            success       = False,
            roll_number   = roll_number,
            profile       = None,
            failure_reason= reason,
            message       = message or reason.value,
        )

    def to_dict(self) -> dict:
        return {
            "success":        self.success,
            "roll_number":    self.roll_number,
            "failure_reason": self.failure_reason.value if self.failure_reason else None,
            "message":        self.message,
            "profile":        self.profile.to_dict() if self.profile else None,
        }


# ── Lookup service ────────────────────────────────────────────────────────────

class RegistryLookup:
    """
    Stateless roll-number lookup service.

    Usage
    ─────
        lookup = RegistryLookup(registry)
        result = lookup.by_roll_number("cs2021001")   # case-insensitive
        if result.success:
            print(result.profile.full_name)
        else:
            print(result.failure_reason)
    """

    def __init__(self, registry: StudentRegistry) -> None:
        self._registry = registry

    def by_roll_number(self, raw_input: str) -> LookupResult:
        """
        Look up a student by raw roll-number input.

        Pipeline:
        1. Empty check
        2. Normalize (strip, uppercase)
        3. Format validation
        4. Registry lookup
        5. Active check
        """
        # 1. Empty check
        if not raw_input or not str(raw_input).strip():
            return LookupResult.fail(
                roll_number = "",
                reason      = LookupFailureReason.EMPTY_INPUT,
                message     = "Roll number input is empty.",
            )

        # 2. Normalize
        normalized = str(raw_input).strip().upper()

        # 3. Format validation
        if not ROLL_NUMBER_PATTERN.match(normalized):
            return LookupResult.fail(
                roll_number = normalized,
                reason      = LookupFailureReason.INVALID_FORMAT,
                message     = (
                    f"'{normalized}' is not a valid roll number. "
                    f"Expected 4–15 uppercase letters/digits (e.g. CS2021001)."
                ),
            )

        # 4. Registry lookup
        profile = self._registry.get(normalized)
        if profile is None:
            return LookupResult.fail(
                roll_number = normalized,
                reason      = LookupFailureReason.NOT_FOUND,
                message     = f"No student found with roll number '{normalized}'.",
            )

        # 5. Active check
        if not profile.is_active:
            return LookupResult.fail(
                roll_number = normalized,
                reason      = LookupFailureReason.STUDENT_INACTIVE,
                message     = (
                    f"Student '{profile.full_name}' ({normalized}) account is inactive."
                ),
            )

        return LookupResult.ok(profile)

    def metadata(self, raw_input: str) -> dict:
        """
        Convenience method: return metadata dict directly.
        Returns an error dict if lookup fails — never raises.
        """
        result = self.by_roll_number(raw_input)
        return result.to_dict()

    def is_valid_student(self, raw_input: str) -> bool:
        """Quick boolean check — True only if student is found and active."""
        return self.by_roll_number(raw_input).success
