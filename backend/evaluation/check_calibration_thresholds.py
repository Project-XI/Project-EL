#!/usr/bin/env python3
"""
ORACLE Calibration Threshold Checker

Verifies that calibration metrics meet acceptable quality thresholds.
Used in CI/CD to gate PRs and deployments.

Usage:
    python check_calibration_thresholds.py
    python check_calibration_thresholds.py --signal-precision 0.80 --viva-validity 0.85
    python check_calibration_thresholds.py --strict  # Use strict thresholds
"""

import json
import sys
from pathlib import Path
from datetime import datetime


class ThresholdChecker:
    """Checks calibration metrics against quality thresholds."""
    
    # Standard thresholds
    STANDARD_THRESHOLDS = {
        "signal_precision": 0.80,
        "signal_recall": 0.80,
        "signal_f1": 0.80,
        "failure_precision": 0.75,
        "failure_recall": 0.70,
        "failure_propagation_accuracy": 0.80,
        "viva_validity": 0.85,
        "viva_grounding": 0.90,
        "confidence_calibration_rmse": 0.12,
    }
    
    # Strict thresholds (for main branch)
    STRICT_THRESHOLDS = {
        "signal_precision": 0.85,
        "signal_recall": 0.82,
        "signal_f1": 0.83,
        "failure_precision": 0.80,
        "failure_recall": 0.77,
        "failure_propagation_accuracy": 0.85,
        "viva_validity": 0.90,
        "viva_grounding": 0.92,
        "confidence_calibration_rmse": 0.10,
    }
    
    def __init__(self, strict: bool = False):
        self.strict = strict
        self.thresholds = self.STRICT_THRESHOLDS if strict else self.STANDARD_THRESHOLDS
        self.results = []
        self.passed = True
    
    def check(self, results_dir: str = "backend/evaluation/calibration/results") -> bool:
        """
        Check calibration metrics against thresholds.
        
        Args:
            results_dir: Directory containing calibration reports
            
        Returns:
            True if all metrics pass, False otherwise
        """
        results_path = Path(results_dir)
        
        # Find latest calibration report
        if not results_path.exists():
            print("❌ No calibration results directory found")
            self.passed = False
            return False
        
        reports = sorted(results_path.glob("calibration_report_*.json"))
        if not reports:
            print("❌ No calibration reports found in", results_path)
            self.passed = False
            return False
        
        latest_report = reports[-1]
        print(f"📋 Loading: {latest_report.name}")
        
        try:
            with open(latest_report) as f:
                report = json.load(f)
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in {latest_report}")
            self.passed = False
            return False
        
        # Extract metrics
        metrics = report.get("aggregate_metrics", {})
        
        # Check signal metrics
        self._check_metric(
            "Signal Precision",
            metrics.get("signals", {}).get("average_precision", 0),
            self.thresholds["signal_precision"]
        )
        
        self._check_metric(
            "Signal Recall",
            metrics.get("signals", {}).get("average_recall", 0),
            self.thresholds["signal_recall"]
        )
        
        self._check_metric(
            "Signal F1 Score",
            metrics.get("signals", {}).get("average_f1_score", 0),
            self.thresholds["signal_f1"]
        )
        
        # Check failure metrics
        self._check_metric(
            "Failure Precision",
            metrics.get("failures", {}).get("average_precision", 0),
            self.thresholds["failure_precision"]
        )
        
        self._check_metric(
            "Failure Propagation Accuracy",
            metrics.get("failures", {}).get("average_propagation_accuracy", 0),
            self.thresholds["failure_propagation_accuracy"]
        )
        
        # Check viva metrics
        self._check_metric(
            "Viva Validity Rate",
            metrics.get("viva", {}).get("average_validity_rate", 0),
            self.thresholds["viva_validity"]
        )
        
        self._check_metric(
            "Viva Grounding Rate",
            metrics.get("viva", {}).get("average_grounding_rate", 0),
            self.thresholds["viva_grounding"]
        )
        
        # Print summary
        self._print_summary(report)
        
        return self.passed
    
    def _check_metric(self, name: str, actual: float, threshold: float) -> None:
        """Check a single metric against threshold."""
        passed = actual >= threshold
        status = "✅ PASS" if passed else "❌ FAIL"
        
        self.results.append({
            "name": name,
            "actual": actual,
            "threshold": threshold,
            "passed": passed,
        })
        
        print(f"{status} | {name:.<40} {actual:.3f} (threshold: {threshold:.3f})")
        
        if not passed:
            self.passed = False
    
    def _print_summary(self, report: dict) -> None:
        """Print summary and recommendations."""
        print("\n" + "="*70)
        
        passed_count = sum(1 for r in self.results if r["passed"])
        total_count = len(self.results)
        
        print(f"\n📊 RESULTS: {passed_count}/{total_count} metrics passed")
        
        if self.passed:
            print("\n✅ All calibration metrics within acceptable ranges!")
            print("\n🎯 Status: READY FOR", 
                  "STRICT VALIDATION" if self.strict else "MERGE")
        else:
            print("\n❌ Some metrics below thresholds")
            print("\n💡 Recommendations from ORACLE:")
            for rec in report.get("calibration_recommendations", []):
                print(f"  • {rec}")
            
            print("\n🔍 Failed metrics:")
            for result in self.results:
                if not result["passed"]:
                    gap = result["threshold"] - result["actual"]
                    print(f"  • {result['name']}: {gap:.3f} points below threshold")
        
        print("="*70)
    
    def export_report(self, output_file: str = None) -> str:
        """Export check results to JSON."""
        if output_file is None:
            timestamp = datetime.now().isoformat()
            output_file = f"calibration_check_{timestamp}.json"
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "strict_mode": self.strict,
            "passed": self.passed,
            "metrics": self.results,
            "thresholds": self.thresholds,
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📁 Report saved to {output_file}")
        return output_file


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Check ORACLE calibration metrics against thresholds"
    )
    parser.add_argument(
        "--signal-precision",
        type=float,
        default=None,
        help="Signal precision threshold (default: 0.80)"
    )
    parser.add_argument(
        "--signal-recall",
        type=float,
        default=None,
        help="Signal recall threshold (default: 0.80)"
    )
    parser.add_argument(
        "--viva-validity",
        type=float,
        default=None,
        help="Viva validity threshold (default: 0.85)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Use strict thresholds (for main branch)"
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default="backend/evaluation/calibration/results",
        help="Directory containing calibration reports"
    )
    
    args = parser.parse_args()
    
    # Create checker
    checker = ThresholdChecker(strict=args.strict)
    
    # Override defaults if provided
    if args.signal_precision is not None:
        checker.thresholds["signal_precision"] = args.signal_precision
    if args.signal_recall is not None:
        checker.thresholds["signal_recall"] = args.signal_recall
    if args.viva_validity is not None:
        checker.thresholds["viva_validity"] = args.viva_validity
    
    # Run checks
    success = checker.check(args.results_dir)
    
    # Export report
    checker.export_report()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
