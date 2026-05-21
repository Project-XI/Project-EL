from typing import Optional

from pydantic import BaseModel


class TranscriptEntry(BaseModel):
    turn_id: int
    question_id: str
    question_text: str
    follow_up_to_turn_id: Optional[int] = None


class CandidateResponse(BaseModel):
    turn_id: int
    response_text: str
