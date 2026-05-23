from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from src.core.config import settings
from src.services.voice.models.transcript_models import FinalTranscript, TranscriptChunk
from src.services.voice.providers.base_provider import BaseTranscriptionProvider, TranscriptionProviderError


@dataclass
class _DeepgramConnectionState:
    socket: Any = None
    connected: bool = False
    reconnect_attempts: int = 0


class DeepgramProviderError(TranscriptionProviderError):
    pass


class DeepgramTranscriptionProvider(BaseTranscriptionProvider):
    """Streaming-safe Deepgram adapter that only transcribes audio.

    The provider buffers transmitted audio to support deterministic replay
    during reconnect attempts. It does not evaluate answers or drive viva logic.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        model: Optional[str] = None,
        language: Optional[str] = None,
        endpoint: Optional[str] = None,
        sample_rate_hz: Optional[int] = None,
        channels: Optional[int] = None,
        reconnect_attempts: int = 3,
        reconnect_backoff_seconds: float = 0.5,
        receive_timeout_seconds: float = 0.15,
    ):
        self.api_key = api_key or settings.DEEPGRAM_API_KEY
        self.model = model or settings.DEEPGRAM_MODEL
        self.language = language or settings.DEEPGRAM_LANGUAGE
        self.endpoint = endpoint or settings.DEEPGRAM_ENDPOINT
        self.sample_rate_hz = sample_rate_hz or settings.VOICE_SAMPLE_RATE_HZ
        self.channels = channels or settings.VOICE_CHANNELS
        self.reconnect_attempts = reconnect_attempts
        self.reconnect_backoff_seconds = reconnect_backoff_seconds
        self.receive_timeout_seconds = receive_timeout_seconds

        self._connection = _DeepgramConnectionState()
        self._audio_buffer: List[bytes] = []
        self._chunks: List[TranscriptChunk] = []
        self._session_id: Optional[str] = None

    def _build_uri(self) -> str:
        query = urlencode(
            {
                "model": self.model,
                "language": self.language,
                "encoding": "linear16",
                "sample_rate": str(self.sample_rate_hz),
                "channels": str(self.channels),
                "interim_results": "true",
                "smart_format": "true",
                "punctuate": "true",
            }
        )
        return f"{self.endpoint}?{query}"

    async def connect(self) -> None:
        if not self.api_key:
            raise DeepgramProviderError("Deepgram API key is required for voice transcription.")

        try:
            import websockets
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise DeepgramProviderError("The websockets package is required for Deepgram streaming.") from exc

        uri = self._build_uri()
        headers = {"Authorization": f"Token {self.api_key}"}

        try:
            try:
                socket = await websockets.connect(uri, additional_headers=headers, ping_interval=20, close_timeout=5)
            except TypeError:
                socket = await websockets.connect(uri, extra_headers=headers, ping_interval=20, close_timeout=5)
        except Exception as exc:  # pragma: no cover - network boundary
            raise DeepgramProviderError(f"Failed to connect to Deepgram: {exc}") from exc

        self._connection = _DeepgramConnectionState(socket=socket, connected=True, reconnect_attempts=0)

    async def _ensure_connection(self) -> None:
        if not self._connection.connected or self._connection.socket is None:
            await self.connect()

    async def _reconnect_and_replay(self) -> None:
        await self.close()
        await asyncio.sleep(self.reconnect_backoff_seconds)
        await self.connect()
        for chunk in self._audio_buffer:
            await self._connection.socket.send(chunk)

    async def _drain_events(self) -> List[TranscriptChunk]:
        events: List[TranscriptChunk] = []
        if not self._connection.socket:
            return events

        while True:
            try:
                message = await asyncio.wait_for(self._connection.socket.recv(), timeout=self.receive_timeout_seconds)
            except asyncio.TimeoutError:
                break
            except Exception as exc:  # pragma: no cover - network boundary
                raise DeepgramProviderError(f"Deepgram receive failed: {exc}") from exc

            if isinstance(message, bytes):
                continue

            try:
                payload = json.loads(message)
            except json.JSONDecodeError:
                continue

            chunk = self._parse_message(payload)
            if chunk is not None:
                events.append(chunk)
                self._chunks.append(chunk)

        return events

    def _parse_message(self, payload: Dict[str, Any]) -> Optional[TranscriptChunk]:
        channel = payload.get("channel") or {}
        alternatives = channel.get("alternatives") or []
        if not alternatives:
            return None

        transcript_text = alternatives[0].get("transcript", "").strip()
        if not transcript_text:
            return None

        confidence = float(alternatives[0].get("confidence") or 0.0)
        is_final = bool(payload.get("is_final") or payload.get("speech_final"))
        sequence_number = len(self._chunks) + 1

        return TranscriptChunk(
            session_id=self._session_id or "voice-session",
            sequence_number=sequence_number,
            raw_text=transcript_text,
            confidence=confidence,
            is_final=is_final,
            provider="deepgram",
            metadata={
                "deepgram": payload,
                "received_at": datetime.utcnow().isoformat(),
            },
        )

    async def transcribe_chunk(self, audio_bytes: bytes, *, sequence_number: int, is_final: bool = False) -> List[TranscriptChunk]:
        if not audio_bytes:
            return []

        self._audio_buffer.append(audio_bytes)
        await self._ensure_connection()

        try:
            await self._connection.socket.send(audio_bytes)
        except Exception:
            self._connection.connected = False
            await self._reconnect_and_replay()
            await self._connection.socket.send(audio_bytes)

        chunks = await self._drain_events()
        if is_final:
            await self.finalize_transcript()
        return chunks

    async def finalize_transcript(self) -> FinalTranscript:
        if self._connection.socket is None:
            raw_text = " ".join(chunk.raw_text for chunk in self._chunks).strip()
            confidence = self._aggregate_confidence()
            return FinalTranscript(
                session_id=self._session_id or "voice-session",
                raw_text=raw_text,
                confidence=confidence,
                provider="deepgram",
                chunk_count=len(self._chunks),
                metadata={"finalized_without_socket": True},
            )

        try:
            await self._connection.socket.close()
        except Exception as exc:  # pragma: no cover - network boundary
            raise DeepgramProviderError(f"Failed to close Deepgram socket cleanly: {exc}") from exc
        finally:
            self._connection.connected = False

        raw_text = " ".join(chunk.raw_text for chunk in self._chunks).strip()
        confidence = self._aggregate_confidence()
        return FinalTranscript(
            session_id=self._session_id or "voice-session",
            raw_text=raw_text,
            confidence=confidence,
            provider="deepgram",
            chunk_count=len(self._chunks),
            metadata={"finalized_at": datetime.utcnow().isoformat()},
        )

    def _aggregate_confidence(self) -> float:
        if not self._chunks:
            return 0.0
        return round(sum(chunk.confidence for chunk in self._chunks) / len(self._chunks), 4)

    async def close(self) -> None:
        socket = self._connection.socket
        self._connection.connected = False
        self._connection.socket = None
        if socket is not None:
            try:
                await socket.close()
            except Exception:
                pass

    def bind_session(self, session_id: str) -> None:
        self._session_id = session_id
