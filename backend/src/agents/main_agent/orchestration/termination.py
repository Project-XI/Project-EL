"""
termination.py
──────────────
Termination condition evaluator for the Viva Flow Orchestrator.

Responsibilities
────────────────
- Evaluate whether a session should end after each orchestrator step.
- Expose each termination condition as a named, independently testable check.
- Return a TerminationVerdict with the reason so decisions are auditable.

Rules
─────
- Pure functions — no state mutations, no side effects.
- All conditions are explicit and enumerable.
- Conditions are checked in priority order (hard limits first).
- Deterministic: same state + config → same verdict.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from .pacing import PacingConfig, questions_remaining
from .session_state import SessionPhase, SessionState


# ── Termination reasons ───────────────────────────────────────────────────────

class TerminationReason(str, Enum):
    QUESTION_CAP_REACHED     = "question_cap_reached"
    NO_TARGETS_REMAINING     = "no_targets_remaining"
    MAX_TURNS_EXCEEDED       = "max_turns_exceeded"
    MIN_COVERAGE_MET         = "min_coverage_met_and_no_high_priority_left"
    ALREADY_TERMINATED       = "already_terminated"


# ── Verdict ───────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TerminationVerdict:
    should_terminate: bool
    reason: Optional[TerminationReason] = None

    @staticmethod
    def no() -> "TerminationVerdict":
        return TerminationVerdict(should_terminate=False)

    @staticmethod
    def yes(reason: TerminationReason) -> "TerminationVerdict":
        return TerminationVerdict(should_terminate=True, reason=reason)


# ── Hard limits ───────────────────────────────────────────────────────────────

MAX_TURNS_HARD_LIMIT: int = 30
"""Absolute maximum turns regardless of config — safety net."""


# ── Individual condition checks ───────────────────────────────────────────────

def check_already_terminated(state: SessionState) -> Optional[TerminationVerdict]:
    if state.is_terminated:
        return TerminationVerdict.yes(TerminationReason.ALREADY_TERMINATED)
    return None


def check_question_cap(state: SessionState, config: PacingConfig) -> Optional[TerminationVerdict]:
    if state.total_questions_asked >= config.max_questions:
        return TerminationVerdict.yes(TerminationReason.QUESTION_CAP_REACHED)
    return None


def check_max_turns(state: SessionState) -> Optional[TerminationVerdict]:
    if state.turn_index >= MAX_TURNS_HARD_LIMIT:
        return TerminationVerdict.yes(TerminationReason.MAX_TURNS_EXCEEDED)
    return None


def check_no_targets_remaining(
    state: SessionState,
    remaining_target_count: int,
    config: PacingConfig,
) -> Optional[TerminationVerdict]:
    """Terminate if no targets remain AND minimum questions have been asked."""
    if remaining_target_count == 0 and state.total_questions_asked >= config.min_questions:
        return TerminationVerdict.yes(TerminationReason.NO_TARGETS_REMAINING)
    return None


def check_min_coverage_met(
    state: SessionState,
    remaining_high_priority_count: int,
    config: PacingConfig,
) -> Optional[TerminationVerdict]:
    """
    Terminate if minimum questions have been asked and no high-priority
    (importance_score >= 0.85) targets remain unasked.
    """
    if (
        state.total_questions_asked >= config.min_questions
        and remaining_high_priority_count == 0
        and questions_remaining(state, config) <= 0
    ):
        return TerminationVerdict.yes(TerminationReason.MIN_COVERAGE_MET)
    return None


# ── Primary evaluator ─────────────────────────────────────────────────────────

def evaluate_termination(
    state: SessionState,
    config: PacingConfig,
    remaining_target_count: int,
    remaining_high_priority_count: int,
) -> TerminationVerdict:
    """
    Evaluate all termination conditions in priority order.

    Priority (highest first):
    1. Already terminated
    2. Max turns hard limit
    3. Question cap reached
    4. No targets remaining (and min met)
    5. Min coverage met + no high priority left

    Returns the first matching verdict, or TerminationVerdict.no().
    """
    checks = [
        check_already_terminated(state),
        check_max_turns(state),
        check_question_cap(state, config),
        check_no_targets_remaining(state, remaining_target_count, config),
        check_min_coverage_met(state, remaining_high_priority_count, config),
    ]
    for verdict in checks:
        if verdict is not None:
            return verdict
    return TerminationVerdict.no()
