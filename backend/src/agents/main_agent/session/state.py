from typing import Optional

from src.agents.main_agent.models import (
    CandidateResponse,
    ContradictionEntry,
    SessionLifecycle,
    SessionState,
    SessionTransition,
    TranscriptEntry,
)
from src.agents.main_agent.session.history import build_replay_view
from src.agents.main_agent.session.persistence import (
    SessionStateStorage,
    deserialize_state,
    serialize_state,
)
from src.agents.main_agent.session.transitions import validate_transition


class SessionStateManager:
    def __init__(self, state: SessionState):
        self.state = state

    @classmethod
    def create(cls, session_id: str) -> "SessionStateManager":
        return cls(SessionState(session_id=session_id))

    @classmethod
    def from_json(cls, payload: str) -> "SessionStateManager":
        return cls(deserialize_state(payload))

    @classmethod
    def recover(cls, session_id: str, storage: SessionStateStorage) -> Optional["SessionStateManager"]:
        payload = storage.load(session_id)
        if payload is None:
            return None
        return cls.from_json(payload)

    def transition_to(self, to_stage: SessionLifecycle) -> None:
        from_stage = self.state.lifecycle_stage
        validate_transition(from_stage, to_stage)
        if from_stage == to_stage:
            return
        self.state.lifecycle_stage = to_stage
        self.state.transitions.append(SessionTransition(from_stage=from_stage, to_stage=to_stage))

    def ask_question(
        self,
        question_id: str,
        question_text: str,
        follow_up_to_turn_id: Optional[int] = None,
    ) -> int:
        turn_id = self.state.next_turn_id
        self.state.next_turn_id += 1
        self.state.question_history.append(
            TranscriptEntry(
                turn_id=turn_id,
                question_id=question_id,
                question_text=question_text,
                follow_up_to_turn_id=follow_up_to_turn_id,
            )
        )
        if follow_up_to_turn_id is not None:
            chain_key = str(follow_up_to_turn_id)
            self.state.follow_up_chains.setdefault(chain_key, []).append(turn_id)
        return turn_id

    def record_response(self, turn_id: int, response_text: str) -> None:
        turn_exists = any(question.turn_id == turn_id for question in self.state.question_history)
        if not turn_exists:
            raise ValueError(f"Cannot record response for unknown turn {turn_id}")
        self.state.response_history.append(CandidateResponse(turn_id=turn_id, response_text=response_text))

    def add_contradiction(self, turn_id: int, detail: str) -> None:
        self.state.contradiction_history.append(ContradictionEntry(turn_id=turn_id, detail=detail))

    def update_weak_area(self, topic: str, increment: int = 1) -> None:
        self.state.weak_areas[topic] = self.state.weak_areas.get(topic, 0) + increment

    def update_topic_coverage(self, topic: str, status: str) -> None:
        self.state.coverage_state.topics[topic] = status

    def replay_view(self):
        return build_replay_view(self.state)

    def to_json(self) -> str:
        return serialize_state(self.state)

    def save(self, storage: SessionStateStorage) -> None:
        storage.save(self.state.session_id, self.to_json())

