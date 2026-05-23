"""
test_roll_verification.py
──────────────────────────
Comprehensive test suite for the GATEKEEPER Roll Number Verification Flow.

Uses the REAL student roster (35 students) as test fixtures.

Test categories (per Issue #16 acceptance criteria)
────────────────────────────────────────────────────
1. Student profile fetch tests (real roll numbers)
2. Invalid roll number rejection tests
3. Official student info display tests
4. Registry integration tests
5. Batch verification tests
6. Manual verification flow tests

Run:
    export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
    backend/venv/bin/python3 -m pytest backend/tests/test_roll_verification.py -v
"""

from __future__ import annotations

import pytest
from typing import List

from src.agents.gatekeeper.roll_verification.fixtures import (
    STUDENT_REGISTRY_FIXTURES,
    VALID_ROLL_NUMBERS,
    ROLL_TO_NAME,
    build_fixture_registry,
)
from src.agents.gatekeeper.roll_verification.display import (
    StudentDisplayCard,
    format_display_card,
    format_not_found,
    format_inactive,
)
from src.agents.gatekeeper.roll_verification.flow import (
    FlowStatus,
    RollVerificationFlow,
    VerificationFlowResult,
)
from src.agents.gatekeeper.registry.student_schema import (
    AcademicYear,
    Department,
    StudentProfile,
    StudentBatch,
)
from src.agents.gatekeeper.registry.registry_store import StudentRegistry


# ── Helpers ───────────────────────────────────────────────────────────────────

def _flow(require_manual: bool = False) -> RollVerificationFlow:
    return RollVerificationFlow(require_manual_confirmation=require_manual)


# ══════════════════════════════════════════════════════════════════════════════
# 1. STUDENT PROFILE FETCH TESTS (real roll numbers)
# ══════════════════════════════════════════════════════════════════════════════

class TestStudentProfileFetch:

    def test_raj_rasal_verified(self):
        result = _flow().verify("150096725066")
        assert result.is_verified
        assert result.display_card.full_name == "Raj Rasal"

    def test_sahil_ghone_verified(self):
        result = _flow().verify("150096725002")
        assert result.is_verified
        assert "Sahil" in result.display_card.full_name

    def test_all_35_real_students_verified(self):
        """Every student in the official roster must verify successfully."""
        flow = _flow()
        failed = []
        for roll in VALID_ROLL_NUMBERS:
            result = flow.verify(roll)
            if not result.is_verified:
                failed.append((roll, result.status))
        assert failed == [], f"These students failed verification: {failed}"

    def test_verified_result_has_correct_roll_number(self):
        result = _flow().verify("150096725069")
        assert result.roll_number == "150096725069"

    def test_verified_result_has_display_card(self):
        result = _flow().verify("150096725080")   # Dharmit Sathvara
        assert result.display_card is not None

    def test_display_card_name_matches_roster(self):
        for roll, expected_name in ROLL_TO_NAME.items():
            result = _flow().verify(roll)
            assert result.display_card.full_name == expected_name, (
                f"Name mismatch for {roll}: got '{result.display_card.full_name}', "
                f"expected '{expected_name}'"
            )

    def test_verified_profile_has_photo_reference(self):
        result = _flow().verify("150096725089")   # Pranav Santhosh Nair
        assert result.display_card.photo_reference == "photos/150096725089.jpg"

    def test_verified_profile_email_derived_from_roll(self):
        result = _flow().verify("150096725002")
        assert result.display_card.email == "150096725002@college.edu"

    def test_verified_status_is_active(self):
        result = _flow().verify("150096725048")   # Aaryan Kuchekar
        assert result.display_card.status_label == "ACTIVE"

    # Spot checks for name casing / normalization
    @pytest.mark.parametrize("roll,expected", [
        ("150096725052", "Shivam Sah"),         # was SHIVAM SAH
        ("150096725089", "Pranav Santhosh Nair"),# was PRANAV Santhosh NAIR
        ("150096725048", "Aaryan Kuchekar"),     # was Aaryan kuchekar
    ])
    def test_name_title_cased(self, roll, expected):
        result = _flow().verify(roll)
        assert result.display_card.full_name == expected


