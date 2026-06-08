from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class EventType(str, Enum):
    SESSION_CREATED = "session_created"
    SESSION_CONFIGURED = "session_configured"
    SESSION_READY = "session_ready"
    SESSION_LIVE = "session_live"
    SESSION_ACTIVE_VIVA = "session_active_viva"
    SESSION_ARCHIVED = "session_archived"
    STUDENT_ADMITTED = "student_admitted"
    STUDENT_REJECTED = "student_rejected"
    ORACLE_ANALYSIS_STARTED = "oracle_analysis_started"
    ORACLE_ANALYSIS_COMPLETED = "oracle_analysis_completed"
    SESSION_STARTED = "session_started"
    SESSION_COMPLETED = "session_completed"
    IDENTITY_VERIFIED = "identity_verified"
    CONTEXT_GENERATED = "context_generated"
    QUESTION_POSED = "question_posed"
    ANSWER_RECEIVED = "answer_received"
    BEHAVIOUR_FLAGGED = "behaviour_flagged"
    SYSTEM_ERROR = "system_error"
    
    # Face Detection Events
    FACE_EMBEDDING_COMPARED = "face_embedding.compared"
    IDENTITY_CONFLICT_DETECTED = "identity_conflict.detected"
    CONFLICT_ALERT_CREATED = "conflict_alert.created"
    MANUAL_REVIEW_REQUIRED = "manual_review.required"
    ACCESS_DENIED_CONFLICT = "access.denied_conflict"
    
    # Admin Review Events
    ADMIN_REVIEW_STARTED = "admin_review.started"
    ADMIN_REVIEW_APPROVED = "admin_review.approved"
    ADMIN_REVIEW_REJECTED = "admin_review.rejected"
    ADMIN_OVERRIDE_ACTION = "admin_override.action"
    
    # ORACLE Events
    FILE_RECEIVED = "file_received"
    PDF_PARSED = "pdf_parsed"
    DOCX_PARSED = "docx_parsed"
    REPO_CLONED = "repo_cloned"
    STRUCTURE_ANALYZED = "structure_analyzed"
    TECH_STACK_DETECTED = "tech_stack_detected"
    PROJECT_GRAPH_BUILT = "project_graph.built"
    CONTEXT_SYNTHESIZED = "context_synthesized"
    CONTEXT_READY = "context.ready"
    AGENT_PROGRESS = "agent.progress"
    
    # Implementation Intelligence Events
    IMPLEMENTATION_FLOW_DETECTED = "implementation_flow.detected"
    AUTH_FLOW_INFERRED = "auth_flow.inferred"
    API_LIFECYCLE_MAPPED = "api_lifecycle_mapped"
    MIDDLEWARE_CHAIN_ANALYZED = "middleware_chain.analyzed"
    DB_INTERACTION_DETECTED = "db_interaction_detected"
    SECURITY_RISK_FLAGGED = "security_risk.flagged"
    FAILURE_PATH_DETECTED = "failure_path.detected"
    DEAD_PATH_DETECTED = "dead_path.detected"
    EXCEPTION_FLOW_ANALYZED = "exception_flow.analyzed"
    
    # Stage 4: ORACLE Intelligence Handoff
    ORACLE_INTELLIGENCE_READY = "oracle_intelligence_ready"
    
    # Stage 5: MAIN Agent Viva Events
    VIVA_SESSION_STARTED = "viva_session_started"
    VIVA_QUESTION_ASKED = "viva_question_asked"
    VIVA_RESPONSE_RECEIVED = "viva_response_received"
    VIVA_EVALUATION_COMPLETE = "viva_evaluation_complete"
    VIVA_FOLLOW_UP_GENERATED = "viva_follow_up_generated"
    VIVA_CONTRADICTION_DETECTED = "viva_contradiction_detected"
    VIVA_TOPIC_ESCALATED = "viva_topic_escalated"
    VIVA_SESSION_COMPLETED = "viva_session_completed"
    
    # Stage 6: Voice Infrastructure Events
    VOICE_SESSION_STARTED = "voice_session_started"
    VOICE_QUESTION_PLAYED = "voice_question_played"
    VOICE_LISTENING_STARTED = "voice_listening_started"
    VOICE_LISTENING_STOPPED = "voice_listening_stopped"
    VOICE_TRANSCRIPTION_RECEIVED = "voice_transcription_received"
    VOICE_TRANSCRIPTION_NORMALIZED = "voice_transcription_normalized"
    VOICE_SESSION_ENDED = "voice_session_ended"

    # Stage 7: SENTINEL Parallel Oversight Events
    INTEGRITY_ALERT_GENERATED = "integrity_alert_generated"
    PROLONGED_OFFSCREEN_FOCUS = "prolonged_offscreen_focus"
    REPEATED_GAZE_SHIFT = "repeated_gaze_shift"
    SESSION_INTERRUPTION = "session_interruption"
    SUSPICIOUS_AUDIO_PATTERN = "suspicious_audio_pattern"
    LOW_VISIBILITY_WARNING = "low_visibility_warning"
    MANUAL_REVIEW_RECOMMENDED = "manual_review_recommended"

    # Stage 8: MAIN Agent Evaluation Loop Events
    IMPLEMENTATION_FAMILIARITY_UPDATED = "implementation_familiarity_updated"
    CONTRADICTION_CHAIN_UPDATED = "contradiction_chain_updated"
    FOLLOW_UP_ESCALATION = "follow_up_escalation"

    # Stage 9: Curriculum Progression Events
    CURRICULUM_TRANSITION_STARTED = "curriculum_transition_started"
    CURRICULUM_TOPIC_COMPLETED = "curriculum_topic_completed"

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
