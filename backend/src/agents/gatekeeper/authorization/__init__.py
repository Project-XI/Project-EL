"""
authorization/__init__.py
─────────────────────────
Public surface of the GATEKEEPER authorization package.
"""

from .access_decision import AccessDecision, DecisionStatus
from .auth_engine import AuthorizationEngine

__all__ = [
    "AccessDecision",
    "DecisionStatus",
    "AuthorizationEngine",
]
