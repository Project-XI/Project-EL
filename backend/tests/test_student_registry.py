"""
test_student_registry.py
─────────────────────────
Comprehensive test suite for the GATEKEEPER Student Registry.

Test categories (per Issue #14 acceptance criteria)
────────────────────────────────────────────────────
1. Student record storage tests
2. Roll-number lookup tests
3. Invalid roll number handling tests
4. Student metadata retrieval tests
5. Schema validation tests
6. GatekeeperAgent integration tests

Run:
    export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
    backend/venv/bin/python3 -m pytest backend/tests/test_student_registry.py -v
"""

from __future__ import annotations

import pytest
import asyncio
from typing import Optional

from src.agents.gatekeeper.registry.student_schema import (
    AcademicYear,
    Department,
    StudentBatch,
    StudentProfile,
    REGISTRY_SCHEMA_VERSION,
)
from src.agents.gatekeeper.registry.registry_store import (
    StudentRegistry,
    RegistryError,
    SAMPLE_STUDENTS,
)
from src.agents.gatekeeper.registry.lookup import (
    LookupFailureReason,
    LookupResult,
    RegistryLookup,
)
from src.agents.gatekeeper.agent import GatekeeperAgent


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _profile(
    roll: str = "CS2021001",
    name: str = "Aman Koli",
    email: str = "aman@college.edu",
    dept: Department = Department.COMPUTER_SCIENCE,
    year: AcademicYear = AcademicYear.THIRD,
    batch: StudentBatch = StudentBatch.A,
    active: bool = True,
) -> StudentProfile:
    return StudentProfile(
        roll_number    = roll,
        full_name      = name,
        email          = email,
        department     = dept,
        year           = year,
        batch          = batch,
        is_active      = active,
    )


def _registry(*profiles: StudentProfile) -> StudentRegistry:
    r = StudentRegistry()
    for p in profiles:
        r.add(p)
    return r


def _lookup(*profiles: StudentProfile) -> RegistryLookup:
    return RegistryLookup(_registry(*profiles))


# ══════════════════════════════════════════════════════════════════════════════
# 1. STUDENT RECORD STORAGE
# ══════════════════════════════════════════════════════════════════════════════

class TestStudentRecordStorage:

    def test_add_student_increments_count(self):
        r = StudentRegistry()
        r.add(_profile())
        assert r.count == 1

    def test_add_multiple_students(self):
        r = StudentRegistry()
        r.add(_profile("CS2021001"))
        r.add(_profile("CS2021002", name="Raj Koli", email="raj@college.edu"))
        assert r.count == 2

    def test_duplicate_roll_raises_error(self):
        r = StudentRegistry()
        r.add(_profile("CS2021001"))
        with pytest.raises(RegistryError):
            r.add(_profile("CS2021001"))

    def test_upsert_replaces_existing(self):
        r = StudentRegistry()
        r.add(_profile("CS2021001", name="Old Name"))
        r.upsert(_profile("CS2021001", name="New Name"))
        assert r.get("CS2021001").full_name == "New Name"

    def test_seed_loads_all_fixtures(self):
        r = StudentRegistry()
        r.seed(SAMPLE_STUDENTS)
        assert r.count == len(SAMPLE_STUDENTS)

    def test_seed_is_idempotent(self):
        r = StudentRegistry()
        r.seed(SAMPLE_STUDENTS)
        r.seed(SAMPLE_STUDENTS)   # second call should not raise
        assert r.count == len(SAMPLE_STUDENTS)

    def test_remove_existing_student(self):
        r = StudentRegistry()
        r.add(_profile("CS2021001"))
        removed = r.remove("CS2021001")
        assert removed is True
        assert r.count == 0

    def test_remove_nonexistent_returns_false(self):
        r = StudentRegistry()
        assert r.remove("NOTEXIST") is False

    def test_by_department_filters_correctly(self):
        r = StudentRegistry()
        r.add(_profile("CS2021001", dept=Department.COMPUTER_SCIENCE))
        r.add(_profile("IT2021001", name="Priya", email="priya@c.edu",
                       dept=Department.INFORMATION_TECHNOLOGY))
        cs = r.by_department(Department.COMPUTER_SCIENCE)
        assert len(cs) == 1
        assert cs[0].roll_number == "CS2021001"

    def test_by_batch_filters_correctly(self):
        r = StudentRegistry()
        r.add(_profile("CS2021001", batch=StudentBatch.A))
        r.add(_profile("CS2021002", name="Raj", email="raj@c.edu", batch=StudentBatch.B))
        batch_a = r.by_batch(Department.COMPUTER_SCIENCE, AcademicYear.THIRD, StudentBatch.A)
        assert len(batch_a) == 1

    def test_inactive_student_excluded_from_by_department(self):
        r = StudentRegistry()
        r.add(_profile("CS2021001", active=False))
        result = r.by_department(Department.COMPUTER_SCIENCE)
        assert len(result) == 0


