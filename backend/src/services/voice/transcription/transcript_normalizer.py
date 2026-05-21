from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Sequence

from src.services.voice.models.transcript_models import NormalizedTranscript, TranscriptCorrection


@dataclass(frozen=True)
class NormalizationRule:
    name: str
    pattern: str
    replacement: str
    reason: str


DEFAULT_ENGINEERING_TERMS: Sequence[NormalizationRule] = (
    NormalizationRule("jwt", r"\b(?:jwd|jwt|json web token|jsonwebtoken)\b", "JWT", "Standardize authentication token terminology."),
    NormalizationRule("redis", r"\b(?:radius|red\s+is|reddis|redis)\b", "Redis", "Normalize cache/database terminology."),
    NormalizationRule("fastapi", r"\b(?:fast\s*ap\s*i|fast\s*api|fastapi)\b", "FastAPI", "Normalize backend framework naming."),
    NormalizationRule("websocket", r"\b(?:web\s*socket|websockets?)\b", "WebSocket", "Normalize streaming transport naming."),
    NormalizationRule("postgresql", r"\b(?:post\s*gres\s*ql|postgresql|post\s*gres)\b", "PostgreSQL", "Normalize SQL database naming."),
    NormalizationRule("graphql", r"\bgraphql\b", "GraphQL", "Normalize graph query terminology."),
    NormalizationRule("oauth", r"\b(?:o\s*auth|oauth)\b", "OAuth", "Normalize authorization terminology."),
    NormalizationRule("rest", r"\brestful\b", "REST", "Normalize API style naming."),
    NormalizationRule("ci_cd", r"\b(?:ci\s*/\s*cd|cicd)\b", "CI/CD", "Normalize delivery pipeline terminology."),
    NormalizationRule("orm", r"\bobject relational mapper\b", "ORM", "Compress common database abstraction phrasing."),
)


class TranscriptNormalizer:
    """Deterministic cleanup for technical viva transcripts.

    The normalizer only rewrites known engineering terms. It never invents
    content or alters answer meaning beyond terminology correction.
    """

    def __init__(self, rules: Iterable[NormalizationRule] | None = None):
        self.rules: List[NormalizationRule] = list(rules or DEFAULT_ENGINEERING_TERMS)

    def normalize(self, text: str, *, confidence: float = 0.0, session_id: str = "voice-session") -> NormalizedTranscript:
        raw_text = (text or "").strip()
        normalized_text = raw_text
        corrections: List[TranscriptCorrection] = []
        applied_rules: List[str] = []

        for rule in self.rules:
            updated_text, count = re.subn(rule.pattern, rule.replacement, normalized_text, flags=re.IGNORECASE)
            if count:
                corrections.append(
                    TranscriptCorrection(
                        source_text=normalized_text,
                        normalized_text=updated_text,
                        reason=rule.reason,
                        rule_name=rule.name,
                    )
                )
                applied_rules.append(rule.name)
                normalized_text = updated_text

        return NormalizedTranscript(
            session_id=session_id,
            raw_text=raw_text,
            normalized_text=normalized_text,
            confidence=confidence,
            normalized_confidence=confidence,
            corrections=corrections,
            applied_rules=applied_rules,
            metadata={"correction_count": len(corrections)},
        )
