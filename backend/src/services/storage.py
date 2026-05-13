from abc import ABC, abstractmethod
from typing import Optional, List
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
        self.base_path = base_path
        # Ensure path exists (placeholder)
        
    def save_session(self, session: VivaSession):
        print(f"Saving session {session.session_id} to {self.base_path}")
        # In implementation: json.dump(session.dict(), file)
        
    def get_session(self, session_id: str) -> Optional[VivaSession]:
        # In implementation: json.load(file)
        return None

    def append_transcript(self, session_id: str, entry: TranscriptEntry):
        print(f"Appending transcript for {session_id}: {entry.role}: {entry.content[:20]}...")
