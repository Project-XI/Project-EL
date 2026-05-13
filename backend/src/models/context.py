from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class TechStack(BaseModel):
    languages: List[str] = []
    frameworks: List[str] = []
    databases: List[str] = []
    tools: List[str] = []

class ArchitectureDetail(BaseModel):
    pattern: Optional[str] = None
    components: List[str] = []
    data_flow: Optional[str] = None

class ImplementationDecision(BaseModel):
    feature: str
    decision: str
    rationale: Optional[str] = None

class StructuredContext(BaseModel):
    project_name: str
    technologies: TechStack
    architecture: ArchitectureDetail
    algorithms: List[str] = []
    api_endpoints: List[str] = []
    decisions: List[ImplementationDecision] = []
    raw_summary: Optional[str] = None
