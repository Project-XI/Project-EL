"""
TranscriptEntry and related record types for the viva session transcript.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional


class TranscriptEntry:
    """
    A single named-blob in the viva transcript (plain class, no dataclass
    so callers can freely mutate fields between turn cycles).

    Parameters
    ----------
    role:
        ``"examiner"`` or ``"candidate"``.
    content:
        The text spoken / written in this turn.
    turn_index:
        Zero-based sequential index in the session.
    topic:
        The knowledge topic this turn touches.
    quality_score:
        Optional float 0.0 – 1.0 assigned by ORACLE (examining agent only).
    is_follow_up:
        ``True`` when this question is a direct follow-up of a prior turn.
    parent_turn_index:
        The turn this question follows from (relevant only for follow-ups).
    metadata:
        Free-form extension bucket.
    """

    def __init__(
        self,
        role: str,
        content: str,
        turn_index: int,
        topic: Optional[str] = None,
        quality_score: Optional[float] = None,
        is_follow_up: bool = False,
        parent_turn_index: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.role = role
        self.content = content
        self.turn_index = turn_index
        self.topic = topic
        self.quality_score = quality_score
        self.is_follow_up = is_follow_up
        self.parent_turn_index = parent_turn_index
        self.metadata: Dict[str, Any] = metadata if metadata is not None else {}

    # ── Factory helpers ────────────────────────────────────────────────────

    @staticmethod
    def examiner_question(
        text: str,
        turn_index: int,
        **kwargs: Any,
    ) -> "TranscriptEntry":
        return TranscriptEntry(
            role="examiner",
            content=text,
            turn_index=turn_index,
            is_follow_up=kwargs.pop("is_follow_up", False),
            parent_turn_index=kwargs.pop("parent_turn_index", None),
            topic=kwargs.pop("topic", None),
            metadata=kwargs,
        )

    @staticmethod
    def candidate_response(
        text: str,
        turn_index: int,
        **kwargs: Any,
    ) -> "TranscriptEntry":
        return TranscriptEntry(
            role="candidate",
            content=text,
            turn_index=turn_index,
            quality_score=kwargs.pop("quality_score", None),
            topic=kwargs.pop("topic", None),
            metadata=kwargs,
        )

    # ── Serialisation ──────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "turn_index": self.turn_index,
            "topic": self.topic,
            "quality_score": self.quality_score,
            "is_follow_up": self.is_follow_up,
            "parent_turn_index": self.parent_turn_index,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TranscriptEntry":
        return cls(
            role=data["role"],
            content=data["content"],
            turn_index=data["turn_index"],
            topic=data.get("topic"),
            quality_score=data.get("quality_score"),
            is_follow_up=data.get("is_follow_up", False),
            parent_turn_index=data.get("parent_turn_index"),
            metadata=dict(data.get("metadata", {})),
        )

    def __repr__(self) -> str:
        return (
            f"TranscriptEntry(role={self.role!r}, turn_index={self.turn_index}, "
            f"topic={self.topic!r}, is_follow_up={self.is_follow_up})"
        )
