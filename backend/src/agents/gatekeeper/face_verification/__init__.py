"""
face_verification/__init__.py
──────────────────────────────
Public surface of the GATEKEEPER face verification package.
"""

from .face_result import FaceVerificationResult, FaceMatchStatus
from .face_verifier import FaceVerifier

__all__ = [
    "FaceVerificationResult",
    "FaceMatchStatus",
    "FaceVerifier",
]
