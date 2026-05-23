from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from src.services.voice.models.transcript_models import FinalTranscript, TranscriptChunk


class TranscriptionProviderError(RuntimeError):
    """Raised when a transcription provider cannot complete its work."""


class BaseTranscriptionProvider(ABC):
    """Abstract transcription provider for streaming-safe viva input."""

    @abstractmethod
    async def connect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def transcribe_chunk(self, audio_bytes: bytes, *, sequence_number: int, is_final: bool = False) -> List[TranscriptChunk]:
        raise NotImplementedError

    @abstractmethod
    async def finalize_transcript(self) -> FinalTranscript:
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError
