"""
registry/__init__.py
─────────────────────
Public surface of the GATEKEEPER student registry package.
"""

from .student_schema import StudentProfile, Department, AcademicYear, StudentBatch
from .registry_store import StudentRegistry
from .lookup import RegistryLookup, LookupResult, LookupFailureReason

__all__ = [
    "StudentProfile",
    "Department",
    "AcademicYear",
    "StudentBatch",
    "StudentRegistry",
    "RegistryLookup",
    "LookupResult",
    "LookupFailureReason",
]
