"""
verification_pipeline.py
─────────────────────────
Central Face Verification Pipeline for the GATEKEEPER agent.

Responsibilities
────────────────
- Accept a live FaceCapture + registered FaceEmbedding (or roll number for lookup).
- Generate live embedding using the configured engine.
- Compare live vs registered embedding.
- Apply threshold → produce a VerificationResult.
- Handle all failure modes (no face, no reference, quality, error) explicitly.

Rules
─────
- Stateless class — all dependencies injected at construction.
- Pipeline is deterministic: same capture + same reference → same result.
- All failure paths produce a VerificationResult, never an exception.
- Threshold and engine are swappable (for testing and production tuning).
- Decision logic lives here — not in the engine or comparator.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from .comparator import DEFAULT_COSINE_THRESHOLD, EmbeddingComparator
from .embedding_engine import AbstractEmbeddingEngine, StubEmbeddingEngine
from .models import (
    EmbeddingSource,
    FaceCapture,
    FaceEmbedding,
    VerificationResult,
    VerificationStatus,
)

logger = logging.getLogger(__name__)

PIPELINE_VERSION = "1.0.0"

# Minimum image dimensions for a quality check
MIN_WIDTH:  int = 64
MIN_HEIGHT: int = 64


class FaceVerificationPipeline:
    """
    Deterministic face verification pipeline.

    Usage (basic)
    ─────────────
        engine   = StubEmbeddingEngine()
        pipeline = FaceVerificationPipeline(engine=engine, threshold=0.80)

        live_capture = FaceCapture(
            roll_number="CS2021001",
            image_path="capture.jpg",
            capture_source=EmbeddingSource.LIVE_CAPTURE,
        )
        result = pipeline.verify(
            live_capture         = live_capture,
            registered_embedding = registered_emb,
        )

    Usage (with registry store)
    ───────────────────────────
        pipeline = FaceVerificationPipeline(
            engine              = engine,
            embedding_store     = {"CS2021001": [0.1, -0.2, ...]},
        )
        result = pipeline.verify_by_roll(live_capture)
    """

    def __init__(
        self,
        engine: Optional[AbstractEmbeddingEngine] = None,
        threshold: float = DEFAULT_COSINE_THRESHOLD,
        embedding_store: Optional[Dict[str, List[float]]] = None,
    ) -> None:
        self._engine     = engine or StubEmbeddingEngine()
        self._comparator = EmbeddingComparator(threshold=threshold)
        self._threshold  = threshold
        # Optional pre-computed registered embeddings: roll_number → vector
        self._store: Dict[str, List[float]] = embedding_store or {}

    # ── Primary entry points ──────────────────────────────────────────────────

    def verify(
        self,
        live_capture: FaceCapture,
        registered_embedding: FaceEmbedding,
    ) -> VerificationResult:
        """
        Verify a live capture against a known registered embedding.

        Pipeline:
        1. Quality check (image dimensions)
        2. Generate live embedding
        3. Compare with registered embedding
        4. Apply threshold → VERIFIED or MISMATCH
        """
        roll = live_capture.roll_number

        # 1. Quality check
        quality_fail = self._check_quality(live_capture)
        if quality_fail:
            return quality_fail

        # 2. Generate live embedding
        live_embedding = self._generate_safe(live_capture)
        if live_embedding is None:
            return self._result(
                roll       = roll,
                status     = VerificationStatus.NO_FACE,
                confidence = 0.0,
                similarity = None,
                message    = (
                    f"No face detected in the live capture for '{roll}'. "
                    f"Ensure the camera is positioned correctly and lighting is adequate."
                ),
            )

        # 3. Compare
        score = self._comparator.compare(live_embedding, registered_embedding)

        # 4. Decision
        if self._comparator.is_match(score):
            return self._result(
                roll       = roll,
                status     = VerificationStatus.VERIFIED,
                confidence = score.confidence,
                similarity = score,
                message    = (
                    f"Identity verified for '{roll}' "
                    f"(confidence={score.confidence:.2%}, "
                    f"cosine={score.cosine_similarity:.4f})."
                ),
            )
        else:
            return self._result(
                roll       = roll,
                status     = VerificationStatus.MISMATCH,
                confidence = score.confidence,
                similarity = score,
                message    = (
                    f"Face mismatch for '{roll}' — "
                    f"confidence {score.confidence:.2%} is below threshold "
                    f"{self._threshold:.2%}."
                ),
            )

    def verify_by_roll(self, live_capture: FaceCapture) -> VerificationResult:
        """
        Verify using the internal embedding store (roll_number → vector).

        Returns NO_REFERENCE if the student has no registered embedding.
        """
        roll = live_capture.roll_number.strip().upper()
        vec  = self._store.get(roll)
        if vec is None:
            return self._result(
                roll       = roll,
                status     = VerificationStatus.NO_REFERENCE,
                confidence = 0.0,
                similarity = None,
                message    = (
                    f"No registered face embedding found for roll number '{roll}'. "
                    f"Student must complete face registration before access."
                ),
            )

        registered = FaceEmbedding(
            roll_number = roll,
            vector      = vec,
            source      = EmbeddingSource.REGISTRATION,
            model_name  = self._engine.model_name,
        )
        return self.verify(live_capture, registered)

    def register_embedding(
        self,
        capture: FaceCapture,
    ) -> Optional[FaceEmbedding]:
        """
        Generate and store a registration embedding for a student.

        Returns the embedding on success, None if generation failed.
        The embedding vector is stored in the internal store for later verify_by_roll() calls.
        """
        embedding = self._generate_safe(capture)
        if embedding:
            self._store[capture.roll_number.strip().upper()] = embedding.vector
            logger.info("[Pipeline] registered embedding for %s", capture.roll_number)
        return embedding

    def has_registered(self, roll_number: str) -> bool:
        """True if the student has a registered embedding in the store."""
        return roll_number.strip().upper() in self._store

    # ── Internals ─────────────────────────────────────────────────────────────

    def _generate_safe(self, capture: FaceCapture) -> Optional[FaceEmbedding]:
        """Call the engine and catch any unexpected exception."""
        try:
            return self._engine.generate(capture)
        except Exception as exc:
            logger.error("[Pipeline] embedding generation error: %s", exc)
            return None

    def _check_quality(self, capture: FaceCapture) -> Optional[VerificationResult]:
        """Return a LOW_QUALITY result if dimensions are below minimum, else None."""
        if capture.width and capture.height:
            if capture.width < MIN_WIDTH or capture.height < MIN_HEIGHT:
                return self._result(
                    roll       = capture.roll_number,
                    status     = VerificationStatus.LOW_QUALITY,
                    confidence = 0.0,
                    similarity = None,
                    message    = (
                        f"Image quality too low for '{capture.roll_number}': "
                        f"{capture.width}×{capture.height}px "
                        f"(minimum {MIN_WIDTH}×{MIN_HEIGHT}px required)."
                    ),
                )
        return None

    def _result(
        self,
        roll:       str,
        status:     VerificationStatus,
        confidence: float,
        similarity,
        message:    str,
    ) -> VerificationResult:
        logger.info(
            "[Pipeline] %s | roll=%s | conf=%.2f | %s",
            status.value, roll, confidence, message,
        )
        return VerificationResult(
            roll_number      = roll,
            status           = status,
            confidence_score = confidence,
            similarity       = similarity,
            threshold_used   = self._threshold,
            message          = message,
            pipeline_version = PIPELINE_VERSION,
        )
