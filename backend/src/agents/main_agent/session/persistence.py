from abc import ABC, abstractmethod
from typing import Dict, Optional

from src.agents.main_agent.models import SessionState


class SessionStateStorage(ABC):
    @abstractmethod
    def save(self, session_id: str, payload: str) -> None:
        pass

    @abstractmethod
    def load(self, session_id: str) -> Optional[str]:
        pass


class InMemorySessionStateStorage(SessionStateStorage):
    def __init__(self):
        self._store: Dict[str, str] = {}

    def save(self, session_id: str, payload: str) -> None:
        self._store[session_id] = payload

    def load(self, session_id: str) -> Optional[str]:
        return self._store.get(session_id)


def serialize_state(state: SessionState) -> str:
    return state.model_dump_json()


def deserialize_state(payload: str) -> SessionState:
    return SessionState.model_validate_json(payload)

