"""
pipeline/__init__.py
────────────────────
Public surface of the GATEKEEPER verification pipeline.
"""

from .pipeline_result import PipelineResult
from .gatekeeper_pipeline import GatekeeperPipeline

__all__ = [
    "PipelineResult",
    "GatekeeperPipeline",
]
