"""
categories.py
─────────────
Static, extensible category registry for the Topic Coverage Tracker.

Responsibilities
────────────────
- Define the canonical set of viva coverage domains.
- Map each domain to its expected topic tags and minimum coverage threshold.
- Remain stable across the viva lifecycle (no runtime mutation).
- Be simple enough for contributors to extend safely with one entry.

Rules
─────
- No runtime logic — pure data declarations.
- Tags must be lowercase strings (normalized on lookup).
- Adding a new category requires only one new CoverageCategory entry here.
- No imports from ORACLE internals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List


# ── Category definition ───────────────────────────────────────────────────────

@dataclass(frozen=True)
class CoverageCategory:
    """
    A single viva coverage domain.

    name            : Canonical display name (matches VivaCategory values).
    tags            : Canonical lowercase topic tags expected in this domain.
    min_questions   : Minimum questions to consider this domain 'covered'.
    weight          : Relative importance of this domain (0.0–1.0).
                      Used by heuristics to prioritise gap-closing.
    """
    name: str
    tags: FrozenSet[str]
    min_questions: int = 1
    weight: float = 1.0

    def matches_tag(self, tag: str) -> bool:
        """True if a lowercase tag belongs to this category."""
        return tag.lower() in self.tags


# ── Registry ──────────────────────────────────────────────────────────────────

CATEGORY_REGISTRY: Dict[str, CoverageCategory] = {
    "Architecture": CoverageCategory(
        name          = "Architecture",
        tags          = frozenset({
            "architecture", "rest", "microservice", "monolith",
            "api design", "dependency injection", "module boundary",
            "service layer", "router", "controller",
        }),
        min_questions = 1,
        weight        = 0.85,
    ),
    "Tradeoff": CoverageCategory(
        name          = "Tradeoff",
        tags          = frozenset({
            "tradeoff", "spa vs ssr", "nosql vs sql", "polyglot",
            "cost", "consistency", "cap theorem", "eventual consistency",
            "latency vs throughput",
        }),
        min_questions = 1,
        weight        = 0.75,
    ),
    "Security": CoverageCategory(
        name          = "Security",
        tags          = frozenset({
            "security", "jwt", "auth", "authentication", "authorization",
            "token", "csrf", "xss", "injection", "revocation",
            "tls", "encryption", "cors",
        }),
        min_questions = 1,
        weight        = 0.95,
    ),
    "Scalability": CoverageCategory(
        name          = "Scalability",
        tags          = frozenset({
            "scalability", "connection pool", "horizontal scaling",
            "cache", "redis", "load balancer", "rate limit",
            "queue", "throughput", "replica",
        }),
        min_questions = 1,
        weight        = 0.80,
    ),
    "Failure-Path": CoverageCategory(
        name          = "Failure-Path",
        tags          = frozenset({
            "failure", "fallback", "circuit breaker", "retry",
            "timeout", "cascade", "degrade", "error handling",
            "exception", "dead letter",
        }),
        min_questions = 1,
        weight        = 0.90,
    ),
    "Runtime": CoverageCategory(
        name          = "Runtime",
        tags          = frozenset({
            "runtime", "async", "event loop", "thread", "blocking",
            "memory", "gc", "latency", "concurrency", "task queue",
            "io bound", "cpu bound",
        }),
        min_questions = 1,
        weight        = 0.80,
    ),
}

# Convenience: all canonical category names
ALL_CATEGORY_NAMES: FrozenSet[str] = frozenset(CATEGORY_REGISTRY.keys())


def resolve_category(tag_or_name: str) -> str:
    """
    Map a raw tag or category name to a canonical category name.

    Returns the first matching category name, or 'Architecture' as fallback.
    Matching priority: exact name → tag scan.
    """
    normalized = tag_or_name.strip()
    # Exact name match
    if normalized in CATEGORY_REGISTRY:
        return normalized
    # Tag scan
    normalized_lower = normalized.lower()
    for cat_name, cat in CATEGORY_REGISTRY.items():
        if cat.matches_tag(normalized_lower):
            return cat_name
    return "Architecture"  # Safe fallback
