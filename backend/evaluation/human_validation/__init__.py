"""
Human Comparative Validation Framework

Structured evaluation of ORACLE outputs against expert human judgment.
All metrics are evidence-backed with explicit reasoning and code citations.
"""

from .models import (
    EvaluatorRole,
    SignalRelevanceScore,
    FailureRealism,
    VivaQuestionRealism,
    SignalComparison,
    FailureComparison,
    VivaComparison,
    ArchitecturalAssessment,
    ExecutionBehaviorComparison,
    HumanEvaluationSession,
    ComparativeValidationReport,
)

from .evaluator import HumanComparativeEvaluator
from .datasets import HumanDatasetSourceManifest, HumanReviewDatasetStore, DEFAULT_DATASET_MANIFESTS, bundle_datasets
from .trust_audit import TrustAuditPipeline, TrustAuditReport, TrustAuditFinding, TrustAuditSeverity
from .comparative_calibration_runner import ComparativeCalibrationRunner
from .engineering_review_corpus import (
    EngineeredReviewEntry,
    EngineeringReviewCategory,
    ReviewerType,
    ENGINEERING_REVIEW_CORPUS,
    ALL_ENGINEERING_REVIEWS,
    get_reviews_by_category,
    get_reviews_by_implementation_area,
    get_reviews_by_resulted_in_issue,
    get_reviews_by_reviewer_seniority,
)
from .comparative_reasoning_evaluator import (
    ReasoningAlignment,
    ReasoningComparisonResult,
    ComparativeReasoningReport,
    ComparativeReasoningEvaluator,
)
from .failure_corpus import (
    FailureCorpusCategory,
    FailureCorpusRepository,
    FAILURE_CORPUS,
    get_corpus_by_category,
    get_corpus_by_severity,
    get_corpus_by_framework,
)
from .viva_session_conductor import (
    VivaQuestionType,
    CandidateResponseQuality,
    VivaQuestion,
    CandidateResponse,
    VivaSession,
    VivaSessionConductor,
)
from .reasoning_depth_analyzer import (
    ReasoningDepth,
    UnderstandingIndicator,
    MemorizationIndicator,
    ReasoningDepthAssessment,
    CandidateProfile,
    ReasoningDepthAnalyzer,
)

__all__ = [
    "EvaluatorRole",
    "SignalRelevanceScore",
    "FailureRealism",
    "VivaQuestionRealism",
    "SignalComparison",
    "FailureComparison",
    "VivaComparison",
    "ArchitecturalAssessment",
    "ExecutionBehaviorComparison",
    "HumanEvaluationSession",
    "ComparativeValidationReport",
    "HumanComparativeEvaluator",
    "HumanDatasetSourceManifest",
    "HumanReviewDatasetStore",
    "DEFAULT_DATASET_MANIFESTS",
    "bundle_datasets",
    "TrustAuditPipeline",
    "TrustAuditReport",
    "TrustAuditFinding",
    "TrustAuditSeverity",
    "ComparativeCalibrationRunner",
    "EngineeredReviewEntry",
    "EngineeringReviewCategory",
    "ReviewerType",
    "ENGINEERING_REVIEW_CORPUS",
    "ALL_ENGINEERING_REVIEWS",
    "get_reviews_by_category",
    "get_reviews_by_implementation_area",
    "get_reviews_by_resulted_in_issue",
    "get_reviews_by_reviewer_seniority",
    "ReasoningAlignment",
    "ReasoningComparisonResult",
    "ComparativeReasoningReport",
    "ComparativeReasoningEvaluator",
    "FailureCorpusCategory",
    "FailureCorpusRepository",
    "FAILURE_CORPUS",
    "get_corpus_by_category",
    "get_corpus_by_severity",
    "get_corpus_by_framework",
    "VivaQuestionType",
    "CandidateResponseQuality",
    "VivaQuestion",
    "CandidateResponse",
    "VivaSession",
    "VivaSessionConductor",
    "ReasoningDepth",
    "UnderstandingIndicator",
    "MemorizationIndicator",
    "ReasoningDepthAssessment",
    "CandidateProfile",
    "ReasoningDepthAnalyzer",
]
