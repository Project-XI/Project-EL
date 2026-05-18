"""Structured human review dataset storage for comparative validation.

This module stores and loads human review datasets without inventing values.
It is designed to work with real PR reviews, architecture discussions,
maintainer comments, and interview evaluations exported into JSON.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, List, Sequence

from pydantic import BaseModel, Field

from .human_evaluator_models import (
    ACADEMIC_CODE_REVIEW_DATASET,
    ARCHITECTURE_REVIEW_DATASET,
    BACKEND_INTERVIEW_DATASET,
    GITHUB_PR_REVIEW_DATASET,
    HumanReviewDatapoint,
    HumanReviewDataset,
    ReviewerRole,
)


class HumanDatasetSourceManifest(BaseModel):
    """Metadata describing a structured human review dataset source."""

    name: str
    source_type: str
    repository_name: str
    reviewer_role: ReviewerRole
    description: str
    storage_file: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


DEFAULT_DATASET_MANIFESTS: List[HumanDatasetSourceManifest] = [
    HumanDatasetSourceManifest(
        name=GITHUB_PR_REVIEW_DATASET.name,
        source_type="pr_review",
        repository_name=",".join(GITHUB_PR_REVIEW_DATASET.source_repositories),
        reviewer_role=ReviewerRole.SENIOR_BACKEND_ENGINEER,
        description=GITHUB_PR_REVIEW_DATASET.description,
        storage_file="human_reviews/github_pr_reviews.json",
    ),
    HumanDatasetSourceManifest(
        name=BACKEND_INTERVIEW_DATASET.name,
        source_type="code_interview",
        repository_name=",".join(BACKEND_INTERVIEW_DATASET.source_repositories),
        reviewer_role=ReviewerRole.TECH_LEAD,
        description=BACKEND_INTERVIEW_DATASET.description,
        storage_file="human_reviews/backend_interviews.json",
    ),
    HumanDatasetSourceManifest(
        name=ACADEMIC_CODE_REVIEW_DATASET.name,
        source_type="academic_review",
        repository_name=",".join(ACADEMIC_CODE_REVIEW_DATASET.source_repositories),
        reviewer_role=ReviewerRole.PROFESSOR_COMPUTER_SCIENCE,
        description=ACADEMIC_CODE_REVIEW_DATASET.description,
        storage_file="human_reviews/academic_reviews.json",
    ),
    HumanDatasetSourceManifest(
        name=ARCHITECTURE_REVIEW_DATASET.name,
        source_type="architecture_review",
        repository_name=",".join(ARCHITECTURE_REVIEW_DATASET.source_repositories),
        reviewer_role=ReviewerRole.SENIOR_BACKEND_ENGINEER,
        description=ARCHITECTURE_REVIEW_DATASET.description,
        storage_file="human_reviews/architecture_reviews.json",
    ),
]


class HumanReviewDatasetStore:
    """Persistence helpers for structured human review datasets."""

    def __init__(self, base_dir: Path | str | None = None):
        self.base_dir = Path(base_dir or "evaluation/human_validation/data")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_dataset(self, dataset: HumanReviewDataset, filename: str | None = None) -> Path:
        """Persist a dataset as JSON without changing its structure."""

        target_name = filename or f"{dataset.name.lower().replace(' ', '_')}.json"
        path = self.base_dir / target_name
        path.write_text(dataset.model_dump_json(indent=2), encoding="utf-8")
        return path

    def load_dataset(self, path: Path | str) -> HumanReviewDataset:
        """Load a structured human review dataset from JSON."""

        dataset_path = Path(path)
        payload = json.loads(dataset_path.read_text(encoding="utf-8"))
        return HumanReviewDataset.model_validate(payload)

    def save_datapoints(
        self,
        datapoints: Sequence[HumanReviewDatapoint],
        filename: str,
    ) -> Path:
        """Persist raw datapoints as JSONL for append-friendly workflows."""

        path = self.base_dir / filename
        with path.open("w", encoding="utf-8") as handle:
            for datapoint in datapoints:
                handle.write(datapoint.model_dump_json())
                handle.write("\n")
        return path

    def load_datapoints(self, path: Path | str) -> List[HumanReviewDatapoint]:
        """Load structured human review datapoints from JSONL or JSON arrays."""

        datapoint_path = Path(path)
        raw = datapoint_path.read_text(encoding="utf-8").strip()
        if not raw:
            return []

        if raw.startswith("["):
            payload = json.loads(raw)
            return [HumanReviewDatapoint.model_validate(item) for item in payload]

        datapoints: List[HumanReviewDatapoint] = []
        for line in raw.splitlines():
            if not line.strip():
                continue
            datapoints.append(HumanReviewDatapoint.model_validate_json(line))
        return datapoints

    def export_manifest(self, filename: str = "human_review_manifest.json") -> Path:
        """Write the dataset source manifest for downstream pipelines."""

        path = self.base_dir / filename
        path.write_text(
            json.dumps([manifest.model_dump(mode="json") for manifest in DEFAULT_DATASET_MANIFESTS], indent=2),
            encoding="utf-8",
        )
        return path


def bundle_datasets(datasets: Iterable[HumanReviewDataset]) -> HumanReviewDataset:
    """Combine multiple datasets into a single structured bundle."""

    datasets = list(datasets)
    if not datasets:
        raise ValueError("At least one dataset is required to build a bundle")

    merged_datapoints: List[HumanReviewDatapoint] = []
    source_repositories: List[str] = []
    reviewer_roles = set()
    source_types = set()

    for dataset in datasets:
        merged_datapoints.extend(dataset.datapoints)
        source_repositories.extend(dataset.source_repositories)
        reviewer_roles.update(dataset.reviewer_roles)
        source_types.update(dataset.source_types)

    return HumanReviewDataset(
        name="Human Review Bundle",
        description="Combined bundle of structured human evaluation datasets",
        created_date=datetime.utcnow(),
        source_repositories=sorted(set(source_repositories)),
        reviewer_roles=sorted(reviewer_roles, key=lambda role: role.value),
        source_types=sorted(source_types),
        datapoints=merged_datapoints,
        total_reviewers=sum(dataset.total_reviewers for dataset in datasets),
        avg_experience_level=(
            sum(dataset.avg_experience_level for dataset in datasets) / len(datasets)
        ),
        geographic_distribution=None,
    )
