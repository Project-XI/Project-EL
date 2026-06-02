"""
student_schema.py
─────────────────
Canonical student data model for the GATEKEEPER registry.

Rules
─────
- All schema changes must be backward-compatible.
- No pipeline logic here — pure data definitions only.
- All Enum values are plain strings for JSON serialization safety.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ── Enumerations ──────────────────────────────────────────────────────────────

class Department(str, Enum):
    COMPUTER_SCIENCE     = "Computer Science"
    INFORMATION_TECH     = "Information Technology"
    ELECTRONICS          = "Electronics"
    MECHANICAL           = "Mechanical"
    CIVIL                = "Civil"
    UNKNOWN              = "Unknown"


class AcademicYear(str, Enum):
    FIRST  = "1"
    SECOND = "2"
    THIRD  = "3"
    FOURTH = "4"


class StudentBatch(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


# ── Student Profile ───────────────────────────────────────────────────────────

@dataclass
class StudentProfile:
    """
    Authoritative student identity record stored in the registry.

    Fields
    ──────
    roll_number     : Unique 12-digit numeric identifier.
    full_name       : Title-cased full name.
    email           : Institutional email derived from roll number.
    department      : Academic department enum.
    year            : Academic year enum.
    batch           : Section / batch label.
    program         : Degree programme (e.g. "B.Tech").
    photo_reference : Path / URL to registered face photo (for face verification).
    is_active       : False if the student is deregistered or suspended.
    """
    roll_number:      str
    full_name:        str
    email:            str
    department:       Department       = Department.COMPUTER_SCIENCE
    year:             AcademicYear     = AcademicYear.THIRD
    batch:            StudentBatch     = StudentBatch.A
    program:          str              = "B.Tech"
    photo_reference:  Optional[str]    = None
    is_active:        bool             = True

    def __post_init__(self) -> None:
        # Normalise name casing at creation time
        self.full_name = self.full_name.strip().title()

    def to_dict(self) -> dict:
        return {
            "roll_number":     self.roll_number,
            "full_name":       self.full_name,
            "email":           self.email,
            "department":      self.department.value,
            "year":            self.year.value,
            "batch":           self.batch.value,
            "program":         self.program,
            "photo_reference": self.photo_reference,
            "is_active":       self.is_active,
        }
