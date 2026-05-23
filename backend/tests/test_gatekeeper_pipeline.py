"""
test_gatekeeper_pipeline.py
───────────────────────────
Tests for the End-to-End GATEKEEPER Verification Pipeline.

Covers:
- Success paths
- Face validation (stub)
- Face history (clone / swap)
- Auth Engine final decisions
"""

from __future__ import annotations

import pytest

from src.agents.gatekeeper.pipeline.gatekeeper_pipeline import GatekeeperPipeline
from src.agents.gatekeeper.face_verification.face_verifier import _OVERRIDE_PASS, _OVERRIDE_FAIL
from src.agents.gatekeeper.registry.registry_store import StudentRegistry
from src.agents.gatekeeper.registry.student_schema import StudentProfile, AcademicYear, Department, StudentBatch


@pytest.fixture
def test_registry():
    """A small registry for deterministic pipeline tests."""
    registry = StudentRegistry()
    registry.add(StudentProfile(
        roll_number="VALID001",
        full_name="Valid Student",
        email="valid@college.edu",
        photo_reference="photos/VALID001.jpg",
        is_active=True,
    ))
    registry.add(StudentProfile(
        roll_number="INACTIVE001",
        full_name="Inactive Student",
        email="inactive@college.edu",
        photo_reference="photos/INACTIVE001.jpg",
        is_active=False,
    ))
    registry.add(StudentProfile(
        roll_number="NOPHOTO001",
        full_name="No Photo Student",
        email="nophoto@college.edu",
        photo_reference=None,
        is_active=True,
    ))
    return registry


@pytest.fixture
def pipeline(test_registry):
    return GatekeeperPipeline(registry=test_registry)


def test_happy_path_exact_match(pipeline):
    """Valid roll + matching face -> GRANTED"""
    result = pipeline.run("VALID001", "photos/VALID001.jpg")
    assert result.is_admitted is True
    assert result.access_decision.decision.value == "granted"
    assert result.stage_results["roll_verification"]["is_verified"] is True
    assert result.stage_results["face_verification"]["matched"] is True
    assert result.stage_results["conflict_detection"]["has_conflict"] is False


def test_invalid_roll_denied(pipeline):
    """Roll number not in registry -> DENIED"""
    result = pipeline.run("UNKNOWN999", "photos/VALID001.jpg")
    assert result.is_admitted is False
    assert result.access_decision.decision.value == "denied"
    assert "UNKNOWN999" in result.access_decision.reasons[0]


def test_inactive_student_denied(pipeline):
    """Student is inactive -> DENIED"""
    result = pipeline.run("INACTIVE001", "photos/INACTIVE001.jpg")
    assert result.is_admitted is False
    assert result.access_decision.decision.value == "denied"
    assert "inactive" in result.access_decision.reasons[0].lower()


def test_no_photo_registered_denied(pipeline):
    """Student has no registered photo -> DENIED"""
    result = pipeline.run("NOPHOTO001", "some_face.jpg")
    assert result.is_admitted is False
    assert result.access_decision.decision.value == "denied"
    assert "No reference photo" in result.access_decision.reasons[0]


def test_face_mismatch_admin_review(pipeline):
    """Face does not match -> PENDING_ADMIN_REVIEW"""
    result = pipeline.run("VALID001", "wrong_face.jpg")
    assert result.is_admitted is False
    assert result.access_decision.decision.value == "pending_admin_review"
    assert result.access_decision.requires_admin_review is True
    assert "does not match" in result.access_decision.reasons[0]


def test_face_override_pass(pipeline):
    """Admin override PASS -> GRANTED"""
    result = pipeline.run("VALID001", _OVERRIDE_PASS)
    assert result.is_admitted is True


def test_face_override_fail(pipeline):
    """Admin override FAIL -> PENDING_ADMIN_REVIEW"""
    result = pipeline.run("VALID001", _OVERRIDE_FAIL)
    assert result.is_admitted is False
    assert result.access_decision.decision.value == "pending_admin_review"


def test_identity_swap_conflict(pipeline):
    """Same roll number uses different faces -> HIGH severity conflict -> DENIED"""
    # 1. First session: valid match
    r1 = pipeline.run("VALID001", "photos/VALID001.jpg")
    assert r1.is_admitted is True

    # 2. Second session: someone else forces an override pass on the same roll
    # Or just use the prefix matcher which also grants access
    r2 = pipeline.run("VALID001", "VALID001_some_other_cam.jpg")
    
    # We expect DENIED because the history checker sees a different face for VALID001
    assert r2.is_admitted is False
    assert r2.access_decision.decision.value == "denied"
    
    conflict = r2.stage_results["conflict_detection"]
    assert conflict["has_conflict"] is True
    assert conflict["conflict_type"] == "face_swap"
    assert conflict["severity"] == "high"


def test_identity_clone_conflict(test_registry):
    """Same face used for different roll numbers -> CRITICAL severity conflict -> DENIED"""
    # Add a second valid student
    test_registry.add(StudentProfile(
        roll_number="VALID002",
        full_name="Valid Student Two",
        email="valid2@college.edu",
        photo_reference="photos/VALID002.jpg",
        is_active=True,
    ))
    pipeline = GatekeeperPipeline(registry=test_registry)

    # 1. First student verifies using a face
    r1 = pipeline.run("VALID001", _OVERRIDE_PASS)
    assert r1.is_admitted is True

    # 2. Second student tries to use the exact same face
    r2 = pipeline.run("VALID002", _OVERRIDE_PASS)
    
    assert r2.is_admitted is False
    assert r2.access_decision.decision.value == "denied"

    conflict = r2.stage_results["conflict_detection"]
    assert conflict["has_conflict"] is True
    assert conflict["conflict_type"] == "face_clone"
    assert conflict["severity"] == "critical"
