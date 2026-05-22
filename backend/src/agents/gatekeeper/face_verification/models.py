"""
models.py
─────────
Data contracts for the Face Verification Engine.

Responsibilities
────────────────
- Define all typed input/output structures consumed by the pipeline.
- Keep models decoupled from any ML library.
- Ensure every model is serializable to plain dict — safe for logging.

Rules
─────
- All models are frozen Pydantic BaseModels or plain dataclasses.
- FaceEmbedding stores vectors as plain List[float] — no numpy objects.
- VerificationResult is the single output contract — GATEKEEPER reads this.
- FaceCapture accepts raw bytes or a file path — never stores the image itself
  in the embedding store.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


# ── Enumerations ──────────────────────────────────────────────────────────────

class VerificationStatus(str, Enum):
    VERIFIED      = "verified"       # Face matched within threshold
    MISMATCH      = "mismatch"       # Face did not match
    NO_FACE       = "no_face"        # No face detected in capture
    LOW_QUALITY   = "low_quality"    # Image too blurry / small / dark
    NO_REFERENCE  = "no_reference"   # No registered embedding for this student
    ERROR         = "error"          # Unexpected processing failure


class EmbeddingSource(str, Enum):
    REGISTRATION  = "registration"   # Stored at enrollment time
    LIVE_CAPTURE  = "live_capture"   # Captured at exam entry
    STUB          = "stub"           # Test/mock embedding


# ── Face capture ──────────────────────────────────────────────────────────────

class FaceCapture(BaseModel):
    """
    A single face capture event — input to the embedding engine.

    image_data     : Raw image bytes (JPEG/PNG). Mutually exclusive with image_path.
    image_path     : Path to image file. Used when bytes are not in memory.
    roll_number    : Student identity this capture is associated with.
    capture_source : "live_capture" or "registration".
    width          : Image width in pixels (optional, for quality check).
    height         : Image height in pixels (optional, for quality check).
    """
    model_config = {"frozen": True}

    roll_number:    str
    image_data:     Optional[bytes] = Field(default=None, exclude=True)  # Not serialized
    image_path:     Optional[str]   = None
    capture_source: EmbeddingSource = EmbeddingSource.LIVE_CAPTURE
    width:          Optional[int]   = None
    height:         Optional[int]   = None

    def has_image(self) -> bool:
        return self.image_data is not None or (self.image_path is not None)

    def to_dict(self) -> dict:
        return {
            "roll_number":    self.roll_number,
            "image_path":     self.image_path,
            "capture_source": self.capture_source.value,
            "width":          self.width,
            "height":         self.height,
            "has_image":      self.has_image(),
        }


# ── Face embedding ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class FaceEmbedding:
    """
    A numerical face embedding vector.

    vector         : Plain list of floats — no numpy, safe to serialize.
    roll_number    : Student this embedding belongs to.
    source         : Where the embedding came from.
    model_name     : Which embedding model produced this (for traceability).
    dimension      : Length of the vector (for validation).
    """
    roll_number: str
    vector:      List[float]
    source:      EmbeddingSource
    model_name:  str  = "stub-v1"
    dimension:   int  = field(default=0)

    def __post_init__(self):
        # Set dimension from vector if not provided
        object.__setattr__(self, "dimension", len(self.vector))

    def is_valid(self) -> bool:
        return len(self.vector) > 0 and all(isinstance(v, (int, float)) for v in self.vector)

    def to_dict(self) -> dict:
        return {
            "roll_number": self.roll_number,
            "source":      self.source.value,
            "model_name":  self.model_name,
            "dimension":   self.dimension,
            "is_valid":    self.is_valid(),
        }


# ── Similarity score ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SimilarityScore:
    """Raw comparison result between two embeddings."""
    cosine_similarity: float        # -1.0 to 1.0
    euclidean_distance: float       # 0.0 to ∞
    confidence: float               # 0.0 to 1.0  (derived)

    def to_dict(self) -> dict:
        return {
            "cosine_similarity":  round(self.cosine_similarity, 4),
            "euclidean_distance": round(self.euclidean_distance, 4),
            "confidence":         round(self.confidence, 4),
        }


# ── Verification result ───────────────────────────────────────────────────────

@dataclass(frozen=True)
class VerificationResult:
    """
    Complete output of the Face Verification Pipeline.

    GATEKEEPER reads:
      - status          : pass/fail decision
      - confidence_score: 0.0–1.0
      - is_verified     : boolean shortcut
    """
    roll_number:      str
    status:           VerificationStatus
    confidence_score: float               # 0.0 = no match, 1.0 = perfect match
    similarity:       Optional[SimilarityScore]
    threshold_used:   float               # The threshold applied to decide
    message:          str
    pipeline_version: str = "1.0.0"

    @property
    def is_verified(self) -> bool:
        return self.status == VerificationStatus.VERIFIED

    @property
    def is_mismatch(self) -> bool:
        return self.status == VerificationStatus.MISMATCH

    def to_dict(self) -> dict:
        return {
            "roll_number":      self.roll_number,
            "status":           self.status.value,
            "is_verified":      self.is_verified,
            "is_mismatch":      self.is_mismatch,
            "confidence_score": round(self.confidence_score, 4),
            "threshold_used":   self.threshold_used,
            "message":          self.message,
            "pipeline_version": self.pipeline_version,
            "similarity":       self.similarity.to_dict() if self.similarity else None,
        }
