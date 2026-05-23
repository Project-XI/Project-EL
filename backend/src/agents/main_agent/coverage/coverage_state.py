"""
coverage_state.py
─────────────────
Immutable coverage state model for the Topic Coverage Tracker.

Responsibilities
────────────────
- Represent the full coverage snapshot at any point in the viva.
- Track per-topic entry records (asked count, tags, outcomes).
- Support functional updates (replace, not mutate).
- Be trivially serializable (plain Python types only).

Rules
─────
- Frozen dataclasses — state is replaced, never mutated.
- All update methods return a new CoverageState.
- No dependency on ORACLE internals.
- Serialization: model_dump() → plain dict with no custom types.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Dict, FrozenSet, List, Optional, Tuple


# ── Coverage status ───────────────────────────────────────────────────────────

class CoverageStatus(str, Enum):
    NOT_STARTED = "not_started"   # Category has 0 questions asked
    PARTIAL     = "partial"       # Below min_questions threshold
    COVERED     = "covered"       # Met or exceeded min_questions
    SATURATED   = "saturated"     # Significantly over min_questions (diminishing returns)


# ── Topic entry ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TopicEntry:
    """
    Immutable record of all asks for a single question_target topic.

    question_target : Canonical topic identifier (matches NormalizedVivaTarget).
    category        : Which coverage domain this belongs to.
    tags            : Lowercase topic tags for this entry.
    ask_count       : How many times this topic has been asked.
    answered        : True if at least one answer was received.
    turn_first_asked: Turn index when first asked (for ordering).
    """
    question_target: str
    category: str
    tags: FrozenSet[str]
    ask_count: int = 0
    answered: bool = False
    turn_first_asked: int = 0

    def increment(self, answered: bool = False) -> "TopicEntry":
        """Return a new entry with ask_count+1 and optional answered flag."""
        return replace(
            self,
            ask_count = self.ask_count + 1,
            answered  = self.answered or answered,
        )

    def to_dict(self) -> dict:
        return {
            "question_target":  self.question_target,
            "category":         self.category,
            "tags":             sorted(self.tags),
            "ask_count":        self.ask_count,
            "answered":         self.answered,
            "turn_first_asked": self.turn_first_asked,
        }


# ── Coverage state ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CoverageState:
    """
    Complete, immutable snapshot of topic coverage at one point in the viva.

    topics           : Dict[question_target → TopicEntry]
    category_counts  : Dict[category_name → total ask_count]
    covered_categories: Set of category names that met their min_questions.
    total_turns      : Total viva turns elapsed (for saturation checks).
    """
    topics: Dict[str, TopicEntry] = field(default_factory=dict)
    category_counts: Dict[str, int] = field(default_factory=dict)
    covered_categories: FrozenSet[str] = field(default_factory=frozenset)
    total_turns: int = 0

    # ── Derived properties ────────────────────────────────────────────────────

    @property
    def asked_targets(self) -> FrozenSet[str]:
        return frozenset(self.topics.keys())

    @property
    def answered_targets(self) -> FrozenSet[str]:
        return frozenset(t for t, e in self.topics.items() if e.answered)

    @property
    def total_asked(self) -> int:
        return len(self.topics)

    def category_ask_count(self, category: str) -> int:
        return self.category_counts.get(category, 0)

    def is_covered(self, category: str) -> bool:
        return category in self.covered_categories

    def has_been_asked(self, question_target: str) -> bool:
        return question_target in self.topics

    # ── Functional updates ────────────────────────────────────────────────────

    def record_ask(
        self,
        question_target: str,
        category: str,
        tags: FrozenSet[str],
        turn_index: int,
        min_questions_for_category: int = 1,
    ) -> "CoverageState":
        """
        Return new state reflecting a question being asked.

        Creates a new TopicEntry if the target hasn't been seen before.
        """
        existing = self.topics.get(question_target)
        if existing:
            updated_entry = existing.increment(answered=False)
        else:
            updated_entry = TopicEntry(
                question_target  = question_target,
                category         = category,
                tags             = tags,
                ask_count        = 1,
                answered         = False,
                turn_first_asked = turn_index,
            )

        new_topics = {**self.topics, question_target: updated_entry}
        new_counts = dict(self.category_counts)
        new_counts[category] = new_counts.get(category, 0) + 1

        # Recompute covered categories
        covered = set(self.covered_categories)
        if new_counts[category] >= min_questions_for_category:
            covered.add(category)

        return replace(
            self,
            topics             = new_topics,
            category_counts    = new_counts,
            covered_categories = frozenset(covered),
            total_turns        = self.total_turns + 1,
        )

    def record_answer(self, question_target: str) -> "CoverageState":
        """Return new state marking the topic as answered."""
        if question_target not in self.topics:
            return self
        updated = self.topics[question_target].increment(answered=True)
        new_topics = {**self.topics, question_target: updated}
        return replace(self, topics=new_topics)

    def advance_turn(self) -> "CoverageState":
        """Increment total_turns without recording a topic."""
        return replace(self, total_turns=self.total_turns + 1)

    # ── Serialization ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Return a plain-dict representation for export / logging."""
        return {
            "topics":             {k: v.to_dict() for k, v in self.topics.items()},
            "category_counts":    dict(self.category_counts),
            "covered_categories": sorted(self.covered_categories),
            "total_turns":        self.total_turns,
            "total_asked":        self.total_asked,
        }

    @classmethod
    def empty(cls) -> "CoverageState":
        """Return a zeroed CoverageState for session initialization."""
        return cls()
