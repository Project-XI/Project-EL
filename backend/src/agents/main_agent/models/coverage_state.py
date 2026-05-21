from typing import Dict
from pydantic import BaseModel, Field


class CoverageState(BaseModel):
    topics: Dict[str, str] = Field(default_factory=dict)

