"""
registry_store.py
─────────────────
In-memory student registry store for the GATEKEEPER agent.

Responsibilities
────────────────
- Store StudentProfile records keyed by roll number.
- Support bulk seeding from fixture lists.
- Expose filtered views (active-only, all).
- Never raise — return None / empty on misses.

Rules
─────
- Stateful but not persistent (use a DB adapter in production).
- Thread-safety is not required for the current single-process design.
- No validation logic here — that belongs in lookup.py.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from .student_schema import StudentProfile

logger = logging.getLogger(__name__)


class StudentRegistry:
    """
    In-memory student data store.

    Usage
    ─────
        registry = StudentRegistry()
        registry.add(profile)
        profile = registry.get("150096725066")   # → StudentProfile | None
        all_active = registry.all_active()        # → List[StudentProfile]
    """

    def __init__(self) -> None:
        self._store: Dict[str, StudentProfile] = {}

    # ── Write operations ──────────────────────────────────────────────────────

    def add(self, profile: StudentProfile) -> None:
        """Add or overwrite a single student profile."""
        self._store[profile.roll_number] = profile
        logger.debug("[Registry] Added student: %s (%s)", profile.full_name, profile.roll_number)

    def seed(self, profiles: List[StudentProfile]) -> None:
        """Bulk-load a list of profiles. Overwrites duplicates."""
        for p in profiles:
            self.add(p)
        logger.info("[Registry] Seeded %d student profiles.", len(profiles))

    def remove(self, roll_number: str) -> bool:
        """Remove a student by roll number. Returns True if removed."""
        if roll_number in self._store:
            del self._store[roll_number]
            return True
        return False

    def deactivate(self, roll_number: str) -> bool:
        """Mark a student as inactive without removing the record."""
        profile = self._store.get(roll_number)
        if profile:
            profile.is_active = False
            return True
        return False

    # ── Read operations ───────────────────────────────────────────────────────

    def get(self, roll_number: str) -> Optional[StudentProfile]:
        """
        Retrieve a student by roll number regardless of active status.
        Returns None if not found.
        """
        return self._store.get(roll_number)

    def get_active(self, roll_number: str) -> Optional[StudentProfile]:
        """Retrieve a student only if they are active. Returns None otherwise."""
        profile = self._store.get(roll_number)
        if profile and profile.is_active:
            return profile
        return None

    def all_active(self) -> List[StudentProfile]:
        """Return all active student profiles."""
        return [p for p in self._store.values() if p.is_active]

    def all_students(self) -> List[StudentProfile]:
        """Return every student profile (active and inactive)."""
        return list(self._store.values())

    def exists(self, roll_number: str) -> bool:
        """True if a roll number is in the registry (regardless of active status)."""
        return roll_number in self._store

    # ── Meta ──────────────────────────────────────────────────────────────────

    @property
    def count(self) -> int:
        """Total number of students (active + inactive)."""
        return len(self._store)

    @property
    def active_count(self) -> int:
        """Number of active students."""
        return sum(1 for p in self._store.values() if p.is_active)

    def __repr__(self) -> str:
        return f"<StudentRegistry students={self.count} active={self.active_count}>"
