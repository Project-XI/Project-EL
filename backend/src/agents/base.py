from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from src.core.events import EventEmitter
from src.models.events import EventType

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name

    def emit_event(self, session_id: str, event_type: EventType, payload: Dict[str, Any]):
        """Standard method for agents to emit structured events."""
        return EventEmitter.emit(
            session_id=session_id,
            agent_name=self.name,
            event_type=event_type,
            payload=payload
        )

    @abstractmethod
    async def process(self, session_id: str, input_data: Any) -> Any:
        """Main processing loop for the agent."""
        pass

    def log_info(self, message: str):
        print(f"[{self.name}] INFO: {message}")
