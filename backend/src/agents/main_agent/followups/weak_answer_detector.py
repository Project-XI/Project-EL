"""
weak_answer_detector.py
───────────────────────
Detects whether a candidate's answer is shallow, generic, or incomplete.

Responsibilities
────────────────
- Classify a raw answer string against known weakness patterns.
- Return a WeaknessSignal describing what kind of weakness was detected.
- Never make inference decisions — only surface signals for StrategyEngine.

Rules
─────
- Pure functions + a stateless class.
- No LLM calls, no external I/O.
- Deterministic: same answer text → same WeaknessSignal.
- Patterns are enumerated explicitly — no hidden scoring.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


# ── Weakness types ────────────────────────────────────────────────────────────

class WeaknessType(str, Enum):
    GENERIC_DEFINITION  = "generic_definition"   # Textbook answer, no implementation detail
    VAGUE_CLAIM         = "vague_claim"          # "It's efficient", "It works well"
    MISSING_MECHANISM   = "missing_mechanism"    # Describes what, not how
    NO_FAILURE_MENTION  = "no_failure_mention"   # Ignores error/edge paths
    CONTRADICTS_PRIOR   = "contradicts_prior"    # Conflicts with earlier answer
    TOO_SHORT           = "too_short"            # Fewer than minimum meaningful tokens
    REPEATED_ANSWER     = "repeated_answer"      # Near-duplicate of a prior answer


# ── Configurable thresholds ───────────────────────────────────────────────────

MIN_MEANINGFUL_WORDS: int = 12        # Below this → too_short
VAGUE_TERMS: List[str] = [
    "it works", "it's efficient", "it's fast", "it's good",
    "generally", "usually", "basically", "kind of", "sort of",
    "i think", "i believe", "i guess", "probably",
    "it handles", "it manages", "it deals with",
]
GENERIC_OPENERS: List[str] = [
    "it is a", "this is a", "it refers to", "it means",
    "by definition", "according to", "in simple terms",
    "is basically", "is simply", "is essentially",
]
MECHANISM_KEYWORDS: List[str] = [
    "because", "therefore", "when", "if", "then", "specifically",
    "by calling", "by using", "through", "via", "which causes",
    "which triggers", "the flow is", "the sequence", "the path",
]
FAILURE_KEYWORDS: List[str] = [
    "fail", "error", "exception", "timeout", "retry", "fallback",
    "circuit", "degrad", "unavailab", "500", "reject",
]


# ── Signal dataclass ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class WeaknessSignal:
    """Describes one detected weakness in a candidate answer."""
    weakness_type: WeaknessType
    description: str
    confidence: float               # 0.0–1.0
    trigger_phrase: Optional[str]   # The phrase that triggered detection


@dataclass(frozen=True)
class WeaknessReport:
    """Aggregated weakness analysis for a single answer."""
    answer_text: str
    signals: List[WeaknessSignal]
    is_shallow: bool                # True if any high-confidence signal detected
    primary_weakness: Optional[WeaknessType]

    @property
    def has_any_weakness(self) -> bool:
        return len(self.signals) > 0


# ── Detector ──────────────────────────────────────────────────────────────────

class WeakAnswerDetector:
    """
    Stateless detector that classifies candidate answers for weakness signals.

    Usage
    ─────
        report = WeakAnswerDetector.analyze(answer_text, question_category="Security")
        if report.is_shallow:
            # trigger follow-up via StrategyEngine
    """

    @staticmethod
    def analyze(
        answer_text: str,
        question_category: str = "",
        prior_answers: Optional[List[str]] = None,
    ) -> WeaknessReport:
        """
        Analyze an answer string and return a WeaknessReport.

        Parameters
        ──────────
        answer_text       : Raw candidate answer string.
        question_category : Viva category (e.g. 'Security') — tunes detection.
        prior_answers     : Previous answers in the session for repetition check.
        """
        text_lower = answer_text.lower().strip()
        words = text_lower.split()
        signals: List[WeaknessSignal] = []

        # 1. Too short
        if len(words) < MIN_MEANINGFUL_WORDS:
            signals.append(WeaknessSignal(
                weakness_type  = WeaknessType.TOO_SHORT,
                description    = f"Answer has only {len(words)} words (min {MIN_MEANINGFUL_WORDS}).",
                confidence     = 0.95,
                trigger_phrase = answer_text[:60],
            ))

        # 2. Vague claims
        for term in VAGUE_TERMS:
            if term in text_lower:
                signals.append(WeaknessSignal(
                    weakness_type  = WeaknessType.VAGUE_CLAIM,
                    description    = f"Vague claim detected: '{term}'",
                    confidence     = 0.75,
                    trigger_phrase = term,
                ))
                break

        # 3. Generic definition openers
        for opener in GENERIC_OPENERS:
            if text_lower.startswith(opener) or f" {opener}" in text_lower:
                signals.append(WeaknessSignal(
                    weakness_type  = WeaknessType.GENERIC_DEFINITION,
                    description    = f"Answer reads as a textbook definition (opener: '{opener}').",
                    confidence     = 0.80,
                    trigger_phrase = opener,
                ))
                break

        # 4. Missing mechanism — no causal/procedural language
        has_mechanism = any(kw in text_lower for kw in MECHANISM_KEYWORDS)
        if not has_mechanism and len(words) >= MIN_MEANINGFUL_WORDS:
            signals.append(WeaknessSignal(
                weakness_type  = WeaknessType.MISSING_MECHANISM,
                description    = "Answer describes what but not how (no causal/procedural language).",
                confidence     = 0.70,
                trigger_phrase = None,
            ))

        # 5. No failure mention — applies most to Security / Failure-Path categories
        high_risk_categories = {"security", "failure-path", "runtime", "scalability"}
        if question_category.lower() in high_risk_categories:
            has_failure = any(kw in text_lower for kw in FAILURE_KEYWORDS)
            if not has_failure:
                signals.append(WeaknessSignal(
                    weakness_type  = WeaknessType.NO_FAILURE_MENTION,
                    description    = f"No failure or error path mentioned for a '{question_category}' question.",
                    confidence     = 0.78,
                    trigger_phrase = None,
                ))

        # 6. Repeated answer (near-duplicate of prior)
        if prior_answers:
            for prior in prior_answers:
                prior_words = set(prior.lower().split())
                curr_words  = set(words)
                if len(prior_words) > 0:
                    overlap = len(prior_words & curr_words) / len(prior_words)
                    if overlap > 0.70:
                        signals.append(WeaknessSignal(
                            weakness_type  = WeaknessType.REPEATED_ANSWER,
                            description    = f"Answer overlaps {overlap:.0%} with a prior response.",
                            confidence     = 0.85,
                            trigger_phrase = None,
                        ))
                        break

        is_shallow = any(s.confidence >= 0.75 for s in signals)
        primary = signals[0].weakness_type if signals else None

        return WeaknessReport(
            answer_text      = answer_text,
            signals          = signals,
            is_shallow       = is_shallow,
            primary_weakness = primary,
        )
