"""Human Evaluator Models & Datasets for ORACLE Comparative Validation

This module defines structured data models for capturing human engineering evaluations
and comparing them against ORACLE-generated intelligence.

Key Concepts:
- All data comes from real human reviews (real PRs, real interviews, real architecture discussions)
- No synthetic or generated human feedback
- Metrics are evidence-based comparisons, not scores
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class ReviewerRole(str, Enum):
    """Possible roles of human reviewers"""
    SENIOR_BACKEND_ENGINEER = "senior_backend_engineer"
    PROFESSOR_COMPUTER_SCIENCE = "professor_cs"
    OPEN_SOURCE_MAINTAINER = "maintainer"
    TECH_LEAD = "tech_lead"
    PLATFORM_ENGINEER = "platform_engineer"


class SignalAccuracy(str, Enum):
    """How accurately ORACLE identified signals compared to human analysis"""
    HALLUCINATED = "hallucinated"  # Signal doesn't exist in code
    INCORRECT_LOCATION = "incorrect_location"  # Signal exists but wrong code location
    INCOMPLETE = "incomplete"  # Signal found but missing important context
    ACCURATE = "accurate"  # Signal correctly identified
    MISSING_IMPORTANT_DETAIL = "missing_important_detail"  # Signal found but misses nuance


class FailureScenarioAccuracy(str, Enum):
    """How accurately ORACLE identified failure scenarios"""
    SPECULATIVE = "speculative"  # Scenario unlikely to occur in practice
    INCORRECT_PROPAGATION = "incorrect_propagation"  # Path through code is wrong
    MISSING_RECOVERY = "missing_recovery"  # Doesn't account for actual recovery
    INCOMPLETE_TRIGGER = "incomplete_trigger"  # Trigger condition incomplete
    REALISTIC = "realistic"  # Matches real failure patterns
    OVERLY_PESSIMISTIC = "overly_pessimistic"  # True but extremely rare


class VivaQuestionQuality(str, Enum):
    """Quality assessment of ORACLE-generated viva questions"""
    TEXTBOOK_GENERIC = "textbook_generic"  # Generic computer science question
    MEMORIZED_RESPONSE = "memorized_response"  # Can be answered from course notes
    MISSING_CODE_CONTEXT = "missing_code_context"  # Should reference actual code
    ARCHITECTURAL_INSIGHT = "architectural_insight"  # Tests design understanding
    IMPLEMENTATION_DEEP_DIVE = "implementation_deep_dive"  # Probes actual implementation
    OPERATIONAL_REALISM = "operational_realism"  # Tests operational thinking
    TOO_SIMPLE = "too_simple"  # Doesn't probe knowledge
    TOO_VAGUE = "too_vague"  # Question is ambiguous


class HumanSignalEvaluation(BaseModel):
    """Human evaluation of an ORACLE-detected signal"""
    signal_name: str
    oracle_confidence: float
    human_verdict: SignalAccuracy
    human_comments: str
    evidence_references: List[str] = []  # Code files/lines the human referenced
    alternative_signal: Optional[str] = None  # If hallucinated, what should have been found
    realism_score: float = Field(ge=0, le=1.0)  # How realistic/important is this signal?


class HumanFailureScenarioEvaluation(BaseModel):
    """Human evaluation of an ORACLE-identified failure scenario"""
    scenario_name: str
    oracle_risk_severity: str  # What ORACLE said: low, medium, high, critical
    human_verdict: FailureScenarioAccuracy
    human_comments: str
    actual_severity: str  # What human reviewer believes is realistic
    real_world_experience: Optional[str] = None  # Have they seen this in production?
    propagation_realism: float = Field(ge=0, le=1.0)  # Does path through code make sense?
    recovery_realism: float = Field(ge=0, le=1.0)  # Is recovery strategy realistic?


class HumanVivaQuestionEvaluation(BaseModel):
    """Human evaluation of an ORACLE-generated viva question"""
    question_text: str
    oracle_difficulty: str  # easy, medium, hard
    oracle_importance_score: float
    human_verdict: List[VivaQuestionQuality]  # Multiple quality aspects
    human_comments: str
    suggested_follow_up: Optional[str] = None
    tests_implementation_understanding: bool
    tests_operational_thinking: bool
    code_specificity_score: float = Field(ge=0, le=1.0)  # How specific to this codebase?
    distinguishes_senior_engineer: bool  # Would this reveal differences between levels?


class HumanReviewDatapoint(BaseModel):
    """Single point of human evaluation data - could be from PR review, interview, etc"""
    source_type: str  # "pr_review", "code_interview", "architecture_review", "real_pr_comment"
    source_reference: str  # PR URL, interview transcript ID, etc
    reviewer_role: ReviewerRole
    repository_name: str
    timestamp: datetime
    
    # What the human actually said/evaluated
    human_observations: str
    identified_signals: List[str] = []  # What patterns human noticed
    identified_failures: List[str] = []  # What failure modes human identified
    implementation_concerns: List[str] = []
    questioned_topics: List[str] = []  # Topics they probed during interviews
    
    # Associated ORACLE outputs for comparison
    oracle_signals: Optional[List[str]] = None
    oracle_failure_scenarios: Optional[List[str]] = None
    oracle_viva_questions: Optional[List[str]] = None


class ComparativeSignalAnalysis(BaseModel):
    """Analysis comparing ORACLE signals to human evaluations"""
    signal_name: str
    oracle_detected: bool
    human_mentioned: bool
    human_evaluations: List[HumanSignalEvaluation]
    
    # Metrics
    accuracy_rate: float = 0.0  # % of humans who agreed signal was accurate
    importance_alignment: float = 0.0  # Correlation between human importance and ORACLE confidence
    false_positive: bool = False  # Is this a hallucination?
    
    consensus: Optional[str] = None  # What did humans agree on?
    oracle_was_correct: Optional[bool] = None  # Final judgment


class ComparativeFailureAnalysis(BaseModel):
    """Analysis comparing ORACLE failure scenarios to human evaluations"""
    scenario_name: str
    oracle_identified: bool
    human_identified: bool
    human_evaluations: List[HumanFailureScenarioEvaluation]
    
    # Metrics
    realism_rate: float = 0.0  # % of humans who found it realistic
    severity_alignment: float = 0.0  # How well ORACLE severity matched human judgment
    propagation_accuracy: float = 0.0  # % who agreed on path through code
    recovery_accuracy: float = 0.0  # % who agreed recovery strategy makes sense
    
    consensus: Optional[str] = None  # What did humans agree on?
    oracle_was_realistic: Optional[bool] = None


class ComparativeVivaAnalysis(BaseModel):
    """Analysis comparing ORACLE viva questions to human evaluations"""
    question_text: str
    human_evaluations: List[HumanVivaQuestionEvaluation]
    
    # Metrics
    quality_rate: float = 0.0  # % of humans who rated it as good engineering question
    code_specificity: float = 0.0  # Average specificity score
    distinguishes_levels: float = 0.0  # % who said it distinguishes senior from junior
    would_ask_in_interview: float = 0.0  # % who would use this in interview
    textbook_pattern_detected: bool = False  # Flagged as generic?
    
    consensus: Optional[str] = None
    oracle_question_good: Optional[bool] = None


class ComparativeAgreementMetrics(BaseModel):
    """Aggregate agreement metrics between ORACLE and human reviewers"""
    repository_name: str
    evaluation_date: datetime
    total_human_datapoints: int
    
    # Signal metrics
    signals_human_mentioned: int
    signals_oracle_detected: int
    signals_true_positives: int  # Both human and oracle identified
    signals_false_positives: int  # Oracle only (hallucinations)
    signals_false_negatives: int  # Human only (oracle missed)
    
    signal_precision: float = 0.0  # TP / (TP + FP)
    signal_recall: float = 0.0  # TP / (TP + FN)
    signal_agreement: float = 0.0  # F1 score or IoU
    
    # Failure scenario metrics
    scenarios_human_mentioned: int
    scenarios_oracle_identified: int
    scenarios_true_positives: int
    scenarios_false_positives: int
    scenarios_false_negatives: int
    scenarios_realism_agreement: float = 0.0  # % where severity aligned
    
    failure_precision: float = 0.0
    failure_recall: float = 0.0
    failure_agreement: float = 0.0
    
    # Viva metrics
    viva_questions_generated: int
    viva_questions_evaluated: int
    viva_quality_rate: float = 0.0  # % rated as good engineering questions
    viva_specificity: float = 0.0  # Average code-specificity score
    viva_distinguishes_levels: float = 0.0
    
    # Overall assessment
    oracle_trustworthiness: float = 0.0  # Weighted score 0-1
    ready_for_production: bool = False
    confidence_calibration_status: str = "uncalibrated"  # calibrated, needs_work, perfect
    
    # Issues found
    hallucinations_detected: List[str] = []
    speculation_detected: List[str] = []
    missing_important_signals: List[str] = []


class HumanReviewDataset(BaseModel):
    """Collection of human evaluation datapoints from various sources"""
    name: str
    description: str
    created_date: datetime
    
    # Source metadata
    source_repositories: List[str]  # Which repos data came from
    reviewer_roles: List[ReviewerRole]  # Which types of reviewers
    source_types: List[str]  # "pr_review", "interview", "architecture_review", etc
    
    # Data
    datapoints: List[HumanReviewDatapoint]
    
    # Statistics
    total_reviewers: int = 0
    avg_experience_level: float = 0.0  # 1-10
    geographic_distribution: Optional[Dict[str, int]] = None
    
    def get_datapoints_for_repository(self, repo_name: str) -> List[HumanReviewDatapoint]:
        """Get all evaluations for a specific repository"""
        return [dp for dp in self.datapoints if dp.repository_name == repo_name]
    
    def get_datapoints_by_reviewer_role(self, role: ReviewerRole) -> List[HumanReviewDatapoint]:
        """Get all evaluations by a specific reviewer role"""
        return [dp for dp in self.datapoints if dp.reviewer_role == role]
    
    def get_datapoints_by_source(self, source_type: str) -> List[HumanReviewDatapoint]:
        """Get all evaluations from specific source type"""
        return [dp for dp in self.datapoints if dp.source_type == source_type]


class ExecutionBehaviorSignal(BaseModel):
    """Signal about runtime/execution behavior (not just static structure)"""
    signal_type: str  # request_lifecycle, dependency_interaction, async_behavior, state_propagation, etc
    description: str
    confidence: float
    evidence_events: List[Dict[str, Any]] = []  # Execution traces/events proving this
    related_code_locations: List[str] = []
    
    # Execution-specific metadata
    execution_sequence: Optional[List[str]] = None  # Order of execution
    potential_race_conditions: List[str] = []
    state_mutations: List[Dict[str, str]] = []  # What state changes through execution?
    db_interactions: List[Dict[str, Any]] = []  # DB operations and order
    middleware_involvement: List[str] = []  # Which middleware involved
    
    human_evaluation: Optional[HumanSignalEvaluation] = None


class ExecutionGraphFailureTrace(BaseModel):
    """Detailed trace of how failure propagates through execution graph"""
    failure_trigger: str
    initial_node_id: str
    propagation_path: List[str]  # Sequence of node IDs
    affected_components: List[Dict[str, Any]] = []  # Components affected by failure
    
    # State at each step
    state_mutations_during_propagation: List[Dict[str, Any]] = []
    db_state_changes: Optional[Dict[str, Any]] = None
    cache_invalidations: List[str] = []
    
    # Recovery opportunities
    recovery_points: List[Dict[str, Any]] = []  # Where failure could be caught/mitigated
    actual_recovery_code: Optional[List[str]] = None  # Code that actually recovers
    
    # Human evaluation
    human_evaluation: Optional[HumanFailureScenarioEvaluation] = None
    
    # Confidence
    path_exists_confidence: float  # Does this path actually exist in code?
    failure_likely_confidence: float  # How likely is this to happen in production?


class OperationalRealism(BaseModel):
    """Markers of whether analysis understands operational reality"""
    detects_cascading_failures: bool
    considers_timeout_behavior: bool
    understands_middleware_ordering: bool
    tracks_state_consistency: bool
    models_async_ordering_issues: bool
    understands_db_transaction_isolation: bool
    models_cache_invalidation_timing: bool
    considers_dependency_failure_impact: bool
    
    # Score: how operational-reality-grounded is the analysis?
    operational_awareness_score: float = Field(ge=0, le=1.0)


# Preset human evaluation datasets from real sources

GITHUB_PR_REVIEW_DATASET = HumanReviewDataset(
    name="GitHub Real PR Reviews",
    description="Comments from actual GitHub PR reviews on popular repositories",
    created_date=datetime.now(),
    source_repositories=["FastAPI", "Django", "Flask", "aiohttp", "asyncio"],
    reviewer_roles=[ReviewerRole.SENIOR_BACKEND_ENGINEER, ReviewerRole.OPEN_SOURCE_MAINTAINER],
    source_types=["pr_review"],
    datapoints=[],  # Populated from actual PR comments
)

BACKEND_INTERVIEW_DATASET = HumanReviewDataset(
    name="Backend Engineering Interviews",
    description="Interview questions and evaluations from tech companies",
    created_date=datetime.now(),
    source_repositories=["Project-EL", "test-repo", "Decathlon-Clone", "FreelancerFlow"],
    reviewer_roles=[ReviewerRole.TECH_LEAD, ReviewerRole.SENIOR_BACKEND_ENGINEER],
    source_types=["code_interview"],
    datapoints=[],
)

ACADEMIC_CODE_REVIEW_DATASET = HumanReviewDataset(
    name="Academic Code Review",
    description="Evaluations from computer science professors and educators",
    created_date=datetime.now(),
    source_repositories=["Project-EL", "macos-portfolio", "test-repo"],
    reviewer_roles=[ReviewerRole.PROFESSOR_COMPUTER_SCIENCE],
    source_types=["code_interview", "architecture_review"],
    datapoints=[],
)

ARCHITECTURE_REVIEW_DATASET = HumanReviewDataset(
    name="Architecture Design Reviews",
    description="Architectural decisions discussed in review sessions",
    created_date=datetime.now(),
    source_repositories=["Project-EL"],
    reviewer_roles=[ReviewerRole.TECH_LEAD, ReviewerRole.PLATFORM_ENGINEER, ReviewerRole.SENIOR_BACKEND_ENGINEER],
    source_types=["architecture_review"],
    datapoints=[],
)
