"""
patterns.py
───────────
Deterministic follow-up question patterns for the Strategy Engine.

Responsibilities
────────────────
- Define a catalogue of FollowUpPattern templates, one per weakness type
  and viva category combination.
- Each pattern produces a focused, implementation-specific follow-up prompt
  by substituting evidence placeholders.
- No free-form generation — only template substitution from ORACLE data.

Rules
─────
- All patterns are static — defined at module load time.
- Template substitution uses only inputs provided to fill().
- fill() is pure: same inputs → same output.
- Patterns never invent facts not present in the evidence dict.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from .weak_answer_detector import WeaknessType


# ── Pattern dataclass ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class FollowUpPattern:
    """
    A single reusable follow-up template.

    template      : String with {placeholder} slots.
    weakness_types: Which weakness types this pattern addresses.
    categories    : Which viva categories this pattern suits (empty = all).
    priority      : Lower number = tried first.
    requires_keys : Evidence keys that must be present for fill() to succeed.
    """
    name: str
    template: str
    weakness_types: List[WeaknessType]
    categories: List[str]
    priority: int
    requires_keys: List[str]

    def can_apply(
        self,
        weakness_type: WeaknessType,
        category: str,
        evidence: Dict[str, str],
    ) -> bool:
        """Return True if this pattern matches and has required evidence."""
        if weakness_type not in self.weakness_types:
            return False
        if self.categories and category not in self.categories:
            return False
        return all(k in evidence for k in self.requires_keys)

    def fill(self, evidence: Dict[str, str]) -> str:
        """Substitute template placeholders with evidence values."""
        try:
            return self.template.format(**evidence)
        except KeyError:
            return self.template  # Graceful: return template as-is if key missing


# ── Pattern catalogue ─────────────────────────────────────────────────────────

FOLLOW_UP_PATTERNS: List[FollowUpPattern] = [

    # ── MISSING_MECHANISM patterns ────────────────────────────────────────────

    FollowUpPattern(
        name          = "mechanism_code_path",
        template      = (
            "Walk me through the exact code path in this codebase "
            "when {trigger_event}. "
            "Name the function or module entry point and trace it to completion."
        ),
        weakness_types= [WeaknessType.MISSING_MECHANISM],
        categories    = [],
        priority      = 1,
        requires_keys = ["trigger_event"],
    ),

    FollowUpPattern(
        name          = "mechanism_sequence",
        template      = (
            "You described what happens but not how. "
            "What is the exact sequence of calls or events when {scenario}? "
            "Be specific to this implementation."
        ),
        weakness_types= [WeaknessType.MISSING_MECHANISM],
        categories    = [],
        priority      = 2,
        requires_keys = ["scenario"],
    ),

    # ── NO_FAILURE_MENTION patterns ───────────────────────────────────────────

    FollowUpPattern(
        name          = "failure_cascade",
        template      = (
            "Your answer did not address failure paths. "
            "If {failure_scenario}, what happens to this system? "
            "Which components fail first and does the system degrade gracefully?"
        ),
        weakness_types= [WeaknessType.NO_FAILURE_MENTION],
        categories    = ["Failure-Path", "Security", "Runtime", "Scalability"],
        priority      = 1,
        requires_keys = ["failure_scenario"],
    ),

    FollowUpPattern(
        name          = "failure_http_status",
        template      = (
            "When {failure_scenario} occurs, what HTTP status code does "
            "this API return to the client? "
            "Show the exact error handling path in the code."
        ),
        weakness_types= [WeaknessType.NO_FAILURE_MENTION],
        categories    = ["Security", "Failure-Path"],
        priority      = 2,
        requires_keys = ["failure_scenario"],
    ),

    # ── GENERIC_DEFINITION patterns ───────────────────────────────────────────

    FollowUpPattern(
        name          = "generic_to_implementation",
        template      = (
            "That's the general definition. Now be specific to this project: "
            "where exactly in the codebase is {concept} implemented? "
            "What file or module handles it and how?"
        ),
        weakness_types= [WeaknessType.GENERIC_DEFINITION],
        categories    = [],
        priority      = 1,
        requires_keys = ["concept"],
    ),

    FollowUpPattern(
        name          = "generic_tradeoff_challenge",
        template      = (
            "You gave a textbook answer. In this specific {architecture} architecture, "
            "what is the most significant tradeoff made and why was it acceptable?"
        ),
        weakness_types= [WeaknessType.GENERIC_DEFINITION],
        categories    = ["Architecture", "Tradeoff"],
        priority      = 2,
        requires_keys = ["architecture"],
    ),

    # ── VAGUE_CLAIM patterns ──────────────────────────────────────────────────

    FollowUpPattern(
        name          = "vague_quantify",
        template      = (
            "You said {vague_phrase}. Quantify that. "
            "Under what load or conditions does this hold true, "
            "and at what point does it break down in this system?"
        ),
        weakness_types= [WeaknessType.VAGUE_CLAIM],
        categories    = ["Scalability", "Runtime", "Architecture"],
        priority      = 1,
        requires_keys = ["vague_phrase"],
    ),

    FollowUpPattern(
        name          = "vague_concrete",
        template      = (
            "That claim needs evidence. "
            "Point to a specific component in this {backend_framework} backend "
            "that demonstrates what you just described."
        ),
        weakness_types= [WeaknessType.VAGUE_CLAIM],
        categories    = [],
        priority      = 2,
        requires_keys = ["backend_framework"],
    ),

    # ── TOO_SHORT patterns ────────────────────────────────────────────────────

    FollowUpPattern(
        name          = "short_expand_runtime",
        template      = (
            "Your answer was too brief. Expand: what happens at runtime "
            "when {scenario} is called? Include the request lifecycle, "
            "any middleware involved, and the response path."
        ),
        weakness_types= [WeaknessType.TOO_SHORT],
        categories    = ["Runtime", "Architecture"],
        priority      = 1,
        requires_keys = ["scenario"],
    ),

    FollowUpPattern(
        name          = "short_expand_security",
        template      = (
            "That answer is incomplete. For {concept}: "
            "what is the full attack surface? "
            "What does an attacker gain if this is misconfigured in this system?"
        ),
        weakness_types= [WeaknessType.TOO_SHORT],
        categories    = ["Security"],
        priority      = 1,
        requires_keys = ["concept"],
    ),

    FollowUpPattern(
        name          = "short_generic_expand",
        template      = (
            "Give a more complete answer. Specifically: what triggers it, "
            "what executes, and what is the observable outcome in this project?"
        ),
        weakness_types= [WeaknessType.TOO_SHORT],
        categories    = [],
        priority      = 3,
        requires_keys = [],
    ),

    # ── REPEATED_ANSWER patterns ──────────────────────────────────────────────

    FollowUpPattern(
        name          = "repeat_different_angle",
        template      = (
            "You've touched on this before. Approach it from a different angle: "
            "specifically, how does {concept} behave differently "
            "under {failure_scenario}?"
        ),
        weakness_types= [WeaknessType.REPEATED_ANSWER],
        categories    = [],
        priority      = 1,
        requires_keys = ["concept", "failure_scenario"],
    ),

    FollowUpPattern(
        name          = "repeat_implementation_detail",
        template      = (
            "You have covered the concept. Now go to the implementation: "
            "which specific module in this {backend_framework} project owns this? "
            "What does it return on failure?"
        ),
        weakness_types= [WeaknessType.REPEATED_ANSWER],
        categories    = [],
        priority      = 2,
        requires_keys = ["backend_framework"],
    ),
]


# ── Pattern selector ──────────────────────────────────────────────────────────

def select_pattern(
    weakness_type: WeaknessType,
    category: str,
    evidence: Dict[str, str],
) -> Optional[FollowUpPattern]:
    """
    Return the highest-priority applicable pattern for the given weakness.

    Returns None if no pattern can be applied with available evidence.
    """
    eligible = [
        p for p in FOLLOW_UP_PATTERNS
        if p.can_apply(weakness_type, category, evidence)
    ]
    if not eligible:
        return None
    eligible.sort(key=lambda p: p.priority)
    return eligible[0]


def select_all_patterns(
    weakness_type: WeaknessType,
    category: str,
    evidence: Dict[str, str],
) -> List[FollowUpPattern]:
    """Return all applicable patterns sorted by priority (for fallback chains)."""
    eligible = [
        p for p in FOLLOW_UP_PATTERNS
        if p.can_apply(weakness_type, category, evidence)
    ]
    eligible.sort(key=lambda p: p.priority)
    return eligible
