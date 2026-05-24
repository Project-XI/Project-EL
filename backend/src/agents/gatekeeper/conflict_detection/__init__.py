"""
conflict_detection/__init__.py
──────────────────────────────
Public surface of the GATEKEEPER identity conflict detection package.
"""

from .conflict_detector import ConflictReport, ConflictSeverity, ConflictType, IdentityConflictDetector

__all__ = [
    "ConflictReport",
    "ConflictSeverity",
    "ConflictType",
    "IdentityConflictDetector",
]
