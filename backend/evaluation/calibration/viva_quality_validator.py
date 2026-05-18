"""
Viva Question Realism Validator

Validates that generated viva questions:
- Are specific to implementation details, not generic textbook questions
- Reference actual code evidence and failure scenarios
- Assess architectural challenges relevant to the codebase
- Reflect senior-engineer code review discussion style
- Not speculative or unsupported

Rejects:
- Generic framework trivia ("What is FastAPI?")
- Textbook answers ("Explain the MVC pattern")
- Unsupported speculation ("How would you add machine learning?")
- Template-based shallow questions
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple
from src.models.context import VivaTarget


@dataclass
class VivaQualityIssue:
    """A detected quality issue in a viva question."""
    issue_type: str  # generic, textbook, speculative, shallow, non_grounded
    severity: str  # critical, high, medium, low
    description: str
    evidence: str


@dataclass
class VivaQuestionValidation:
    """Validation result for a single viva question."""
    question: str
    topic: str
    
    # Specificity checks
    is_generic: bool = False
    is_textbook: bool = False
    is_speculative: bool = False
    
    # Grounding checks
    has_code_evidence: bool = False
    evidence_files: List[str] = field(default_factory=list)
    references_failure_scenario: bool = False
    
    # Quality assessment
    implementation_specificity: float = 0.0  # 0.0-1.0
    architectural_relevance: float = 0.0  # 0.0-1.0
    operational_realism: float = 0.0  # 0.0-1.0
    overall_quality_score: float = 0.0  # Weighted average
    
    # Issues detected
    quality_issues: List[VivaQualityIssue] = field(default_factory=list)
    
    # Difficulty assessment
    difficulty: str = "foundational"  # foundational, medium, hard
    
    def is_valid(self) -> bool:
        """Question passes validation if no critical/high issues."""
        severe_issues = [
            i for i in self.quality_issues
            if i.severity in ["critical", "high"]
        ]
        return len(severe_issues) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "question": self.question,
            "is_valid": self.is_valid(),
            "specificity_score": round(self.implementation_specificity, 2),
            "relevance_score": round(self.architectural_relevance, 2),
            "realism_score": round(self.operational_realism, 2),
            "overall_quality": round(self.overall_quality_score, 2),
            "difficulty": self.difficulty,
            "grounded": self.has_code_evidence and self.references_failure_scenario,
            "issues": [
                {
                    "type": i.issue_type,
                    "severity": i.severity,
                    "description": i.description
                }
                for i in self.quality_issues
            ],
        }


@dataclass
class VivaValidationReport:
    """Complete validation report for all viva questions."""
    repository_name: str
    total_questions: int
    
    valid_questions: List[VivaQuestionValidation] = field(default_factory=list)
    invalid_questions: List[VivaQuestionValidation] = field(default_factory=list)
    
    # Aggregate metrics
    validity_rate: float = 0.0  # % of questions that pass validation
    average_specificity: float = 0.0
    average_relevance: float = 0.0
    average_realism: float = 0.0
    grounding_rate: float = 0.0  # % properly grounded in code/scenarios
    
    # Issues summary
    generic_questions: List[str] = field(default_factory=list)
    speculative_questions: List[str] = field(default_factory=list)
    non_grounded_questions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "repository": self.repository_name,
            "total_questions": self.total_questions,
            "valid_questions": len(self.valid_questions),
            "invalid_questions": len(self.invalid_questions),
            "validity_rate": round(self.validity_rate, 3),
            "average_specificity": round(self.average_specificity, 3),
            "average_relevance": round(self.average_relevance, 3),
            "average_realism": round(self.average_realism, 3),
            "grounding_rate": round(self.grounding_rate, 3),
            "issues": {
                "generic": len(self.generic_questions),
                "speculative": len(self.speculative_questions),
                "non_grounded": len(self.non_grounded_questions),
            }
        }


class VivaQualityValidator:
    """Validates viva question quality and realism."""
    
    # Patterns that indicate generic/textbook questions
    GENERIC_PATTERNS = {
        "What is ": "Generic framework trivia",
        "Explain the ": "Textbook definition question",
        "How does ": "Generic implementation question",
        "Define ": "Dictionary-style definition",
        "Describe ": "Generic description request",
    }
    
    # Patterns that indicate speculative questions
    SPECULATIVE_PATTERNS = {
        "would you add": "Speculative feature addition",
        "how might you": "Speculative implementation",
        "imagine if": "Hypothetical scenario",
        "suppose you": "Hypothetical scenario",
        "could you": "Open-ended speculation",
    }
    
    @staticmethod
    def validate_viva_questions(
        generated_questions: List[VivaTarget],
        repository_name: str,
        detected_signals: List[Any] = None,
        failure_scenarios: List[Any] = None,
    ) -> VivaValidationReport:
        """
        Validate generated viva questions.
        
        Args:
            generated_questions: List of VivaTarget from EvidenceGroundedVivaGenerator
            repository_name: Name of repository
            detected_signals: Observable signals for cross-reference
            failure_scenarios: Failure scenarios for cross-reference
            
        Returns:
            VivaValidationReport with detailed validation
        """
        report = VivaValidationReport(
            repository_name=repository_name,
            total_questions=len(generated_questions),
        )
        
        for viva in generated_questions:
            validation = VivaQualityValidator._validate_single_question(
                viva, detected_signals or [], failure_scenarios or []
            )
            
            if validation.is_valid():
                report.valid_questions.append(validation)
            else:
                report.invalid_questions.append(validation)
            
            # Track issue types
            if validation.is_generic:
                report.generic_questions.append(viva.focus)
            if validation.is_speculative:
                report.speculative_questions.append(viva.focus)
            if not validation.has_code_evidence:
                report.non_grounded_questions.append(viva.focus)
        
        # Calculate aggregate metrics
        if report.valid_questions:
            report.validity_rate = len(report.valid_questions) / len(generated_questions)
            
            avg_specificity = sum(q.implementation_specificity for q in report.valid_questions)
            report.average_specificity = avg_specificity / len(report.valid_questions)
            
            avg_relevance = sum(q.architectural_relevance for q in report.valid_questions)
            report.average_relevance = avg_relevance / len(report.valid_questions)
            
            avg_realism = sum(q.operational_realism for q in report.valid_questions)
            report.average_realism = avg_realism / len(report.valid_questions)
        
        grounded = sum(
            1 for q in report.valid_questions
            if q.has_code_evidence and q.references_failure_scenario
        )
        if report.valid_questions:
            report.grounding_rate = grounded / len(report.valid_questions)
        
        return report
    
    @staticmethod
    def _validate_single_question(
        viva: VivaTarget,
        detected_signals: List[Any],
        failure_scenarios: List[Any],
    ) -> VivaQuestionValidation:
        """Validate a single viva question."""
        question_text = viva.focus
        
        validation = VivaQuestionValidation(
            question=question_text,
            topic=getattr(viva, 'topic', 'Unknown'),
        )
        
        # Check for generic patterns
        for pattern, reason in VivaQualityValidator.GENERIC_PATTERNS.items():
            if pattern.lower() in question_text.lower():
                validation.is_generic = True
                validation.quality_issues.append(VivaQualityIssue(
                    issue_type="generic",
                    severity="high",
                    description=f"Generic pattern detected: {reason}",
                    evidence=pattern
                ))
                break
        
        # Check for speculative patterns
        for pattern, reason in VivaQualityValidator.SPECULATIVE_PATTERNS.items():
            if pattern.lower() in question_text.lower():
                validation.is_speculative = True
                validation.quality_issues.append(VivaQualityIssue(
                    issue_type="speculative",
                    severity="critical",
                    description=f"Speculative pattern: {reason}",
                    evidence=pattern
                ))
                break
        
        # Check code grounding
        implementation_context = getattr(viva, 'implementation_context', '')
        evidence_files = getattr(viva, 'evidence_files', [])
        
        if evidence_files and len(evidence_files) > 0:
            validation.has_code_evidence = True
            validation.evidence_files = evidence_files
            validation.implementation_specificity = 0.8
        else:
            validation.quality_issues.append(VivaQualityIssue(
                issue_type="non_grounded",
                severity="high",
                description="No evidence files referenced",
                evidence="None"
            ))
            validation.implementation_specificity = 0.2
        
        # Check failure scenario grounding
        if implementation_context and any(
            scenario.scenario_name in implementation_context
            for scenario in failure_scenarios
        ):
            validation.references_failure_scenario = True
            validation.operational_realism = 0.9
        else:
            validation.operational_realism = 0.4
        
        # Assess difficulty
        if "critical" in question_text.lower() or "failure" in question_text.lower():
            validation.difficulty = "hard"
        elif "trade" in question_text.lower() or "design" in question_text.lower():
            validation.difficulty = "medium"
        else:
            validation.difficulty = "foundational"
        
        # Architectural relevance
        if any(pattern in question_text.lower() for pattern in [
            "architecture", "design", "pattern", "tradeoff", "consistency"
        ]):
            validation.architectural_relevance = 0.85
        else:
            validation.architectural_relevance = 0.5
        
        # Calculate overall quality score (weighted)
        validation.overall_quality_score = (
            validation.implementation_specificity * 0.4 +
            validation.architectural_relevance * 0.35 +
            validation.operational_realism * 0.25
        )
        
        return validation
