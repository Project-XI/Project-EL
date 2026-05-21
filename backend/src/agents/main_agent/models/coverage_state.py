from enum import Enum
from typing import Dict

from pydantic import BaseModel, Field


class CoverageStatus(str, Enum):
    COVERED = "covered"
    PARTIAL = "partial"
    NOT_COVERED = "not_covered"


class CoverageState(BaseModel):
    topics: Dict[str, CoverageStatus] = Field(default_factory=dict)
