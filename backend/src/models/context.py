from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum

class ProjectNode(BaseModel):
    id: str
    label: str
    type: str
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

class InconsistencyFlag(BaseModel):
    issue: str
    severity: str
    confidence: float
    evidence: List[str]

class EvidenceModel(BaseModel):
    value: Any
    confidence: float
    evidence: List[str] = []

class FlowNodeType(str, Enum):
    ROUTE = "ROUTE"
    API_CALL = "API_CALL"
    MIDDLEWARE = "MIDDLEWARE"
    AUTH_HANDLER = "AUTH_HANDLER"
    DB_QUERY = "DB_QUERY"
    SERVICE_LAYER = "SERVICE_LAYER"
    STATE_STORE = "STATE_STORE"
    MODEL_INFERENCE = "MODEL_INFERENCE"
    EXCEPTION_HANDLER = "EXCEPTION_HANDLER"

class FlowNode(BaseModel):
    id: str
    label: str
    type: FlowNodeType
    metadata: Dict[str, Any] = {}

class FlowEdge(BaseModel):
    source: str
    target: str
    relationship: str
    confidence: float
    evidence: List[str] = []

class ExecutionGraph(BaseModel):
    nodes: List[FlowNode] = []
    edges: List[FlowEdge] = []
    middleware: List[str] = []
    db_calls: List[str] = []
    auth_points: List[str] = []
    risk_flags: List[str] = []
    failure_paths: List[str] = []

class ImplementationFlow(BaseModel):
    steps: List[str]
    confidence: float
    flow_confidence: Dict[str, float]
    evidence: List[str]

class RuntimeRisk(BaseModel):
    value: str
    severity: str # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    confidence: float
    evidence: List[str]

class VivaTarget(BaseModel):
    topic: str
    question_target: str
    difficulty: str # "easy", "medium", "hard"
    importance_score: float
    focus: str
    # Extended intelligence fields
    category: str = "Architecture"  # Architecture, Tradeoff, Security, Scalability, Failure-Path, Runtime
    depth_score: float = 5.0       # 0-10 engineering depth
    related_node: str = ""         # graph node this question targets
    confidence: float = 0.8        # engine confidence in question relevance
    reasoning_summary: str = ""    # brief explanation of why this was generated

class StructuredContext(BaseModel):
    project_name: EvidenceModel
    project_type: EvidenceModel
    frontend_framework: EvidenceModel
    backend_framework: EvidenceModel
    database_used: EvidenceModel
    authentication_system: EvidenceModel
    architecture_pattern: EvidenceModel
    
    # Implementation Intelligence
    execution_graph: ExecutionGraph = Field(default_factory=ExecutionGraph)
    implementation_flows: Dict[str, ImplementationFlow] = {}
    authentication_flow: Optional[ImplementationFlow] = None
    api_lifecycle: Optional[ImplementationFlow] = None
    database_interaction_flow: Optional[ImplementationFlow] = None
    middleware_chain: List[EvidenceModel] = []
    security_flows: List[EvidenceModel] = []
    failure_paths: List[EvidenceModel] = []
    runtime_risks: List[RuntimeRisk] = []
    
    # Reasoning & Analysis
    implementation_reasoning: List[ImplementationReasoning] = []
    tradeoff_analysis: List[EvidenceModel] = []
    
    # Viva Intelligence
    implementation_viva_targets: List[VivaTarget] = []
    viva_intelligence_targets: List[VivaTarget] = [] # Legacy support
    
    # Meta
    inconsistencies: List[InconsistencyFlag] = []
    complexity_mismatch: Optional[EvidenceModel] = None
    raw_summary: Optional[str] = None