# ══════════════════════════════════════════════════════════════════════════════
# 2. ROLL-NUMBER LOOKUP
# ══════════════════════════════════════════════════════════════════════════════

class TestRollNumberLookup:

    def test_lookup_existing_student_succeeds(self):
        result = _lookup(_profile("CS2021001")).by_roll_number("CS2021001")
        assert result.success is True
        assert result.profile.roll_number == "CS2021001"

    def test_lookup_case_insensitive(self):
        result = _lookup(_profile("CS2021001")).by_roll_number("cs2021001")
        assert result.success is True

    def test_lookup_strips_whitespace(self):
        result = _lookup(_profile("CS2021001")).by_roll_number("  CS2021001  ")
        assert result.success is True

    def test_lookup_missing_student_returns_failure(self):
        result = _lookup().by_roll_number("CS9999999")
        assert result.success is False
        assert result.failure_reason == LookupFailureReason.NOT_FOUND

    def test_is_valid_student_true_for_existing(self):
        lookup = _lookup(_profile("CS2021001"))
        assert lookup.is_valid_student("CS2021001") is True

    def test_is_valid_student_false_for_missing(self):
        lookup = _lookup()
        assert lookup.is_valid_student("CS9999999") is False

    def test_metadata_returns_dict(self):
        lookup = _lookup(_profile("CS2021001"))
        meta = lookup.metadata("CS2021001")
        assert isinstance(meta, dict)
        assert meta["success"] is True
        assert meta["profile"]["roll_number"] == "CS2021001"

    def test_metadata_returns_error_dict_for_missing(self):
        lookup = _lookup()
        meta = lookup.metadata("CS9999999")
        assert meta["success"] is False
        assert meta["profile"] is None


# ══════════════════════════════════════════════════════════════════════════════
# 3. INVALID ROLL NUMBER HANDLING
# ══════════════════════════════════════════════════════════════════════════════

class TestInvalidRollNumberHandling:

    def test_empty_string_returns_empty_input(self):
        result = _lookup().by_roll_number("")
        assert result.failure_reason == LookupFailureReason.EMPTY_INPUT

    def test_whitespace_only_returns_empty_input(self):
        result = _lookup().by_roll_number("   ")
        assert result.failure_reason == LookupFailureReason.EMPTY_INPUT

    def test_none_input_returns_empty_input(self):
        result = _lookup().by_roll_number(None)  # type: ignore
        assert result.failure_reason == LookupFailureReason.EMPTY_INPUT

    def test_too_short_roll_number_invalid_format(self):
        result = _lookup().by_roll_number("CS1")
        assert result.failure_reason == LookupFailureReason.INVALID_FORMAT

    def test_special_chars_invalid_format(self):
        result = _lookup().by_roll_number("CS-2021-001")
        assert result.failure_reason == LookupFailureReason.INVALID_FORMAT

    def test_spaces_in_roll_number_invalid_format(self):
        result = _lookup().by_roll_number("CS 2021001")
        assert result.failure_reason == LookupFailureReason.INVALID_FORMAT

    def test_inactive_student_returns_inactive_reason(self):
        r = StudentRegistry()
        r.add(_profile("CS2021001", active=False))
        lookup = RegistryLookup(r)
        result = lookup.by_roll_number("CS2021001")
        assert result.failure_reason == LookupFailureReason.STUDENT_INACTIVE

    def test_lookup_never_raises(self):
        """No matter what input, lookup should never raise an exception."""
        lookup = _lookup()
        for bad_input in ["", None, "!@#$", "A" * 100, 12345, [], {}]:
            try:
                result = lookup.by_roll_number(bad_input)  # type: ignore
                assert result.success is False
            except Exception as e:
                pytest.fail(f"Lookup raised unexpectedly for input {bad_input!r}: {e}")

    def test_get_safe_returns_none_for_malformed(self):
        r = StudentRegistry()
        assert r.get_safe("CS-BAD!") is None

    def test_result_to_dict_always_serializable(self):
        import json
        result = _lookup().by_roll_number("BADFORMAT!!!")
        d = result.to_dict()
        json.dumps(d)   # Must not raise


# ══════════════════════════════════════════════════════════════════════════════
# 4. STUDENT METADATA RETRIEVAL
# ══════════════════════════════════════════════════════════════════════════════

