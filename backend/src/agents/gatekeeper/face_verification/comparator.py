"""
comparator.py
─────────────
Embedding comparison and confidence scoring for the Face Verification Engine.

Responsibilities
────────────────
- Compare two FaceEmbedding vectors using cosine similarity.
- Compute euclidean distance as a secondary metric.
- Derive a normalized confidence score (0.0–1.0).
- Apply a configurable threshold to determine match/mismatch.
- Return a typed SimilarityScore — never raises.

Rules
─────
- Pure functions — no state, no ML imports.
- Deterministic: same vectors → same score every time.
- Cosine similarity is the primary metric (threshold-based decision).
- Confidence is derived as (cosine_similarity + 1) / 2 → range [0.0, 1.0].
- Zero-norm vectors handled safely (returns confidence=0.0).
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import List, Tuple

from .models import FaceEmbedding, SimilarityScore

logger = logging.getLogger(__name__)

# ── Default thresholds ────────────────────────────────────────────────────────

DEFAULT_COSINE_THRESHOLD: float = 0.80
"""
Cosine similarity threshold for a VERIFIED decision.
Cosine similarity ≥ threshold → VERIFIED.
Range: 0.0–1.0. Higher = stricter.

Typical values:
  0.90  → very strict  (exam hall, high-security)
  0.80  → standard     (default)
  0.70  → lenient      (lower quality cameras)
"""


# ── Comparator ────────────────────────────────────────────────────────────────

class EmbeddingComparator:
    """
    Stateless face embedding comparator.

    Usage
    ─────
        comparator = EmbeddingComparator(threshold=0.82)
        score      = comparator.compare(live_embedding, registered_embedding)
        is_match   = comparator.is_match(score)
    """

    def __init__(self, threshold: float = DEFAULT_COSINE_THRESHOLD) -> None:
        if not (0.0 < threshold <= 1.0):
            raise ValueError(f"Threshold must be in (0.0, 1.0], got {threshold}")
        self.threshold = threshold

    def compare(
        self,
        embedding_a: FaceEmbedding,
        embedding_b: FaceEmbedding,
    ) -> SimilarityScore:
        """
        Compare two embeddings and return a SimilarityScore.

        Never raises — returns confidence=0.0 on dimension mismatch or zero-norm.
        """
        vec_a = embedding_a.vector
        vec_b = embedding_b.vector

        if len(vec_a) != len(vec_b) or len(vec_a) == 0:
            logger.warning(
                "[Comparator] dimension mismatch or empty: %d vs %d",
                len(vec_a), len(vec_b),
            )
            return SimilarityScore(
                cosine_similarity  = 0.0,
                euclidean_distance = float("inf"),
                confidence         = 0.0,
            )

        cosine   = _cosine_similarity(vec_a, vec_b)
        euclidean= _euclidean_distance(vec_a, vec_b)
        confidence = (cosine + 1.0) / 2.0   # Map [-1,1] → [0,1]

        logger.debug(
            "[Comparator] cosine=%.4f euclidean=%.4f confidence=%.4f",
            cosine, euclidean, confidence,
        )
        return SimilarityScore(
            cosine_similarity  = cosine,
            euclidean_distance = euclidean,
            confidence         = confidence,
        )

    def is_match(self, score: SimilarityScore) -> bool:
        """True if cosine similarity meets or exceeds the threshold."""
        return score.cosine_similarity >= self.threshold

    def compare_vectors(
        self,
        vec_a: List[float],
        vec_b: List[float],
    ) -> SimilarityScore:
        """Convenience: compare raw float lists directly."""
        dummy_a = FaceEmbedding(roll_number="A", vector=vec_a, source="stub")  # type: ignore
        dummy_b = FaceEmbedding(roll_number="B", vector=vec_b, source="stub")  # type: ignore
        return self.compare(dummy_a, dummy_b)


# ── Pure math helpers ─────────────────────────────────────────────────────────

def _dot_product(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _norm(v: List[float]) -> float:
    return math.sqrt(sum(x * x for x in v))


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """
    Cosine similarity between two vectors.
    Returns 0.0 if either vector is zero-norm.
    """
    norm_a = _norm(a)
    norm_b = _norm(b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return _dot_product(a, b) / (norm_a * norm_b)


def _euclidean_distance(a: List[float], b: List[float]) -> float:
    """Euclidean (L2) distance between two vectors."""
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
