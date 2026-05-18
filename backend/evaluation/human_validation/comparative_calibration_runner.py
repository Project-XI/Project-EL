"""Comparative calibration runner for human validation.

This runner combines three data sources:
- ORACLE analysis output
- Structured human review datasets
- Trust audit findings

It does not create synthetic evaluation values. All output must be backed by
actual human review datapoints and real ORACLE analysis payloads supplied at run time.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .comparative_evaluator import ComparativeEvaluationRunner
from .datasets import HumanReviewDatasetStore, bundle_datasets
from .human_evaluator_models import HumanReviewDataset
from .trust_audit import TrustAuditPipeline


@dataclass
class ComparativeCalibrationResult:
    repository_name: str
    comparative_report: Dict[str, Any]
    trust_audit: Dict[str, Any]
    human_dataset_summary: Dict[str, Any]
    oracle_source: Dict[str, Any]
    generated_at: str


class ComparativeCalibrationRunner:
    """Orchestrate human comparison and trust auditing in one pass."""

    def __init__(self, results_dir: Path | str | None = None):
        self.results_dir = Path(results_dir or "evaluation/human_validation/results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.dataset_store = HumanReviewDatasetStore()
        self.comparative_runner = ComparativeEvaluationRunner()
        self.trust_audit = TrustAuditPipeline()

    def load_datasets(self, dataset_paths: Iterable[Path | str]) -> List[HumanReviewDataset]:
        datasets = [self.dataset_store.load_dataset(path) for path in dataset_paths]
        if not datasets:
            raise ValueError("At least one human review dataset is required")
        return datasets

    def run_from_paths(
        self,
        repository_name: str,
        oracle_analysis_path: Path | str,
        dataset_paths: Iterable[Path | str],
    ) -> Path:
        oracle_analysis = json.loads(Path(oracle_analysis_path).read_text(encoding="utf-8"))
        datasets = self.load_datasets(dataset_paths)
        bundled_dataset = bundle_datasets(datasets)

        comparative_report = self.comparative_runner.run_comparative_evaluation(
            repository_name=repository_name,
            oracle_analysis=oracle_analysis,
            human_evaluation_dataset=bundled_dataset.datapoints,
        )
        trust_report = self.trust_audit.audit(oracle_analysis)

        result = ComparativeCalibrationResult(
            repository_name=repository_name,
            comparative_report=json.loads(comparative_report.to_json()),
            trust_audit=trust_report.model_dump(mode="json"),
            human_dataset_summary=self._dataset_summary(bundled_dataset),
            oracle_source={
                "path": str(Path(oracle_analysis_path)),
                "keys": sorted(oracle_analysis.keys()),
            },
            generated_at=datetime.utcnow().isoformat(),
        )

        output_path = self.results_dir / (
            f"comparative_calibration_{repository_name}_"
            f"{datetime.utcnow().isoformat().replace(':', '-')}.json"
        )
        output_path.write_text(json.dumps(result.__dict__, indent=2), encoding="utf-8")
        return output_path

    @staticmethod
    def _dataset_summary(dataset: HumanReviewDataset) -> Dict[str, Any]:
        return {
            "name": dataset.name,
            "description": dataset.description,
            "created_date": dataset.created_date.isoformat(),
            "source_repositories": dataset.source_repositories,
            "reviewer_roles": [role.value for role in dataset.reviewer_roles],
            "source_types": dataset.source_types,
            "total_reviewers": dataset.total_reviewers,
            "avg_experience_level": dataset.avg_experience_level,
            "datapoint_count": len(dataset.datapoints),
        }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run comparative calibration against human review datasets")
    parser.add_argument("--repository-name", required=True, help="Repository name being evaluated")
    parser.add_argument("--oracle-analysis", required=True, help="Path to ORACLE analysis JSON")
    parser.add_argument(
        "--human-dataset",
        action="append",
        required=True,
        help="Path to a structured human review dataset JSON. Repeat for multiple datasets.",
    )
    parser.add_argument(
        "--results-dir",
        default="evaluation/human_validation/results",
        help="Directory for comparative calibration outputs",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    runner = ComparativeCalibrationRunner(results_dir=args.results_dir)
    output_path = runner.run_from_paths(
        repository_name=args.repository_name,
        oracle_analysis_path=args.oracle_analysis,
        dataset_paths=args.human_dataset,
    )
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
