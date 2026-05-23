from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .event_log import TranscriptEventLog
from .schemas import TranscriptEventKind, TranscriptEventRecord, TranscriptRecord, TranscriptTurnRecord
from .serializer import TranscriptSerializer


class TranscriptStore(ABC):
    """Storage interface for transcript records."""

    @abstractmethod
    def load(self, session_id: str) -> Optional[TranscriptRecord]:
        raise NotImplementedError

    @abstractmethod
    def save(self, record: TranscriptRecord) -> TranscriptRecord:
        raise NotImplementedError

    @abstractmethod
    def append_event(
        self,
        session_id: str,
        *,
        kind: TranscriptEventKind,
        step_id: str,
        payload: Dict[str, Any],
        evidence_links: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TranscriptEventRecord:
        raise NotImplementedError

    @abstractmethod
    def append_turn(self, turn: TranscriptTurnRecord) -> TranscriptTurnRecord:
        raise NotImplementedError

    @abstractmethod
    def export_json(self, session_id: str) -> str:
        raise NotImplementedError


class FileTranscriptStore(TranscriptStore):
    """File-backed transcript store with replay-safe JSON export."""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _path(self, session_id: str) -> Path:
        return self.base_path / f"{session_id}.transcript.json"

    def _empty_record(self, session_id: str) -> TranscriptRecord:
        return TranscriptRecord(session_id=session_id)

    def load(self, session_id: str) -> Optional[TranscriptRecord]:
        path = self._path(session_id)
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as file_obj:
            return TranscriptSerializer.load(file_obj)

    def _load_or_create(self, session_id: str) -> TranscriptRecord:
        return self.load(session_id) or self._empty_record(session_id)

    def _write_atomic(self, record: TranscriptRecord) -> None:
        path = self._path(record.session_id)
        temp_path = path.with_suffix(path.suffix + ".tmp")
        payload = TranscriptSerializer.dumps(record)
        temp_path.write_text(payload, encoding="utf-8")
        temp_path.replace(path)

    def save(self, record: TranscriptRecord) -> TranscriptRecord:
        updated = record.model_copy(update={"updated_at": datetime.utcnow()})
        self._write_atomic(updated)
        return updated

    def append_event(
        self,
        session_id: str,
        *,
        kind: TranscriptEventKind,
        step_id: str,
        payload: Dict[str, Any],
        evidence_links: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TranscriptEventRecord:
        record = self._load_or_create(session_id)
        event_log = TranscriptEventLog(session_id=session_id)
        for event in record.events:
            event_log._events.append(event)

        event = event_log.append(
            kind=kind,
            step_id=step_id,
            payload=payload,
            evidence_links=evidence_links,
            metadata=metadata,
        )
        record.events = event_log.events
        record.updated_at = event.created_at
        self._write_atomic(record)
        return event

    def append_turn(self, turn: TranscriptTurnRecord) -> TranscriptTurnRecord:
        record = self._load_or_create(turn.session_id)
        existing_index = next((index for index, existing in enumerate(record.turns) if existing.turn_id == turn.turn_id), None)
        turn = turn.model_copy(update={"updated_at": datetime.utcnow()})
        if existing_index is None:
            record.turns.append(turn)
        else:
            record.turns[existing_index] = turn
        record.updated_at = turn.updated_at
        self._write_atomic(record)
        return turn

    def update_turn(
        self,
        session_id: str,
        turn_id: str,
        *,
        question_text: Optional[str] = None,
        answer_text: Optional[str] = None,
        normalized_answer_text: Optional[str] = None,
        evaluation: Optional[Dict[str, Any]] = None,
        contradiction_events: Optional[List[Dict[str, Any]]] = None,
        fairness_events: Optional[List[Dict[str, Any]]] = None,
        follow_up_questions: Optional[List[str]] = None,
        evidence_links: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TranscriptTurnRecord:
        record = self._load_or_create(session_id)
        found = next((turn for turn in record.turns if turn.turn_id == turn_id), None)
        if found is None:
            found = TranscriptTurnRecord(
                turn_id=turn_id,
                session_id=session_id,
                step_id=turn_id,
                order_index=len(record.turns),
                question_text=question_text or "",
                answer_text=answer_text,
                normalized_answer_text=normalized_answer_text,
                evaluation=evaluation,
                contradiction_events=contradiction_events or [],
                fairness_events=fairness_events or [],
                follow_up_questions=follow_up_questions or [],
                evidence_links=evidence_links or [],
                metadata=metadata or {},
            )
            record.turns.append(found)
        else:
            if question_text is not None:
                found.question_text = question_text
            if answer_text is not None:
                found.answer_text = answer_text
            if normalized_answer_text is not None:
                found.normalized_answer_text = normalized_answer_text
            if evaluation is not None:
                found.evaluation = evaluation
            if contradiction_events is not None:
                found.contradiction_events = contradiction_events
            if fairness_events is not None:
                found.fairness_events = fairness_events
            if follow_up_questions is not None:
                found.follow_up_questions = follow_up_questions
            if evidence_links is not None:
                found.evidence_links = evidence_links
            if metadata is not None:
                found.metadata = metadata
            found.updated_at = datetime.utcnow()

        record.updated_at = found.updated_at
        self._write_atomic(record)
        return found

    def export_json(self, session_id: str) -> str:
        record = self._load_or_create(session_id)
        return TranscriptSerializer.dumps(record)
