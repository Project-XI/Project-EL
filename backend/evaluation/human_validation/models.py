"""
Human Comparative Evaluation Models

Structured data models for comparing ORACLE outputs against human expertise.
All metrics are evidence-backed with no speculative scoring.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal, Any
from enum import Enum
from datetime import datetime
import json


class EvaluatorRole(str, Enum):
    """Evaluator expertise levels - grounded in real credentials."""
    SENIOR_BACKEND_ENGINEER = "senior_backend_engineer"  # 7+ years, system design
    BACKEND_ENGINEER = "backend_engineer"  # 3-7 years, solid fundamentals
    JUNIOR_ENGINEER = "junior_engineer"  # <3 years, basic competency
    SYSTEMS_ARCHITECT = "systems_architect"  # Specializes in design/trade-offs
    PROFESSOR = "professor"  # Academic teaching systems/architecture
    OPEN_SOURCE_MAINTAINER = "open_source_maintainer"  # Real-world project experience
    CODE_REVIEWER = "code_reviewer"  # PR/design review expertise
    QA_ENGINEER = "qa_engineer"  # Testing/failure scenario expertise


class SignalRelevanceScore(str, Enum):
    """Signal relevance grading - based on whether it helps engineers understand implementation."""
    NOT_RELEVANT = "not_relevant"  # Doesn't help understand implementation
    TANGENTIAL = "tangential"  # Mentioned but not core
    RELEVANT = "relevant"  # Helps understand key behavior
    CRITICAL = "critical"  # Essential to understanding implementation


class FailureRealism(str, Enum):
    """Failure scenario realism - grounded in whether scenario actually affects runtime."""
    HYPOTHETICAL = "hypothetical"  # Theoretically possible but contrived
    RARE = "rare"  # Possible but unlikely to occur in practice
    REALISTIC = "realistic"  # Actually happens in production systems
    COMMON = "common"  # Frequently observed failure mode


class VivaQuestionRealism(str, Enum):
    """Viva question realism - grounded in what real interviews actually test."""
    GENERIC_TEXTBOOK = "generic_textbook"  # Could apply to any framework
    SPECULATIVE = "speculative"  # Requires hypothetical scenario
    CODEBASE_GROUNDED = "codebase_grounded"  # Specific to this implementation
    INTERVIEW_REALISTIC = "interview_realistic"  # Resembles actual engineering interviews


@dataclass
class SignalComparison:
    """Comparison of ORACLE signal against human evaluation."""
    signal_name: str
    oracle_detected: bool
    oracle_confidence: float
    
    # Human evaluator assessment
    evaluator_role: EvaluatorRole
    human_considers_relevant: bool
    relevance_score: SignalRelevanceScore
    reasoning: str
    code_evidence_cited: Optional[str] = None
    
    # Agreement metrics
    agreement: bool = field(init=False)
    agreement_confidence: float = field(init=False)
    
    # Metadata
    evaluated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Calculate agreement metrics."""
        # Agreement: ORACLE detected AND human found relevant (not just not-relevant)
        self.agreement = (
            self.oracle_detected == self.human_considers_relevant and
            self.relevance_score != SignalRelevanceScore.NOT_RELEVANT
        )
        
        # Confidence: agreement_confidence = oracle_confidence if oracle agrees with human
        if self.agreement:
            self.agreement_confidence = self.oracle_confidence
        else:
            # Disagreement confidence = 1 - oracle_confidence (ORACLE was wrong)
            self.agreement_confidence = 1.0 - self.oracle_confidence


