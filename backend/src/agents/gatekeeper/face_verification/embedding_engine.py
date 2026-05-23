"""
embedding_engine.py
────────────────────
Face embedding generation engines for the Face Verification Engine.

Responsibilities
────────────────
- Define an abstract engine interface that any ML backend can implement.
- Provide a StubEmbeddingEngine for deterministic testing.
- Provide a FileBasedEmbeddingEngine for loading pre-computed embeddings.
- Ensure engine output is always a FaceEmbedding or None (never raises).

Rules
─────
- AbstractEmbeddingEngine defines the contract — all engines implement it.
- StubEmbeddingEngine is deterministic: same roll_number → same vector.
- Real engines (DeepFace, FaceNet, InsightFace) plug in by subclassing.
- No engine stores state between calls — fully stateless.
- Never import torch/tensorflow at module level — engines import lazily.
"""

from __future__ import annotations

import hashlib
import logging
import math
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from .models import EmbeddingSource, FaceCapture, FaceEmbedding

logger = logging.getLogger(__name__)

# Default embedding dimension for the stub
STUB_EMBEDDING_DIM: int = 128


# ── Abstract interface ────────────────────────────────────────────────────────

class AbstractEmbeddingEngine(ABC):
    """
    Contract for all face embedding engines.

    Implementors
    ────────────
    - StubEmbeddingEngine      : Deterministic hash-based stub (testing)
    - FileBasedEmbeddingEngine : Loads pre-computed .npy or JSON embeddings
    - DeepFaceEngine           : Real DeepFace integration (future)
    - FaceNetEngine            : Real FaceNet integration (future)

    All engines must return None on failure — never raise.
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Human-readable model identifier for traceability."""

    @property
    @abstractmethod
    def embedding_dim(self) -> int:
        """Expected dimension of produced embeddings."""

    @abstractmethod
    def generate(self, capture: FaceCapture) -> Optional[FaceEmbedding]:
        """
        Generate a face embedding from a FaceCapture.

        Returns FaceEmbedding on success, None if:
        - No face detected
        - Image quality too low
        - Processing error
        """


# ── Stub engine (deterministic, no ML dependency) ─────────────────────────────

class StubEmbeddingEngine(AbstractEmbeddingEngine):
    """
    Hash-based stub engine — for testing and CI.

    Determinism guarantee:
      same roll_number + same image_path → identical vector every time.

    Mismatch simulation:
      Pass `mismatch_roll_numbers` to force a different vector for those IDs
      (simulates a face that doesn't match their registration photo).

    No face simulation:
      Pass `no_face_roll_numbers` to return None (no face detected).
    """

    def __init__(
        self,
        mismatch_roll_numbers: Optional[set] = None,
        no_face_roll_numbers: Optional[set] = None,
        dim: int = STUB_EMBEDDING_DIM,
    ) -> None:
        self._mismatch = mismatch_roll_numbers or set()
        self._no_face  = no_face_roll_numbers or set()
        self._dim      = dim

    @property
    def model_name(self) -> str:
        return "stub-v1"

    @property
    def embedding_dim(self) -> int:
        return self._dim

    def generate(self, capture: FaceCapture) -> Optional[FaceEmbedding]:
        """
        Generate a deterministic embedding from roll_number hash.

        If roll_number is in no_face set → returns None.
        If roll_number is in mismatch set → generates a deliberately
        different vector (salt added to hash seed).
        """
        roll = capture.roll_number

        if roll in self._no_face:
            logger.debug("[StubEngine] no-face simulated for %s", roll)
            return None

        # Mismatch: add salt to make a different vector
        seed = f"{roll}:mismatch" if roll in self._mismatch else roll
        vector = self._hash_to_vector(seed, self._dim)

        return FaceEmbedding(
            roll_number = roll,
            vector      = vector,
            source      = capture.capture_source,
            model_name  = self.model_name,
        )

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _hash_to_vector(seed: str, dim: int) -> List[float]:
        """
        Convert a seed string to a unit-normalized float vector of length dim.
        Deterministic: same seed → same vector.
        """
        # Use SHA-256 to get a repeatable byte stream
        digest = hashlib.sha256(seed.encode()).digest()
        # Extend if needed by repeating the digest
        raw_bytes = (digest * ((dim // len(digest)) + 2))[:dim]
        # Map each byte to a float in [-1, 1]
        raw_floats = [(b - 127.5) / 127.5 for b in raw_bytes]
        # L2-normalize to unit sphere
        norm = math.sqrt(sum(v * v for v in raw_floats)) or 1.0
        return [v / norm for v in raw_floats]


# ── File-based engine (pre-computed embeddings) ────────────────────────────────

class FileBasedEmbeddingEngine(AbstractEmbeddingEngine):
    """
    Loads pre-computed embeddings from a dict or JSON store.

    This allows registration embeddings to be computed offline (e.g. during
    student enrollment) and stored, rather than recomputed on every request.

    Usage
    ─────
        store = {
            "CS2021001": [0.12, -0.34, ...],   # 128-dim vector
        }
        engine = FileBasedEmbeddingEngine(embedding_store=store)
        embedding = engine.generate(capture)
    """

    def __init__(
        self,
        embedding_store: Dict[str, List[float]],
        dim: int = STUB_EMBEDDING_DIM,
        model_name_str: str = "file-based-v1",
    ) -> None:
        self._store     = embedding_store
        self._dim       = dim
        self._model_name= model_name_str

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def embedding_dim(self) -> int:
        return self._dim

    def generate(self, capture: FaceCapture) -> Optional[FaceEmbedding]:
        """Return a pre-computed embedding for the roll number, or None."""
        vector = self._store.get(capture.roll_number.strip().upper())
        if vector is None:
            logger.debug("[FileEngine] no embedding stored for %s", capture.roll_number)
            return None
        return FaceEmbedding(
            roll_number = capture.roll_number,
            vector      = list(vector),
            source      = EmbeddingSource.REGISTRATION,
            model_name  = self.model_name,
        )
