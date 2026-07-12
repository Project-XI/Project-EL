from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class IdentityRecord:
    record_id: str
    roll_number: str
    embedding_hash: str
    session_id: str
    exam_timestamp: datetime
    verification_result: str
    confidence: float
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "roll_number": self.roll_number,
            "embedding_hash": self.embedding_hash,
            "session_id": self.session_id,
            "exam_timestamp": self.exam_timestamp.isoformat(),
            "verification_result": self.verification_result,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
        }


class IdentityHistoryStore:
    def __init__(self):
        self._records: Dict[str, IdentityRecord] = {}
        self._roll_index: Dict[str, List[str]] = {}

    def _hash_embedding(self, embedding: List[float]) -> str:
        return hashlib.sha256(json.dumps(embedding, sort_keys=True).encode()).hexdigest()[:16]

    def _generate_record_id(self, roll_number: str, session_id: str, timestamp: datetime) -> str:
        raw = f"{timestamp.isoformat()}:{roll_number}:{session_id}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def add_record(
        self,
        roll_number: str,
        embedding: List[float],
        session_id: str,
        exam_timestamp: Optional[datetime] = None,
        verification_result: str = "verified",
        confidence: float = 1.0,
    ) -> IdentityRecord:
        timestamp = exam_timestamp or datetime.now(timezone.utc)
        record_id = self._generate_record_id(roll_number, session_id, timestamp)
        embedding_hash = self._hash_embedding(embedding)

        record = IdentityRecord(
            record_id=record_id,
            roll_number=roll_number,
            embedding_hash=embedding_hash,
            session_id=session_id,
            exam_timestamp=timestamp,
            verification_result=verification_result,
            confidence=confidence,
        )

        self._records[record_id] = record
        if roll_number not in self._roll_index:
            self._roll_index[roll_number] = []
        self._roll_index[roll_number].append(record_id)

        return record

    def get_history_for_roll(self, roll_number: str) -> List[IdentityRecord]:
        record_ids = self._roll_index.get(roll_number, [])
        return [self._records[rid] for rid in record_ids]

    def get_record(self, record_id: str) -> Optional[IdentityRecord]:
        return self._records.get(record_id)

    def get_all_records(self) -> List[IdentityRecord]:
        return list(self._records.values())

    def get_sessions_for_roll(self, roll_number: str) -> List[str]:
        records = self.get_history_for_roll(roll_number)
        return [r.session_id for r in records]

    def get_records_by_session(self, session_id: str) -> List[IdentityRecord]:
        return [r for r in self._records.values() if r.session_id == session_id]

    def get_verification_events(self, roll_number: Optional[str] = None) -> List[Dict[str, Any]]:
        records = self.get_all_records()
        if roll_number:
            records = [r for r in records if r.roll_number == roll_number]
        return [
            {
                "roll_number": r.roll_number,
                "session_id": r.session_id,
                "exam_timestamp": r.exam_timestamp.isoformat(),
                "verification_result": r.verification_result,
                "confidence": r.confidence,
            }
            for r in sorted(records, key=lambda x: x.exam_timestamp)
        ]

    def get_embedding_hashes_for_roll(self, roll_number: str) -> List[str]:
        records = self.get_history_for_roll(roll_number)
        return [r.embedding_hash for r in records]

    def has_embedding(self, embedding_hash: str) -> bool:
        return any(r.embedding_hash == embedding_hash for r in self._records.values())

    def count(self) -> int:
        return len(self._records)

    def clear(self):
        self._records.clear()
        self._roll_index.clear()