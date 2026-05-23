"""
pipeline_result.py
──────────────────
Typed output object for the entire GATEKEEPER pipeline.

Rules
─────
- Frozen dataclass — immutable after creation.
- Fully serializable.
- Exposes final admission boolean plus complete audit dictionary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from src.agents.gatekeeper.authorization.access_decision import AccessDecision


@dataclass(frozen=True)
class PipelineResult:
    """
    Final output emitted by the Gatekeeper pipeline.
    """
    is_admitted:          bool
    access_decision:      AccessDecision
    pipeline_duration_ms: float
    stage_results:        Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "is_admitted":          self.is_admitted,
            "pipeline_duration_ms": self.pipeline_duration_ms,
            "access_decision":      self.access_decision.to_dict(),
            "stage_results":        self.stage_results,
        }
