"""
session_state.py
────────────────
Immutable session state model for the Viva Flow Orchestrator.

Rules
─────
- State is always replaced, never mutated in-place (functional style).
- The orchestrator reads state, emits a decision, and the caller persists the
  next state — keeping sequencing policy separate from state storage.
- All fields are plain Python types so the object is trivially serializable.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Dict, FrozenSet, List, Optional, Tuple


# ── Enumerations ──────────────────────────────────────────────────────────────

class SessionPhase(str, Enum):
    """Lifecycle phases of a viva session."""
    INITIALIZING   = "initializing"   # Before first question
    ACTIVE         = "active"         # Questions in progress
    FOLLOW_UP      = "follow_up"      # In a follow-up branch
    WRAPPING_UP    = "wrapping_up"    # Last question posted
    TERMINATED     = "terminated"     # Session closed


class QuestionOutcome(str, Enum):
    """How a posted question was resolved."""
    PENDING    = "pending"    # No response yet
    ANSWERED   = "answered"   # Candidate gave a complete answer
    PARTIAL    = "partial"    # Partial / shallow answer → follow-up triggered
    SKIPPED    = "skipped"    # Orchestrator moved on
    TIMED_OUT  = "timed_out"  # No response within allowed turns


# ── Question record ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class QuestionRecord:
    """
    Immutable record of a single posted question.

    Stored in SessionState.history — never modified after creation.
    """
    question_target: str
    category: str
    difficulty: str
    importance_score: float
    depth_score: float
    turn_index: int                    # Which orchestrator turn this was asked on
    outcome: QuestionOutcome = QuestionOutcome.PENDING
    follow_up_count: int = 0          # How many follow-ups this Q generated


# ── Session state ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SessionState:
    """
    Complete, immutable snapshot of viva session progress.

    The orchestrator receives this, makes decisions, and returns
    a new SessionState via `advance()`. The old state is never modified.
    """
    session_id: str

    # Lifecycle
    phase: SessionPhase = SessionPhase.INITIALIZING
    turn_index: int = 0                    # Number of orchestrator decisions made

    # Question tracking
    history: Tuple[QuestionRecord, ...] = field(default_factory=tuple)
    pending_question: Optional[QuestionRecord] = None
    active_follow_up_target: Optional[str] = None  # question_target being followed up

    # Coverage tracking (category → count asked)
    category_coverage: Dict[str, int] = field(default_factory=dict)

    # Termination metadata
    termination_reason: Optional[str] = None

    # ── Derived properties ────────────────────────────────────────────────────

    @property
    def total_questions_asked(self) -> int:
        return len(self.history)

    @property
    def answered_targets(self) -> FrozenSet[str]:
        """Set of question_targets that have been asked (any outcome)."""
        return frozenset(r.question_target for r in self.history)

    @property
    def is_active(self) -> bool:
        return self.phase in (SessionPhase.ACTIVE, SessionPhase.FOLLOW_UP, SessionPhase.WRAPPING_UP)

    @property
    def is_terminated(self) -> bool:
        return self.phase == SessionPhase.TERMINATED

    # ── State transitions ─────────────────────────────────────────────────────

    def record_question(self, record: QuestionRecord) -> "SessionState":
        """Return new state with this question appended to history."""
        new_coverage = dict(self.category_coverage)
        new_coverage[record.category] = new_coverage.get(record.category, 0) + 1
        return replace(
            self,
            history=self.history + (record,),
            pending_question=record,
            turn_index=self.turn_index + 1,
            category_coverage=new_coverage,
            phase=SessionPhase.ACTIVE if self.phase == SessionPhase.INITIALIZING else self.phase,
        )

    def resolve_pending(self, outcome: QuestionOutcome) -> "SessionState":
        """Return new state with the pending question resolved."""
        if self.pending_question is None:
            return self
        resolved = QuestionRecord(
            question_target  = self.pending_question.question_target,
            category         = self.pending_question.category,
            difficulty       = self.pending_question.difficulty,
            importance_score = self.pending_question.importance_score,
            depth_score      = self.pending_question.depth_score,
            turn_index       = self.pending_question.turn_index,
            outcome          = outcome,
            follow_up_count  = self.pending_question.follow_up_count,
        )
        updated_history = self.history[:-1] + (resolved,)
        return replace(self, history=updated_history, pending_question=None)

    def enter_follow_up(self, target: str) -> "SessionState":
        return replace(self, phase=SessionPhase.FOLLOW_UP, active_follow_up_target=target)

    def exit_follow_up(self) -> "SessionState":
        return replace(self, phase=SessionPhase.ACTIVE, active_follow_up_target=None)

    def begin_wrap_up(self) -> "SessionState":
        return replace(self, phase=SessionPhase.WRAPPING_UP)

    def terminate(self, reason: str) -> "SessionState":
        return replace(
            self,
            phase=SessionPhase.TERMINATED,
            pending_question=None,
            termination_reason=reason,
        )

    def advance_turn(self) -> "SessionState":
        """Increment turn counter without posting a question (e.g. follow-up evaluation)."""
        return replace(self, turn_index=self.turn_index + 1)
