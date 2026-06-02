"""
history_checker.py
──────────────────
Face history checker for the GATEKEEPER pipeline.

Responsibilities
────────────────
- Check whether a face is new for a given roll number.
- Detect conflicting faces already recorded in history.
- Return a typed HistoryCheckResult.

Rules
─────
- Reads from FaceHistoryStore — does not write (pipeline does the write).
- Stateless logic — store injected at construction.
- Never raises.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List

from .history_store import FaceHistoryStore

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HistoryCheckResult:
    """
    Result of a face history check for one (roll_number, face_id) pair.

    Fields
    ──────
    roll_number         : The roll number checked.
    face_id             : The face ID checked.
    is_new_face         : True if this face_id was never seen for this roll.
    conflict_face_ids   : Other face IDs already recorded for this roll.
    is_cloned_face      : True if this face_id is already used by another roll.
    clone_roll_numbers  : Roll numbers this face_id has appeared under before.
    """
    roll_number:        str
    face_id:            str
    is_new_face:        bool
    conflict_face_ids:  List[str]  = field(default_factory=list)
    is_cloned_face:     bool       = False
    clone_roll_numbers: List[str]  = field(default_factory=list)

    @property
    def has_any_conflict(self) -> bool:
        """True if either a face-swap or a face-clone conflict was detected."""
        return bool(self.conflict_face_ids) or self.is_cloned_face

    def to_dict(self) -> dict:
        return {
            "roll_number":        self.roll_number,
            "face_id":            self.face_id,
            "is_new_face":        self.is_new_face,
            "conflict_face_ids":  self.conflict_face_ids,
            "is_cloned_face":     self.is_cloned_face,
            "clone_roll_numbers": self.clone_roll_numbers,
            "has_any_conflict":   self.has_any_conflict,
        }


class FaceHistoryChecker:
    """
    Checks a (roll_number, face_id) pair against recorded history.

    Usage
    ─────
        checker = FaceHistoryChecker(store)
        result  = checker.check("150096725066", "photos/150096725066.jpg")
        if result.has_any_conflict:
            # escalate to conflict detector
    """

    def __init__(self, store: FaceHistoryStore) -> None:
        self._store = store

    def check(self, roll_number: str, face_id: str) -> HistoryCheckResult:
        """
        Check history for face-swap and face-clone signals.

        Face-swap  : roll_number already has a different face recorded.
        Face-clone : face_id already appeared under a different roll number.
        """
        is_new_face = self._store.is_new_face_for_roll(roll_number, face_id)

        # Conflict type 1 — face swap: roll already has different faces
        existing_faces_for_roll = self._store.get_faces_for_roll(roll_number)
        conflict_faces = [f for f in existing_faces_for_roll if f != face_id]

        # Conflict type 2 — face clone: this face used with other rolls
        rolls_for_this_face = self._store.get_rolls_for_face(face_id)
        clone_rolls = [r for r in rolls_for_this_face if r != roll_number]
        is_cloned_face = len(clone_rolls) > 0

        if conflict_faces:
            logger.warning(
                "[FaceHistory] Face-swap signal: roll=%s new_face=%s, existing=%s",
                roll_number, face_id, conflict_faces
            )
        if is_cloned_face:
            logger.warning(
                "[FaceHistory] Face-clone signal: face=%s already seen under rolls=%s",
                face_id, clone_rolls
            )

        return HistoryCheckResult(
            roll_number        = roll_number,
            face_id            = face_id,
            is_new_face        = is_new_face,
            conflict_face_ids  = conflict_faces,
            is_cloned_face     = is_cloned_face,
            clone_roll_numbers = clone_rolls,
        )
