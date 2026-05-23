"""
roll_verification/__init__.py
──────────────────────────────
Public surface of the GATEKEEPER Roll Number Verification Flow package.
"""

from .fixtures import STUDENT_REGISTRY_FIXTURES, build_fixture_registry
from .display import StudentDisplayCard, format_display_card
from .flow import RollVerificationFlow, VerificationFlowResult, FlowStatus

__all__ = [
    "RollVerificationFlow",
    "VerificationFlowResult",
    "FlowStatus",
    "StudentDisplayCard",
    "format_display_card",
    "STUDENT_REGISTRY_FIXTURES",
    "build_fixture_registry",
]
