"""
pacing.py
─────────
Pacing policy for the Viva Flow Orchestrator.

Responsibilities
────────────────
- Calculate how many questions remain.
- Decide the target difficulty for the next question given turn progress.
- Decide whether a follow-up slot should be opened on this turn.
- Expose all configuration as named constants (no magic numbers elsewhere).

Rules
─────
- Pure functions only — no state held in this module.
- All functions accept explicit parameters; none read global state.
- Deterministic: same inputs → same outputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .session_state import SessionState


# ── Configuration constants ───────────────────────────────────────────────────

DEFAULT_MIN_QUESTIONS: int = 3    # Minimum questions before wrap-up is allowed
DEFAULT_MAX_QUESTIONS: int = 10   # Hard cap on questions per session
DEFAULT_MAX_FOLLOW_UPS: int = 2   # Max follow-ups per primary question
WARM_UP_TURNS: int = 2            # First N turns use easier questions

DIFFICULTY_RAMP: List[str] = ["easy", "medium", "medium", "hard", "hard"]
"""Difficulty sequence indexed by turn progress quintile (0–4)."""


# ── Pacing configuration ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class PacingConfig:
    """
    Runtime-overridable pacing parameters.
    Instantiate with defaults or override per-session.
    """
    min_questions: int = DEFAULT_MIN_QUESTIONS
    max_questions: int = DEFAULT_MAX_QUESTIONS
    max_follow_ups: int = DEFAULT_MAX_FOLLOW_UPS
    warm_up_turns: int = WARM_UP_TURNS


# ── Pacing calculations ───────────────────────────────────────────────────────

def target_difficulty(state: SessionState, config: PacingConfig) -> str:
    """
    Return the target difficulty string for the next question.

    Warm-up turns always return 'easy'.
    After that, ramps through the DIFFICULTY_RAMP based on session progress.
    """
    asked = state.total_questions_asked
    if asked < config.warm_up_turns:
        return "easy"
    # Map progress (0.0 → 1.0) onto 5 buckets
    progress = min(asked / max(config.max_questions, 1), 1.0)
    bucket = min(int(progress * len(DIFFICULTY_RAMP)), len(DIFFICULTY_RAMP) - 1)
    return DIFFICULTY_RAMP[bucket]


def questions_remaining(state: SessionState, config: PacingConfig) -> int:
    """Return how many more questions can still be posed this session."""
    return max(0, config.max_questions - state.total_questions_asked)


def should_open_follow_up(
    state: SessionState,
    answer_was_shallow: bool,
    config: PacingConfig,
) -> bool:
    """
    Decide whether to open a follow-up branch after a shallow answer.

    Conditions (all must be true):
    - The answer signal was shallow (caller decides this).
    - We are not already in a follow-up branch.
    - The pending question has not already exhausted its follow-up quota.
    - There are still questions remaining in the budget.
    """
    from .session_state import SessionPhase
    if not answer_was_shallow:
        return False
    if state.phase == SessionPhase.FOLLOW_UP:
        return False  # Don't nest follow-ups
    if state.pending_question is None:
        return False
    if state.pending_question.follow_up_count >= config.max_follow_ups:
        return False
    if questions_remaining(state, config) <= 0:
        return False
    return True


def is_wrap_up_turn(state: SessionState, config: PacingConfig) -> bool:
    """
    Return True if the orchestrator should post the final question and close.

    Triggers when:
    - The next question would hit the max cap, OR
    - Already past min threshold and no targets remain (caller checks targets).
    """
    return state.total_questions_asked >= config.max_questions - 1


def session_progress_fraction(state: SessionState, config: PacingConfig) -> float:
    """0.0 at start, 1.0 when max_questions reached. Clipped to [0, 1]."""
    return min(state.total_questions_asked / max(config.max_questions, 1), 1.0)
