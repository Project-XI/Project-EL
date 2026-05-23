"""
heuristics.py
─────────────
Coverage gap detection heuristics for the Topic Coverage Tracker.

Responsibilities
────────────────
- Identify which categories are under-covered or not started.
- Rank categories by gap priority so the orchestrator can close gaps first.
- Detect saturation (over-questioning one area) for balance enforcement.
- All logic is deterministic and operates only on CoverageState + registry.

Rules
─────
- Pure functions only — no state, no side effects.
- Deterministic: same state + registry → same output.
- No ORACLE logic re-implementation.
- Gap priority is explicit: NOT_STARTED > PARTIAL > low-weight covered.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from .categories import CATEGORY_REGISTRY, CoverageCategory, resolve_category
from .coverage_state import CoverageState, CoverageStatus


# ── Gap record ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CoverageGap:
    """Describes a single coverage gap for one category."""
    category: str
    status: CoverageStatus
    asked: int
    minimum: int
    weight: float
    gap_score: float         # Higher = more urgent to fill
    suggested_tags: List[str]


# ── Status resolver ───────────────────────────────────────────────────────────

SATURATION_MULTIPLIER: int = 3
"""Category is 'saturated' when asked >= min_questions × this multiplier."""


def resolve_status(
    asked: int,
    min_questions: int,
) -> CoverageStatus:
    if asked == 0:
        return CoverageStatus.NOT_STARTED
    if asked >= min_questions * SATURATION_MULTIPLIER:
        return CoverageStatus.SATURATED
    if asked >= min_questions:
        return CoverageStatus.COVERED
    return CoverageStatus.PARTIAL


# ── Gap scoring ───────────────────────────────────────────────────────────────

_STATUS_URGENCY: Dict[CoverageStatus, float] = {
    CoverageStatus.NOT_STARTED: 1.0,
    CoverageStatus.PARTIAL:     0.6,
    CoverageStatus.COVERED:     0.2,
    CoverageStatus.SATURATED:   0.0,
}


def gap_score(
    status: CoverageStatus,
    category_weight: float,
    asked: int,
    min_questions: int,
) -> float:
    """
    Compute a priority score for filling this coverage gap.

    Higher score → higher urgency to ask a question in this category.
    """
    urgency = _STATUS_URGENCY.get(status, 0.0)
    shortfall = max(0, min_questions - asked) / max(min_questions, 1)
    return urgency * category_weight + shortfall * 0.3


# ── Public API ────────────────────────────────────────────────────────────────

def detect_gaps(state: CoverageState) -> List[CoverageGap]:
    """
    Return a list of CoverageGap objects for all registered categories,
    sorted by gap_score descending (most urgent first).
    """
    gaps: List[CoverageGap] = []
    for cat_name, cat in CATEGORY_REGISTRY.items():
        asked = state.category_ask_count(cat_name)
        status = resolve_status(asked, cat.min_questions)
        score = gap_score(status, cat.weight, asked, cat.min_questions)
        gaps.append(CoverageGap(
            category      = cat_name,
            status        = status,
            asked         = asked,
            minimum       = cat.min_questions,
            weight        = cat.weight,
            gap_score     = score,
            suggested_tags= sorted(cat.tags)[:5],   # Top 5 tags for guidance
        ))
    gaps.sort(key=lambda g: (-g.gap_score, g.category))
    return gaps


def uncovered_categories(state: CoverageState) -> List[str]:
    """
    Return category names that are NOT_STARTED, sorted by weight descending.
    """
    result = []
    for cat_name, cat in CATEGORY_REGISTRY.items():
        asked = state.category_ask_count(cat_name)
        if asked == 0:
            result.append((cat.weight, cat_name))
    result.sort(key=lambda x: -x[0])
    return [name for _, name in result]


def partially_covered_categories(state: CoverageState) -> List[str]:
    """Return categories with PARTIAL status, sorted by weight descending."""
    result = []
    for cat_name, cat in CATEGORY_REGISTRY.items():
        asked = state.category_ask_count(cat_name)
        status = resolve_status(asked, cat.min_questions)
        if status == CoverageStatus.PARTIAL:
            result.append((cat.weight, cat_name))
    result.sort(key=lambda x: -x[0])
    return [name for _, name in result]


def saturated_categories(state: CoverageState) -> List[str]:
    """Return categories that are over-questioned."""
    result = []
    for cat_name, cat in CATEGORY_REGISTRY.items():
        asked = state.category_ask_count(cat_name)
        if resolve_status(asked, cat.min_questions) == CoverageStatus.SATURATED:
            result.append(cat_name)
    return sorted(result)


def most_urgent_gap(state: CoverageState) -> Optional[CoverageGap]:
    """Return the single highest-priority coverage gap, or None if fully covered."""
    gaps = [g for g in detect_gaps(state) if g.gap_score > 0]
    return gaps[0] if gaps else None


def coverage_summary_text(state: CoverageState) -> str:
    """Return a human-readable one-line coverage summary for logging."""
    gaps = detect_gaps(state)
    parts = [f"{g.category}:{g.status.value}({g.asked})" for g in gaps]
    return " | ".join(parts)


def is_breadth_sufficient(state: CoverageState, min_categories: int = 3) -> bool:
    """
    Return True if at least min_categories have been covered (≥ min_questions asked).
    Used by the orchestrator to decide if a session has enough breadth to end.
    """
    covered = sum(
        1 for cat_name, cat in CATEGORY_REGISTRY.items()
        if state.category_ask_count(cat_name) >= cat.min_questions
    )
    return covered >= min_categories
