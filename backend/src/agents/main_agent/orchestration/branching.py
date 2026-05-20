"""
branching.py
────────────
Follow-up branching logic for the Viva Flow Orchestrator.

Responsibilities
────────────────
- Determine whether a candidate's answer warrants a follow-up.
- Generate the follow-up viva target from the original target's context.
- Track how many follow-ups have been opened for a given question.
- Enforce the follow-up depth limit (max_follow_ups from pacing config).

Rules
─────
- Pure functions; no state stored here.
- No LLM calls, no AST parsing, no scoring speculation.
- Follow-ups are derived deterministically from the parent target + signals.
- The caller decides what "shallow" means; this module acts on a boolean flag.
"""

from __future__ import annotations

from typing import Optional

from src.agents.main_agent.integration.oracle_schema import (
    DifficultyLevel,
    NormalizedVivaTarget,
    VivaCategory,
)
from .session_state import QuestionRecord, SessionState


# ── Follow-up escalation map ──────────────────────────────────────────────────

_DIFFICULTY_ESCALATION: dict[str, DifficultyLevel] = {
    "easy":   DifficultyLevel.MEDIUM,
    "medium": DifficultyLevel.HARD,
    "hard":   DifficultyLevel.HARD,   # Already at max — same difficulty
}

# Prompt prefixes by category to make follow-ups feel directed
_FOLLOW_UP_PREFIX: dict[str, str] = {
    "Architecture":  "Drill deeper: ",
    "Tradeoff":      "Challenge the tradeoff: ",
    "Security":      "Probe the attack surface: ",
    "Scalability":   "Push the limits: ",
    "Failure-Path":  "Trace the failure further: ",
    "Runtime":       "Investigate the runtime impact: ",
}


# ── Public API ────────────────────────────────────────────────────────────────

def build_follow_up_target(
    parent: NormalizedVivaTarget,
    failure_hint: Optional[str] = None,
) -> NormalizedVivaTarget:
    """
    Create a follow-up NormalizedVivaTarget from a parent target.

    The follow-up:
    - Escalates difficulty by one level.
    - Prefixes the focus with a category-specific prompt.
    - Optionally appends a failure hint drawn from ORACLE failure scenarios.
    - Inherits topic, category, related_node, and evidence from the parent.
    """
    escalated_diff = _DIFFICULTY_ESCALATION.get(
        parent.difficulty.value, DifficultyLevel.HARD
    )
    category_str = parent.category.value
    prefix = _FOLLOW_UP_PREFIX.get(category_str, "Follow up: ")
    base_focus = parent.focus
    if failure_hint:
        base_focus = f"{base_focus} Specifically address: {failure_hint}"

    return NormalizedVivaTarget(
        topic            = parent.topic,
        question_target  = f"{parent.question_target} [follow-up]",
        difficulty       = escalated_diff,
        category         = parent.category,
        importance_score = min(parent.importance_score + 0.05, 1.0),  # Slight urgency boost
        depth_score      = min(parent.depth_score + 1.0, 10.0),       # Deeper probe
        focus            = f"{prefix}{base_focus}",
        related_node     = parent.related_node,
        confidence       = parent.confidence,
        reasoning_summary= f"Follow-up generated from shallow answer on: {parent.question_target}",
        evidence         = parent.evidence,
    )


def follow_up_allowed(
    state: SessionState,
    max_follow_ups: int,
) -> bool:
    """
    Return True if a follow-up branch can be opened in the current state.

    Checks:
    - A pending question exists.
    - Its follow_up_count is below the max.
    - The session is not already in a nested follow-up (no nesting).
    """
    from .session_state import SessionPhase
    if state.pending_question is None:
        return False
    if state.pending_question.follow_up_count >= max_follow_ups:
        return False
    if state.phase == SessionPhase.FOLLOW_UP:
        return False  # No nested follow-ups
    return True


def increment_follow_up_count(record: QuestionRecord) -> QuestionRecord:
    """
    Return a new QuestionRecord with follow_up_count incremented by 1.
    Records are frozen dataclasses — this returns a new instance.
    """
    from dataclasses import replace
    return replace(record, follow_up_count=record.follow_up_count + 1)
