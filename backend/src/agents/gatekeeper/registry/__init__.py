"""
registry/__init__.py
────────────────────
Public surface of the GATEKEEPER Student Registry package.
"""

from .student_schema import StudentProfile, StudentBatch, Department
from .registry_store import StudentRegistry
from .lookup import RegistryLookup, LookupResult

__all__ = [
    "StudentProfile",
    "StudentBatch",
    "Department",
    "StudentRegistry",
    "RegistryLookup",
    "LookupResult",
]
