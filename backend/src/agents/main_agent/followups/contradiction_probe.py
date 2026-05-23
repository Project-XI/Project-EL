"""
contradiction_probe.py
──────────────────────
Contradiction detection and probing for the Strategy Engine.

Responsibilities
────────────────
- Compare a new answer against the session's prior answer history.
- Detect factual contradictions using explicit keyword-opposition patterns.
- Generate a targeted contradiction probe prompt grounded in both answers.
- Return a ContradictionResult with the conflicting claims for audit.

Rules
─────
- Pure functions — no state, no external calls.
- Deterministic: same answer pair → same result.
- No speculative inference — only explicit keyword opposition matching.
- Contradictions must cite both the prior claim and the new claim.
- Never invents facts: all probe text draws from the input strings only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


# ── Opposition pairs ──────────────────────────────────────────────────────────
# Each entry is (term_a, term_b) — if both appear across two answers, contradiction flagged.

OPPOSITION_PAIRS: List[Tuple[str, str]] = [
    ("stateless", "stateful"),
    ("synchronous", "asynchronous"),
    ("sync", "async"),
    ("cached", "not cached"),
    ("authenticated", "unauthenticated"),
    ("encrypted", "not encrypted"),
    ("sql", "nosql"),
    ("relational", "document"),
    ("monolith", "microservice"),
    ("horizontal", "vertical"),
    ("jwt", "session"),
    ("rest", "graphql"),
    ("blocking", "non-blocking"),
    ("strongly typed", "dynamically typed"),
    ("validated", "not validated"),
    ("authorized", "unauthorized"),
    ("persistent", "in-memory"),
    ("pooled", "not pooled"),
]

# Negation patterns that flip a claim
NEGATION_MARKERS: List[str] = [
    "does not", "doesn't", "did not", "didn't",
    "is not", "isn't", "are not", "aren't",
    "no ", "never ", "without ",
]


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ContradictionResult:
    """Describes a detected contradiction between two candidate answers."""
    detected: bool
    prior_claim: str             # Excerpt from the earlier answer
    new_claim: str               # Excerpt from the current answer
    conflicting_term: str        # The keyword pair that triggered detection
    probe_prompt: str            # Ready-to-use follow-up prompt
    confidence: float


# ── Detection helpers ─────────────────────────────────────────────────────────

def _contains(text: str, term: str) -> bool:
    return term.lower() in text.lower()


def _negated(text: str, term: str) -> bool:
    """Return True if term appears negated in text."""
    lower = text.lower()
    for marker in NEGATION_MARKERS:
        idx = lower.find(marker)
        if idx != -1:
            nearby = lower[idx: idx + len(marker) + len(term) + 5]
            if term.lower() in nearby:
                return True
    return False


def _effective_claim(text: str, term: str) -> str:
    """Return the semantic claim: term or NOT term based on negation."""
    if _negated(text, term):
        return f"NOT {term}"
    return term


# ── Primary detector ──────────────────────────────────────────────────────────

def detect_contradiction(
    new_answer: str,
    prior_answers: List[str],
) -> ContradictionResult:
    """
    Compare new_answer against each prior_answer to find contradictions.

    Returns the first contradiction found, or a no-contradiction result.
    """
    for prior in reversed(prior_answers):  # Most recent prior first
        for term_a, term_b in OPPOSITION_PAIRS:
            prior_has_a = _contains(prior, term_a)
            prior_has_b = _contains(prior, term_b)
            new_has_a   = _contains(new_answer, term_a)
            new_has_b   = _contains(new_answer, term_b)

            prior_claim_a = _effective_claim(prior, term_a) if prior_has_a else None
            prior_claim_b = _effective_claim(prior, term_b) if prior_has_b else None
            new_claim_a   = _effective_claim(new_answer, term_a) if new_has_a else None
            new_claim_b   = _effective_claim(new_answer, term_b) if new_has_b else None

            # Opposition check: prior said A, now says B (or vice versa)
            contradiction = None
            if prior_claim_a and new_claim_b and prior_claim_a != f"NOT {term_a}":
                contradiction = (prior_claim_a, new_claim_b, f"{term_a} ↔ {term_b}")
            elif prior_claim_b and new_claim_a and prior_claim_b != f"NOT {term_b}":
                contradiction = (prior_claim_b, new_claim_a, f"{term_b} ↔ {term_a}")

            if contradiction:
                prior_c, new_c, conflict_term = contradiction
                probe = _build_probe_prompt(prior_c, new_c, conflict_term)
                return ContradictionResult(
                    detected         = True,
                    prior_claim      = prior_c,
                    new_claim        = new_c,
                    conflicting_term = conflict_term,
                    probe_prompt     = probe,
                    confidence       = 0.85,
                )

    return ContradictionResult(
        detected         = False,
        prior_claim      = "",
        new_claim        = "",
        conflicting_term = "",
        probe_prompt     = "",
        confidence       = 0.0,
    )


def _build_probe_prompt(prior_claim: str, new_claim: str, conflict_term: str) -> str:
    return (
        f"Earlier you indicated this system uses '{prior_claim}', "
        f"but now you described it as '{new_claim}'. "
        f"These are conflicting claims around {conflict_term}. "
        f"Which is accurate for this specific implementation, and where in the codebase can this be verified?"
    )
