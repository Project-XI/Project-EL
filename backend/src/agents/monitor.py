from typing import Any, Dict
from .base import BaseAgent
from ..models.events import EventType

class BehaviourMonitorAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="BehaviourMonitor")

    async def process(self, session_id: str, metadata: Dict[str, Any]) -> None:
        """
        Receives gaze and audio metadata to detect suspicious behavior.
        Logs behavioural events only.
        """
        self.log_info(f"Monitoring behaviour for session {session_id}")
        
        # Example metadata: {"gaze_off_screen_duration": 5.5, "audio_noise_level": "high"}
        
        if metadata.get("gaze_off_screen_duration", 0) > 3.0:
            self.emit_event(
                session_id=session_id,
                event_type=EventType.BEHAVIOUR_FLAGGED,
                payload={
                    "reason": "gaze_off_screen",
                    "duration": metadata["gaze_off_screen_duration"]
                }
            )
            self.log_info("Flagged: Student looking away for too long.")
        
        return None
