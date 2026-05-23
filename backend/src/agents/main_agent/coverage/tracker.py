"""
tracker.py
──────────
Central Topic Coverage Tracker for the MAIN Agent viva flow.

Responsibilities
────────────────
- Consume session events (question asked, answer received) and update CoverageState.
- Expose gap detection and breadth checks to the orchestrator.
- Surface a serializable snapshot for logging and export at any time.
- Integrate with session state without duplicating it.

Rules
─────
- Lightweight class that wraps CoverageState functionally.
- No mutable instance state held in the tracker itself — callers own state.
- All methods are pure: receive state, return new state + optional report.
- Deterministic: same events in same order → same final state.
- Never imports ORACLE internals.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Set

from src.agents.main_agent.integration.oracle_schema import (
    NormalizedOracleOutput,
    NormalizedVivaTarget,
)
from .categories import CATEGORY_REGISTRY, resolve_category
from .coverage_state import CoverageState, TopicEntry
from .heuristics import (
    CoverageGap,
    coverage_summary_text,
    detect_gaps,
    is_breadth_sufficient,
    most_urgent_gap,
    saturated_categories,
    uncovered_categories,
)

logger = logging.getLogger(__name__)


# ── Coverage report ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CoverageReport:
    """
    A point-in-time coverage audit — safe to log and export.

    All fields are plain types; no opaque objects.
    """
    session_id: str
    total_turns: int
    total_topics_asked: int
    covered_categories: List[str]
    uncovered_categories: List[str]
    partial_categories: List[str]
    saturated_categories: List[str]
    gaps: List[CoverageGap]
    most_urgent_gap: Optional[CoverageGap]
    breadth_sufficient: bool
    summary_line: str

    def to_dict(self) -> dict:
        return {
            "session_id":           self.session_id,
            "total_turns":          self.total_turns,
            "total_topics_asked":   self.total_topics_asked,
            "covered_categories":   self.covered_categories,
            "uncovered_categories": self.uncovered_categories,
            "partial_categories":   self.partial_categories,
            "saturated_categories": self.saturated_categories,
            "breadth_sufficient":   self.breadth_sufficient,
            "most_urgent_gap":      (
                self.most_urgent_gap.category if self.most_urgent_gap else None
            ),
            "summary_line":         self.summary_line,
        }


# ── Tracker ───────────────────────────────────────────────────────────────────

class CoverageTracker:
    """
    Stateless Topic Coverage Tracker.

    Usage
    ─────
        tracker = CoverageTracker()
        state = CoverageState.empty()

        # When a question is issued:
        state = tracker.record_question(state, viva_target, turn_index=1)

        # When the candidate answers:
        state = tracker.record_answer(state, question_target="JWT Lifecycle")

        # Query coverage:
        report = tracker.build_report(state, session_id="s1")
        gap    = tracker.next_gap(state)
    """

    def __init__(self, min_breadth_categories: int = 3):
        self.min_breadth_categories = min_breadth_categories

    # ── Event recording ───────────────────────────────────────────────────────

    def record_question(
        self,
        state: CoverageState,
        target: NormalizedVivaTarget,
        turn_index: int,
    ) -> CoverageState:
        """
        Record that a question was issued.
        Returns an updated CoverageState (caller must persist it).
        """
        category = target.category.value
        cat_def = CATEGORY_REGISTRY.get(category)
        min_q = cat_def.min_questions if cat_def else 1

        # Build tag set: category tags that overlap with target's topic/focus words
        tags = self._extract_tags(target, category)

        new_state = state.record_ask(
            question_target            = target.question_target,
            category                   = category,
            tags                       = tags,
            turn_index                 = turn_index,
            min_questions_for_category = min_q,
        )
        logger.debug(
            "[CoverageTracker] question recorded: target=%s cat=%s turn=%d",
            target.question_target, category, turn_index,
        )
        return new_state

    def record_answer(
        self,
        state: CoverageState,
        question_target: str,
    ) -> CoverageState:
        """
        Mark a topic as answered.
        Returns updated CoverageState (caller must persist it).
        """
        new_state = state.record_answer(question_target)
        logger.debug(
            "[CoverageTracker] answer recorded: target=%s", question_target
        )
        return new_state

    def initialize_from_oracle(
        self,
        oracle_output: NormalizedOracleOutput,
    ) -> CoverageState:
        """
        Build the initial (empty) CoverageState for a session.

        ORACLE evidence informs the initial topic map shape but the tracker
        logic itself does not duplicate ORACLE reasoning.
        """
        # We start empty — the topic map is populated as questions are asked.
        # ORACLE targets are only used to discover available categories.
        return CoverageState.empty()

    # ── Gap detection ─────────────────────────────────────────────────────────

    def next_gap(self, state: CoverageState) -> Optional[CoverageGap]:
        """Return the most urgent coverage gap, or None if fully covered."""
        return most_urgent_gap(state)

    def is_repetitive(self, state: CoverageState, question_target: str) -> bool:
        """
        Return True if this question_target has already been asked.
        Used by the orchestrator to avoid repetitive questioning.
        """
        return state.has_been_asked(question_target)

    def uncovered(self, state: CoverageState) -> List[str]:
        """Return categories with zero questions asked, by descending weight."""
        return uncovered_categories(state)

    def all_gaps(self, state: CoverageState) -> List[CoverageGap]:
        """Return all coverage gaps sorted by urgency."""
        return detect_gaps(state)

    def breadth_ok(self, state: CoverageState) -> bool:
        """True if enough distinct categories have been covered."""
        return is_breadth_sufficient(state, self.min_breadth_categories)

    # ── Reporting ─────────────────────────────────────────────────────────────

    def build_report(
        self,
        state: CoverageState,
        session_id: str,
    ) -> CoverageReport:
        """
        Build a full, serializable CoverageReport from current state.
        Safe to call at any point during or after the session.
        """
        from .heuristics import partially_covered_categories
        gaps = detect_gaps(state)
        covered = sorted(state.covered_categories)
        uncov = uncovered_categories(state)
        partial = partially_covered_categories(state)
        saturated = saturated_categories(state)
        urgent = most_urgent_gap(state)

        report = CoverageReport(
            session_id           = session_id,
            total_turns          = state.total_turns,
            total_topics_asked   = state.total_asked,
            covered_categories   = covered,
            uncovered_categories = uncov,
            partial_categories   = partial,
            saturated_categories = saturated,
            gaps                 = gaps,
            most_urgent_gap      = urgent,
            breadth_sufficient   = is_breadth_sufficient(state, self.min_breadth_categories),
            summary_line         = coverage_summary_text(state),
        )
        logger.info(
            "[CoverageTracker] report built for %s: %s",
            session_id, report.summary_line,
        )
        return report

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _extract_tags(target: NormalizedVivaTarget, category: str) -> FrozenSet[str]:
        """
        Derive a tag set for a viva target by intersecting its text
        with the category's known tag vocabulary.
        """
        cat_def = CATEGORY_REGISTRY.get(category)
        if not cat_def:
            return frozenset({category.lower()})

        searchable = (
            f"{target.topic} {target.question_target} {target.focus}"
        ).lower()
        matched = frozenset(tag for tag in cat_def.tags if tag in searchable)
        # Always include the category itself as a tag fallback
        return matched or frozenset({category.lower()})
