import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional

from ..models.session import VivaSession, TranscriptEntry

class StorageProvider(ABC):
    @abstractmethod
    def save_session(self, session: VivaSession):
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[VivaSession]:
        pass

    @abstractmethod
    def append_transcript(self, session_id: str, entry: TranscriptEntry):
        pass

class FileStorageProvider(StorageProvider):
    """Simple JSON-based file storage for development."""
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _session_file(self, session_id: str) -> Path:
        return self.base_path / f"{session_id}.json"

    def _load_record(self, session_id: str) -> Dict[str, Any]:
        path = self._session_file(session_id)
        if not path.exists():
            return {
                "session": None,
                "transcript": [],
                "artifacts": [],
                "state_transitions": [],
            }
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _save_record(self, session_id: str, record: Dict[str, Any]) -> None:
        path = self._session_file(session_id)
        with path.open("w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, sort_keys=True, default=str)

    def get_session_record(self, session_id: str) -> Dict[str, Any]:
        """Return raw persisted session record for audit and replay checks."""
        return self._load_record(session_id)
        
    def save_session(self, session: VivaSession):
        record = self._load_record(session.session_id)
        record["session"] = session.model_dump(mode="json")
        # Keep transcript mirrored under top-level for simple replay exports.
        record["transcript"] = [entry.model_dump(mode="json") for entry in session.transcript]
        self._save_record(session.session_id, record)
        
    def get_session(self, session_id: str) -> Optional[VivaSession]:
        record = self._load_record(session_id)
        payload = record.get("session")
        if not payload:
            return None
        return VivaSession.model_validate(payload)

    def append_transcript(self, session_id: str, entry: TranscriptEntry):
        record = self._load_record(session_id)
        record.setdefault("transcript", []).append(entry.model_dump(mode="json"))
        self._save_record(session_id, record)

    def append_artifact(self, session_id: str, artifact_type: str, payload: Dict[str, Any]) -> None:
        """Append deterministic per-turn artifacts for explainability and replay."""
        record = self._load_record(session_id)
        record.setdefault("artifacts", []).append(
            {
                "artifact_type": artifact_type,
                "payload": payload,
            }
        )
        self._save_record(session_id, record)

    def append_state_transition(self, session_id: str, payload: Dict[str, Any]) -> None:
        record = self._load_record(session_id)
        record.setdefault("state_transitions", []).append(payload)
        self._save_record(session_id, record)
