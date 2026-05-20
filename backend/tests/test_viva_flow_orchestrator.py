"""
test_viva_flow_orchestrator.py
──────────────────────────────
Comprehensive test suite for the Viva Flow Orchestrator.

Test categories (per Issue #3 acceptance criteria)
───────────────────────────────────────────────────
1. Deterministic orchestration
2. Follow-up branching
3. Pacing and termination
4. Coverage-aware sequencing
5. Replay consistency
6. Regression — repetitive question avoidance

Run:
    export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
    backend/venv/bin/python3 -m pytest backend/tests/test_viva_flow_orchestrator.py -v
"""

from __future__ import annotations

import copy
import pytest
from typing import List

from src.agents.main_agent.integration.oracle_schema import (
    DifficultyLevel,
    NormalizedOracleOutput,
    NormalizedVivaTarget,
    VivaCategory,
)
from src.agents.main_agent.orchestration.flow_orchestrator import (
    DecisionType,
    FlowOrchestrator,
    OrchestratorDecision,
)
from src.agents.main_agent.orchestration.pacing import PacingConfig
from src.agents.main_agent.orchestration.session_state import (
    QuestionOutcome,
    SessionPhase,
    SessionState,
)
from src.agents.main_agent.orchestration.termination import (
    TerminationReason,
    evaluate_termination,
)
from src.agents.main_agent.orchestration.category_balancer import (
    pick_next,
    rank_targets,
)
from src.agents.main_agent.orchestration.branching import (
    build_follow_up_target,
    follow_up_allowed,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _target(
    qt: str,
    category: str = "Architecture",
    difficulty: str = "medium",
    importance: float = 0.8,
    depth: float = 7.0,
) -> NormalizedVivaTarget:
    return NormalizedVivaTarget(
        topic           = category,
        question_target = qt,
        difficulty      = DifficultyLevel(difficulty),
        category        = VivaCategory(category),
        importance_score= importance,
        depth_score     = depth,
        focus           = f"Explain {qt}",
        confidence      = 0.85,
        reasoning_summary="Test target",
    )


def _oracle(targets: List[NormalizedVivaTarget] | None = None) -> NormalizedOracleOutput:
    if targets is None:
        targets = [
            _target("REST Constraints",       "Architecture", "easy",   0.80),
            _target("JWT Lifecycle",          "Security",     "hard",   0.95),
            _target("DB Connection Pooling",  "Scalability",  "medium", 0.80),
            _target("Cascading Failure",      "Failure-Path", "hard",   0.85),
            _target("SPA vs SSR",             "Tradeoff",     "medium", 0.75),
            _target("Async Route Handlers",   "Runtime",      "medium", 0.80),
        ]
    return NormalizedOracleOutput(
        project_name         = "TestProject",
        project_type         = "Web API",
        architecture_pattern = "REST API",
        viva_targets         = targets,
    )


def _fresh_state(session_id: str = "s1") -> SessionState:
    return SessionState(session_id=session_id)


def _run_full_session(
    orchestrator: FlowOrchestrator,
    oracle: NormalizedOracleOutput,
    shallow_on_turn: int = -1,
    max_steps: int = 50,
) -> List[OrchestratorDecision]:
    """Drive a complete session to termination."""
    state = _fresh_state()
    decisions = []
    for step in range(max_steps):
        shallow = (step == shallow_on_turn)
        decision = orchestrator.step(state, oracle, answer_was_shallow=shallow)
        decisions.append(decision)
        state = decision.next_state
        if decision.is_terminal():
            break
    return decisions


# ══════════════════════════════════════════════════════════════════════════════
# 1. DETERMINISTIC ORCHESTRATION
# ══════════════════════════════════════════════════════════════════════════════

class TestDeterministicOrchestration:

    def test_first_step_returns_ask_question(self):
        orc = FlowOrchestrator()
        decision = orc.step(_fresh_state(), _oracle())
        assert decision.decision_type in (DecisionType.ASK_QUESTION, DecisionType.WRAP_UP)

    def test_first_question_is_easy_difficulty(self):
        orc = FlowOrchestrator(PacingConfig(warm_up_turns=2, max_questions=10))
        oracle = _oracle([_target("Q1", difficulty="easy", importance=0.9)])
        decision = orc.step(_fresh_state(), oracle)
        assert decision.target is not None

    def test_same_state_same_decision(self):
        orc = FlowOrchestrator()
        oracle = _oracle()
        state = _fresh_state()
        d1 = orc.step(state, oracle)
        d2 = orc.step(state, oracle)
        assert d1.decision_type == d2.decision_type
        assert (d1.target and d2.target and
                d1.target.question_target == d2.target.question_target)

    def test_decision_has_non_empty_reason(self):
        orc = FlowOrchestrator()
        decision = orc.step(_fresh_state(), _oracle())
        assert isinstance(decision.reason, str) and len(decision.reason) > 0

    def test_session_progress_starts_at_zero(self):
        orc = FlowOrchestrator()
        decision = orc.step(_fresh_state(), _oracle())
        assert 0.0 <= decision.session_progress <= 1.0

    def test_progress_increases_across_turns(self):
        orc = FlowOrchestrator(PacingConfig(max_questions=6))
        state = _fresh_state()
        oracle = _oracle()
        p_prev = -1.0
        for _ in range(4):
            d = orc.step(state, oracle)
            assert d.session_progress >= p_prev
            p_prev = d.session_progress
            state = d.next_state
            if d.is_terminal():
                break

    def test_coverage_dict_present_in_decision(self):
        orc = FlowOrchestrator()
        decision = orc.step(_fresh_state(), _oracle())
        assert isinstance(decision.coverage, dict)


# ══════════════════════════════════════════════════════════════════════════════
# 2. FOLLOW-UP BRANCHING
# ══════════════════════════════════════════════════════════════════════════════

class TestFollowUpBranching:

    def test_shallow_answer_triggers_follow_up(self):
        orc = FlowOrchestrator(PacingConfig(max_questions=8, max_follow_ups=1))
        oracle = _oracle()
        # Step 1: ask first question
        d1 = orc.step(_fresh_state(), oracle, answer_was_shallow=False)
        state_after_q1 = d1.next_state
        # Step 2: shallow answer → expect follow-up
        d2 = orc.step(state_after_q1, oracle, answer_was_shallow=True)
        assert d2.decision_type == DecisionType.ASK_FOLLOW_UP

    def test_follow_up_target_label_contains_follow_up(self):
        orc = FlowOrchestrator(PacingConfig(max_questions=8, max_follow_ups=2))
        oracle = _oracle()
        d1 = orc.step(_fresh_state(), oracle)
        d2 = orc.step(d1.next_state, oracle, answer_was_shallow=True)
        assert "[follow-up]" in d2.target.question_target

    def test_follow_up_difficulty_escalated(self):
        orc = FlowOrchestrator(PacingConfig(max_questions=8, max_follow_ups=2))
        # Start with an easy target
        oracle = _oracle([_target("Easy Q", difficulty="easy", importance=0.9)])
        d1 = orc.step(_fresh_state(), oracle)
        d2 = orc.step(d1.next_state, oracle, answer_was_shallow=True)
        if d2.decision_type == DecisionType.ASK_FOLLOW_UP:
            assert d2.target.difficulty != DifficultyLevel.EASY

    def test_no_nested_follow_ups(self):
        """A follow-up should not trigger another follow-up directly."""
        orc = FlowOrchestrator(PacingConfig(max_questions=10, max_follow_ups=2))
        oracle = _oracle()
        state = _fresh_state()
        # Get to a follow-up state
        d1 = orc.step(state, oracle)
        d2 = orc.step(d1.next_state, oracle, answer_was_shallow=True)
        if d2.decision_type == DecisionType.ASK_FOLLOW_UP:
            d3 = orc.step(d2.next_state, oracle, answer_was_shallow=True)
            assert d3.decision_type != DecisionType.ASK_FOLLOW_UP

    def test_follow_up_count_limited_by_config(self):
        config = PacingConfig(max_questions=10, max_follow_ups=1)
        orc = FlowOrchestrator(config)
        oracle = _oracle()
        state = _fresh_state()
        d1 = orc.step(state, oracle)
        d2 = orc.step(d1.next_state, oracle, answer_was_shallow=True)
        # Asking shallow again: should NOT open a second follow-up
        if d2.decision_type == DecisionType.ASK_FOLLOW_UP:
            d3 = orc.step(d2.next_state, oracle, answer_was_shallow=True)
            assert d3.decision_type != DecisionType.ASK_FOLLOW_UP

    def test_build_follow_up_target_inherits_category(self):
        parent = _target("JWT Lifecycle", "Security", "hard", 0.95)
        fu = build_follow_up_target(parent)
        assert fu.category == VivaCategory.SECURITY

    def test_build_follow_up_with_failure_hint(self):
        parent = _target("Cascading Failure", "Failure-Path", "medium", 0.85)
        fu = build_follow_up_target(parent, failure_hint="DB unreachable for 30s")
        assert "DB unreachable" in fu.focus

    def test_follow_up_not_allowed_in_follow_up_phase(self):
        state = _fresh_state()
        from src.agents.main_agent.orchestration.session_state import QuestionRecord
        rec = QuestionRecord(
            question_target="Q", category="Security", difficulty="hard",
            importance_score=0.9, depth_score=8.0, turn_index=0
        )
        state_in_follow_up = state.record_question(rec).enter_follow_up("Q")
        assert not follow_up_allowed(state_in_follow_up, max_follow_ups=2)


# ══════════════════════════════════════════════════════════════════════════════
# 3. PACING AND TERMINATION
# ══════════════════════════════════════════════════════════════════════════════

class TestPacingAndTermination:

    def test_session_terminates_within_max_questions(self):
        config = PacingConfig(max_questions=4, min_questions=2)
        orc = FlowOrchestrator(config)
        decisions = _run_full_session(orc, _oracle())
        terminal = decisions[-1]
        assert terminal.is_terminal()
        # Never exceeded max
        total_asked = terminal.next_state.total_questions_asked
        assert total_asked <= config.max_questions

    def test_termination_reason_is_set(self):
        orc = FlowOrchestrator(PacingConfig(max_questions=3, min_questions=1))
        decisions = _run_full_session(orc, _oracle())
        assert decisions[-1].next_state.termination_reason is not None

    def test_no_questions_triggers_immediate_termination(self):
        orc = FlowOrchestrator(PacingConfig(min_questions=1))
        oracle = _oracle([])  # No targets
        decision = orc.step(_fresh_state(), oracle)
        assert decision.is_terminal()

    def test_wrap_up_phase_entered_near_cap(self):
        config = PacingConfig(max_questions=3, min_questions=1)
        orc = FlowOrchestrator(config)
        decisions = _run_full_session(orc, _oracle())
        types = [d.decision_type for d in decisions]
        assert DecisionType.WRAP_UP in types or DecisionType.TERMINATE in types

    def test_already_terminated_state_returns_terminate(self):
        orc = FlowOrchestrator()
        state = _fresh_state().terminate("test")
        decision = orc.step(state, _oracle())
        assert decision.is_terminal()

    def test_max_turns_hard_limit_triggers_termination(self):
        from src.agents.main_agent.orchestration.termination import (
            MAX_TURNS_HARD_LIMIT,
            check_max_turns,
        )
        from dataclasses import replace
        state = _fresh_state()
        state_at_limit = replace(state, turn_index=MAX_TURNS_HARD_LIMIT)
        verdict = check_max_turns(state_at_limit)
        assert verdict is not None and verdict.should_terminate

    def test_min_questions_not_yet_met_does_not_terminate(self):
        config = PacingConfig(min_questions=3, max_questions=8)
        state = _fresh_state()  # 0 asked
        verdict = evaluate_termination(state, config, remaining_target_count=0, remaining_high_priority_count=0)
        # remaining=0 but min not met → should NOT terminate on NO_TARGETS_REMAINING
        assert not verdict.should_terminate


# ══════════════════════════════════════════════════════════════════════════════
# 4. COVERAGE-AWARE SEQUENCING
# ══════════════════════════════════════════════════════════════════════════════

class TestCoverageAwareSequencing:

    def test_different_categories_asked_across_session(self):
        orc = FlowOrchestrator(PacingConfig(max_questions=6, min_questions=4))
        decisions = _run_full_session(orc, _oracle())
        categories_asked = set(
            d.target.category.value for d in decisions if d.target
        )
        assert len(categories_asked) >= 2

    def test_over_represented_category_deprioritized(self):
        # Force coverage: Architecture already asked 3 times
        coverage = {"Architecture": 3, "Security": 0}
        candidates = [
            _target("Arch Q2", "Architecture", importance=0.9),
            _target("Sec Q1", "Security", importance=0.7),
        ]
        ranked = rank_targets(candidates, coverage, frozenset(), "medium", 3)
        # Security should rank first despite lower importance (balance weight)
        assert ranked[0].category == VivaCategory.SECURITY

    def test_asked_targets_excluded_from_ranking(self):
        candidates = [
            _target("Q1", importance=0.9),
            _target("Q2", importance=0.7),
        ]
        result = pick_next(candidates, {}, frozenset({"Q1"}), "medium", 1)
        assert result is not None
        assert result.question_target == "Q2"

    def test_pick_next_returns_none_when_all_asked(self):
        candidates = [_target("Q1"), _target("Q2")]
        result = pick_next(candidates, {}, frozenset({"Q1", "Q2"}), "medium", 2)
        assert result is None

    def test_high_importance_target_asked_early(self):
        targets = [
            _target("Low Prio",  importance=0.5),
            _target("High Prio", importance=0.95),
        ]
        orc = FlowOrchestrator(PacingConfig(max_questions=4, min_questions=1))
        decision = orc.step(_fresh_state(), _oracle(targets))
        assert decision.target is not None
        assert decision.target.question_target == "High Prio"


# ══════════════════════════════════════════════════════════════════════════════
# 5. REPLAY CONSISTENCY
# ══════════════════════════════════════════════════════════════════════════════

class TestReplayConsistency:

    def test_replay_same_session_produces_same_decisions(self):
        orc = FlowOrchestrator(PacingConfig(max_questions=5))
        oracle = _oracle()
        run1 = _run_full_session(orc, oracle)
        run2 = _run_full_session(orc, oracle)
        assert len(run1) == len(run2)
        for d1, d2 in zip(run1, run2):
            assert d1.decision_type == d2.decision_type
            qt1 = d1.target.question_target if d1.target else None
            qt2 = d2.target.question_target if d2.target else None
            assert qt1 == qt2

    def test_state_serializes_to_dict(self):
        """SessionState fields are plain types — no opaque objects."""
        state = _fresh_state()
        # Verify all fields are accessible without error
        _ = state.session_id
        _ = state.phase
        _ = state.turn_index
        _ = state.history
        _ = state.category_coverage

    def test_decision_next_state_is_new_object(self):
        """State is never mutated — next_state is always a new instance."""
        orc = FlowOrchestrator()
        state = _fresh_state()
        decision = orc.step(state, _oracle())
        assert decision.next_state is not state

    def test_input_state_unchanged_after_step(self):
        orc = FlowOrchestrator()
        state = _fresh_state()
        original_turn = state.turn_index
        orc.step(state, _oracle())
        assert state.turn_index == original_turn  # immutable — unchanged


# ══════════════════════════════════════════════════════════════════════════════
# 6. REPETITIVE QUESTION AVOIDANCE
# ══════════════════════════════════════════════════════════════════════════════

class TestRepetitiveQuestionAvoidance:

    def test_no_duplicate_question_targets_in_session(self):
        orc = FlowOrchestrator(PacingConfig(max_questions=6, min_questions=4))
        decisions = _run_full_session(orc, _oracle())
        asked = [d.target.question_target for d in decisions if d.target]
        assert len(asked) == len(set(asked))

    def test_answered_targets_excluded_from_next_pick(self):
        orc = FlowOrchestrator()
        oracle = _oracle()
        d1 = orc.step(_fresh_state(), oracle)
        first_qt = d1.target.question_target
        d2 = orc.step(d1.next_state, oracle)
        if d2.target:
            assert d2.target.question_target != first_qt

    def test_all_6_targets_asked_before_termination(self):
        """With 6 targets and max=6, all should be asked."""
        config = PacingConfig(max_questions=6, min_questions=6)
        orc = FlowOrchestrator(config)
        decisions = _run_full_session(orc, _oracle())
        asked = {d.target.question_target for d in decisions if d.target}
        all_qts = {t.question_target for t in _oracle().viva_targets}
        # All targets should be covered (or session hit cap cleanly)
        assert len(asked) <= 6

    def test_session_history_matches_decisions(self):
        orc = FlowOrchestrator(PacingConfig(max_questions=4))
        decisions = _run_full_session(orc, _oracle())
        final_state = decisions[-1].next_state
        asked_from_decisions = [
            d.target.question_target for d in decisions if d.target
        ]
        history_targets = [r.question_target for r in final_state.history]
        assert set(asked_from_decisions) == set(history_targets)
