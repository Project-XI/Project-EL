from typing import Any, Dict, List
from .base import BaseAgent
from ..models.events import EventType
from ..models.session import TranscriptEntry

class MainExaminerAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="MainExaminer")

    async def process(self, session_id: str, student_response: str) -> str:
        """
        Conducts viva questioning and generates follow-ups.
        """
        self.log_info(f"Processing response in session {session_id}")
        
        # 1. Retrieve session context & history
        # 2. Analyze response using LLM
        # 3. Generate adaptive follow-up
        
        next_question = "Can you explain why you chose FastAPI over Flask for this project?"
        
        self.emit_event(
            session_id=session_id,
            event_type=EventType.QUESTION_POSED,
            payload={"question": next_question}
        )
        
        return next_question

    def get_initial_question(self, session_id: str, context: Dict[str, Any]) -> str:
        question = f"I see you worked on {context.get('project_name')}. Let's start there."
        self.emit_event(session_id, EventType.QUESTION_POSED, {"question": question})
        return question
