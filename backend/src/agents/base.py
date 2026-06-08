import os
import requests
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from src.core.events import EventEmitter
from src.models.events import EventType

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.repo_slug = "Project-XI/Project-EL"

    def emit_event(self, session_id: str, event_type: EventType, payload: Dict[str, Any]):
        """Standard method for agents to emit structured events."""
        # Also dispatch a repository event for progress updates
        if str(event_type) == EventType.AGENT_PROGRESS.value and self.github_token:
            self._dispatch_github_event(session_id, payload)
            
        return EventEmitter.emit(
            session_id=session_id,
            agent_name=self.name,
            event_type=event_type,
            payload=payload
        )

    def _dispatch_github_event(self, session_id: str, payload: Dict[str, Any]):
        """Sends a repository_dispatch event to GitHub."""
        url = f"https://api.github.com/repos/{self.repo_slug}/dispatches"
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "event_type": "agent-progress",
            "client_payload": {
                "session_id": session_id,
                **payload
            }
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 204:
                self.log_info(f"Successfully dispatched agent-progress event for {payload.get('agent')}")
            else:
                self.log_info(f"Failed to dispatch event: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_info(f"Error dispatching GitHub event: {e}")

    @abstractmethod
    async def process(self, session_id: str, input_data: Any, log_callback=None) -> Any:
        """Main processing loop for the agent."""
        pass

    def log_info(self, message: str):
        print(f"[{self.name}] INFO: {message}")

