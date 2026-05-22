"""
student_schema.py
─────────────────
Versioned, validated data contracts for the Student Registry.

Responsibilities
────────────────
- Define the canonical StudentProfile model consumed by GATEKEEPER.
- Define Department, Year, and Batch enumerations.
- Enforce strict field validation (roll number format, name length, etc.)
- Remain decoupled from storage — no DB imports here.

Rules
─────
- All models are immutable Pydantic BaseModels.
- Roll number format: uppercase letters + digits, 6–12 chars (e.g. CS2021001).
- Photo reference is a URL string or a relative path — never raw bytes.
- Adding new fields requires only a schema version bump.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator

# ── Schema version ────────────────────────────────────────────────────────────
REGISTRY_SCHEMA_VERSION = "1.0.0"

# ── Roll number format ────────────────────────────────────────────────────────
ROLL_NUMBER_PATTERN = re.compile(r"^[A-Z0-9]{4,15}$")


# ── Enumerations ──────────────────────────────────────────────────────────────

class Department(str, Enum):
    COMPUTER_SCIENCE       = "CS"
    INFORMATION_TECHNOLOGY = "IT"
    ELECTRONICS            = "EC"
    ELECTRICAL             = "EE"
    MECHANICAL             = "ME"
    CIVIL                  = "CE"
    CHEMICAL               = "CH"
    DATA_SCIENCE           = "DS"
    ARTIFICIAL_INTELLIGENCE= "AI"
    OTHER                  = "OT"


class AcademicYear(str, Enum):
    FIRST  = "1"
    SECOND = "2"
    THIRD  = "3"
    FOURTH = "4"
    PG1    = "PG1"
    PG2    = "PG2"


class StudentBatch(str, Enum):
    """Batch section within a year (A–F or numeric)."""
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"


# ── Student Profile ───────────────────────────────────────────────────────────

class StudentProfile(BaseModel):
    """
    Canonical student identity record for GATEKEEPER.

    All fields validated at construction time.
    Immutable once created (model_config frozen=True).
    """
    model_config = {"frozen": True}

    schema_version: str       = REGISTRY_SCHEMA_VERSION

    # Identity
    roll_number: str          = Field(..., description="Unique student roll number")
    full_name: str            = Field(..., min_length=2, max_length=120)
    email: str                = Field(..., description="Official institution email")

    # Academic metadata
    department: Department
    year: AcademicYear
    batch: StudentBatch
    program: str              = Field(default="B.Tech", max_length=50)

    # Photo reference (URL or relative path — never raw bytes)
    photo_reference: Optional[str] = Field(default=None, description="URL or path to student photo")

    # Optional extended metadata
    guardian_name: Optional[str]   = Field(default=None, max_length=120)
    is_active: bool                = True

    # ── Validators ────────────────────────────────────────────────────────────

    @field_validator("roll_number")
    @classmethod
    def validate_roll_number(cls, v: str) -> str:
        normalized = v.strip().upper()
        if not ROLL_NUMBER_PATTERN.match(normalized):
            raise ValueError(
                f"Invalid roll number format '{v}'. "
                f"Must be 4–15 uppercase letters/digits (e.g. CS2021001)."
            )
        return normalized

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError(f"Invalid email address: '{v}'")
        return v

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        v = v.strip()
        if not v.replace(" ", "").replace("-", "").replace("'", "").isalpha():
            raise ValueError(f"Full name must contain only letters, spaces, hyphens: '{v}'")
        return v

    def to_dict(self) -> dict:
        """Return a plain-dict representation safe for logging and export."""
        return {
            "schema_version":  self.schema_version,
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
