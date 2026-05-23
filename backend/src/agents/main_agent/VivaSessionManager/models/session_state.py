"""
Viva session state model classes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Session Lifecycle Stage
# ---------------------------------------------------------------------------

class SessionLifecycleStage(str, Enum):
    """Explicit lifecycle stages for a viva session."""

    IDLE = "idle"
    INITIALIZED = "initialized"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    TERMINATED = "terminated"
    ERROR = "error"


# ---------------------------------------------------------------------------
# Supporting Records
# ---------------------------------------------------------------------------

@dataclass
class WeakAreaRecord:
    """Tracks a topic the candidate struggled with."""

    topic: str
    confidence: float = 0.0
    occurrence_count: int = 0
    first_seen_at: Optional[str] = None
    last_seen_at: Optional[str] = None

    def merge(self, other: "WeakAreaRecord") -> "WeakAreaRecord":
        confidence = other.confidence if other.confidence < self.confidence else self.confidence
        return WeakAreaRecord(
            topic=self.topic,
            confidence=min(self.confidence, other.confidence),
            occurrence_count=self.occurrence_count + other.occurrence_count,
            first_seen_at=self.first_seen_at or other.first_seen_at,
            last_seen_at=other.last_seen_at or self.last_seen_at,
        )


@dataclass
class ContradictionEntry:
    """A candidate statement that contradicts a prior answer."""

    turn_index: int
    claim: str
    prior_claim: str
    severity: float = 0.0
    noted_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_index": self.turn_index,
            "claim": self.claim,
            "prior_claim": self.prior_claim,
            "severity": self.severity,
            "noted_at": self.noted_at,
        }


@dataclass
class FollowUpRecord:
    """Tracks one follow-up chain originating from a given question turn."""

    origin_turn_index: int
    chain_depth: int = 0
    is_exhausted: bool = False
    follow_up_indices: List[int] = field(default_factory=list)

    def add_turn(self, turn_index: int) -> None:
        """Append a follow-up turn, guarding against duplicate entries."""
        if turn_index not in self.follow_up_indices:
            self.follow_up_indices.append(turn_index)
            self.chain_depth = len(self.follow_up_indices)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "origin_turn_index": self.origin_turn_index,
            "chain_depth": self.chain_depth,
            "is_exhausted": self.is_exhausted,
            "follow_up_indices": self.follow_up_indices,
        }


# ---------------------------------------------------------------------------
# Per-turn records
# ---------------------------------------------------------------------------

@dataclass
class RecordedQuestion:
    """An asked question within the session."""

    turn_index: int
    question_text: str
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    target_category: Optional[str] = None
    asked_at: Optional[str] = None
    is_follow_up: bool = False
    parent_turn_index: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_index": self.turn_index,
            "question_text": self.question_text,
            "topic": self.topic,
            "difficulty": self.difficulty,
            "target_category": self.target_category,
            "asked_at": self.asked_at,
            "is_follow_up": self.is_follow_up,
            "parent_turn_index": self.parent_turn_index,
        }


@dataclass
class RecordedResponse:
    """A candidate response mapped to a specific question turn."""

    turn_index: int
    response_text: str
    quality_score: Optional[float] = None
    detected_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_index": self.turn_index,
            "response_text": self.response_text,
            "quality_score": self.quality_score,
            "detected_at": self.detected_at,
        }


# ---------------------------------------------------------------------------
# Root Session State
# ---------------------------------------------------------------------------

@dataclass
class SessionState:
    """
    Durable, JSON-serialisable container for the entire viva session.

    All fields are plain Python types so the structure can be round-tripped
    through ``json.loads / json.dumps`` without any custom encoder.
    """

    session_id: str
    candidate_id: Optional[str] = None
    started_at: Optional[str] = None
    updated_at: Optional[str] = None

    lifecycle_stage: str = SessionLifecycleStage.IDLE.value

    questions: List[Dict[str, Any]] = field(default_factory=list)
    responses: List[Dict[str, Any]] = field(default_factory=list)

    topic_coverage: Dict[str, int] = field(default_factory=dict)
    weak_areas: List[Dict[str, Any]] = field(default_factory=list)
    contradictions: List[Dict[str, Any]] = field(default_factory=list)
    follow_up_chains: List[Dict[str, Any]] = field(default_factory=list)

    schema_version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def current_turn_index(self) -> int:
        return len(self.questions)

    @property
    def is_active(self) -> bool:
        return self.lifecycle_stage in {
            SessionLifecycleStage.INITIALIZED.value,
            SessionLifecycleStage.IN_PROGRESS.value,
            SessionLifecycleStage.PAUSED.value,
        }

    # ── Mutation helpers ───────────────────────────────────────────────────

    def record_question(self, question: Dict[str, Any]) -> int:
        turn = len(self.questions)
        record = {
            "turn_index": turn,
            "question_text": question["question_text"],
            "topic": question.get("topic"),
            "difficulty": question.get("difficulty"),
            "target_category": question.get("target_category"),
            "asked_at": question.get("asked_at") or self._now(),
            "is_follow_up": question.get("is_follow_up", False),
            "parent_turn_index": question.get("parent_turn_index"),
        }
        self.questions.append(record)
        topic = question.get("topic")
        if topic:
            self.topic_coverage[topic] = self.topic_coverage.get(topic, 0) + 1
        self.updated_at = self._now()
        return turn

    def record_response(self, response: Dict[str, Any]) -> int:
        turn = response.get("turn_index", len(self.responses))
        record = {
            "turn_index": turn,
            "response_text": response["response_text"],
            "quality_score": response.get("quality_score"),
            "detected_at": response.get("detected_at") or self._now(),
        }
        self.responses.append(record)
        self.updated_at = self._now()
        return turn

    def add_contradiction(self, contradiction: Dict[str, Any]) -> None:
        entry = {
            "turn_index": contradiction["turn_index"],
            "claim": contradiction["claim"],
            "prior_claim": contradiction["prior_claim"],
            "severity": contradiction.get("severity", 0.0),
            "noted_at": contradiction.get("noted_at") or self._now(),
        }
        self.contradictions.append(entry)
        self.updated_at = self._now()

    def register_weak_area(self, topic: str, confidence: float = 0.5) -> None:
        for existing in self.weak_areas:
            if existing["topic"] == topic:
                existing["occurrence_count"] += 1
                existing["confidence"] = min(existing["confidence"], confidence)
                existing["last_seen_at"] = self._now()
                self.updated_at = self._now()
                return
        self.weak_areas.append({
            "topic": topic,
            "confidence": confidence,
            "occurrence_count": 1,
            "first_seen_at": self._now(),
            "last_seen_at": self._now(),
        })
        self.updated_at = self._now()

    def start_follow_up_chain(self, origin_turn_index: int) -> None:
        self.follow_up_chains.append({
            "origin_turn_index": origin_turn_index,
            "chain_depth": 0,
            "is_exhausted": False,
            "follow_up_indices": [],
        })

    def advance_follow_up_chain(self, origin_turn_index: int, turn_index: int) -> None:
        for chain in self.follow_up_chains:
            if chain["origin_turn_index"] == origin_turn_index:
                if turn_index not in chain["follow_up_indices"]:
                    chain["follow_up_indices"].append(turn_index)
                    chain["chain_depth"] = len(chain["follow_up_indices"])
                self.updated_at = self._now()
                return

    # ── Serialisation ──────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "candidate_id": self.candidate_id,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "lifecycle_stage": self.lifecycle_stage,
            "questions": list(self.questions),
            "responses": list(self.responses),
            "topic_coverage": dict(self.topic_coverage),
            "weak_areas": list(self.weak_areas),
            "contradictions": list(self.contradictions),
            "follow_up_chains": list(self.follow_up_chains),
            "schema_version": self.schema_version,
            "metadata": dict(self.metadata),
        }

    def to_json(self, **kwargs: Any) -> str:
        return json.dumps(self.to_dict(), **kwargs)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionState":
        stage = data.get("lifecycle_stage", SessionLifecycleStage.IDLE.value)
        valid_stages = {s.value for s in SessionLifecycleStage}
        if stage not in valid_stages:
            stage = SessionLifecycleStage.IDLE.value
        return cls(
            session_id=data["session_id"],
            candidate_id=data.get("candidate_id"),
            started_at=data.get("started_at"),
            updated_at=data.get("updated_at"),
            lifecycle_stage=stage,
            questions=list(data.get("questions", [])),
            responses=list(data.get("responses", [])),
            topic_coverage=dict(data.get("topic_coverage", {})),
            weak_areas=list(data.get("weak_areas", [])),
            contradictions=list(data.get("contradictions", [])),
            follow_up_chains=list(data.get("follow_up_chains", [])),
            schema_version=data.get("schema_version", "1.0.0"),
            metadata=dict(data.get("metadata", {})),
        )

    @classmethod
    def from_json(cls, raw: str) -> "SessionState":
        return cls.from_dict(json.loads(raw))

    @staticmethod
    def _now() -> str:
        return datetime.utcnow().isoformat()
