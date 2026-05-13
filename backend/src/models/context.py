from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field

class EvidenceModel(BaseModel):
    value: Any
    confidence: float
    evidence: List[str] = []

class ProjectNode(BaseModel):
    id: str
    label: str
    type: str # e.g., "frontend", "backend", "database", "middleware"
    metadata: Dict[str, Any] = {}

class ProjectEdge(BaseModel):
    source: str
    target: str
    relationship: str
    confidence: float
    evidence: List[str] = []

class ProjectGraph(BaseModel):
    nodes: List[ProjectNode] = []
    edges: List[ProjectEdge] = []

class ImplementationReasoning(BaseModel):
    technology: str
    probable_reasoning: List[str]
    confidence: float
    evidence: List[str]

class VivaTarget(BaseModel):
    topic: str
    question_target: str
    difficulty: str # "easy", "medium", "hard"
    focus: str

class InconsistencyFlag(BaseModel):
    issue: str
    severity: str # "low", "medium", "high"
    confidence: float
    evidence: List[str]

class StructuredContext(BaseModel):
    project_name: EvidenceModel
    project_type: EvidenceModel
    frontend_framework: EvidenceModel
    backend_framework: EvidenceModel
    database_used: EvidenceModel
    authentication_system: EvidenceModel
    architecture_pattern: EvidenceModel
    
    # Advanced Intelligence
    project_graph: ProjectGraph = Field(default_factory=ProjectGraph)
    implementation_reasoning: List[ImplementationReasoning] = []
    tradeoff_analysis: List[EvidenceModel] = []
    
    # Viva Intelligence
    viva_intelligence_targets: List[VivaTarget] = []
    failure_scenarios: List[str] = []
    scalability_questions: List[str] = []
    optimization_questions: List[str] = []
    cross_question_targets: List[str] = []
    
    # Detection Flags
    inconsistencies: List[InconsistencyFlag] = []
    complexity_mismatch: Optional[EvidenceModel] = None
    
    # Metadata
    raw_summary: Optional[str] = None
    
    # Pydantic V2 compatibility is inherent in the class definition
    # but we ensure all calls use .model_dump()
