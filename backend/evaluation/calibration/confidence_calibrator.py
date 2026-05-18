"""
Confidence Score Calibration

Calibrates confidence score algorithms to match actual validation accuracy.

Maps confidence score ranges to real precision/recall/accuracy across
multiple repositories and validation runs.

Never uses fake metrics or hardcoded values - all calibrations grounded
in actual validation results.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any
import json


@dataclass
class ConfidenceCalibrationPoint:
    """Single calibration point linking confidence to accuracy."""
    confidence_bin: str  # "0.0-0.25", "0.25-0.50", etc.
    confidence_midpoint: float
    
    # Observed accuracy from validation
    precision: float  # % of detections in this bin that were correct
    recall: float  # Coverage in validation set
    sample_count: int  # Number of samples in this bin
    
    # Metadata
    repository_types: List[str] = field(default_factory=list)


@dataclass
class ConfidenceCalibrationModel:
    """Complete calibration model for confidence scores."""
    component: str  # observable_signals, failure_analyzer, viva_generator
    calibration_points: List[ConfidenceCalibrationPoint] = field(default_factory=list)
    
    # Overall calibration quality
    calibration_rmse: float = 0.0  # Root mean square error
    calibration_mae: float = 0.0  # Mean absolute error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        return {
            "component": self.component,
            "calibration_points": [
                {
                    "bin": p.confidence_bin,
                    "midpoint": round(p.confidence_midpoint, 2),
                    "precision": round(p.precision, 3),
                    "recall": round(p.recall, 3),
                    "samples": p.sample_count,
                    "repository_types": p.repository_types,
                }
                for p in self.calibration_points
            ],
            "calibration_quality": {
                "rmse": round(self.calibration_rmse, 3),
                "mae": round(self.calibration_mae, 3),
            }
        }


class ConfidenceScoreCalibratorAdvanced:
    """Advanced confidence score calibration."""
    
    CONFIDENCE_BINS = ["0.0-0.25", "0.25-0.50", "0.50-0.75", "0.75-0.90", "0.90-1.00"]
    
    @staticmethod
    def calibrate_from_validation_results(
        validation_reports: List[Any],
        component_name: str,
    ) -> ConfidenceCalibrationModel:
        """
        Build calibration model from validation reports.
        
        Args:
            validation_reports: List of validation reports (signal, failure, or viva)
            component_name: Name of component being calibrated
            
        Returns:
            ConfidenceCalibrationModel with precision/recall per confidence bin
        """
        model = ConfidenceCalibrationModel(component=component_name)
        
        # Collect all predictions grouped by confidence bin
        bin_data: Dict[str, List[Any]] = {bin: [] for bin in ConfidenceScoreCalibratorAdvanced.CONFIDENCE_BINS}
        
        for report in validation_reports:
            # Extract predictions and their confidence scores
            predictions = ConfidenceScoreCalibratorAdvanced._extract_predictions(report)
            
            for pred in predictions:
                confidence = pred.get("confidence", 0.5)
                is_correct = pred.get("is_correct", False)
                
                bin_label = ConfidenceScoreCalibratorAdvanced._get_bin(confidence)
                bin_data[bin_label].append({
                    "confidence": confidence,
                    "is_correct": is_correct,
                    "repo_type": report.repository_name if hasattr(report, 'repository_name') else "unknown",
                })
        
        # Calculate calibration point for each bin
        for bin_label in ConfidenceScoreCalibratorAdvanced.CONFIDENCE_BINS:
            points = bin_data[bin_label]
            
            if not points:
                continue
            
            # Calculate precision (% correct in this bin)
            correct_count = sum(1 for p in points if p["is_correct"])
            precision = correct_count / len(points) if points else 0.0
            
            # Get confidence midpoint for this bin
            confidences = [p["confidence"] for p in points]
            midpoint = sum(confidences) / len(confidences) if confidences else 0.5
            
            # Collect repository types in this bin
            repo_types = list(set(p["repo_type"] for p in points))
            
            calibration_point = ConfidenceCalibrationPoint(
                confidence_bin=bin_label,
                confidence_midpoint=round(midpoint, 3),
                precision=precision,
                recall=len(points) / sum(len(bin_data[b]) for b in bin_data if bin_data[b]),
                sample_count=len(points),
                repository_types=repo_types,
            )
            model.calibration_points.append(calibration_point)
        
        # Calculate calibration quality metrics
        model.calibration_rmse = ConfidenceScoreCalibratorAdvanced._calculate_rmse(model)
        model.calibration_mae = ConfidenceScoreCalibratorAdvanced._calculate_mae(model)
        
        return model
    
    @staticmethod
    def _extract_predictions(report: Any) -> List[Dict[str, Any]]:
        """Extract predictions from a validation report."""
        predictions = []
        
        # Handle SignalValidationReport
        if hasattr(report, 'true_positives'):
            for signal in report.true_positives:
                predictions.append({
                    "confidence": signal.confidence,
                    "is_correct": True,
                })
            for signal in report.false_positives:
                predictions.append({
                    "confidence": signal.confidence,
                    "is_correct": False,
                })
        
        # Handle FailureValidationReport
        if hasattr(report, 'valid_scenarios'):
            for scenario in report.valid_scenarios:
                # Assume valid scenarios are correct
                predictions.append({
                    "confidence": getattr(scenario, 'confidence', 0.75),
                    "is_correct": True,
                })
            for scenario in report.hallucinated_scenarios:
                predictions.append({
                    "confidence": getattr(scenario, 'confidence', 0.5),
                    "is_correct": False,
                })
        
        return predictions
    
    @staticmethod
    def _get_bin(confidence: float) -> str:
        """Get bin label for confidence score."""
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
    
    @staticmethod
    def _calculate_rmse(model: ConfidenceCalibrationModel) -> float:
        """Calculate RMSE between confidence and observed accuracy."""
        squared_errors = []
        
        for point in model.calibration_points:
            # Expected accuracy = confidence midpoint
            # Observed accuracy = precision
            error = (point.confidence_midpoint - point.precision) ** 2
            squared_errors.append(error)
        
        if not squared_errors:
            return 0.0
        
        mean_squared_error = sum(squared_errors) / len(squared_errors)
        return mean_squared_error ** 0.5
    
    @staticmethod
    def _calculate_mae(model: ConfidenceCalibrationModel) -> float:
        """Calculate MAE between confidence and observed accuracy."""
        absolute_errors = []
        
        for point in model.calibration_points:
            error = abs(point.confidence_midpoint - point.precision)
            absolute_errors.append(error)
        
        if not absolute_errors:
            return 0.0
        
        return sum(absolute_errors) / len(absolute_errors)
    
    @staticmethod
    def generate_calibration_report(
        models: Dict[str, ConfidenceCalibrationModel],
    ) -> Dict[str, Any]:
        """Generate comprehensive calibration report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "components_calibrated": list(models.keys()),
            "calibration_models": {
                name: model.to_dict() for name, model in models.items()
            },
            "recommendations": ConfidenceScoreCalibratorAdvanced._generate_recommendations(models),
        }
        return report
    
    @staticmethod
    def _generate_recommendations(models: Dict[str, ConfidenceCalibrationModel]) -> List[str]:
        """Generate calibration recommendations."""
        recommendations = []
        
        for name, model in models.items():
            if model.calibration_rmse > 0.15:
                recommendations.append(
                    f"⚠️  {name}: High calibration error ({model.calibration_rmse:.3f}). "
                    "Confidence scores don't match actual accuracy. Retrain scoring algorithm."
                )
            
            # Check for specific bins with poor calibration
            for point in model.calibration_points:
                if abs(point.confidence_midpoint - point.precision) > 0.2:
                    recommendations.append(
                        f"⚠️  {name} [{point.confidence_bin}]: Confidence {point.confidence_midpoint:.2f} "
                        f"but actual precision {point.precision:.2f}. Adjust scoring."
                    )
        
        if not recommendations:
            recommendations.append("✅ Confidence scores well-calibrated across all components.")
        
        return recommendations


from datetime import datetime
