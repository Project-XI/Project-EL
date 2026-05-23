"""
coverage/__init__.py
────────────────────
Public surface of the Topic Coverage Tracker package.
"""

from .coverage_state import CoverageState, TopicEntry, CoverageStatus
from .tracker import CoverageTracker
from .categories import CATEGORY_REGISTRY, CoverageCategory

__all__ = [
    "CoverageTracker",
    "CoverageState",
    "TopicEntry",
    "CoverageStatus",
    "CoverageCategory",
    "CATEGORY_REGISTRY",
]