@dataclass
class FailureComparison:
    """Comparison of ORACLE failure scenario against human evaluation."""
    failure_name: str
    oracle_detected: bool
    oracle_severity: float  # 0.0-1.0
    oracle_propagation_confidence: float
    
    # Human evaluator assessment
    evaluator_role: EvaluatorRole
    human_considers_realistic: bool
    realism_score: FailureRealism
    production_likelihood: float  # 0.0-1.0 from evaluator's perspective
    reasoning: str
    
    # Propagation path assessment
    propagation_path_exists: bool  # Human verified path through code
    code_evidence_cited: Optional[str] = None
    
    # Agreement metrics
    agreement: bool = field(init=False)
    realism_agreement: bool = field(init=False)
    severity_delta: float = field(init=False)
    
    # Metadata
    evaluated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Calculate agreement metrics."""
        # Agreement: both detect AND both consider realistic
        self.agreement = (
            self.oracle_detected == self.human_considers_realistic and
            self.human_considers_realistic
        )
        
        # Realism agreement: scenario realism matches production likelihood
        self.realism_agreement = (
            self.realism_score in [FailureRealism.REALISTIC, FailureRealism.COMMON] and
            self.production_likelihood >= 0.7
        )
        
        # Severity delta: difference between ORACLE and human assessments
        # Positive = ORACLE overestimated, Negative = ORACLE underestimated
        self.severity_delta = self.oracle_severity - self.production_likelihood


@dataclass
class VivaComparison:
    """Comparison of ORACLE viva question against human evaluation."""
    question_text: str
    oracle_generated: bool
    oracle_specificity_score: float  # 0.0-1.0
    
    # Human evaluator assessment
    evaluator_role: EvaluatorRole
    human_accepts_question: bool  # Would this appear in real interviews?
    realism_score: VivaQuestionRealism
    grounding_code_locations: List[str]  # Code files/lines this tests
    reasoning: str
    
    # Interview simulation results (optional)
    tested_against_weak_answers: bool = False
    weak_answer_detection_rate: Optional[float] = None  # % of weak answers caught
    
    # Agreement metrics
    agreement: bool = field(init=False)
    realism_match: bool = field(init=False)
    
    # Metadata
    evaluated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Calculate agreement metrics."""
        # Agreement: ORACLE generated AND human accepts as realistic
        self.agreement = (
            self.oracle_generated == self.human_accepts_question and
            self.human_accepts_question
        )
        
        # Realism match: question scored as realistic/grounded, not textbook/speculative
        self.realism_match = self.realism_score in [
            VivaQuestionRealism.CODEBASE_GROUNDED,
            VivaQuestionRealism.INTERVIEW_REALISTIC
        ]


