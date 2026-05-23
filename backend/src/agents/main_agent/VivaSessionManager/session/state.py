"""
VivaSessionState — top-level coordinator for a viva session.

Combines:
- a :class:`~models.session_state.SessionState`   (durable JSON fragment),
- a :class:`SessionHistory`                        (ordered Q&A layer), and
- a :class:`~models.coverage_state.CoverageState`  (topic coverage layer)

into one ergonomic interface accessible only by MAIN.

Not thread-safe — callers must operate exclusively from a single async
coroutine within an event loop.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from vsm.models.session_state import (
    ContradictionEntry,
    FollowUpRecord,
    RecordedQuestion,
    RecordedResponse,
    SessionLifecycleStage,
    SessionState,
    WeakAreaRecord,
)
from vsm.models.coverage_state import CoverageState
from vsm.session.history import SessionHistory
from vsm.session.persistence import SessionPersistence
from vsm.session.transitions import (
    InvalidTransitionError,
    TransitionManager,
    is_terminal,
)


class VivaSessionState:
    """
    High-level session state facade owned exclusively by MAIN.

    Parameters
    ----------
    session_id:
        Unique session identifier.
    candidate_id:
        Optional candidate / student identifier.
    storage_backend:
        Optional :class:`SessionPersistence`.  When provided,
        :meth:`save` / :meth:`load` are hydrated automatically.
    schema_version:
        Schema version tag stored in the durable fragment.
    """

    def __init__(
        self,
        session_id: str,
        candidate_id: Optional[str] = None,
        storage_backend: Optional[SessionPersistence] = None,
        *,
        schema_version: str = "1.0.0",
    ) -> None:
        self.session_id = session_id
        self.candidate_id = candidate_id

        self._state = SessionState(
            session_id=session_id,
            candidate_id=candidate_id,
            lifecycle_stage=SessionLifecycleStage.INITIALIZED.value,
            schema_version=schema_version,
        )
        self._history = SessionHistory(session_id)
        self._coverage = CoverageState()
        self._transition_manager = TransitionManager(self._history)
        self._persistence = storage_backend

    # ---- Lifecycle / stage --------------------------------------------------

    @property
    def current_stage(self) -> str:
        return self._state.lifecycle_stage

    @property
    def is_active(self) -> bool:
        return self._state.is_active

    @property
    def turn_index(self) -> int:
        """Zero-based index of the *next* question turn."""
        return self._history.get_question_count()

    def advance_stage(self, to_stage: SessionLifecycleStage) -> None:
        """Transition to a new lifecycle stage after FSM validation."""
        from_stage = self._state.lifecycle_stage
        self._transition_manager.validate_transition(from_stage, to_stage.value)
        self._state.lifecycle_stage = to_stage.value
        self._state.updated_at = self._now()

    # ---- Question + response recording --------------------------------------

    def record_question(
        self,
        question_text: str,
        topic: Optional[str] = None,
        difficulty: Optional[str] = None,
        target_category: Optional[str] = None,
        is_follow_up: bool = False,
        parent_turn_index: Optional[int] = None,
    ) -> int:
        """
        Record a new question, advance topic coverage and durable state,
        and return the turn index assigned to it.
        """
        q = RecordedQuestion(
            turn_index=0,
            question_text=question_text,
            topic=topic,
            difficulty=difficulty,
            target_category=target_category,
            is_follow_up=is_follow_up,
            parent_turn_index=parent_turn_index,
        )
        history_turn = self._history.record_question(q)

        # Re-key after insertion so the in-memory object is consistent
        stored_q = self._history.get_question(history_turn)
        if stored_q:
            stored_q.turn_index = history_turn

        self._state.record_question({
            "question_text": question_text,
            "topic": topic,
            "difficulty": difficulty,
            "target_category": target_category,
            "is_follow_up": is_follow_up,
            "parent_turn_index": parent_turn_index,
        })
        if topic:
            self._coverage.record_question_for(topic)
        return history_turn

    def record_response(
        self,
        turn_index: int,
        response_text: str,
        quality_score: Optional[float] = None,
    ) -> int:
        """Record a candidate response mapped to its turn index."""
        r = RecordedResponse(
            turn_index=turn_index,
            response_text=response_text,
            quality_score=quality_score,
        )
        self._history.record_response(r)
        self._state.record_response({
            "turn_index": turn_index,
            "response_text": response_text,
            "quality_score": quality_score,
        })
        return turn_index

    # ---- Contradiction memory ------------------------------------------------

    def add_contradiction(
        self,
        turn_index: int,
        claim: str,
        prior_claim: str,
        severity: float = 0.0,
    ) -> None:
        self._state.add_contradiction({
            "turn_index": turn_index,
            "claim": claim,
            "prior_claim": prior_claim,
            "severity": severity,
        })

    # ---- Weak-area tracking -------------------------------------------------

    def register_weak_area(self, topic: str, confidence: float = 0.5) -> None:
        self._state.register_weak_area(topic, confidence)

    # ---- Topic coverage ------------------------------------------------------

    @property
    def coverage_state(self) -> CoverageState:
        return self._coverage

    def set_planned_topics(self, topics: List[str]) -> None:
        self._coverage.planned_topics = list(topics)
        self._coverage.recompute_percentage()

    def get_topic_coverage_percentage(self) -> float:
        return self._coverage.coverage_percentage

    # ---- Follow-up chains ----------------------------------------------------

    def start_follow_up_chain(self, origin_turn_index: int) -> None:
        self._history.start_follow_up_chain(origin_turn_index)
        self._state.start_follow_up_chain(origin_turn_index)

    def advance_follow_up_chain(
        self, origin_turn_index: int, turn_index: int
    ) -> None:
        self._history.advance_follow_up_chain(origin_turn_index, turn_index)
        self._state.advance_follow_up_chain(origin_turn_index, turn_index)

    # ---- Serialisation -------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self._state.to_dict(),
            "coverage": self._coverage.to_dict(),
            "history": self._history.to_dict(),
        }

    def to_json(self, **kwargs: Any) -> str:
        import json
        return json.dumps(self.to_dict(), **kwargs)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VivaSessionState":
        if "state" not in data:
            raise ValueError("Expected top-level 'state' key in persisted data.")
        self = cls.__new__(cls)
        self._state = SessionState.from_dict(data["state"])
        self.session_id = self._state.session_id
        self.candidate_id = self._state.candidate_id
        self._coverage = CoverageState.from_dict(data.get("coverage", {}))
        self._history = SessionHistory.from_dict(
            data.get("history", {"session_id": self.session_id})
        )
        self._transition_manager = TransitionManager(self._history)
        self._persistence = None
        return self

    @classmethod
    def from_json(cls, raw: str) -> "VivaSessionState":
        import json
        return cls.from_dict(json.loads(raw))

    # ---- Persistence ---------------------------------------------------------

    def save(self) -> Any:
        if self._persistence is None:
            raise RuntimeError(
                "No persistence backend attached to this VivaSessionState."
            )
        return self._persistence.save(self.session_id, self.to_dict())

    @classmethod
    def load(cls, session_id: str, persistence: SessionPersistence) -> "VivaSessionState":
        """Load a previously persisted session state from *persistence*."""
        data = persistence.load(session_id)
        if data is None:
            raise KeyError(f"No persisted session found for id={session_id!r}")
        instance = cls.from_dict(data)
        instance._persistence = persistence
        return instance

    # ---- Replay helpers ------------------------------------------------------

    def replay_view(self) -> List[Dict[str, Any]]:
        """
        Produce a deterministic, ordered replay of every completed Q&A turn.

        Invoking this immediately after loading from a persisted dict
        yields an identical list, fulfilling the replay-safety criterion.
        """
        qa = self._history.get_qa_pairs()
        view: List[Dict[str, Any]] = []
        for turn_index, (question, response) in enumerate(qa):
            entry: Dict[str, Any] = {
                "turn_index": turn_index,
                "question": question.question_text,
                "topic": question.topic,
                "response": response.response_text if response else None,
                "quality_score": response.quality_score if response else None,
                "is_follow_up": question.is_follow_up,
            }
            view.append(entry)
        return view

    # ---- Meta / repr ---------------------------------------------------------

    @staticmethod
    def _now() -> str:
        return datetime.utcnow().isoformat()

    def __repr__(self) -> str:
        return (
            f"VivaSessionState(session_id={self.session_id!r}, "
            f"stage={self._state.lifecycle_stage!r}, "
            f"turns={self.turn_index})"
        )
