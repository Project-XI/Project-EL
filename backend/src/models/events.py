from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class EventType(str, Enum):
    SESSION_STARTED = "session_started"
    SESSION_COMPLETED = "session_completed"
    IDENTITY_VERIFIED = "identity_verified"
    CONTEXT_GENERATED = "context_generated"
    QUESTION_POSED = "question_posed"
    ANSWER_RECEIVED = "answer_received"
    BEHAVIOUR_FLAGGED = "behaviour_flagged"
    SYSTEM_ERROR = "system_error"
    
    # ORACLE Events
    FILE_RECEIVED = "file_received"
    PDF_PARSED = "pdf_parsed"
    DOCX_PARSED = "docx_parsed"
    REPO_CLONED = "repo_cloned"
    STRUCTURE_ANALYZED = "structure_analyzed"
    TECH_STACK_DETECTED = "tech_stack_detected"
    PROJECT_GRAPH_BUILT = "project_graph_built"
    CONTEXT_SYNTHESIZED = "context_synthesized"
    CONTEXT_READY = "context_ready"

class PlatformEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: str
    agent_name: str
    event_type: EventType
    payload: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        use_enum_values = True
