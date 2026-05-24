"""
registry_store.py
─────────────────
In-memory Student Registry store for GATEKEEPER.

Responsibilities
────────────────
- Store, retrieve, and manage StudentProfile records.
- Support roll-number lookup (primary key).
- Support batch/department queries for session routing.
- Handle invalid roll numbers safely — never raises on bad input.
- Seed from a static fixture list for development/testing.

Rules
─────
- Storage is a plain dict[str, StudentProfile] — lightweight, serializable.
- Registry is the single source of truth for all student identity queries.
- All mutating operations return the registry itself (fluent interface).
- Thread-safety: single-process use; no locking required at this stage.
- Never imports from ORACLE or MAIN Agent packages.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Dict, Iterator, List, Optional

from .student_schema import (
    AcademicYear,
    Department,
    StudentBatch,
    StudentProfile,
    ROLL_NUMBER_PATTERN,
)

logger = logging.getLogger(__name__)


class RegistryError(Exception):
    """Raised for invalid registry operations (duplicate, not found, etc.)."""


class StudentRegistry:
    """
    In-memory student identity registry for GATEKEEPER.

    Usage
    ─────
        registry = StudentRegistry()
        registry.seed(SAMPLE_STUDENTS)

        profile = registry.get("CS2021001")  # returns StudentProfile or None
        exists  = registry.exists("CS2021001")
        batch   = registry.by_batch(Department.COMPUTER_SCIENCE, AcademicYear.THIRD, StudentBatch.A)
    """

    def __init__(self) -> None:
        self._store: Dict[str, StudentProfile] = {}
        # Attempt to load persistent registry from backend/data/students.json if present
        try:
            base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
            default_path = os.path.join(base, 'backend', 'data', 'students.json')
            if os.path.exists(default_path):
                self.load_from_file(default_path)
        except Exception:
            # ignore persistence errors for in-memory fallback
            pass

    # ── Write operations ──────────────────────────────────────────────────────

    def add(self, profile: StudentProfile) -> "StudentRegistry":
        """
        Add a student profile to the registry.
        Raises RegistryError if the roll number already exists.
        """
        if profile.roll_number in self._store:
            raise RegistryError(
                f"Student with roll number '{profile.roll_number}' already exists."
            )
        self._store[profile.roll_number] = profile
        logger.debug("[StudentRegistry] added: %s (%s)", profile.roll_number, profile.full_name)
        return self

    def upsert(self, profile: StudentProfile) -> "StudentRegistry":
        """Add or replace a student profile (idempotent)."""
        self._store[profile.roll_number] = profile
        return self

    def remove(self, roll_number: str) -> bool:
        """Remove a student. Returns True if removed, False if not found."""
        roll_number = roll_number.strip().upper()
        if roll_number in self._store:
            del self._store[roll_number]
            return True
        return False

    def seed(self, profiles: List[StudentProfile]) -> "StudentRegistry":
        """Bulk-load profiles (upsert semantics — safe to call multiple times)."""
        for p in profiles:
            self.upsert(p)
        logger.info("[StudentRegistry] seeded %d student records.", len(profiles))
        try:
            # attempt to persist after seeding
            base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
            default_path = os.path.join(base, 'backend', 'data', 'students.json')
            self.save_to_file(default_path)
        except Exception:
            pass
        return self

    # ── Persistence helpers ─────────────────────────────────────────────────
    def to_serializable(self) -> List[dict]:
        return [p.to_dict() for p in self._store.values()]

    def save_to_file(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_serializable(), f, indent=2)

    def load_from_file(self, path: str) -> "StudentRegistry":
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Expect list of dicts
            for item in data:
                try:
                    # Convert enum strings back to model types via StudentProfile
                    profile = StudentProfile(
                        roll_number=item.get('roll_number'),
                        full_name=item.get('full_name'),
                        email=item.get('email'),
                        department=item.get('department'),
                        year=item.get('year'),
                        batch=item.get('batch'),
                        program=item.get('program', 'B.Tech'),
                        photo_reference=item.get('photo_reference'),
                        guardian_name=item.get('guardian_name'),
                        is_active=item.get('is_active', True),
                    )
                    self.upsert(profile)
                except Exception:
                    continue
            logger.info("[StudentRegistry] loaded %d records from %s", len(self._store), path)
        except Exception as e:
            logger.warning("[StudentRegistry] failed to load from %s: %s", path, e)
        return self

    # ── Read operations ───────────────────────────────────────────────────────

    def get(self, roll_number: str) -> Optional[StudentProfile]:
        """
        Look up a student by roll number.
        Returns None if not found — never raises on bad input.
        """
        if not isinstance(roll_number, str):
            return None
        return self._store.get(roll_number.strip().upper())

    def exists(self, roll_number: str) -> bool:
        """Return True if the roll number is in the registry."""
        return self.get(roll_number) is not None

    def get_safe(self, roll_number: str) -> Optional[StudentProfile]:
        """
        Safe lookup with explicit format validation before hitting the store.
        Returns None for both missing and malformed roll numbers.
        """
        if not isinstance(roll_number, str):
            return None
        normalized = roll_number.strip().upper()
        if not ROLL_NUMBER_PATTERN.match(normalized):
            logger.warning("[StudentRegistry] malformed roll number: '%s'", roll_number)
            return None
        return self._store.get(normalized)

    def by_department(self, department: Department) -> List[StudentProfile]:
        """Return all active students in a department, sorted by roll number."""
        return sorted(
            [s for s in self._store.values() if s.department == department and s.is_active],
            key=lambda s: s.roll_number,
        )

    def by_year(self, year: AcademicYear) -> List[StudentProfile]:
        """Return all active students in a given year."""
        return [s for s in self._store.values() if s.year == year and s.is_active]

    def by_batch(
        self,
        department: Department,
        year: AcademicYear,
        batch: StudentBatch,
    ) -> List[StudentProfile]:
        """Return all active students in a specific dept/year/batch."""
        return [
            s for s in self._store.values()
            if s.department == department
            and s.year == year
            and s.batch == batch
            and s.is_active
        ]

    def all_active(self) -> List[StudentProfile]:
        """Return all active student profiles."""
        return [s for s in self._store.values() if s.is_active]

    def metadata(self, roll_number: str) -> Optional[dict]:
        """
        Return full metadata dict for a student, or None if not found.
        Safe for logging — no raw objects in output.
        """
        profile = self.get_safe(roll_number)
        return profile.to_dict() if profile else None

    # ── Utility ───────────────────────────────────────────────────────────────

    @property
    def count(self) -> int:
        return len(self._store)

    def __len__(self) -> int:
        return self.count

    def __iter__(self) -> Iterator[StudentProfile]:
        return iter(self._store.values())

    def __repr__(self) -> str:
        return f"<StudentRegistry records={self.count}>"


# ── Development fixture data ──────────────────────────────────────────────────

SAMPLE_STUDENTS: List[StudentProfile] = [
    StudentProfile(
        roll_number    = "CS2021001",
        full_name      = "Aman Koli",
        email          = "aman.koli@college.edu",
        department     = Department.COMPUTER_SCIENCE,
        year           = AcademicYear.THIRD,
        batch          = StudentBatch.A,
        program        = "B.Tech",
        photo_reference= "photos/CS2021001.jpg",
        is_active      = True,
    ),
    StudentProfile(
        roll_number    = "CS2021002",
        full_name      = "Raj Koli",
        email          = "raj.koli@college.edu",
        department     = Department.COMPUTER_SCIENCE,
        year           = AcademicYear.THIRD,
        batch          = StudentBatch.A,
        program        = "B.Tech",
        photo_reference= "photos/CS2021002.jpg",
        is_active      = True,
    ),
    StudentProfile(
        roll_number    = "IT2022010",
        full_name      = "Priya Sharma",
        email          = "priya.sharma@college.edu",
        department     = Department.INFORMATION_TECHNOLOGY,
        year           = AcademicYear.SECOND,
        batch          = StudentBatch.B,
        program        = "B.Tech",
        photo_reference= "photos/IT2022010.jpg",
        is_active      = True,
    ),
    StudentProfile(
        roll_number    = "DS2020005",
        full_name      = "Neha Patel",
        email          = "neha.patel@college.edu",
        department     = Department.DATA_SCIENCE,
        year           = AcademicYear.FOURTH,
        batch          = StudentBatch.C,
        program        = "B.Tech",
        photo_reference= "photos/DS2020005.jpg",
        is_active      = True,
    ),
    StudentProfile(
        roll_number    = "AI2023001",
        full_name      = "Arjun Mehta",
        email          = "arjun.mehta@college.edu",
        department     = Department.ARTIFICIAL_INTELLIGENCE,
        year           = AcademicYear.FIRST,
        batch          = StudentBatch.A,
        program        = "B.Tech",
        photo_reference= None,
        is_active      = True,
    ),
]
