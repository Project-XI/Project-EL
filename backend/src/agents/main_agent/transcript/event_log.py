from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from .schemas import TranscriptEventKind, TranscriptEventRecord


class TranscriptEventLog:
    """Ordered event log for explainable viva persistence."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._events: List[TranscriptEventRecord] = []

    @property
    def events(self) -> List[TranscriptEventRecord]:
        return list(self._events)

    def append(
        self,
        *,
        kind: TranscriptEventKind,
        step_id: str,
        payload: Dict[str, Any],
        evidence_links: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TranscriptEventRecord:
        event = TranscriptEventRecord(
            event_id=str(uuid.uuid4()),
            session_id=self.session_id,
            step_id=step_id,
            order_index=len(self._events),
            kind=kind,
            payload=payload,
            evidence_links=evidence_links or [],
            created_at=datetime.utcnow(),
            metadata=metadata or {},
        )
        self._events.append(event)
        return event
