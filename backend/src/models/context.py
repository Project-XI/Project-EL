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
    label: Optional[str] = None

class ProjectGraph(BaseModel):
    nodes: List[ProjectNode] = []
    edges: List[ProjectEdge] = []

class StructuredContext(BaseModel):
    project_name: EvidenceModel
    project_type: EvidenceModel
    frontend_framework: EvidenceModel
    backend_framework: EvidenceModel
    database_used: EvidenceModel
    authentication_system: EvidenceModel
    architecture_pattern: EvidenceModel
    
    # Lists of complex objects or simple strings with evidence
    algorithms_detected: List[EvidenceModel] = []
    external_apis_used: List[EvidenceModel] = []
    key_modules: List[EvidenceModel] = []
    core_features: List[EvidenceModel] = []
    
    # Viva Intelligence
    possible_viva_topics: List[str] = []
    cross_question_targets: List[str] = []
    possible_failure_points: List[str] = []
    optimization_opportunities: List[str] = []
    scalability_concerns: List[str] = []
    security_concerns: List[str] = []
    
    project_graph: ProjectGraph = Field(default_factory=ProjectGraph)
    raw_summary: Optional[str] = None
