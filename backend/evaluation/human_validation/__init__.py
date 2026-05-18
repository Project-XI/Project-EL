"""
ORACLE Implementation Familiarity Assessment Framework

Stable, evidence-grounded system for evaluating implementation familiarity through
technical viva sessions. All analysis is explainable and bias-audited.

Core Modules:
- viva_session_conductor: Orchestrate viva sessions, score responses
- reasoning_depth_analyzer: Analyze reasoning patterns and implementation familiarity
- fairness_audit: Detect bias and false positives
- trust_audit: Verify evidence grounding and detect overconfidence
- engineering_review_corpus: Real engineering review data (grounding source)
- failure_corpus: Failure pattern scenarios (probing targets)

Note: This package prioritizes stability and clarity. Exports are limited to
core symbols needed for end-to-end assessment.
"""

# ============================================================================
# CORE VIVA SESSION ORCHESTRATION
# ============================================================================
from .viva_session_conductor import (
    VivaQuestionType,
    CandidateResponseQuality,
    VivaQuestion,
    CandidateResponse,
    VivaSession,
    VivaSessionConductor,
)

# ============================================================================
# IMPLEMENTATION FAMILIARITY ANALYSIS
# ============================================================================
from .reasoning_depth_analyzer import (
    ReasoningDepth,
    UnderstandingIndicator,
    MemorizationIndicator,
    ReasoningDepthAssessment,
    CandidateProfile,
    ReasoningDepthAnalyzer,
)

# ============================================================================
# TRUSTWORTHINESS & FAIRNESS AUDITING
# ============================================================================
from .trust_audit import (
    TrustAuditPipeline,
    TrustAuditReport,
    TrustAuditFinding,
    TrustAuditSeverity,
)

from .fairness_audit import (
    FairnessAuditReport,
    FairnessAuditIssue,
    FairnessAuditSeverity,
    FairnessAuditor,
)

# ============================================================================
# GROUNDING DATA (Engineering Context)
# ============================================================================
from .engineering_review_corpus import (
    EngineeredReviewEntry,
    EngineeringReviewCategory,
    ReviewerType,
    ALL_ENGINEERING_REVIEWS,
    get_reviews_by_category,
)

from .failure_corpus import (
    FailureCorpusCategory,
    FailureCorpusRepository,
    FAILURE_CORPUS,
    get_corpus_by_category,
)

# ============================================================================
# COMPARATIVE VALIDATION (Testing & Benchmarking)
# ============================================================================
from .comparative_reasoning_evaluator import (
    ReasoningAlignment,
    ReasoningComparisonResult,
    ComparativeReasoningReport,
    ComparativeReasoningEvaluator,
)

from .comparative_calibration_runner import ComparativeCalibrationRunner

# ============================================================================
# INFRASTRUCTURE (Data & CLI)
# ============================================================================
from .datasets import bundle_datasets

# ============================================================================
# PUBLIC API
# ============================================================================

__all__ = [
    # Viva Session (6 symbols)
    "VivaQuestionType",
    "CandidateResponseQuality",
    "VivaQuestion",
    "CandidateResponse",
    "VivaSession",
    "VivaSessionConductor",
    
    # Implementation Familiarity Analysis (6 symbols)
    "ReasoningDepth",
    "UnderstandingIndicator",
    "MemorizationIndicator",
    "ReasoningDepthAssessment",
    "CandidateProfile",
    "ReasoningDepthAnalyzer",
    
    # Trust & Fairness (8 symbols)
    "TrustAuditPipeline",
    "TrustAuditReport",
    "TrustAuditFinding",
    "TrustAuditSeverity",
    "FairnessAuditReport",
    "FairnessAuditIssue",
    "FairnessAuditSeverity",
    "FairnessAuditor",
    
    # Engineering Context (8 symbols)
    "EngineeredReviewEntry",
    "EngineeringReviewCategory",
    "ReviewerType",
    "ALL_ENGINEERING_REVIEWS",
    "get_reviews_by_category",
    "FailureCorpusCategory",
    "FailureCorpusRepository",
    "FAILURE_CORPUS",
    "get_corpus_by_category",
    
    # Comparative Validation (4 symbols)
    "ReasoningAlignment",
    "ReasoningComparisonResult",
    "ComparativeReasoningReport",
    "ComparativeReasoningEvaluator",
    
    # CLI & Infrastructure (2 symbols)
    "ComparativeCalibrationRunner",
    "bundle_datasets",
]
