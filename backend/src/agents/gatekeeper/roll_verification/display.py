"""
display.py
──────────
Student info display formatter for the Roll Number Verification Flow.

Responsibilities
────────────────
- Convert a StudentProfile into a clean, structured display card.
- Support plain-text, dict, and single-line summary formats.
- Used by manual verification staff to visually confirm identity.
- Never modifies the profile — read-only formatting only.

Rules
─────
- Pure functions — no state, no DB calls.
- All output is plain strings or plain dicts — safe to log and display.
- photo_reference is included for staff to pull up the registered photo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.agents.gatekeeper.registry.student_schema import StudentProfile


# ── Display card ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class StudentDisplayCard:
    """
    A formatted snapshot of student identity for display to verification staff.

    All fields are plain strings — no Enum objects, no nested models.
    """
    roll_number:     str
    full_name:       str
    email:           str
    department:      str
    year:            str
    batch:           str
    program:         str
    photo_reference: Optional[str]
    is_active:       bool
    status_label:    str          # "ACTIVE" or "INACTIVE"

    def to_dict(self) -> dict:
        return {
            "roll_number":     self.roll_number,
            "full_name":       self.full_name,
            "email":           self.email,
            "department":      self.department,
            "year":            f"Year {self.year}",
            "batch":           f"Batch {self.batch}",
            "program":         self.program,
            "photo_reference": self.photo_reference,
            "status":          self.status_label,
        }

    def one_line(self) -> str:
        """Single-line summary for logging and quick display."""
        return (
            f"[{self.roll_number}] {self.full_name} | "
            f"{self.department} Year-{self.year} Batch-{self.batch} | "
            f"{self.status_label}"
        )

    def pretty(self) -> str:
        """Multi-line formatted card for terminal / staff display."""
        lines = [
            "┌─────────────────────────────────────────┐",
            f"│  STUDENT IDENTITY CARD                  │",
            "├─────────────────────────────────────────┤",
            f"│  Roll No  : {self.roll_number:<28} │",
            f"│  Name     : {self.full_name:<28} │",
            f"│  Email    : {self.email:<28} │",
            f"│  Dept     : {self.department:<28} │",
            f"│  Year     : {self.year:<28} │",
            f"│  Batch    : {self.batch:<28} │",
            f"│  Program  : {self.program:<28} │",
            f"│  Status   : {self.status_label:<28} │",
            f"│  Photo    : {(self.photo_reference or 'N/A'):<28} │",
            "└─────────────────────────────────────────┘",
        ]
        return "\n".join(lines)


# ── Formatter ─────────────────────────────────────────────────────────────────

def format_display_card(profile: StudentProfile) -> StudentDisplayCard:
    """
    Convert a StudentProfile into a StudentDisplayCard.
    Pure function — no side effects.
    """
    return StudentDisplayCard(
        roll_number     = profile.roll_number,
        full_name       = profile.full_name,
        email           = profile.email,
        department      = profile.department.value,
        year            = profile.year.value,
        batch           = profile.batch.value,
        program         = profile.program,
        photo_reference = profile.photo_reference,
        is_active       = profile.is_active,
        status_label    = "ACTIVE" if profile.is_active else "INACTIVE",
    )


def format_not_found(roll_number: str) -> str:
    """Standard rejection message for invalid/missing roll numbers."""
    return (
        f"❌ No student found for roll number '{roll_number}'.\n"
        f"   Please check the roll number and try again.\n"
        f"   If the issue persists, contact the examination office."
    )


def format_inactive(card: StudentDisplayCard) -> str:
    """Warning message shown when a student account is inactive."""
    return (
        f"⚠️  Student '{card.full_name}' ({card.roll_number}) is INACTIVE.\n"
        f"   Access denied. Contact the examination office."
    )
