"""
Observable Signal Calibration Validator

Validates that:
- Signal detection matches expected patterns
- Confidence scores are calibrated to actual accuracy
- False positives/negatives are tracked
- Evidence grounding is maintained
- No unsupported quality judgments are made
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
from src.models.context import EvidenceModel
from src.services.intelligence.observable_signals_engine import EngineeringSignal

@dataclass
class SignalValidationResult:
    """Result of validating a single observable signal."""
    signal_name: str
    expected: bool
    detected: bool
    confidence: float
    evidence_files: List[str]
    
    # Validation outcomes
    is_true_positive: bool = False  # Expected and detected
    is_false_positive: bool = False  # Not expected but detected
    is_false_negative: bool = False  # Expected but not detected
    is_true_negative: bool = False  # Not expected and not detected
    
    # Calibration metrics
    confidence_accuracy: Optional[float] = None  # How well does confidence match reality?
    evidence_grounding_valid: bool = True
    grounding_issues: List[str] = field(default_factory=list)


@dataclass
class SignalValidationReport:
    """Complete validation report for all signals in a repository."""
    repository_name: str
    total_expected: int
    total_detected: int
    
    true_positives: List[SignalValidationResult] = field(default_factory=list)
    false_positives: List[SignalValidationResult] = field(default_factory=list)
    false_negatives: List[SignalValidationResult] = field(default_factory=list)
    true_negatives: List[SignalValidationResult] = field(default_factory=list)
    
    # Aggregate metrics
    precision: float = 0.0  # TP / (TP + FP)
    recall: float = 0.0  # TP / (TP + FN)
    f1_score: float = 0.0
    average_confidence: float = 0.0
    
    # Issues found
    confidence_calibration_issues: List[str] = field(default_factory=list)
    grounding_issues: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "repository": self.repository_name,
            "total_expected": self.total_expected,
            "total_detected": self.total_detected,
            "true_positives": len(self.true_positives),
            "false_positives": len(self.false_positives),
            "false_negatives": len(self.false_negatives),
            "precision": round(self.precision, 3),
            "recall": round(self.recall, 3),
            "f1_score": round(self.f1_score, 3),
            "average_confidence": round(self.average_confidence, 3),
            "confidence_calibration_issues": self.confidence_calibration_issues,
            "grounding_issues": self.grounding_issues,
        }


class ObservableSignalValidator:
    """Validates observable signals against expected patterns."""
    
    @staticmethod
    def validate_signals(
        detected_signals: List[EngineeringSignal],
        expected_signals: List[Any],  # ExpectedSignal from fixtures
        repository_name: str
    ) -> SignalValidationReport:
        """
        Validate detected signals against expected signals.
        
        Args:
            detected_signals: Actual signals extracted by ObservableSignalsEngine
            expected_signals: Expected signals from repository fixture
            repository_name: Name of repository being validated
            
        Returns:
            SignalValidationReport with detailed validation metrics
        """
        report = SignalValidationReport(
            repository_name=repository_name,
            total_expected=len(expected_signals),
            total_detected=len(detected_signals)
        )
        
        # Index detected signals by name for lookup
        detected_by_name = {s.signal_name: s for s in detected_signals}
        expected_by_name = {s.signal_name: s for s in expected_signals}
        
        # Track which expected signals were found
        found_expected = set()
        
        # Validate each detected signal
        for detected_signal in detected_signals:
            expected = expected_by_name.get(detected_signal.signal_name)
            
            result = SignalValidationResult(
                signal_name=detected_signal.signal_name,
                expected=expected is not None,
                detected=True,
                confidence=detected_signal.confidence,
                evidence_files=detected_signal.evidence_files,
            )
            
            if expected:
                # Expected and detected - check if it meets quality bar
                found_expected.add(detected_signal.signal_name)
                result.is_true_positive = True
                
                # Validate confidence meets minimum
                if detected_signal.confidence < expected.expected_confidence_min:
                    report.confidence_calibration_issues.append(
                        f"{detected_signal.signal_name}: confidence {detected_signal.confidence:.2f} "
                        f"below minimum {expected.expected_confidence_min:.2f}"
                    )
                    result.confidence_accuracy = (
                        detected_signal.confidence / expected.expected_confidence_min
                    )
                else:
                    result.confidence_accuracy = 1.0
                
                # Validate evidence grounding
                if not detected_signal.evidence_files:
                    result.evidence_grounding_valid = False
                    result.grounding_issues.append(
                        f"{detected_signal.signal_name}: no evidence files referenced"
                    )
                    report.grounding_issues.append(
                        f"Signal '{detected_signal.signal_name}' lacks evidence grounding"
                    )
                
                report.true_positives.append(result)
            else:
                # Not expected but detected - potential false positive
                result.is_false_positive = True
                report.false_positives.append(result)
                report.confidence_calibration_issues.append(
                    f"Unexpected signal detected: {detected_signal.signal_name} "
                    f"(confidence: {detected_signal.confidence:.2f})"
                )
        
        # Check for false negatives (expected but not detected)
        for expected_signal in expected_signals:
            if expected_signal.signal_name not in found_expected:
                result = SignalValidationResult(
                    signal_name=expected_signal.signal_name,
                    expected=True,
                    detected=False,
                    confidence=0.0,
                    evidence_files=[],
                )
                result.is_false_negative = True
                report.false_negatives.append(result)
                report.grounding_issues.append(
                    f"Expected signal not detected: {expected_signal.signal_name} "
                    f"({expected_signal.failure_indicates})"
                )
        
        # Calculate aggregate metrics
        tp = len(report.true_positives)
        fp = len(report.false_positives)
        fn = len(report.false_negatives)
        
        if tp + fp > 0:
            report.precision = tp / (tp + fp)
        if tp + fn > 0:
            report.recall = tp / (tp + fn)
        
        # F1 score
        if report.precision + report.recall > 0:
            report.f1_score = 2 * (report.precision * report.recall) / (
                report.precision + report.recall
            )
        
        # Average confidence across all detected signals
        if detected_signals:
            report.average_confidence = sum(s.confidence for s in detected_signals) / len(
                detected_signals
            )
        
        return report


class ConfidenceCalibrator:
    """Calibrates confidence scores to actual validation accuracy."""
    
    @staticmethod
    def calibrate_confidence_scores(
        validation_reports: List[SignalValidationReport],
    ) -> Dict[str, Any]:
        """
        Analyze confidence score calibration across multiple repositories.
        
        Returns mapping of confidence ranges to actual accuracy (precision/recall).
        """
        # Group signals by confidence bucket
        confidence_buckets = {
            "0.0-0.25": [],
            "0.25-0.50": [],
            "0.50-0.75": [],
            "0.75-0.90": [],
            "0.90-1.00": [],
        }
        
        for report in validation_reports:
            all_signals = (
                report.true_positives + 
                report.false_positives + 
                report.false_negatives
            )
            
            for signal in all_signals:
                if signal.detected:
                    bucket = ObservableSignalValidator._get_confidence_bucket(signal.confidence)
                    confidence_buckets[bucket].append(signal)
        
        # Calculate calibration for each bucket
        calibration = {}
        for bucket, signals in confidence_buckets.items():
            if not signals:
                continue
            
            tp_in_bucket = sum(1 for s in signals if s.is_true_positive)
            fp_in_bucket = sum(1 for s in signals if s.is_false_positive)
            
            accuracy = tp_in_bucket / len(signals) if signals else 0
            calibration[bucket] = {
                "sample_size": len(signals),
                "accuracy": round(accuracy, 3),
                "true_positives": tp_in_bucket,
                "false_positives": fp_in_bucket,
            }
        
        return calibration
    
    @staticmethod
    def _get_confidence_bucket(confidence: float) -> str:
        """Get the bucket label for a confidence score."""
        if confidence < 0.25:
            return "0.0-0.25"
        elif confidence < 0.50:
            return "0.25-0.50"
        elif confidence < 0.75:
            return "0.50-0.75"
        elif confidence < 0.90:
            return "0.75-0.90"
        else:
            return "0.90-1.00"
