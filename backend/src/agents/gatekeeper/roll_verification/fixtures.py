"""
fixtures.py
───────────
Official student registry fixtures for the Roll Number Verification Flow.

This file contains the real student roster used as test fixtures to validate
that the verification pipeline correctly identifies, fetches, and displays
student profiles from actual roll numbers.

Data source: Official class roster (provided 2026-05-23)
Roll number format: 12-digit numeric string (e.g. 150096725002)

Rules
─────
- All names are title-cased for consistency.
- Department defaults to CS, Year to THIRD, Batch to A (same cohort).
- Photo reference follows convention: photos/<roll_number>.jpg
- Use build_fixture_registry() to get a seeded StudentRegistry.
"""

from __future__ import annotations

from typing import List

from src.agents.gatekeeper.registry.student_schema import (
    AcademicYear,
    Department,
    StudentBatch,
    StudentProfile,
)
from src.agents.gatekeeper.registry.registry_store import StudentRegistry


# ── Real student roster ───────────────────────────────────────────────────────
# Format: (sr_no, roll_number, full_name)

_RAW_ROSTER = [
    (1,  "150096725002", "Sahil Ganesh Ghone"),
    (7,  "150096725009", "Yuvraj Jitendra Singh"),
    (9,  "150096725011", "Ajit Anil Singh"),
    (10, "150096725012", "Ayush Kumar Singh"),
    (16, "150096725020", "Tanish Gawade"),
    (18, "150096725022", "Kunal Lubhana"),
    (25, "150096725029", "Aaditya Manoj Bhosale"),
    (28, "150096725032", "Prince Yadav"),
    (30, "150096725034", "Arnesh Munj"),
    (34, "150096725039", "Sahil Kumar"),
    (40, "150096725045", "Sejal Singh"),
    (42, "150096725048", "Aaryan Kuchekar"),
    (44, "150096725050", "Ankitraj Jha"),
    (46, "150096725052", "Shivam Sah"),
    (49, "150096725056", "Mukesh Choudhary"),
    (50, "150096725057", "Aryaa Bhadane"),
    (52, "150096725060", "Dhruv Chavda"),
    (53, "150096725061", "Aditya Khare"),
    (58, "150096725066", "Raj Rasal"),
    (59, "150096725067", "Sairaj Jadhav"),
    (60, "150096725068", "Rishi Thakker"),
    (61, "150096725069", "Atharva Chaurasiya"),
    (62, "150096725070", "Aditya Sunil Chouksey"),
    (65, "150096725073", "Saudamini Basant Nayak"),
    (67, "150096725075", "Arman Choudhary"),
    (69, "150096725079", "Vaishnavi Sanjay Sankhala"),
    (70, "150096725080", "Dharmit Sathvara"),
    (77, "150096725089", "Pranav Santhosh Nair"),
    (78, "150096725091", "Danesh Mavji Joishar"),
    (79, "150096725092", "Tanay Siddharth Shelar"),
    (81, "150096725095", "Parthiv Kumar"),
    (83, "150096725097", "Pari Pankaj Gothi"),
    (86, "150096725101", "Shankar Mupanna"),
    (87, "150096725102", "Pragati Naidu"),
    (90, "150096725105", "Harsh Kumar"),
]


def _make_profile(sr_no: int, roll_number: str, full_name: str) -> StudentProfile:
    """Build a StudentProfile from roster row with sensible defaults."""
    return StudentProfile(
        roll_number     = roll_number,
        full_name       = full_name.strip().title(),
        email           = f"{roll_number}@college.edu",
        department      = Department.COMPUTER_SCIENCE,
        year            = AcademicYear.THIRD,
        batch           = StudentBatch.A,
        program         = "B.Tech",
        photo_reference = f"photos/{roll_number}.jpg",
        is_active       = True,
    )


# ── Public fixture list ───────────────────────────────────────────────────────

STUDENT_REGISTRY_FIXTURES: List[StudentProfile] = [
    _make_profile(sr, roll, name)
    for sr, roll, name in _RAW_ROSTER
]

# Convenience: set of all valid roll numbers for quick membership tests
VALID_ROLL_NUMBERS: frozenset = frozenset(roll for _, roll, _ in _RAW_ROSTER)

# Convenience: roll → name mapping for quick display
ROLL_TO_NAME: dict = {roll: name.strip().title() for _, roll, name in _RAW_ROSTER}


def build_fixture_registry() -> StudentRegistry:
    """
    Return a StudentRegistry pre-seeded with the official student roster.

    Usage:
        registry = build_fixture_registry()
        profile  = registry.get("150096725066")   # Raj Rasal
    """
    registry = StudentRegistry()
    registry.seed(STUDENT_REGISTRY_FIXTURES)
    return registry
