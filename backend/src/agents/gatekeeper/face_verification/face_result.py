"""
face_result.py
──────────────
Typed result object for the GATEKEEPER face verification step.

Rules
─────
- Frozen dataclass — immutable after creation.
- All fields are plain types — safe to serialize and log.
- No pipeline logic here.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class FaceMatchStatus(str, Enum):
    MATCHED       = "matched"        # Face confirmed against registry photo
    MISMATCH      = "mismatch"       # Face presented does not match registry
    NO_PHOTO      = "no_photo"       # No reference photo registered for student
    UNVERIFIABLE  = "unverifiable"   # Face input was absent or unparseable


@dataclass(frozen=True)
class FaceVerificationResult:
    """
    Output of a single face verification attempt.

    Fields
    ──────
    roll_number     : The roll number this face check was performed against.
    face_id         : The presented face identifier (e.g. a hash, path, or UUID).
    status          : FaceMatchStatus enum value.
    matched         : True only when status == MATCHED.
    confidence      : Match confidence score 0.0–1.0 (1.0 = certain match).
    reason          : Human-readable explanation for staff / audit log.
    photo_reference : The reference photo that was compared against.
    """
    roll_number:     str
    face_id:         Optional[str]
    status:          FaceMatchStatus
    matched:         bool
    confidence:      float
    reason:          str
    photo_reference: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "roll_number":     self.roll_number,
            "face_id":         self.face_id,
            "status":          self.status.value,
            "matched":         self.matched,
            "confidence":      self.confidence,
            "reason":          self.reason,
            "photo_reference": self.photo_reference,
        }