# ══════════════════════════════════════════════════════════════════════════════
# 2. INVALID ROLL NUMBER REJECTION TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestInvalidRollNumberRejection:

    def test_empty_string_rejected(self):
        result = _flow().verify("")
        assert result.status == FlowStatus.INVALID

    def test_whitespace_only_rejected(self):
        result = _flow().verify("   ")
        assert result.status == FlowStatus.INVALID

    def test_none_rejected(self):
        result = _flow().verify(None)   # type: ignore
        assert result.status == FlowStatus.INVALID

    def test_too_short_rejected(self):
        result = _flow().verify("123")
        assert result.status == FlowStatus.INVALID

    def test_special_chars_rejected(self):
        result = _flow().verify("150096-725002")
        assert result.status == FlowStatus.INVALID

    def test_spaces_in_roll_rejected(self):
        result = _flow().verify("150096 725002")
        assert result.status == FlowStatus.INVALID

    def test_nonexistent_valid_format_not_found(self):
        result = _flow().verify("150096799999")
        assert result.status == FlowStatus.NOT_FOUND

    def test_rejected_result_has_no_display_card(self):
        result = _flow().verify("")
        assert result.display_card is None

    def test_rejected_result_is_rejected_property(self):
        result = _flow().verify("BADROLLNUM!!")
        assert result.is_rejected is True

    def test_rejected_result_has_helpful_message(self):
        result = _flow().verify("150096799999")
        assert "150096799999" in result.message

    def test_flow_never_raises_on_garbage_input(self):
        """Verification flow must never raise — handles all input gracefully."""
        bad_inputs = ["", None, "!!!", "A" * 100, 12345, [], {}]
        flow = _flow()
        for bad in bad_inputs:
            try:
                result = flow.verify(bad)   # type: ignore
                assert result.is_rejected or result.is_verified
            except Exception as e:
                pytest.fail(f"Flow raised on input {bad!r}: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# 3. OFFICIAL STUDENT INFO DISPLAY TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestOfficialStudentInfoDisplay:

    def test_display_card_has_all_required_fields(self):
        result = _flow().verify("150096725066")
        card = result.display_card
        assert card.roll_number
        assert card.full_name
        assert card.email
        assert card.department
        assert card.year
        assert card.batch
        assert card.program
        assert card.status_label in ("ACTIVE", "INACTIVE")

    def test_pretty_output_contains_roll_number(self):
        result = _flow().verify("150096725066")
        pretty = result.display_card.pretty()
        assert "150096725066" in pretty

    def test_pretty_output_contains_name(self):
        result = _flow().verify("150096725066")
        pretty = result.display_card.pretty()
        assert "Raj Rasal" in pretty

    def test_one_line_contains_roll_and_name(self):
        result = _flow().verify("150096725066")
        line = result.display_card.one_line()
        assert "150096725066" in line and "Raj Rasal" in line

    def test_to_dict_all_plain_types(self):
        import json
        result = _flow().verify("150096725066")
        d = result.display_card.to_dict()
        json.dumps(d)   # Must not raise

    def test_format_not_found_message_contains_roll(self):
        msg = format_not_found("UNKNOWNROLL")
        assert "UNKNOWNROLL" in msg

    def test_format_inactive_message_contains_name(self):
        profile = STUDENT_REGISTRY_FIXTURES[0]
        card = format_display_card(profile)
        msg = format_inactive(card)
        assert profile.full_name in msg

    def test_result_to_dict_serializable(self):
        import json
        result = _flow().verify("150096725073")
        json.dumps(result.to_dict())   # Must not raise


# ══════════════════════════════════════════════════════════════════════════════
# 4. REGISTRY INTEGRATION TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestRegistryIntegration:

    def test_fixture_registry_has_35_students(self):
        registry = build_fixture_registry()
        assert registry.count == 35

    def test_fixture_registry_get_by_roll(self):
        registry = build_fixture_registry()
        profile = registry.get("150096725066")
        assert profile is not None
        assert profile.full_name == "Raj Rasal"

    def test_fixture_registry_all_active(self):
        registry = build_fixture_registry()
        active = registry.all_active()
        assert len(active) == 35

    def test_custom_registry_injected_into_flow(self):
        registry = StudentRegistry()
        registry.add(StudentProfile(
            roll_number = "TESTROLL001",
            full_name   = "Test Student",
            email       = "test@college.edu",
            department  = Department.COMPUTER_SCIENCE,
            year        = AcademicYear.FIRST,
            batch       = StudentBatch.A,
        ))
        flow   = RollVerificationFlow(registry=registry)
        result = flow.verify("TESTROLL001")
        assert result.is_verified
        assert result.display_card.full_name == "Test Student"

    def test_registry_size_property(self):
        flow = _flow()
        assert flow.registry_size == 35

    def test_inactive_student_returns_inactive_status(self):
        """Add an inactive student and verify the flow returns INACTIVE."""
        registry = StudentRegistry()
        registry.add(StudentProfile(
            roll_number = "INACTIVE001",
            full_name   = "Inactive Student",
            email       = "inactive@college.edu",
            department  = Department.COMPUTER_SCIENCE,
            year        = AcademicYear.SECOND,
            batch       = StudentBatch.B,
            is_active   = False,
        ))
        flow   = RollVerificationFlow(registry=registry)
        result = flow.verify("INACTIVE001")
        assert result.status == FlowStatus.INACTIVE
        assert result.is_rejected is True


# ══════════════════════════════════════════════════════════════════════════════
# 5. BATCH VERIFICATION TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestBatchVerification:

    def test_batch_all_valid_returns_all_verified(self):
        flow = _flow()
        rolls = ["150096725002", "150096725066", "150096725089"]
        results = flow.verify_batch(rolls)
        assert flow.verified_count(results) == 3

    def test_batch_mixed_returns_correct_counts(self):
        flow = _flow()
        rolls = ["150096725002", "BADROLLNUM", "150096799999"]
        results = flow.verify_batch(rolls)
        assert flow.verified_count(results) == 1
        assert flow.rejected_count(results) == 2

    def test_batch_preserves_all_inputs(self):
        flow = _flow()
        rolls = ["150096725002", "150096725066"]
        results = flow.verify_batch(rolls)
        assert set(results.keys()) == set(rolls)

    def test_batch_all_35_students(self):
        flow = _flow()
        results = flow.verify_batch(list(VALID_ROLL_NUMBERS))
        assert flow.verified_count(results) == 35
        assert flow.rejected_count(results) == 0

    def test_batch_empty_list(self):
        flow = _flow()
        results = flow.verify_batch([])
        assert results == {}


# ══════════════════════════════════════════════════════════════════════════════
# 6. MANUAL VERIFICATION FLOW TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestManualVerificationFlow:

    def test_manual_mode_verified_result_flagged(self):
        flow   = _flow(require_manual=True)
        result = flow.verify("150096725066")
        assert result.is_verified
        assert result.requires_manual is True

    def test_non_manual_mode_not_flagged(self):
        flow   = _flow(require_manual=False)
        result = flow.verify("150096725066")
        assert result.requires_manual is False

    def test_manual_mode_display_card_still_present(self):
        flow   = _flow(require_manual=True)
        result = flow.verify("150096725066")
        assert result.display_card is not None

    def test_manual_mode_rejected_not_flagged(self):
        """Manual flag only applies to VERIFIED — rejected stays False."""
        flow   = _flow(require_manual=True)
        result = flow.verify("NOTEXIST")
        assert result.requires_manual is False

    def test_result_status_enum_valid(self):
        result = _flow().verify("150096725066")
        assert result.status in list(FlowStatus)
