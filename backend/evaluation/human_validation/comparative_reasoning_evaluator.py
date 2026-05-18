"""Comparative reasoning evaluator for ORACLE vs real engineering reviews.

Measures alignment between:
- ORACLE-generated implementation signals
- ORACLE failure analysis
- ORACLE viva questions

And:
- Real engineering review reasoning
- Actual discovered issues
- Human engineer concern categorization

All comparisons are explainable and evidence-grounded.
No fabricated metrics. Disagreement is surfaced honestly.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from .engineering_review_corpus import (
    ALL_ENGINEERING_REVIEWS,
    EngineeringReviewCategory,
    EngineeredReviewEntry,
    get_reviews_by_category,
)


class ReasoningAlignment(str, Enum):
    """How well ORACLE reasoning aligns with engineering concern."""
    EXACT_MATCH = "exact_match"  # ORACLE identified same concern with same reasoning
    ALIGNED = "aligned"  # ORACLE identified related concern, reasoning compatible
    PARTIAL = "partial"  # ORACLE identified something related but missed key aspect
    ORTHOGONAL = "orthogonal"  # ORACLE found something valid but unrelated to engineer concern
    MISSED = "missed"  # ORACLE did not identify this concern at all
    CONFLICTING = "conflicting"  # ORACLE reasoning contradicts the engineer's observation


@dataclass
class ReasoningComparisonResult:
    """Result of comparing ORACLE reasoning against an engineering review."""
    
    engineering_review: EngineeredReviewEntry
    oracle_findings: Dict[str, Any]  # ORACLE's observable_signals, failure_scenarios, viva_questions
    
    # Did ORACLE identify the same concern?
    alignment: ReasoningAlignment
    
    # Evidence of alignment or misalignment
    aligned_signals: List[str] = field(default_factory=list)  # ORACLE signals that match engineer concern
    missed_aspects: List[str] = field(default_factory=list)  # Engineer concerns ORACLE didn't identify
    spurious_findings: List[str] = field(default_factory=list)  # ORACLE findings not supported by review
    
    # Reasoning quality
    reasoning_supported_by_code: bool = False  # Is ORACLE reasoning grounded in code evidence?
    reasoning_matches_operational_context: bool = False  # Does it match how the issue actually manifested?
    
    # Specificity assessment
    oracle_specificity: float = 0.0  # How specific to this implementation vs generic?
    engineer_specificity: float = 1.0  # How specific was the engineer's concern?
    specificity_gap: float = 0.0  # Difference (negative = ORACLE too generic)
    
    # Confidence assessment
    oracle_confidence_in_concern: Optional[float] = None  # How sure was ORACLE?
    engineer_certainty: float = 1.0  # Engineer's certainty (1.0 if resulted in issue)
    confidence_mismatch: float = 0.0  # Difference (negative = ORACLE overconfident)
    
    # Explanation
    explanation: str = ""  # Why this alignment/mismatch exists
    
    evaluated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "engineering_review_id": self.engineering_review.id,
            "engineering_concern": self.engineering_review.engineering_concern,
            "alignment": self.alignment.value,
            "aligned_signals": self.aligned_signals,
            "missed_aspects": self.missed_aspects,
            "spurious_findings": self.spurious_findings,
            "reasoning_supported_by_code": self.reasoning_supported_by_code,
            "reasoning_matches_operational": self.reasoning_matches_operational_context,
            "oracle_specificity": self.oracle_specificity,
            "specificity_gap": self.specificity_gap,
            "oracle_confidence": self.oracle_confidence_in_concern,
            "confidence_mismatch": self.confidence_mismatch,
            "explanation": self.explanation,
            "evaluated_at": self.evaluated_at.isoformat(),
        }


@dataclass
class ComparativeReasoningReport:
    """Aggregated report comparing ORACLE reasoning to engineering reviews."""
    
    repository_name: str
    evaluation_date: datetime = field(default_factory=datetime.utcnow)
    
    # Comparison results
    comparisons: List[ReasoningComparisonResult] = field(default_factory=list)
    
    # Aggregate metrics
    alignment_distribution: Dict[str, int] = field(default_factory=dict)  # Count by ReasoningAlignment
    
    # Reasoning quality
    avg_specificity_gap: float = 0.0  # Average how generic ORACLE is vs engineer
    avg_confidence_mismatch: float = 0.0  # Average confidence divergence
    
    # Coverage
    categories_covered: List[str] = field(default_factory=list)  # Which review categories were tested
    total_reviews_compared: int = 0
    exact_match_rate: float = 0.0  # % of EXACT_MATCH alignments
    missed_rate: float = 0.0  # % of MISSED alignments
    
    # Issues
    identified_issues_oracle_missed: List[str] = field(default_factory=list)
    areas_oracle_too_generic: List[str] = field(default_factory=list)
    areas_oracle_overconfident: List[str] = field(default_factory=list)
    
    # Summary
    summary: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "repository_name": self.repository_name,
            "evaluation_date": self.evaluation_date.isoformat(),
            "total_reviews_compared": self.total_reviews_compared,
            "alignment_distribution": self.alignment_distribution,
            "exact_match_rate": self.exact_match_rate,
            "missed_rate": self.missed_rate,
            "avg_specificity_gap": self.avg_specificity_gap,
            "avg_confidence_mismatch": self.avg_confidence_mismatch,
            "categories_covered": self.categories_covered,
            "identified_issues_oracle_missed": self.identified_issues_oracle_missed,
            "areas_oracle_too_generic": self.areas_oracle_too_generic,
            "areas_oracle_overconfident": self.areas_oracle_overconfident,
            "summary": self.summary,
            "comparison_count": len(self.comparisons),
        }


class ComparativeReasoningEvaluator:
    """Compare ORACLE reasoning against real engineering reviews."""
    
    def __init__(self, results_dir: Optional[Path | str] = None):
        self.results_dir = Path(results_dir or "evaluation/human_validation/reasoning_reports")
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def compare_oracle_to_reviews(
        self,
        repository_name: str,
        oracle_analysis: Dict[str, Any],
        review_entries: Optional[List[EngineeredReviewEntry]] = None,
    ) -> ComparativeReasoningReport:
        """Compare ORACLE's reasoning against a set of engineering reviews."""
        
        if review_entries is None:
            review_entries = ALL_ENGINEERING_REVIEWS
        
        report = ComparativeReasoningReport(repository_name=repository_name)
        comparisons: List[ReasoningComparisonResult] = []
        
        for review in review_entries:
            comparison = self._compare_single_review(review, oracle_analysis)
            comparisons.append(comparison)
        
        report.comparisons = comparisons
        report.total_reviews_compared = len(comparisons)
        
        # Aggregate metrics
        alignment_counts: Dict[str, int] = {}
        for comparison in comparisons:
            alignment = comparison.alignment.value
            alignment_counts[alignment] = alignment_counts.get(alignment, 0) + 1
        
        report.alignment_distribution = alignment_counts
        
        if report.total_reviews_compared > 0:
            exact_matches = alignment_counts.get(ReasoningAlignment.EXACT_MATCH.value, 0)
            missed = alignment_counts.get(ReasoningAlignment.MISSED.value, 0)
            report.exact_match_rate = exact_matches / report.total_reviews_compared
            report.missed_rate = missed / report.total_reviews_compared
        
        # Average gaps
        specificity_gaps = [c.specificity_gap for c in comparisons if c.specificity_gap]
        if specificity_gaps:
            report.avg_specificity_gap = sum(specificity_gaps) / len(specificity_gaps)
        
        confidence_mismatches = [c.confidence_mismatch for c in comparisons if c.confidence_mismatch != 0]
        if confidence_mismatches:
            report.avg_confidence_mismatch = sum(confidence_mismatches) / len(confidence_mismatches)
        
        # Categorize issues
        report.categories_covered = sorted(set(r.category.value for r in review_entries))
        report.identified_issues_oracle_missed = [
            c.engineering_review.title for c in comparisons if c.alignment == ReasoningAlignment.MISSED
        ]
        report.areas_oracle_too_generic = [
            c.engineering_review.title for c in comparisons if c.specificity_gap < -0.3
        ]
        report.areas_oracle_overconfident = [
            c.engineering_review.title for c in comparisons if c.confidence_mismatch > 0.3
        ]
        
        # Generate summary
        report.summary = self._generate_summary(report)
        
        return report
    
    def _compare_single_review(
        self,
        review: EngineeredReviewEntry,
        oracle_analysis: Dict[str, Any],
    ) -> ReasoningComparisonResult:
        """Compare ORACLE findings against a single engineering review."""
        
        result = ReasoningComparisonResult(
            engineering_review=review,
            oracle_findings=oracle_analysis,
        )
        
        # Extract ORACLE signals (simplified for now; in real implementation would traverse the full analysis)
        oracle_signals = oracle_analysis.get("signals", [])
        oracle_failures = oracle_analysis.get("failure_scenarios", [])
        
        # Check alignment
        result.alignment = self._assess_alignment(
            review=review,
            oracle_signals=oracle_signals,
            oracle_failures=oracle_failures,
            oracle_viva_questions=oracle_analysis.get("viva_questions", []),
        )
        
        # Identify aligned signals
        result.aligned_signals = self._find_aligned_signals(review, oracle_signals)
        
        # Identify missed aspects
        result.missed_aspects = self._identify_missed_aspects(review, oracle_signals)
        
        # Assess reasoning quality
        result.reasoning_supported_by_code = len(review.code_locations) > 0 and len(result.aligned_signals) > 0
        result.reasoning_matches_operational_context = (
            review.operational_context is not None and
            any(ctx in str(oracle_failures) for ctx in [review.operational_context])
        )
        
        # Specificity assessment
        result.oracle_specificity = self._assess_oracle_specificity(review, oracle_signals)
        result.specificity_gap = result.oracle_specificity - result.engineer_specificity
        
        # Confidence assessment
        result.oracle_confidence_in_concern = self._extract_oracle_confidence(oracle_signals)
        result.engineer_certainty = 1.0 if review.resulted_in_issue else 0.7
        if result.oracle_confidence_in_concern is not None:
            result.confidence_mismatch = result.oracle_confidence_in_concern - result.engineer_certainty
        
        # Generate explanation
        result.explanation = self._generate_explanation(result)
        
        return result
    
    def _assess_alignment(
        self,
        review: EngineeredReviewEntry,
        oracle_signals: List[Any],
        oracle_failures: List[Any],
        oracle_viva_questions: List[Any],
    ) -> ReasoningAlignment:
        """Determine how well ORACLE reasoning aligns with the engineering concern."""
        
        # Check for exact match on the concern
        concern_keywords = review.engineering_concern.lower().split()
        signals_text = " ".join(str(s) for s in oracle_signals).lower()
        failures_text = " ".join(str(f) for f in oracle_failures).lower()
        
        keywords_found = sum(1 for kw in concern_keywords if len(kw) > 3 and (kw in signals_text or kw in failures_text))
        
        if keywords_found >= len([kw for kw in concern_keywords if len(kw) > 3]) * 0.8:
            return ReasoningAlignment.EXACT_MATCH
        
        if keywords_found >= len([kw for kw in concern_keywords if len(kw) > 3]) * 0.5:
            return ReasoningAlignment.ALIGNED
        
        if keywords_found > 0:
            return ReasoningAlignment.PARTIAL
        
        if len(oracle_signals) > 0 or len(oracle_failures) > 0:
            return ReasoningAlignment.ORTHOGONAL
        
        return ReasoningAlignment.MISSED
    
    def _find_aligned_signals(
        self,
        review: EngineeredReviewEntry,
        oracle_signals: List[Any],
    ) -> List[str]:
        """Find ORACLE signals that align with the engineering concern."""
        
        aligned: List[str] = []
        concern_keywords = set(kw.lower() for kw in review.engineering_concern.split() if len(kw) > 3)
        
        for signal in oracle_signals:
            signal_text = str(signal).lower()
            if any(kw in signal_text for kw in concern_keywords):
                aligned.append(str(signal))
        
        return aligned
    
    def _identify_missed_aspects(
        self,
        review: EngineeredReviewEntry,
        oracle_signals: List[Any],
    ) -> List[str]:
        """Identify aspects of the engineering concern that ORACLE didn't capture."""
        
        # Simplified: if there are related signals but not many, something was missed
        if len(oracle_signals) < 3:
            aspects = []
            if "propagation" in review.reasoning.lower() and not any("cascade" in str(s).lower() for s in oracle_signals):
                aspects.append("Failure propagation/cascading effects")
            if "timeout" in review.reasoning.lower() and not any("timeout" in str(s).lower() for s in oracle_signals):
                aspects.append("Timeout handling and limits")
            if "retry" in review.reasoning.lower() and not any("retry" in str(s).lower() for s in oracle_signals):
                aspects.append("Retry and backoff logic")
            return aspects
        
        return []
    
    def _assess_oracle_specificity(
        self,
        review: EngineeredReviewEntry,
        oracle_signals: List[Any],
    ) -> float:
        """Assess how specific ORACLE's reasoning is to this implementation vs generic."""
        
        # Check if signals reference specific components from the review
        component_matches = sum(
            1 for component in review.affected_components
            if any(component.lower() in str(signal).lower() for signal in oracle_signals)
        )
        
        if len(review.affected_components) > 0:
            return component_matches / len(review.affected_components)
        
        return 0.5  # Default to medium specificity
    
    def _extract_oracle_confidence(self, oracle_signals: List[Any]) -> Optional[float]:
        """Extract confidence metric from ORACLE signals if available."""
        
        if not oracle_signals:
            return None
        
        # Simplified: look for confidence fields in signal data
        confidences = []
        for signal in oracle_signals:
            if isinstance(signal, dict):
                if "confidence" in signal:
                    confidences.append(float(signal["confidence"]))
        
        if confidences:
            return sum(confidences) / len(confidences)
        
        return None
    
    def _generate_explanation(self, result: ReasoningComparisonResult) -> str:
        """Generate a human-readable explanation of the comparison result."""
        
        if result.alignment == ReasoningAlignment.EXACT_MATCH:
            return (
                f"ORACLE identified the same concern as the engineer: {result.engineering_review.engineering_concern}. "
                f"Signals found: {', '.join(result.aligned_signals[:3])}"
            )
        elif result.alignment == ReasoningAlignment.ALIGNED:
            return (
                f"ORACLE identified related concerns to the engineer's: {result.engineering_review.engineering_concern}. "
                f"Partially aligned signals detected."
            )
        elif result.alignment == ReasoningAlignment.PARTIAL:
            return (
                f"ORACLE found some related signals but missed key aspects: {', '.join(result.missed_aspects[:2])}. "
                f"Engineer's concern was about: {result.engineering_review.engineering_concern}"
            )
        elif result.alignment == ReasoningAlignment.ORTHOGONAL:
            return (
                f"ORACLE found valid signals but unrelated to the engineer's concern. "
                f"Engineer identified: {result.engineering_review.engineering_concern}"
            )
        else:
            return (
                f"ORACLE did not identify the engineer's concern: {result.engineering_review.engineering_concern}. "
                f"This is a missed finding."
            )
    
    def _generate_summary(self, report: ComparativeReasoningReport) -> str:
        """Generate a summary of the comparative analysis."""
        
        parts = [
            f"Repository: {report.repository_name}",
            f"Reviews compared: {report.total_reviews_compared}",
            f"Exact matches: {report.exact_match_rate:.1%}",
            f"Missed findings: {report.missed_rate:.1%}",
        ]
        
        if report.avg_specificity_gap < -0.2:
            parts.append(f"ORACLE reasoning tends to be generic (specificity gap: {report.avg_specificity_gap:.2f})")
        
        if report.avg_confidence_mismatch > 0.2:
            parts.append(f"ORACLE confidence tends to be high relative to uncertainty (mismatch: {report.avg_confidence_mismatch:.2f})")
        
        if report.identified_issues_oracle_missed:
            parts.append(f"Notable missed findings: {len(report.identified_issues_oracle_missed)} engineering concerns")
        
        return " | ".join(parts)
    
    def save_report(self, report: ComparativeReasoningReport) -> Path:
        """Save the comparative reasoning report to disk."""
        
        timestamp = datetime.utcnow().isoformat().replace(":", "-")
        filename = f"comparative_reasoning_{report.repository_name}_{timestamp}.json"
        filepath = self.results_dir / filename
        
        filepath.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
        return filepath
