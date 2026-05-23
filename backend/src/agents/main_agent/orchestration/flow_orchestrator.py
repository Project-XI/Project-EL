"""
flow_orchestrator.py
────────────────────
Central Viva Flow Orchestrator — the single coordinator that MAIN Agent calls.

Responsibilities
────────────────
- Own the sequence of viva actions after initialization.
- Consume NormalizedOracleOutput (never ORACLE internals).
- Decide: ask next question / open follow-up / wrap up / terminate.
- Emit loggable, replayable OrchestratorDecision objects.
- Delegate policy to pacing, branching, category_balancer, and termination.

Rules
─────
- This class holds no mutable state itself — it receives SessionState and
  returns (OrchestratorDecision, new_SessionState).
- Deterministic: same state + oracle output → same decision.
- No LLM calls, no AST parsing, no fairness scoring.
- Never imports StructuredContext or any ORACLE-internal type.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from src.agents.main_agent.integration.oracle_schema import (
    NormalizedOracleOutput,
    NormalizedVivaTarget,
)
from .branching import (
    build_follow_up_target,
    follow_up_allowed,
    increment_follow_up_count,
)
from .category_balancer import coverage_summary, pick_next, rank_targets
from .pacing import (
    PacingConfig,
    is_wrap_up_turn,
    questions_remaining,
    session_progress_fraction,
    should_open_follow_up,
    target_difficulty,
)
from .session_state import (
    QuestionOutcome,
    QuestionRecord,
    SessionPhase,
    SessionState,
)
from .termination import TerminationReason, evaluate_termination

logger = logging.getLogger(__name__)


# ── Decision types ────────────────────────────────────────────────────────────

class DecisionType(str, Enum):
    ASK_QUESTION    = "ask_question"     # Post the next primary question
    ASK_FOLLOW_UP   = "ask_follow_up"    # Post a follow-up on current question
    WRAP_UP         = "wrap_up"          # Post final question then terminate
    TERMINATE       = "terminate"        # End the session immediately
    AWAIT_ANSWER    = "await_answer"     # No action; waiting for candidate input


@dataclass(frozen=True)
class OrchestratorDecision:
    """
    A single, loggable orchestrator decision.

    Emitted on every call to step(). The caller (MAIN Agent) acts on
    decision_type and target, then persists next_state.
    """
    decision_type: DecisionType
    target: Optional[NormalizedVivaTarget]    # The question target to present
    next_state: SessionState                  # State after this decision
    reason: str                               # Human-readable audit trail
    session_progress: float                   # 0.0 → 1.0 session completion
    coverage: dict                            # Category coverage snapshot

    def is_terminal(self) -> bool:
        return self.decision_type == DecisionType.TERMINATE

    def has_question(self) -> bool:
        return self.target is not None


# ── Orchestrator ──────────────────────────────────────────────────────────────

class FlowOrchestrator:
    """
    Stateless viva flow orchestrator.

    Usage
    ─────
        orchestrator = FlowOrchestrator(config=PacingConfig(max_questions=8))
        state = SessionState(session_id="abc123")

        # On each turn:
        decision = orchestrator.step(state, oracle_output, answer_was_shallow=False)
        state = decision.next_state    # Persist this
        # → present decision.target to the candidate
    """

    def __init__(self, config: Optional[PacingConfig] = None):
        self.config = config or PacingConfig()

    # ── Primary entry point ───────────────────────────────────────────────────

    def step(
        self,
        state: SessionState,
        oracle_output: NormalizedOracleOutput,
        answer_was_shallow: bool = False,
    ) -> OrchestratorDecision:
        """
        Advance the orchestration by one step.

        Parameters
        ──────────
        state             : Current immutable session state.
        oracle_output     : Normalized ORACLE output (consumed, not re-computed).
        answer_was_shallow: True if the previous answer signal was incomplete
                            and warrants a follow-up (caller determines this).

        Returns
        ───────
        OrchestratorDecision with the action, the question target (if any),
        and the new SessionState to persist.
        """
        # ── Guard: already terminated ─────────────────────────────────────────
        if state.is_terminated:
            return self._terminate(state, TerminationReason.ALREADY_TERMINATED)

        all_targets = oracle_output.viva_targets
        asked = state.answered_targets
        progress = session_progress_fraction(state, self.config)
        diff = target_difficulty(state, self.config)
        coverage = dict(state.category_coverage)
        cov_summary = coverage_summary(all_targets, coverage)

        remaining = [t for t in all_targets if t.question_target not in asked]
        high_priority_remaining = [
            t for t in remaining if t.importance_score >= 0.85
        ]

        # ── 1. Evaluate termination conditions ────────────────────────────────
        verdict = evaluate_termination(
            state,
            self.config,
            remaining_target_count=len(remaining),
            remaining_high_priority_count=len(high_priority_remaining),
        )
        if verdict.should_terminate:
            return self._terminate(state, verdict.reason, coverage=cov_summary)

        # ── 2. Follow-up branch ───────────────────────────────────────────────
        if should_open_follow_up(state, answer_was_shallow, self.config):
            if follow_up_allowed(state, self.config.max_follow_ups):
                return self._open_follow_up(state, oracle_output, coverage=cov_summary)

        # ── 3. Wrap-up detection ──────────────────────────────────────────────
        if is_wrap_up_turn(state, self.config) or not remaining:
            next_target = pick_next(remaining, coverage, asked, diff, state.total_questions_asked)
            if next_target:
                return self._ask(state, next_target, DecisionType.WRAP_UP, cov_summary, progress)
            return self._terminate(state, TerminationReason.NO_TARGETS_REMAINING, coverage=cov_summary)

        # ── 4. Standard next question ─────────────────────────────────────────
        next_target = pick_next(remaining, coverage, asked, diff, state.total_questions_asked)
        if next_target:
            return self._ask(state, next_target, DecisionType.ASK_QUESTION, cov_summary, progress)

        # ── 5. Fallback: nothing left ─────────────────────────────────────────
        return self._terminate(state, TerminationReason.NO_TARGETS_REMAINING, coverage=cov_summary)

    # ── Session initialization ────────────────────────────────────────────────

    def initialize(
        self,
        session_id: str,
        oracle_output: NormalizedOracleOutput,
    ) -> OrchestratorDecision:
        """
        Start a fresh session. Returns the first OrchestratorDecision.
        """
        state = SessionState(session_id=session_id)
        return self.step(state, oracle_output, answer_was_shallow=False)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _ask(
        self,
        state: SessionState,
        target: NormalizedVivaTarget,
        decision_type: DecisionType,
        coverage: dict,
        progress: float,
    ) -> OrchestratorDecision:
        record = QuestionRecord(
            question_target  = target.question_target,
            category         = target.category.value,
            difficulty       = target.difficulty.value,
            importance_score = target.importance_score,
            depth_score      = target.depth_score,
            turn_index       = state.turn_index,
        )
        next_state = state.record_question(record)
        if decision_type == DecisionType.WRAP_UP:
            next_state = next_state.begin_wrap_up()

        logger.debug(
            "[FlowOrchestrator] %s → %s (cat=%s, diff=%s)",
            decision_type.value, target.question_target,
            target.category.value, target.difficulty.value,
        )
        return OrchestratorDecision(
            decision_type    = decision_type,
            target           = target,
            next_state       = next_state,
            reason           = (
                f"{decision_type.value}: asked '{target.question_target}' "
                f"(importance={target.importance_score:.2f}, cat={target.category.value})"
            ),
            session_progress = progress,
            coverage         = coverage,
        )

    def _open_follow_up(
        self,
        state: SessionState,
        oracle_output: NormalizedOracleOutput,
        coverage: dict,
    ) -> OrchestratorDecision:
        parent = state.pending_question
        # Pick a failure hint from ORACLE if available
        failure_hint: Optional[str] = None
        if oracle_output.failure_scenarios:
            failure_hint = oracle_output.failure_scenarios[0].description

        # Build follow-up target
        parent_as_target = self._record_to_target(parent, oracle_output)
        follow_up = build_follow_up_target(parent_as_target, failure_hint)

        # Increment follow-up count on the parent record
        updated_parent = increment_follow_up_count(parent)
        # Replace last history entry with updated parent
        updated_history = state.history[:-1] + (updated_parent,)
        interim_state = state.__class__(
            session_id             = state.session_id,
            phase                  = SessionPhase.FOLLOW_UP,
            turn_index             = state.turn_index,
            history                = updated_history,
            pending_question       = updated_parent,
            active_follow_up_target= parent.question_target,
            category_coverage      = state.category_coverage,
        )

        record = QuestionRecord(
            question_target  = follow_up.question_target,
            category         = follow_up.category.value,
            difficulty       = follow_up.difficulty.value,
            importance_score = follow_up.importance_score,
            depth_score      = follow_up.depth_score,
            turn_index       = interim_state.turn_index,
        )
        next_state = interim_state.record_question(record)
        progress = session_progress_fraction(interim_state, self.config)
        cov = coverage_summary(oracle_output.viva_targets, dict(next_state.category_coverage))

        logger.debug(
            "[FlowOrchestrator] follow-up on '%s'", parent.question_target
        )
        return OrchestratorDecision(
            decision_type    = DecisionType.ASK_FOLLOW_UP,
            target           = follow_up,
            next_state       = next_state,
            reason           = (
                f"follow-up on '{parent.question_target}' "
                f"(shallow answer, depth escalated)"
            ),
            session_progress = progress,
            coverage         = cov,
        )

    def _terminate(
        self,
        state: SessionState,
        reason: Optional[TerminationReason],
        coverage: Optional[dict] = None,
    ) -> OrchestratorDecision:
        reason_str = reason.value if reason else "unknown"
        next_state = state.terminate(reason_str)
        progress = session_progress_fraction(state, self.config)
        logger.info("[FlowOrchestrator] Session terminated: %s", reason_str)
        return OrchestratorDecision(
            decision_type    = DecisionType.TERMINATE,
            target           = None,
            next_state       = next_state,
            reason           = f"terminated: {reason_str}",
            session_progress = progress,
            coverage         = coverage or {},
        )

    @staticmethod
    def _record_to_target(
        record: QuestionRecord,
        oracle_output: NormalizedOracleOutput,
    ) -> NormalizedVivaTarget:
        """
        Reconstruct a NormalizedVivaTarget from a QuestionRecord for
        follow-up generation. Looks up the original target first.
        """
        from src.agents.main_agent.integration.oracle_schema import VivaCategory, DifficultyLevel
        original = next(
            (t for t in oracle_output.viva_targets
             if t.question_target == record.question_target),
            None,
        )
        if original:
            return original
        # Synthetic fallback (follow-up on a follow-up)
        return NormalizedVivaTarget(
            topic            = record.category,
            question_target  = record.question_target,
            difficulty       = DifficultyLevel(record.difficulty),
            category         = VivaCategory(record.category),
            importance_score = record.importance_score,
            depth_score      = record.depth_score,
            focus            = f"Deepen your answer on {record.question_target}.",
        )
