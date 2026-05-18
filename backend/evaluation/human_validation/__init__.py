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
]