class TestStudentMetadataRetrieval:

    def test_profile_to_dict_has_all_fields(self):
        p = _profile()
        d = p.to_dict()
        for key in ["roll_number", "full_name", "email", "department",
                    "year", "batch", "program", "photo_reference", "is_active"]:
            assert key in d

    def test_metadata_via_registry_returns_dict(self):
        r = StudentRegistry()
        r.add(_profile("CS2021001"))
        meta = r.metadata("CS2021001")
        assert meta is not None
        assert meta["roll_number"] == "CS2021001"

    def test_metadata_none_for_missing(self):
        r = StudentRegistry()
        assert r.metadata("NOTHERE") is None

    def test_photo_reference_stored_correctly(self):
        p = StudentProfile(
            roll_number    = "CS2021001",
            full_name      = "Aman Koli",
            email          = "aman@college.edu",
            department     = Department.COMPUTER_SCIENCE,
            year           = AcademicYear.THIRD,
            batch          = StudentBatch.A,
            photo_reference= "photos/CS2021001.jpg",
        )
        r = StudentRegistry()
        r.add(p)
        fetched = r.get("CS2021001")
        assert fetched.photo_reference == "photos/CS2021001.jpg"

    def test_department_value_in_metadata(self):
        r = StudentRegistry()
        r.add(_profile("CS2021001"))
        meta = r.metadata("CS2021001")
        assert meta["department"] == "CS"

    def test_all_active_returns_only_active(self):
        r = StudentRegistry()
        r.add(_profile("CS2021001", active=True))
        r.add(_profile("CS2021002", name="Raj", email="raj@c.edu", active=False))
        assert len(r.all_active()) == 1


# ══════════════════════════════════════════════════════════════════════════════
# 5. SCHEMA VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

class TestSchemaValidation:

    def test_valid_profile_creates_without_error(self):
        p = _profile()
        assert p.roll_number == "CS2021001"

    def test_roll_number_uppercased_automatically(self):
        p = _profile("cs2021001")
        assert p.roll_number == "CS2021001"

    def test_invalid_roll_number_raises_validation_error(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            _profile("cs-2021-001!")

    def test_email_lowercased_automatically(self):
        p = _profile(email="AMAN@COLLEGE.EDU")
        assert p.email == "aman@college.edu"

    def test_invalid_email_raises(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            _profile(email="notanemail")

    def test_name_too_short_raises(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            _profile(name="A")

    def test_profile_is_immutable(self):
        p = _profile()
        with pytest.raises(Exception):
            p.full_name = "Changed"   # type: ignore

    def test_schema_version_present(self):
        p = _profile()
        assert p.schema_version == REGISTRY_SCHEMA_VERSION


# ══════════════════════════════════════════════════════════════════════════════
# 6. GATEKEEPERAGENT INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════

class TestGatekeeperAgentIntegration:

    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def _agent_with(self, *profiles: StudentProfile) -> GatekeeperAgent:
        r = StudentRegistry()
        for p in profiles:
            r.add(p)
        return GatekeeperAgent(registry=r)

    def test_valid_roll_number_returns_verified(self):
        agent = self._agent_with(_profile("CS2021001"))
        result = self._run(
            agent.process("sess1", {"roll_number": "CS2021001"})
        )
        assert result["gatekeeper_status"] == "verified"

    def test_verified_result_contains_student_profile(self):
        agent = self._agent_with(_profile("CS2021001"))
        result = self._run(
            agent.process("sess1", {"roll_number": "CS2021001"})
        )
        assert result["student_profile"] is not None
        assert result["student_profile"]["roll_number"] == "CS2021001"

    def test_missing_roll_number_returns_rejected(self):
        agent = self._agent_with()
        result = self._run(
            agent.process("sess1", {"roll_number": "CS9999999"})
        )
        assert result["gatekeeper_status"] == "rejected"
        assert result["student_profile"] is None

    def test_empty_roll_number_returns_rejected(self):
        agent = self._agent_with(_profile())
        result = self._run(
            agent.process("sess1", {"roll_number": ""})
        )
        assert result["gatekeeper_status"] == "rejected"
        assert result["gatekeeper_reason"] == LookupFailureReason.EMPTY_INPUT.value

    def test_rejected_result_contains_reason(self):
        agent = self._agent_with()
        result = self._run(
            agent.process("sess1", {"roll_number": "NOTEXIST"})
        )
        assert result["gatekeeper_reason"] == LookupFailureReason.NOT_FOUND.value

    def test_input_data_passed_through_on_success(self):
        agent = self._agent_with(_profile("CS2021001"))
        result = self._run(
            agent.process("sess1", {"roll_number": "CS2021001", "project_url": "http://example.com"})
        )
        assert result.get("project_url") == "http://example.com"

    def test_agent_exposes_registry(self):
        agent = self._agent_with(_profile("CS2021001"))
        assert agent.registry.count == 1

    def test_default_agent_seeds_sample_students(self):
        agent = GatekeeperAgent()
        assert agent.registry.count == len(SAMPLE_STUDENTS)
