"""
Topic coverage state — tracks which viva topics have been touched,
how many times, and whether coverage is sufficient.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class TopicCoverage:
    """Coverage record for a single topic."""

    topic: str
    question_count: int = 0
    asked_at: Optional[str] = None    # ISO-8601 — first time it was asked
    last_asked_at: Optional[str] = None  # ISO-8601 — most recent

    def record_asked(self) -> None:
        now = datetime.utcnow().isoformat()
        self.question_count += 1
        if self.asked_at is None:
            self.asked_at = now
        self.last_asked_at = now

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "question_count": self.question_count,
            "asked_at": self.asked_at,
            "last_asked_at": self.last_asked_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TopicCoverage":
        return cls(
            topic=data["topic"],
            question_count=data.get("question_count", 0),
            asked_at=data.get("asked_at"),
            last_asked_at=data.get("last_asked_at"),
        )


@dataclass
class CoverageState:
    """
    Aggregated coverage snapshot across all viva topics.

    Parameters
    ----------
    planned_topics:
        Ordered list of topics the viva *should* cover.
    topic_records:
        Per-topic coverage records keyed by topic label.
    coverage_percentage:
        Cached float: fraction of *planned* topics that have been asked
        at least once (0.0 – 1.0).  Recomputed when mutated via
        :meth:`recompute_percentage`.
    """

    planned_topics: List[str] = field(default_factory=list)
    topic_records: Dict[str, TopicCoverage] = field(default_factory=dict)
    coverage_percentage: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------

    def register_topic(self, topic: str) -> None:
        if topic not in self.topic_records:
            self.topic_records[topic] = TopicCoverage(topic=topic)

    def record_question_for(self, topic: str) -> None:
        """Register that *topic* has had a question asked; recompute pct."""
        self.register_topic(topic)
        self.topic_records[topic].record_asked()
        self.recompute_percentage()

    def mark_exhausted(self, topic: str) -> None:
        """Mark *topic* as having no further follow-ups needed."""
        self.metadata[f"exhausted:{topic}"] = True

    def is_exhausted(self, topic: str) -> bool:
        return self.metadata.get(f"exhausted:{topic}", False)

    # ------------------------------------------------------------------
    # Derived
    # ------------------------------------------------------------------

    def recompute_percentage(self) -> float:
        if not self.planned_topics:
            self.coverage_percentage = 0.0
            return 0.0
        touched = sum(
            1
            for topic in self.planned_topics
            if topic in self.topic_records
            and self.topic_records[topic].question_count > 0
        )
        self.coverage_percentage = touched / len(self.planned_topics)
        return self.coverage_percentage

    def get_uncovered_planned_topics(self) -> List[str]:
        return [
            t
            for t in self.planned_topics
            if t not in self.topic_records
            or self.topic_records[t].question_count == 0
        ]

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "planned_topics": list(self.planned_topics),
            "topic_records": {
                k: v.to_dict() for k, v in self.topic_records.items()
            },
            "coverage_percentage": self.coverage_percentage,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CoverageState":
        records_raw = data.get("topic_records", {})
        topic_records: Dict[str, TopicCoverage] = {
            k: TopicCoverage.from_dict(v) for k, v in records_raw.items()
        }
        return cls(
            planned_topics=list(data.get("planned_topics", [])),
            topic_records=topic_records,
            coverage_percentage=data.get("coverage_percentage", 0.0),
            metadata=dict(data.get("metadata", {})),
        )
