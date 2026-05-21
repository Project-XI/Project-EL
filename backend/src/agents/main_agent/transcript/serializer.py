from __future__ import annotations

import json
from typing import Any

from .schemas import TranscriptRecord


class TranscriptSerializer:
    """Stable JSON serializer for transcript persistence records."""

    @staticmethod
    def dumps(record: TranscriptRecord) -> str:
        return json.dumps(record.model_dump(mode="json"), indent=2, sort_keys=True, ensure_ascii=True)

    @staticmethod
    def dump(record: TranscriptRecord, file_obj: Any) -> None:
        json.dump(record.model_dump(mode="json"), file_obj, indent=2, sort_keys=True, ensure_ascii=True)

    @staticmethod
    def loads(payload: str) -> TranscriptRecord:
        data = json.loads(payload)
        return TranscriptRecord.model_validate(data)

    @staticmethod
    def load(file_obj: Any) -> TranscriptRecord:
        return TranscriptRecord.model_validate(json.load(file_obj))
