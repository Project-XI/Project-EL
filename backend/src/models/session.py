from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from .events import PlatformEvent

class TranscriptEntry(BaseModel):
    role: str # e.g., "examiner", "student"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class VivaSession(BaseModel):
    session_id: str
    student_id: str
    status: str = "initialized" # "active", "completed", "terminated"
    context_id: Optional[str] = None
    transcript: List[TranscriptEntry] = []
    events: List[PlatformEvent] = []
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None

    class Config:
        use_enum_values = True
