"""
category_balancer.py
────────────────────
Category balancing policy for the Viva Flow Orchestrator.

Responsibilities
────────────────
- Score each available viva target considering category coverage.
- Prefer under-represented categories to distribute question topics.
- Respect importance_score and depth_score from ORACLE.
- Break ties deterministically (by question_target string).

Rules
─────
- Pure functions only — no side effects, no global state.
- Never imports ORACLE internals; only works with NormalizedVivaTarget.
- Deterministic: same candidates + coverage → same ranking.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from src.agents.main_agent.integration.oracle_schema import NormalizedVivaTarget


# ── Scoring weights (tunable without breaking interface) ──────────────────────

WEIGHT_IMPORTANCE:  float = 0.40   # ORACLE importance_score
WEIGHT_DEPTH:       float = 0.25   # ORACLE depth_score (normalized to 0-1)
WEIGHT_BALANCE:     float = 0.25   # Penalty for over-represented category
WEIGHT_DIFFICULTY:  float = 0.10   # Prefer difficulty matching session ramp

DIFFICULTY_RANK: Dict[str, float] = {"easy": 0.33, "medium": 0.66, "hard": 1.0}


# ── Public API ────────────────────────────────────────────────────────────────

def score_target(
    target: NormalizedVivaTarget,
    coverage: Dict[str, int],
    target_difficulty: str,
    total_asked: int,
) -> float:
    """
    Compute a composite score for a single viva target.

    Higher score = higher priority to ask next.
    """
    # Balance penalty: how many times has this category already been asked?
    cat_count = coverage.get(target.category.value, 0)
    max_count = max(coverage.values(), default=0) if coverage else 0
    balance_score = 1.0 - (cat_count / max(max_count + 1, 1))

    # Difficulty alignment
    target_rank = DIFFICULTY_RANK.get(target_difficulty, 0.66)
    actual_rank = DIFFICULTY_RANK.get(target.difficulty.value, 0.66)
    diff_score = 1.0 - abs(target_rank - actual_rank)

    # Depth score is 0-10 → normalize to 0-1
    depth_normalized = min(target.depth_score / 10.0, 1.0)

    composite = (
        WEIGHT_IMPORTANCE * target.importance_score
        + WEIGHT_DEPTH     * depth_normalized
        + WEIGHT_BALANCE   * balance_score
        + WEIGHT_DIFFICULTY * diff_score
    )
    return composite


def rank_targets(
    candidates: List[NormalizedVivaTarget],
    coverage: Dict[str, int],
    asked_targets: frozenset,
    target_difficulty: str = "medium",
    total_asked: int = 0,
) -> List[NormalizedVivaTarget]:
    """
    Return candidates sorted by score descending, excluding already-asked targets.

    Ties broken by question_target alphabetically for determinism.
    """
    eligible = [t for t in candidates if t.question_target not in asked_targets]
    scored = [
        (score_target(t, coverage, target_difficulty, total_asked), t.question_target, t)
        for t in eligible
    ]
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [t for _, _, t in scored]


def pick_next(
    candidates: List[NormalizedVivaTarget],
    coverage: Dict[str, int],
    asked_targets: frozenset,
    target_difficulty: str = "medium",
    total_asked: int = 0,
) -> Optional[NormalizedVivaTarget]:
    """
    Return the single best next viva target, or None if none are available.
    """
    ranked = rank_targets(candidates, coverage, asked_targets, target_difficulty, total_asked)
    return ranked[0] if ranked else None


def coverage_summary(
    candidates: List[NormalizedVivaTarget],
    coverage: Dict[str, int],
) -> Dict[str, Dict[str, int]]:
    """
    Return a dict mapping category → {available, asked} for audit/logging.
    """
    summary: Dict[str, Dict[str, int]] = {}
    for t in candidates:
        cat = t.category.value
        if cat not in summary:
            summary[cat] = {"available": 0, "asked": coverage.get(cat, 0)}
        summary[cat]["available"] += 1
    return summary
