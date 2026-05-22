"""
face_verification/__init__.py
──────────────────────────────
Public surface of the GATEKEEPER Face Verification Engine package.
"""

from .models import (
    FaceCapture,
    FaceEmbedding,
    VerificationResult,
    VerificationStatus,
    EmbeddingSource,
)
from .embedding_engine import (
    AbstractEmbeddingEngine,
    StubEmbeddingEngine,
)
from .comparator import EmbeddingComparator, SimilarityScore
from .verification_pipeline import FaceVerificationPipeline

__all__ = [
    # Models
    "FaceCapture",
    "FaceEmbedding",
    "VerificationResult",
    "VerificationStatus",
    "EmbeddingSource",
    # Engine
    "AbstractEmbeddingEngine",
    "StubEmbeddingEngine",
    # Comparator
    "EmbeddingComparator",
    "SimilarityScore",
    # Pipeline
    "FaceVerificationPipeline",
]
