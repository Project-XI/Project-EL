"""Fairness Audit Framework for Implementation Familiarity Analysis

Detects bias and false positives in implementation familiarity assessment.

Issues to detect:
1. Communication style bias (confident → high familiarity, nervous → low)
2. Demographics bias (accent, experience level)
3. Fluency bias (non-native speakers)
4. Overconfidence (>0.95 scores)
5. False positives (weak communicators marked as non-familiar)
6. False negatives (confident guessers marked as familiar)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class FairnessAuditSeverity(str, Enum):
    """Severity of fairness issues detected."""
    CRITICAL = "critical"  # Likely wrong classification
    HIGH = "high"  # Concerning pattern
    MEDIUM = "medium"  # Worth noting
    LOW = "low"  # Minor concern


class CommunicationStyleBias(str, Enum):
    """Detected communication style that could bias assessment."""
    HIGHLY_CONFIDENT = "highly_confident"  # Strong confidence expressed
    NERVOUS_HEDGING = "nervous_hedging"  # Lots of "I think", "maybe"
    RAPID_SPEECH = "rapid_speech"  # Fast responses (might seem confident)
    SLOW_DELIBERATE = "slow_deliberate"  # Careful, thoughtful responses
    USES_FILLER_WORDS = "uses_filler_words"  # "Um", "like", "you know"
    FORMAL_LANGUAGE = "formal_language"  # Textbook-like phrasing
    CASUAL_LANGUAGE = "casual_language"  # Conversational tone
    NON_NATIVE_ACCENT = "non_native_accent"  # Potential language barrier
    ADMITS_UNCERTAINTY = "admits_uncertainty"  # "I'm not sure, but..."
    AVOIDS_COMMITTING = "avoids_committing"  # Never takes a position


class DemographicContext(str, Enum):
    """Demographic context that could introduce bias."""
    INTERNATIONAL_BACKGROUND = "international"
    NON_TRADITIONAL_PATHWAY = "non_traditional"  # Self-taught, bootcamp, etc.
    EARLY_CAREER = "early_career"  # <2 years experience
    MID_CAREER = "mid_career"  # 2-8 years
    SENIOR_CAREER = "senior_career"  # >8 years
    FIRST_LANGUAGE_NOT_ENGLISH = "non_english"
    NEURODIVERGENT_COMMUNICATION = "neurodivergent"  # May communicate differently
    ANXIETY_PRONE = "anxiety_prone"  # Gets nervous in interviews


@dataclass
class FairnessAuditIssue:
    """A single fairness/bias concern detected."""
    
    issue_id: str
    severity: FairnessAuditSeverity
    category: str  # e.g., "communication_style", "overconfidence", "false_positive"
    description: str
    evidence: str  # What specifically triggered this concern?
    affected_scores: List[str]  # Which scores are affected? e.g., ["familiarity_score"]
    recommendation: str
    
    def to_dict(self) -> Dict:
        return {
            "issue_id": self.issue_id,
            "severity": self.severity.value,
            "category": self.category,
            "description": self.description,
            "evidence": self.evidence,
            "affected_scores": self.affected_scores,
            "recommendation": self.recommendation,
        }


@dataclass
class FairnessAuditReport:
    """Comprehensive fairness audit of an assessment."""
    
    # Required fields
    audit_id: str
    assessment_id: str
    timestamp: datetime
    original_familiarity_score: float
    
    # Optional fields with defaults
    # Issues found
    critical_issues: List[FairnessAuditIssue] = field(default_factory=list)
    high_priority_issues: List[FairnessAuditIssue] = field(default_factory=list)
    medium_priority_issues: List[FairnessAuditIssue] = field(default_factory=list)
    
    # Analysis
    communication_styles_detected: List[CommunicationStyleBias] = field(default_factory=list)
    demographic_context: List[DemographicContext] = field(default_factory=list)
    
    # Scores after bias correction
    bias_adjusted_familiarity_score: Optional[float] = None  # After corrections
    confidence_reduced_to: Optional[str] = None  # e.g., "MEDIUM" if was "HIGH"
    
    # Overall assessment
    assessment_is_reliable: bool = True  # False if bias concerns outweigh evidence
    recommended_manual_review: bool = False
    explanation: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "audit_id": self.audit_id,
            "assessment_id": self.assessment_id,
            "timestamp": self.timestamp.isoformat(),
            "critical_issues": [i.to_dict() for i in self.critical_issues],
            "high_priority_issues": [i.to_dict() for i in self.high_priority_issues],
            "medium_priority_issues": [i.to_dict() for i in self.medium_priority_issues],
            "communication_styles": [s.value for s in self.communication_styles_detected],
            "demographic_context": [d.value for d in self.demographic_context],
            "original_score": self.original_familiarity_score,
            "bias_adjusted_score": self.bias_adjusted_familiarity_score,
            "confidence_reduced_to": self.confidence_reduced_to,
            "is_reliable": self.assessment_is_reliable,
            "manual_review_recommended": self.recommended_manual_review,
            "explanation": self.explanation,
        }


class FairnessAuditor:
    """Audits assessment reports for bias and false positives."""
    
    def __init__(self):
        self.audit_counter = 0
    
    def audit_assessment(
        self,
        assessment_id: str,
        familiarity_score: float,
        confidence: str,  # HIGH/MEDIUM/LOW
        indicators_found: Dict[str, int],  # e.g., {"understanding": 3, "memorization": 0}
        response_texts: List[str],  # All candidate responses
        question_types: List[str],  # Types of questions asked
        demographic_context: Optional[List[DemographicContext]] = None,
    ) -> FairnessAuditReport:
        """
        Audit an assessment for bias and false positives.
        
        Args:
            assessment_id: ID of the assessment being audited
            familiarity_score: The computed familiarity score (0-1)
            confidence: Confidence level (HIGH/MEDIUM/LOW)
            indicators_found: Count of indicators by type
            response_texts: All candidate responses
            question_types: Types of questions asked
            demographic_context: Known demographic context
            
        Returns:
            FairnessAuditReport with issues and recommendations
        """
        self.audit_counter += 1
        audit_id = f"fairness_audit_{self.audit_counter}"
        
        report = FairnessAuditReport(
            audit_id=audit_id,
            assessment_id=assessment_id,
            timestamp=datetime.now(),
            original_familiarity_score=familiarity_score,
            demographic_context=demographic_context or [],
        )
        
        # Check 1: Overconfidence Detection
        self._check_overconfidence(report, familiarity_score, confidence, indicators_found)
        
        # Check 2: Communication Style Bias
        comm_styles = self._analyze_communication_style(response_texts)
        report.communication_styles_detected = comm_styles
        self._check_communication_bias(report, comm_styles, familiarity_score, confidence)
        
        # Check 3: False Positive Patterns
        self._check_false_positive_patterns(report, response_texts, indicators_found)
        
        # Check 4: False Negative Patterns
        self._check_false_negative_patterns(report, response_texts, indicators_found, comm_styles)
        
        # Check 5: Insufficient Evidence
        self._check_insufficient_evidence(report, indicators_found, confidence)
        
        # Check 6: Demographic Bias
        if report.demographic_context:
            self._check_demographic_bias(report, familiarity_score, demographic_context or [])
        
        # Determine overall reliability
        self._compute_overall_reliability(report, familiarity_score, confidence)
        
        return report
    
    def _check_overconfidence(
        self,
        report: FairnessAuditReport,
        score: float,
        confidence: str,
        indicators: Dict[str, int],
    ) -> None:
        """Check if confidence is justified by evidence."""
        total_indicators = sum(indicators.values())
        
        # Rule 1: >0.95 score requires 4+ strong indicators
        if score > 0.95 and total_indicators < 4:
            issue = FairnessAuditIssue(
                issue_id="overconf_001",
                severity=FairnessAuditSeverity.CRITICAL,
                category="overconfidence",
                description=f"Score {score:.2f} with only {total_indicators} indicators",
                evidence=f"Familiarity score {score:.2%} but only {total_indicators} total indicators found",
                affected_scores=["familiarity_score", "confidence"],
                recommendation=f"Reduce confidence from {confidence} to MEDIUM. Score should not exceed 0.85.",
            )
            report.critical_issues.append(issue)
            report.confidence_reduced_to = "MEDIUM"
            report.bias_adjusted_familiarity_score = 0.75
        
        # Rule 2: HIGH confidence requires 3+ indicators
        if confidence == "HIGH" and total_indicators < 3:
            issue = FairnessAuditIssue(
                issue_id="overconf_002",
                severity=FairnessAuditSeverity.HIGH,
                category="overconfidence",
                description="HIGH confidence with insufficient indicators",
                evidence=f"Only {total_indicators} indicators for HIGH confidence claim",
                affected_scores=["confidence"],
                recommendation="Reduce confidence to MEDIUM (2 indicators) or LOW (<2)",
            )
            report.high_priority_issues.append(issue)
            report.confidence_reduced_to = "MEDIUM"
    
    def _analyze_communication_style(self, response_texts: List[str]) -> List[CommunicationStyleBias]:
        """Detect communication style markers."""
        detected = []
        
        combined_text = " ".join(response_texts).lower()
        
        # Confidence markers
        if any(phrase in combined_text for phrase in ["i'm confident", "definitely", "without question", "absolutely"]):
            detected.append(CommunicationStyleBias.HIGHLY_CONFIDENT)
        
        # Hedging markers
        if any(phrase in combined_text for phrase in ["i think", "i believe", "maybe", "might", "could be", "i'm not sure"]):
            detected.append(CommunicationStyleBias.NERVOUS_HEDGING)
        
        # Filler words
        if any(phrase in combined_text for phrase in [" um ", " uh ", " like ", "you know", "kind of", "sort of"]):
            detected.append(CommunicationStyleBias.USES_FILLER_WORDS)
        
        # Formal/textbook language
        textbook_phrases = ["best practice", "industry standard", "design pattern", "architecture", "paradigm"]
        if any(phrase in combined_text for phrase in textbook_phrases):
            detected.append(CommunicationStyleBias.FORMAL_LANGUAGE)
        
        # Admitting uncertainty
        if any(phrase in combined_text for phrase in ["i'm not sure", "i haven't", "i don't know", "still learning"]):
            detected.append(CommunicationStyleBias.ADMITS_UNCERTAINTY)
        
        return detected
    
    def _check_communication_bias(
        self,
        report: FairnessAuditReport,
        comm_styles: List[CommunicationStyleBias],
        score: float,
        confidence: str,
    ) -> None:
        """Check if assessment is biased by communication style."""
        
        # Issue: High score + high confidence + admits uncertainty
        if (score > 0.75 and confidence == "HIGH" and 
            CommunicationStyleBias.ADMITS_UNCERTAINTY in comm_styles):
            issue = FairnessAuditIssue(
                issue_id="comm_bias_001",
                severity=FairnessAuditSeverity.MEDIUM,
                category="communication_style",
                description="High score despite admission of uncertainty",
                evidence="Candidate admits uncertainty but scored high anyway",
                affected_scores=["familiarity_score"],
                recommendation="Review whether candidate truly understands or just admits gaps in a knowledgeable way",
            )
            report.medium_priority_issues.append(issue)
        
        # Issue: Low score + nervous communication
        if (score < 0.5 and 
            CommunicationStyleBias.NERVOUS_HEDGING in comm_styles and
            CommunicationStyleBias.USES_FILLER_WORDS in comm_styles):
            issue = FairnessAuditIssue(
                issue_id="comm_bias_002",
                severity=FairnessAuditSeverity.HIGH,
                category="communication_style",
                description="Low score may reflect communication anxiety, not familiarity",
                evidence="Nervous hedging + filler words but no evidence of misunderstanding",
                affected_scores=["familiarity_score"],
                recommendation="Consider manual review. Nervousness ≠ unfamiliarity.",
            )
            report.high_priority_issues.append(issue)
            report.recommended_manual_review = True
    
    def _check_false_positive_patterns(
        self,
        report: FairnessAuditReport,
        response_texts: List[str],
        indicators: Dict[str, int],
    ) -> None:
        """Detect false positive pattern: weak communicator marked as non-familiar."""
        
        # Look for: low memorization_indicators + admits gaps = likely builder
        memorization_count = indicators.get("memorization", 0)
        understanding_count = indicators.get("understanding", 0)
        
        combined_text = " ".join(response_texts).lower()
        admits_gaps = any(phrase in combined_text for phrase in ["i haven't", "still learning", "edge case", "limitation"])
        
        if memorization_count == 0 and understanding_count >= 2 and admits_gaps:
            # This looks like a real builder
            issue = FairnessAuditIssue(
                issue_id="fp_001",
                severity=FairnessAuditSeverity.MEDIUM,
                category="false_positive",
                description="Likely false positive: real builder marked low",
                evidence=f"0 memorization indicators + {understanding_count} understanding + admits gaps",
                affected_scores=["familiarity_score"],
                recommendation="Increase score. Pattern suggests high implementation familiarity.",
            )
            report.medium_priority_issues.append(issue)
    
    def _check_false_negative_patterns(
        self,
        report: FairnessAuditReport,
        response_texts: List[str],
        indicators: Dict[str, int],
        comm_styles: List[CommunicationStyleBias],
    ) -> None:
        """Detect false negative pattern: confident guesser marked as familiar."""
        
        understanding_count = indicators.get("understanding", 0)
        memorization_count = indicators.get("memorization", 0)
        
        # Look for: high confidence + zero understanding + textbook language
        combined_text = " ".join(response_texts).lower()
        
        if (understanding_count == 0 and memorization_count >= 2 and
            CommunicationStyleBias.HIGHLY_CONFIDENT in comm_styles and
            CommunicationStyleBias.FORMAL_LANGUAGE in comm_styles):
            issue = FairnessAuditIssue(
                issue_id="fn_001",
                severity=FairnessAuditSeverity.MEDIUM,
                category="false_negative",
                description="Likely false negative: confident guesser marked high",
                evidence=f"0 understanding + {memorization_count} memorization + confident + textbook language",
                affected_scores=["familiarity_score"],
                recommendation="Reduce score. Pattern suggests surface knowledge with confident delivery.",
            )
            report.medium_priority_issues.append(issue)
    
    def _check_insufficient_evidence(
        self,
        report: FairnessAuditReport,
        indicators: Dict[str, int],
        confidence: str,
    ) -> None:
        """Check if evidence is sufficient for the stated confidence."""
        
        total = sum(indicators.values())
        
        if total < 2 and confidence in ["HIGH", "MEDIUM"]:
            issue = FairnessAuditIssue(
                issue_id="insuff_001",
                severity=FairnessAuditSeverity.HIGH,
                category="insufficient_evidence",
                description=f"Confidence {confidence} with only {total} indicators",
                evidence=f"Only {total} total indicators detected",
                affected_scores=["confidence"],
                recommendation="Reduce confidence to LOW. Mark as 'Insufficient Data'.",
            )
            report.high_priority_issues.append(issue)
            report.confidence_reduced_to = "LOW"
    
    def _check_demographic_bias(
        self,
        report: FairnessAuditReport,
        score: float,
        demographic_context: List[DemographicContext],
    ) -> None:
        """Check for demographic-correlated bias."""
        
        # Non-native speaker: don't penalize for fluency
        if DemographicContext.FIRST_LANGUAGE_NOT_ENGLISH in demographic_context:
            issue = FairnessAuditIssue(
                issue_id="demo_001",
                severity=FairnessAuditSeverity.MEDIUM,
                category="demographic_bias",
                description="Non-native speaker: separate fluency from familiarity",
                evidence="Candidate's first language is not English",
                affected_scores=["familiarity_score"],
                recommendation="Score based on technical depth, not communication fluency. Consider manual review.",
            )
            report.medium_priority_issues.append(issue)
            report.recommended_manual_review = True
        
        # Early career: don't penalize for experience level
        if DemographicContext.EARLY_CAREER in demographic_context and score < 0.4:
            issue = FairnessAuditIssue(
                issue_id="demo_002",
                severity=FairnessAuditSeverity.LOW,
                category="demographic_bias",
                description="Early career developer: may have high familiarity despite lower experience",
                evidence="Candidate has <2 years experience",
                affected_scores=["familiarity_score"],
                recommendation="Consider years on this specific project, not overall career length.",
            )
            report.medium_priority_issues.append(issue)
    
    def _compute_overall_reliability(
        self,
        report: FairnessAuditReport,
        score: float,
        confidence: str,
    ) -> None:
        """Determine if overall assessment is reliable."""
        
        # Assessment unreliable if critical issues exist
        if report.critical_issues:
            report.assessment_is_reliable = False
            report.recommended_manual_review = True
            report.explanation = "Critical bias/overconfidence issues detected. Manual review recommended."
            return
        
        # Assessment unreliable if high issues + low confidence
        if report.high_priority_issues and confidence != "HIGH":
            report.recommended_manual_review = True
            report.explanation = "Multiple high-priority bias issues detected."
            return
        
        # Assessment is reliable if <3 issues and properly grounded
        if len(report.high_priority_issues) + len(report.medium_priority_issues) <= 2:
            report.assessment_is_reliable = True
            if report.medium_priority_issues:
                report.explanation = f"Assessment reliable with {len(report.medium_priority_issues)} minor concerns noted."
            else:
                report.explanation = "Assessment passed fairness audit."
            return
        
        # Too many issues
        report.assessment_is_reliable = False
        report.recommended_manual_review = True
        report.explanation = f"Too many bias concerns ({len(report.medium_priority_issues)} medium + {len(report.high_priority_issues)} high priority)."