@dataclass
class ArchitecturalAssessment:
    """Architectural credibility assessment from human reviewer."""
    oracle_architectural_analysis: str  # ORACLE's architectural summary
    oracle_confidence_in_analysis: float  # 0.0-1.0
    
    evaluator_role: EvaluatorRole
    human_assessment: str  # Human's architectural summary
    human_agrees_with_oracle: bool
    areas_of_disagreement: List[str] = field(default_factory=list)
    areas_oracle_missed: List[str] = field(default_factory=list)
    missing_architectural_concerns: List[str] = field(default_factory=list)
    
    reasoning: str = ""
    code_evidence: Optional[str] = None
    
    # Credibility score: 0.0-1.0, based on accuracy
    credibility_score: float = field(init=False)
    
    evaluated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Calculate credibility."""
        # Credibility = (areas oracle got right) - (areas oracle missed) - (disagreements)
        # All normalized
        self.credibility_score = max(
            0.0,
            self.oracle_confidence_in_analysis *
            (1.0 - (len(self.areas_of_disagreement) * 0.2)) *
            (1.0 - (len(self.areas_oracle_missed) * 0.15))
        )


@dataclass
class ExecutionBehaviorComparison:
    """Compare ORACLE's execution behavior reasoning to human assessment."""
    analyzed_scenario: str  # e.g., "Database connection loss during request"
    oracle_execution_trace: List[str]  # Steps ORACLE identified
    oracle_confidence: float
    
    evaluator_role: EvaluatorRole
    human_execution_trace: List[str]  # Steps human would trace
    human_execution_accurate: bool  # Does ORACLE match human understanding?
    missing_steps: List[str] = field(default_factory=list)
    incorrectly_inferred_steps: List[str] = field(default_factory=list)
    
    reasoning: str = ""
    code_evidence: Optional[str] = None
    
    # Accuracy metrics
    step_accuracy: float = field(init=False)  # % of steps human agrees with
    
    evaluated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Calculate accuracy metrics."""
        if len(self.human_execution_trace) == 0:
            self.step_accuracy = 0.0
        else:
            # Step accuracy: how many steps overlap
            matching_steps = len(set(self.oracle_execution_trace) & set(self.human_execution_trace))
            self.step_accuracy = matching_steps / len(self.human_execution_trace)


@dataclass
class HumanEvaluationSession:
    """Complete human evaluation session for a single repository."""
    repository_name: str
    evaluator_role: EvaluatorRole
    oracle_context_id: str  # Reference to ORACLE analysis
    
    # Signal comparisons
    signal_comparisons: List[SignalComparison] = field(default_factory=list)
    
    # Failure comparisons
    failure_comparisons: List[FailureComparison] = field(default_factory=list)
    
    # Viva comparisons
    viva_comparisons: List[VivaComparison] = field(default_factory=list)
    
    # Architectural assessment
    architectural_assessment: Optional[ArchitecturalAssessment] = None
    
    # Execution behavior comparisons
    execution_comparisons: List[ExecutionBehaviorComparison] = field(default_factory=list)
    
    # Overall assessment
    oracle_usefulness: float = 0.0  # 0.0-1.0, subjective utility
    oracle_trustworthiness: float = 0.0  # 0.0-1.0, confidence in findings
    overall_reasoning: str = ""
    
    # Metadata
    evaluated_at: datetime = field(default_factory=datetime.utcnow)
    duration_minutes: Optional[float] = None  # How long evaluation took
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "repository_name": self.repository_name,
            "evaluator_role": self.evaluator_role.value,
            "oracle_context_id": self.oracle_context_id,
            "signal_comparisons": [
                {
                    "signal_name": sc.signal_name,
                    "oracle_detected": sc.oracle_detected,
                    "oracle_confidence": sc.oracle_confidence,
                    "human_considers_relevant": sc.human_considers_relevant,
                    "relevance_score": sc.relevance_score.value,
                    "agreement": sc.agreement,
                    "reasoning": sc.reasoning,
                }
                for sc in self.signal_comparisons
            ],
            "failure_comparisons": [
                {
                    "failure_name": fc.failure_name,
                    "oracle_detected": fc.oracle_detected,
                    "oracle_severity": fc.oracle_severity,
                    "human_considers_realistic": fc.human_considers_realistic,
                    "realism_score": fc.realism_score.value,
                    "agreement": fc.agreement,
                    "severity_delta": fc.severity_delta,
                    "reasoning": fc.reasoning,
                }
                for fc in self.failure_comparisons
            ],
            "viva_comparisons": [
                {
                    "question_text": vc.question_text[:100],  # Truncate for readability
                    "oracle_generated": vc.oracle_generated,
                    "human_accepts_question": vc.human_accepts_question,
                    "realism_score": vc.realism_score.value,
                    "agreement": vc.agreement,
                    "reasoning": vc.reasoning,
                }
                for vc in self.viva_comparisons
            ],
            "architectural_assessment": (
                {
                    "human_agrees": self.architectural_assessment.human_agrees_with_oracle,
                    "areas_disagreement": self.architectural_assessment.areas_of_disagreement,
                    "credibility": self.architectural_assessment.credibility_score,
                }
                if self.architectural_assessment
                else None
            ),
            "oracle_usefulness": self.oracle_usefulness,
            "oracle_trustworthiness": self.oracle_trustworthiness,
            "evaluated_at": self.evaluated_at.isoformat(),
            "notes": self.notes,
        }


@dataclass
class ComparativeValidationReport:
    """Aggregated report comparing ORACLE across multiple human evaluations."""
    repository_name: str
    total_evaluations: int
    
    # Signal metrics
    signal_agreement_rate: float  # % of signals where ORACLE and humans agree
    signal_false_positive_rate: float  # % ORACLE detected but humans didn't find relevant
    signal_false_negative_rate: float  # % humans found relevant but ORACLE missed
    signal_avg_relevance: float  # Average relevance score across all signals
    
    # Failure metrics
    failure_agreement_rate: float
    failure_false_positive_rate: float  # Hallucinated or unrealistic scenarios
    failure_realism_match_rate: float  # % where ORACLE severity matches human assessment
    failure_avg_severity_delta: float  # Average over/underestimation
    
    # Viva metrics
    viva_acceptance_rate: float  # % of questions humans would use in interviews
    viva_realism_rate: float  # % grounded in codebase vs generic/speculative
    viva_grounding_rate: float  # % with code evidence
    
    # Architectural metrics
    architectural_credibility: Optional[float] = None  # Average from assessments
    architectural_agreement_rate: Optional[float] = None
    
    # Execution behavior metrics
    execution_step_accuracy: Optional[float] = None
    
    # Overall trustworthiness
    oracle_overall_usefulness: float = 0.0  # Average across evaluators
    oracle_overall_trustworthiness: float = 0.0
    
    # Issues detected
    hallucination_clusters: List[str] = field(default_factory=list)  # Common false positives
    weak_reasoning_areas: List[str] = field(default_factory=list)  # Where ORACLE struggles
    missing_analysis_areas: List[str] = field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    
    generated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(
            {
                "repository_name": self.repository_name,
                "total_evaluations": self.total_evaluations,
                "signal_agreement_rate": self.signal_agreement_rate,
                "signal_false_positive_rate": self.signal_false_positive_rate,
                "signal_false_negative_rate": self.signal_false_negative_rate,
                "failure_agreement_rate": self.failure_agreement_rate,
                "viva_acceptance_rate": self.viva_acceptance_rate,
                "viva_realism_rate": self.viva_realism_rate,
                "oracle_overall_usefulness": self.oracle_overall_usefulness,
                "oracle_overall_trustworthiness": self.oracle_overall_trustworthiness,
                "hallucination_clusters": self.hallucination_clusters,
                "weak_reasoning_areas": self.weak_reasoning_areas,
                "recommendations": self.recommendations,
                "generated_at": self.generated_at.isoformat(),
            },
            indent=2,
        )
