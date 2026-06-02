"""
ORACLE Intelligence Artifacts — Stage 4 Handoff Model

Structured, deterministic intelligence handoff from ORACLE analysis to MAIN Agent.
All artifacts are evidence-grounded, explainable, and audit-safe.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class IntelligenceCategory(str, Enum):
    """Categorizes the type of intelligence artifact."""
    ARCHITECTURE = "ARCHITECTURE"
    RUNTIME_FLOW = "RUNTIME_FLOW"
    SECURITY = "SECURITY"
    SCALABILITY = "SCALABILITY"
    FAILURE_PATH = "FAILURE_PATH"
    OBSERVABLE_SIGNAL = "OBSERVABLE_SIGNAL"
    IMPLEMENTATION_RISK = "IMPLEMENTATION_RISK"
    WEAK_POINT = "WEAK_POINT"


class RuntimeDependency(BaseModel):
    """Tracks runtime dependencies critical to understanding implementation."""
    name: str
    type: str  # "LIBRARY", "SERVICE", "MIDDLEWARE", "DATABASE", "CACHE"
    usage_pattern: str
    criticality: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    evidence_file: Optional[str] = None
    evidence_snippet: Optional[str] = None


class FailureScenario(BaseModel):
    """Describes a specific failure scenario and its propagation."""
    scenario_name: str
    trigger: str  # What causes this failure
    propagation_path: List[str]  # How failure propagates through system
    impact: str  # What breaks as a result
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    detectability: str  # "EASY", "MODERATE", "HARD"
    evidence_file: Optional[str] = None
    related_nodes: List[str] = Field(default_factory=list)


class ExecutionNode(BaseModel):
    """A single node in the execution graph."""
    node_id: str
    label: str
    node_type: str  # "REQUEST_HANDLER", "MIDDLEWARE", "DB_QUERY", "SERVICE_CALL", "CACHE", "AUTH", "ERROR_HANDLER"
    implementation_details: str  # Brief description of what happens here
    dependencies: List[str] = Field(default_factory=list)  # Other nodes this depends on
    failure_modes: List[str] = Field(default_factory=list)  # How this can fail


class ExecutionPath(BaseModel):
    """A traced execution path through the system."""
    path_id: str
    description: str
    nodes: List[str]  # Order of ExecutionNode IDs
    scenario: str  # "HAPPY_PATH", "ERROR_PATH", "EDGE_CASE"
    criticality: str  # "LOW", "MEDIUM", "HIGH"
    evidence_file: Optional[str] = None


class ImplementationSignal(BaseModel):
    """Observable evidence of implementation decisions."""
    signal_type: str  # "DESIGN_PATTERN", "ERROR_HANDLING", "CACHING_STRATEGY", "ASYNC_HANDLING", "STATE_MANAGEMENT"
    description: str
    evidence: str  # Actual code or evidence
    confidence: float  # 0.0 - 1.0
    risk_level: str  # "LOW", "MEDIUM", "HIGH"
    related_risk: Optional[str] = None


class WeakPoint(BaseModel):
    """Areas where implementation is fragile or shows poor understanding."""
    area: str  # What part of the system
    weakness: str  # Specific weakness
    why_problematic: str  # Why this is concerning for a viva
    testing_approach: str  # How to probe this in viva
    evidence_file: Optional[str] = None


class VivaTarget(BaseModel):
    """Focused viva target with grounding and evidence."""
    target_id: str
    question: str
    category: IntelligenceCategory
    difficulty: str  # "FOUNDATIONAL", "MEDIUM", "HARD"
    depth_score: float  # 0-10, how deep understanding is required
    why_important: str  # Why ask this question
    evidence_references: List[str] = Field(default_factory=list)  # Files/lines this relates to
    follow_up_paths: List[str] = Field(default_factory=list)  # Possible follow-ups if answer is shallow
    expected_coverage: List[str] = Field(default_factory=list)  # What student should cover
    red_flags: List[str] = Field(default_factory=list)  # Concerning responses to watch for


class AdaptiveThreshold(BaseModel):
    """Thresholds for adapting viva difficulty."""
    topic: str
    weak_point_triggers: List[str] = Field(default_factory=list)  # Triggers for escalation
    strong_point_indicators: List[str] = Field(default_factory=list)  # Triggers for advancement
    contradiction_escalation: bool = True  # Escalate on contradictions


class IntelligenceArtifact(BaseModel):
    """
    Complete intelligence handoff from ORACLE to MAIN Agent.
    Stage 4 output: structured, deterministic, evidence-grounded.
    """
    # Metadata
    artifact_id: str = Field(default_factory=lambda: f"artifact_{datetime.utcnow().isoformat()}")
    session_id: str
    oracle_version: str = "v1"
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    analysis_duration_seconds: float
    
    # Project context
    project_name: str
    project_type: str
    backend_stack: Dict[str, str]  # framework, db, cache, etc.
    frontend_stack: Optional[Dict[str, str]] = None
    architecture_pattern: str  # e.g., "MVC", "Microservices", "Monolith"
    
    # Core execution intelligence
    execution_graph_nodes: List[ExecutionNode] = Field(default_factory=list)
    execution_paths: List[ExecutionPath] = Field(default_factory=list)
    runtime_dependencies: List[RuntimeDependency] = Field(default_factory=list)
    
    # Failure and risk intelligence
    failure_scenarios: List[FailureScenario] = Field(default_factory=list)
    implementation_risks: List[Dict[str, Any]] = Field(default_factory=list)
    weak_points: List[WeakPoint] = Field(default_factory=list)
    
    # Viva intelligence
    viva_targets: List[VivaTarget] = Field(default_factory=list)
    adaptive_thresholds: List[AdaptiveThreshold] = Field(default_factory=list)
    
    # Implementation signals (observable evidence)
    implementation_signals: List[ImplementationSignal] = Field(default_factory=list)
    
    # Explainability
    summary: str  # Human-readable summary of analysis
    key_findings: List[str] = Field(default_factory=list)
    analysis_confidence: float  # Overall confidence 0.0-1.0
    limitations: List[str] = Field(default_factory=list)  # What wasn't analyzed
    
    # Session binding
    serialization_version: str = "1.0"
    deterministic_hash: Optional[str] = None  # For replay verification


class IntelligenceHandoffEvent(BaseModel):
    """Event emitted when ORACLE completes and hands off to MAIN."""
    event_type: str = "ORACLE_INTELLIGENCE_READY"
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    artifact_id: str
    artifact_summary: Dict[str, Any]  # Quick stats: num_targets, num_risks, etc.
    next_action: str = "MAIN_AGENT_START_VIVA"  # Always this at end of Stage 4


class VivaSessionState(BaseModel):
    """Tracks state of a viva session in Stage 5."""
    session_id: str
    viva_phase: str  # "STARTED", "INTRODUCTORY", "CORE", "DEEP_DIVE", "CONTRADICTION_PROBE", "CLOSING"
    current_topic: Optional[str] = None
    current_target_id: Optional[str] = None
    questions_asked: int = 0
    contradictions_found: int = 0
    weak_areas_detected: List[str] = Field(default_factory=list)
    strong_areas_detected: List[str] = Field(default_factory=list)
    adaptive_difficulty: float = 5.0  # 0-10, increases/decreases based on performance
    
    # Transcript references
    transcript_segment_ids: List[str] = Field(default_factory=list)
    last_question_id: Optional[str] = None
    last_response_text: Optional[str] = None
    evaluation_score: Optional[float] = None


class VoiceSessionConfig(BaseModel):
    """Configuration for voice viva in Stage 6."""
    enabled: bool = True
    tts_provider: str = "system"  # "system", "deepgram", "google"
    stt_provider: str = "deepgram"  # "deepgram", "google", "azure"
    voice_language: str = "en-US"
    speech_rate: float = 1.0
    silence_timeout_ms: int = 3000
    max_response_duration_seconds: int = 120
    enable_transcript_normalization: bool = True
    save_audio_recordings: bool = True
    audio_storage_path: Optional[str] = None
