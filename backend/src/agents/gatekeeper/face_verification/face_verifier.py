"""
face_verifier.py
────────────────
Face verification engine for the GATEKEEPER pipeline.

Design
──────
This is a deterministic stub that implements the full verification contract
using fixture-based matching. The interface is stable — a real CV library
(DeepFace, OpenCV, FaceNet) can drop into _run_cv_match() without changing
any caller code.

Matching Rules (stub)
─────────────────────
- face_id == photo_reference          → MATCHED (confidence 0.98)
- face_id starts with roll_number     → MATCHED (confidence 0.91)
- face_id == "OVERRIDE_PASS"          → MATCHED (confidence 1.0, admin override)
- face_id == "OVERRIDE_FAIL"          → MISMATCH (confidence 0.0, forced failure)
- roll_number has no photo_reference  → NO_PHOTO
- face_id is None or empty            → UNVERIFIABLE
- anything else                       → MISMATCH (confidence 0.0)

Rules
─────
- Stateless — registry injected at construction.
- Deterministic — same inputs always produce same result.
- Never raises.
"""

from __future__ import annotations

import logging
from typing import Optional

from src.agents.gatekeeper.registry.registry_store import StudentRegistry
from .face_result import FaceMatchStatus, FaceVerificationResult

logger = logging.getLogger(__name__)

# Confidence thresholds
_CONFIDENCE_EXACT      = 0.98
_CONFIDENCE_PREFIX     = 0.91
_CONFIDENCE_ADMIN      = 1.00
_CONFIDENCE_MISMATCH   = 0.00

# Sentinel face IDs for testing / admin override
_OVERRIDE_PASS = "OVERRIDE_PASS"
_OVERRIDE_FAIL = "OVERRIDE_FAIL"


class FaceVerifier:
    """
    Deterministic face verification engine.

    Usage
    ─────
        verifier = FaceVerifier(registry)
        result   = verifier.verify("150096725066", face_id="photos/150096725066.jpg")
        if result.matched:
            ...

    Production swap
    ───────────────
    Replace _run_cv_match() with a real CV call. Everything else stays the same.
    """

    def __init__(self, registry: StudentRegistry) -> None:
        self._registry = registry

    # ── Public interface ──────────────────────────────────────────────────────

    def verify(self, roll_number: str, face_id: Optional[str]) -> FaceVerificationResult:
        """
        Verify a presented face against the registry photo for a given roll number.

        Parameters
        ──────────
        roll_number : Normalized roll number (must exist in registry).
        face_id     : The identifier / path / hash of the presented face.
        """
        profile = self._registry.get(roll_number)

        # Guard: no such student in registry
        if profile is None:
            logger.warning("[FaceVerifier] Roll number not in registry: %s", roll_number)
            return FaceVerificationResult(
                roll_number     = roll_number,
                face_id         = face_id,
                status          = FaceMatchStatus.UNVERIFIABLE,
                matched         = False,
                confidence      = 0.0,
                reason          = f"Roll number '{roll_number}' not found in registry.",
                photo_reference = None,
            )

        ref_photo = profile.photo_reference

        # Guard: no reference photo registered
        if not ref_photo:
            logger.info("[FaceVerifier] No photo registered for: %s", roll_number)
            return FaceVerificationResult(
                roll_number     = roll_number,
                face_id         = face_id,
                status          = FaceMatchStatus.NO_PHOTO,
                matched         = False,
                confidence      = 0.0,
                reason          = f"No reference photo registered for '{profile.full_name}'.",
                photo_reference = None,
            )

        # Guard: no face presented
        if not face_id or not face_id.strip():
            logger.info("[FaceVerifier] No face presented for: %s", roll_number)
            return FaceVerificationResult(
                roll_number     = roll_number,
                face_id         = face_id,
                status          = FaceMatchStatus.UNVERIFIABLE,
                matched         = False,
                confidence      = 0.0,
                reason          = "No face ID was presented for verification.",
                photo_reference = ref_photo,
            )

        # Run core match logic
        return self._run_cv_match(roll_number, face_id, ref_photo, profile.full_name)

    # ── Core match logic (swap this for real CV in production) ────────────────

    def _run_cv_match(
        self,
        roll_number: str,
        face_id:     str,
        ref_photo:   str,
        student_name:str,
    ) -> FaceVerificationResult:
        """
        Deterministic stub matching logic.
        Replace body with: return self._deepface_match(face_id, ref_photo)
        """

        # Admin override — forced pass
        if face_id == _OVERRIDE_PASS:
            logger.info("[FaceVerifier] Admin override PASS for: %s", roll_number)
            return FaceVerificationResult(
                roll_number     = roll_number,
                face_id         = face_id,
                status          = FaceMatchStatus.MATCHED,
                matched         = True,
                confidence      = _CONFIDENCE_ADMIN,
                reason          = f"Admin override: forced PASS for {student_name}.",
                photo_reference = ref_photo,
            )

        # Admin override — forced fail
        if face_id == _OVERRIDE_FAIL:
            logger.info("[FaceVerifier] Admin override FAIL for: %s", roll_number)
            return FaceVerificationResult(
                roll_number     = roll_number,
                face_id         = face_id,
                status          = FaceMatchStatus.MISMATCH,
                matched         = False,
                confidence      = _CONFIDENCE_MISMATCH,
                reason          = f"Admin override: forced FAIL for {student_name}.",
                photo_reference = ref_photo,
            )

        # Exact match: face_id == registered photo path
        if face_id == ref_photo:
            logger.info("[FaceVerifier] Exact match for: %s", roll_number)
            return FaceVerificationResult(
                roll_number     = roll_number,
                face_id         = face_id,
                status          = FaceMatchStatus.MATCHED,
                matched         = True,
                confidence      = _CONFIDENCE_EXACT,
                reason          = f"Face verified: exact match for {student_name}.",
                photo_reference = ref_photo,
            )

        # Prefix match: face_id starts with roll number (e.g. "150096725066_cam1.jpg")
        if face_id.startswith(roll_number):
            logger.info("[FaceVerifier] Prefix match for: %s", roll_number)
            return FaceVerificationResult(
                roll_number     = roll_number,
                face_id         = face_id,
                status          = FaceMatchStatus.MATCHED,
                matched         = True,
                confidence      = _CONFIDENCE_PREFIX,
                reason          = f"Face verified: roll-prefixed ID matched for {student_name}.",
                photo_reference = ref_photo,
            )

        # Mismatch
        logger.info("[FaceVerifier] Mismatch for: %s (presented=%s)", roll_number, face_id)
        return FaceVerificationResult(
            roll_number     = roll_number,
            face_id         = face_id,
            status          = FaceMatchStatus.MISMATCH,
            matched         = False,
            confidence      = _CONFIDENCE_MISMATCH,
            reason          = (
                f"Face mismatch: presented ID '{face_id}' does not match "
                f"registered photo for {student_name}."
            ),
            photo_reference = ref_photo,
        )
