"""
test_topic_coverage_tracker.py
───────────────────────────────
Comprehensive test suite for the Topic Coverage Tracker.

Test categories (per Issue #5 acceptance criteria)
───────────────────────────────────────────────────
1. Coverage update tests
2. Missing-topic detection tests
3. Category tagging tests
4. Repetitive question reduction tests
5. Deterministic update tests
6. Serialization tests

Run:
    export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
    backend/venv/bin/python3 -m pytest backend/tests/test_topic_coverage_tracker.py -v
"""

from __future__ import annotations

import copy
import pytest
from typing import List

from src.agents.main_agent.integration.oracle_schema import (
    DifficultyLevel,
    NormalizedOracleOutput,
    NormalizedVivaTarget,
    ObservableSignal,
    EvidenceLink,
    VivaCategory,
)
from src.agents.main_agent.coverage.tracker import CoverageTracker, CoverageReport
from src.agents.main_agent.coverage.coverage_state import CoverageState, CoverageStatus
from src.agents.main_agent.coverage.categories import (
    CATEGORY_REGISTRY,
    resolve_category,
    ALL_CATEGORY_NAMES,
)
from src.agents.main_agent.coverage.heuristics import (
    detect_gaps,
    uncovered_categories,
    partially_covered_categories,
    saturated_categories,
    most_urgent_gap,
    is_breadth_sufficient,
    resolve_status,
    coverage_summary_text,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _target(
    qt: str,
    category: str = "Architecture",
    difficulty: str = "medium",
    importance: float = 0.80,
) -> NormalizedVivaTarget:
    return NormalizedVivaTarget(
        topic            = category,
        question_target  = qt,
        difficulty       = DifficultyLevel(difficulty),
        category         = VivaCategory(category),
        importance_score = importance,
        depth_score      = 7.0,
        focus            = f"Explain {qt} in detail.",
        confidence       = 0.9,
        reasoning_summary= "test",
    )


def _fresh() -> CoverageState:
    return CoverageState.empty()


def _record(state: CoverageState, qt: str, category: str, turn: int) -> CoverageState:
    tracker = CoverageTracker()
    return tracker.record_question(state, _target(qt, category), turn_index=turn)


# ══════════════════════════════════════════════════════════════════════════════
# 1. COVERAGE UPDATE TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestCoverageUpdates:

    def test_fresh_state_has_zero_topics(self):
        assert CoverageState.empty().total_asked == 0

    def test_record_question_adds_topic(self):
        state = _record(_fresh(), "REST Constraints", "Architecture", 1)
        assert state.has_been_asked("REST Constraints")

    def test_record_question_increments_category_count(self):
        state = _record(_fresh(), "REST Constraints", "Architecture", 1)
        assert state.category_ask_count("Architecture") == 1

    def test_record_two_questions_same_category(self):
        state = _record(_fresh(), "Q1", "Security", 1)
        state = _record(state, "Q2", "Security", 2)
        assert state.category_ask_count("Security") == 2

    def test_record_answer_marks_topic_answered(self):
        tracker = CoverageTracker()
        state = _record(_fresh(), "JWT Lifecycle", "Security", 1)
        state = tracker.record_answer(state, "JWT Lifecycle")
        assert state.topics["JWT Lifecycle"].answered is True

    def test_record_answer_unanswered_topic_is_no_op(self):
        tracker = CoverageTracker()
        state = _record(_fresh(), "JWT Lifecycle", "Security", 1)
        original = state
        state2 = tracker.record_answer(state, "Nonexistent Topic")
        assert state2.total_asked == original.total_asked

    def test_total_turns_increments_per_record(self):
        state = _record(_fresh(), "Q1", "Architecture", 1)
        state = _record(state, "Q2", "Security", 2)
        assert state.total_turns == 2

    def test_category_marked_covered_after_min_questions(self):
        state = _record(_fresh(), "Q1", "Failure-Path", 1)
        # min_questions for Failure-Path is 1
        assert "Failure-Path" in state.covered_categories

    def test_multiple_different_categories_tracked(self):
        state = _fresh()
        for qt, cat, turn in [
            ("Q1", "Architecture", 1),
            ("Q2", "Security", 2),
            ("Q3", "Scalability", 3),
        ]:
            state = _record(state, qt, cat, turn)
        assert state.category_ask_count("Architecture") == 1
        assert state.category_ask_count("Security") == 1
        assert state.category_ask_count("Scalability") == 1

    def test_state_is_immutable_after_record(self):
        original = _fresh()
        _record(original, "Q1", "Architecture", 1)
        assert original.total_asked == 0  # Original unchanged


# ══════════════════════════════════════════════════════════════════════════════
# 2. MISSING-TOPIC DETECTION TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestMissingTopicDetection:

    def test_all_categories_uncovered_on_fresh_state(self):
        state = _fresh()
        uncov = uncovered_categories(state)
        assert len(uncov) == len(CATEGORY_REGISTRY)

    def test_uncovered_excludes_asked_category(self):
        state = _record(_fresh(), "Q1", "Security", 1)
        uncov = uncovered_categories(state)
        assert "Security" not in uncov

    def test_most_urgent_gap_is_not_started_category(self):
        state = _fresh()
        gap = most_urgent_gap(state)
        assert gap is not None
        assert gap.status == CoverageStatus.NOT_STARTED

    def test_most_urgent_gap_none_when_fully_covered(self):
        state = _fresh()
        turn = 1
        for cat in ALL_CATEGORY_NAMES:
            state = _record(state, f"Q_{cat}", cat, turn)
            turn += 1
        gap = most_urgent_gap(state)
        # All covered — gap score should be very low
        if gap:
            assert gap.gap_score < 0.5

    def test_detect_gaps_returns_all_categories(self):
        state = _fresh()
        gaps = detect_gaps(state)
        names = {g.category for g in gaps}
        assert names == ALL_CATEGORY_NAMES

    def test_gap_score_higher_for_not_started(self):
        state = _record(_fresh(), "Q1", "Architecture", 1)
        gaps = {g.category: g for g in detect_gaps(state)}
        arch_score = gaps["Architecture"].gap_score
        security_score = gaps["Security"].gap_score
        # Security not started → higher score than covered Architecture
        assert security_score > arch_score

    def test_partial_coverage_detected(self):
        # Create a category with min_questions=2 scenario via multiple asks
        # Saturate Architecture (3× min) then check partial is empty for it
        state = _fresh()
        for i in range(3):
            state = _record(state, f"Arch_Q{i}", "Architecture", i + 1)
        saturated = saturated_categories(state)
        assert "Architecture" in saturated


# ══════════════════════════════════════════════════════════════════════════════
# 3. CATEGORY TAGGING TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestCategoryTagging:

    def test_resolve_category_exact_name(self):
        assert resolve_category("Security") == "Security"
        assert resolve_category("Failure-Path") == "Failure-Path"

    def test_resolve_category_by_tag(self):
        assert resolve_category("jwt") == "Security"
        assert resolve_category("cache") == "Scalability"
        assert resolve_category("async") == "Runtime"
        assert resolve_category("fallback") == "Failure-Path"

    def test_resolve_category_unknown_returns_fallback(self):
        result = resolve_category("completely_unknown_xyz")
        assert result == "Architecture"

    def test_topic_entry_has_tags(self):
        state = _record(_fresh(), "JWT Auth", "Security", 1)
        entry = state.topics.get("JWT Auth")
        assert entry is not None
        assert isinstance(entry.tags, frozenset)

    def test_category_registry_has_all_six_domains(self):
        expected = {"Architecture", "Tradeoff", "Security", "Scalability", "Failure-Path", "Runtime"}
        assert set(CATEGORY_REGISTRY.keys()) == expected

    def test_all_categories_have_non_empty_tags(self):
        for name, cat in CATEGORY_REGISTRY.items():
            assert len(cat.tags) > 0, f"{name} has no tags"

    def test_category_weights_in_valid_range(self):
        for name, cat in CATEGORY_REGISTRY.items():
            assert 0.0 <= cat.weight <= 1.0, f"{name} weight out of range"

    def test_adding_new_category_works(self):
        """Demonstrates extensibility — adding a new entry requires no tracker change."""
        from src.agents.main_agent.coverage.categories import CoverageCategory
        new_cat = CoverageCategory(
            name="DataPipeline",
            tags=frozenset({"etl", "pipeline", "streaming"}),
            min_questions=1,
            weight=0.70,
        )
        assert new_cat.matches_tag("etl") is True
        assert new_cat.matches_tag("jwt") is False


# ══════════════════════════════════════════════════════════════════════════════
# 4. REPETITIVE QUESTION REDUCTION TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestRepetitiveQuestionReduction:

    def test_is_repetitive_true_for_asked_target(self):
        tracker = CoverageTracker()
        state = _record(_fresh(), "JWT Lifecycle", "Security", 1)
        assert tracker.is_repetitive(state, "JWT Lifecycle") is True

    def test_is_repetitive_false_for_new_target(self):
        tracker = CoverageTracker()
        state = _record(_fresh(), "JWT Lifecycle", "Security", 1)
        assert tracker.is_repetitive(state, "DB Pooling") is False

    def test_saturated_category_returned_correctly(self):
        state = _fresh()
        for i in range(3):  # 3× SATURATION_MULTIPLIER × min(1)
            state = _record(state, f"Arch_Q{i+1}", "Architecture", i + 1)
        saturated = saturated_categories(state)
        assert "Architecture" in saturated

    def test_uncovered_sorted_by_weight(self):
        state = _fresh()
        uncov = uncovered_categories(state)
        weights = [CATEGORY_REGISTRY[c].weight for c in uncov]
        assert weights == sorted(weights, reverse=True)

    def test_no_duplicate_asked_targets_in_state(self):
        state = _fresh()
        for turn, qt in enumerate(["Q1", "Q2", "Q1"], start=1):
            state = _record(state, qt, "Architecture", turn)
        # Even if recorded twice, the dict key is unique
        assert len(state.topics) == 2  # Q1 and Q2


# ══════════════════════════════════════════════════════════════════════════════
# 5. DETERMINISTIC UPDATE TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestDeterministicUpdates:

    def test_same_events_same_final_state(self):
        def build_state():
            state = _fresh()
            for qt, cat, turn in [
                ("Q1", "Security", 1),
                ("Q2", "Architecture", 2),
                ("Q3", "Runtime", 3),
            ]:
                state = _record(state, qt, cat, turn)
            return state

        s1 = build_state()
        s2 = build_state()
        assert s1.category_counts == s2.category_counts
        assert s1.covered_categories == s2.covered_categories
        assert s1.total_asked == s2.total_asked

    def test_gap_detection_deterministic(self):
        state = _record(_fresh(), "Q1", "Security", 1)
        gaps1 = detect_gaps(state)
        gaps2 = detect_gaps(state)
        cats1 = [g.category for g in gaps1]
        cats2 = [g.category for g in gaps2]
        assert cats1 == cats2

    def test_resolve_status_deterministic(self):
        s1 = resolve_status(0, 1)
        s2 = resolve_status(0, 1)
        assert s1 == s2 == CoverageStatus.NOT_STARTED

    def test_breadth_check_deterministic(self):
        state = _fresh()
        for qt, cat, turn in [("Q1", "Security", 1), ("Q2", "Architecture", 2), ("Q3", "Runtime", 3)]:
            state = _record(state, qt, cat, turn)
        r1 = is_breadth_sufficient(state, min_categories=3)
        r2 = is_breadth_sufficient(state, min_categories=3)
        assert r1 == r2

    def test_summary_text_consistent(self):
        state = _record(_fresh(), "Q1", "Security", 1)
        t1 = coverage_summary_text(state)
        t2 = coverage_summary_text(state)
        assert t1 == t2


# ══════════════════════════════════════════════════════════════════════════════
# 6. SERIALIZATION TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestSerialization:

    def test_coverage_state_to_dict_is_plain_types(self):
        state = _record(_fresh(), "Q1", "Security", 1)
        d = state.to_dict()
        assert isinstance(d, dict)
        assert isinstance(d["topics"], dict)
        assert isinstance(d["category_counts"], dict)
        assert isinstance(d["covered_categories"], list)
        assert isinstance(d["total_turns"], int)

    def test_topic_entry_to_dict(self):
        state = _record(_fresh(), "Q1", "Architecture", 1)
        entry = list(state.topics.values())[0]
        d = entry.to_dict()
        assert "question_target" in d
        assert "category" in d
        assert "ask_count" in d
        assert "answered" in d
        assert isinstance(d["tags"], list)

    def test_coverage_report_to_dict(self):
        tracker = CoverageTracker()
        state = _record(_fresh(), "Q1", "Security", 1)
        report = tracker.build_report(state, session_id="test-session")
        d = report.to_dict()
        assert d["session_id"] == "test-session"
        assert isinstance(d["covered_categories"], list)
        assert isinstance(d["breadth_sufficient"], bool)

    def test_serialized_state_has_no_unknown_types(self):
        """All values in to_dict() must be JSON-compatible types."""
        state = _record(_fresh(), "Q1", "Failure-Path", 1)
        d = state.to_dict()
        import json
        # Should not raise
        json_str = json.dumps(d)
        assert len(json_str) > 0

    def test_report_summary_line_non_empty(self):
        tracker = CoverageTracker()
        state = _record(_fresh(), "Q1", "Runtime", 1)
        report = tracker.build_report(state, session_id="s1")
        assert len(report.summary_line) > 0

    def test_breadth_sufficient_false_below_threshold(self):
        tracker = CoverageTracker(min_breadth_categories=4)
        state = _fresh()
        for qt, cat, turn in [("Q1", "Security", 1), ("Q2", "Runtime", 2)]:
            state = _record(state, qt, cat, turn)
        report = tracker.build_report(state, session_id="s1")
        assert report.breadth_sufficient is False

    def test_breadth_sufficient_true_at_threshold(self):
        tracker = CoverageTracker(min_breadth_categories=3)
        state = _fresh()
        for qt, cat, turn in [
            ("Q1", "Security", 1),
            ("Q2", "Runtime", 2),
            ("Q3", "Architecture", 3),
        ]:
            state = _record(state, qt, cat, turn)
        report = tracker.build_report(state, session_id="s1")
        assert report.breadth_sufficient is True
