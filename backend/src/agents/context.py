from typing import Any, Dict
from .base import BaseAgent
from ..models.events import EventType
from ..models.context import StructuredContext, TechStack, ArchitectureDetail

class ContextBuilderAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="ContextBuilder")

    async def process(self, session_id: str, source_data: Dict[str, Any]) -> StructuredContext:
        """
        Reads PDFs/GitHub and produces structured JSON context.
        """
        self.log_info(f"Building context for session {session_id}")
        
        # Placeholder for LLM-based extraction logic
        # context_data = await self.llm_service.extract(source_data)
        
        # Mocking structured output
        mock_context = StructuredContext(
            project_name="Example Project",
            technologies=TechStack(languages=["Python"], frameworks=["FastAPI"]),
            architecture=ArchitectureDetail(pattern="Microservices", components=["API Gateway", "Auth Service"]),
            algorithms=["Dijkstra"],
            api_endpoints=["/v1/login", "/v1/data"],
            decisions=[]
        )
        
        self.emit_event(
            session_id=session_id,
            event_type=EventType.CONTEXT_GENERATED,
            payload={"project_name": mock_context.project_name, "tech_count": len(mock_context.technologies.languages)}
        )
        
        return mock_context
