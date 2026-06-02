"""
history_store.py
────────────────
In-memory face history log for the GATEKEEPER pipeline.

Responsibilities
────────────────
- Track which face IDs have been seen for each roll number.
- Track which roll numbers a face ID has been used with.
- Provide conflict detection queries.

Rules
─────
- Stateful per pipeline instance (reset between exam sessions).
- No persistence — a DB adapter can wrap this for production.
- Never raises.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Dict, List, Set

logger = logging.getLogger(__name__)


class FaceHistoryStore:
    """
    Bidirectional face-to-roll and roll-to-face history log.

    Stores two indexes:
    - roll_to_faces : roll_number  → {face_id, ...}
    - face_to_rolls : face_id      → {roll_number, ...}

    Usage
    ─────
        store = FaceHistoryStore()
        store.record("150096725066", "photos/150096725066.jpg")
        store.has_conflict_for_roll("150096725066")   # False — only one face seen
        store.get_rolls_for_face("photos/150096725066.jpg")  # {"150096725066"}
    """

    def __init__(self) -> None:
        self._roll_to_faces: Dict[str, Set[str]] = defaultdict(set)
        self._face_to_rolls: Dict[str, Set[str]] = defaultdict(set)

    # ── Write ─────────────────────────────────────────────────────────────────

    def record(self, roll_number: str, face_id: str) -> None:
        """Register a face_id → roll_number observation."""
        if not roll_number or not face_id:
            return
        self._roll_to_faces[roll_number].add(face_id)
        self._face_to_rolls[face_id].add(roll_number)
        logger.debug("[FaceHistory] Recorded face=%s for roll=%s", face_id, roll_number)

    # ── Read ──────────────────────────────────────────────────────────────────

    def get_faces_for_roll(self, roll_number: str) -> List[str]:
        """All face IDs seen for this roll number."""
        return list(self._roll_to_faces.get(roll_number, set()))

    def get_rolls_for_face(self, face_id: str) -> List[str]:
        """All roll numbers this face ID has been associated with."""
        return list(self._face_to_rolls.get(face_id, set()))

    def has_conflict_for_roll(self, roll_number: str) -> bool:
        """True if more than one distinct face ID has been seen for this roll."""
        return len(self._roll_to_faces.get(roll_number, set())) > 1

    def has_conflict_for_face(self, face_id: str) -> bool:
        """True if this face ID has been used with more than one roll number."""
        return len(self._face_to_rolls.get(face_id, set())) > 1

    def is_new_face_for_roll(self, roll_number: str, face_id: str) -> bool:
        """True if this face_id has never been seen for this roll number before."""
        return face_id not in self._roll_to_faces.get(roll_number, set())

    # ── Meta ──────────────────────────────────────────────────────────────────

    def reset(self) -> None:
        """Clear all history (use between exam sessions)."""
        self._roll_to_faces.clear()
        self._face_to_rolls.clear()
        logger.info("[FaceHistory] Store reset.")

    @property
    def total_observations(self) -> int:
        """Total number of recorded face observations."""
        return sum(len(faces) for faces in self._roll_to_faces.values())
