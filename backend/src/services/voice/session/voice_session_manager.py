from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional

from src.core.config import settings
from src.models.session import TranscriptEntry, VivaSession
from src.services.voice.models.transcript_models import (
    AudioFrame,
    FinalTranscript,
    PlaybackRequest,
    SilenceDetectionResult,
    TranscriptChunk,
    VoiceSessionPhase,
    VoiceSessionSnapshot,
    VoiceTurnTranscript,
)
from src.services.voice.playback.audio_queue import AudioQueue
from src.services.voice.playback.tts_provider import BaseTTSProvider, NullTTSProvider
from src.services.voice.providers.base_provider import BaseTranscriptionProvider
from src.services.voice.transcription.silence_detector import SilenceDetector
from src.services.voice.transcription.transcript_manager import TranscriptManager
from src.services.voice.transcription.transcript_normalizer import TranscriptNormalizer


TurnFinalizedCallback = Callable[[VoiceTurnTranscript], Awaitable[None] | None]


class VoiceSessionManager:
    """Turn-based voice orchestration support for MAIN Agent sessions.

    This manager captures the speech I/O lifecycle only. It does not evaluate
    answers, generate questions, or change viva strategy.
    """

    def __init__(
        self,
        *,
        transcription_provider: BaseTranscriptionProvider,
        tts_provider: Optional[BaseTTSProvider] = None,
        session: Optional[VivaSession] = None,
        session_id: Optional[str] = None,
        student_id: str = "unknown",
        transcript_manager: Optional[TranscriptManager] = None,
        normalizer: Optional[TranscriptNormalizer] = None,
        silence_detector: Optional[SilenceDetector] = None,
        on_turn_finalized: Optional[TurnFinalizedCallback] = None,
    ):
        if session is None and session_id is None:
            raise ValueError("Either session or session_id must be provided.")

        self.session = session or VivaSession(session_id=session_id or "voice-session", student_id=student_id)
        self.session_id = self.session.session_id
        self.transcription_provider = transcription_provider
        self.tts_provider = tts_provider or NullTTSProvider()
        self.audio_queue = AudioQueue()
        self.transcript_manager = transcript_manager or TranscriptManager(normalizer=normalizer or TranscriptNormalizer())
        self.silence_detector = silence_detector or SilenceDetector()
        self.on_turn_finalized = on_turn_finalized

        self.phase = VoiceSessionPhase.IDLE
        self._lock = asyncio.Lock()
        self._active_question_text: str = ""
        self._pending_audio_frames: List[AudioFrame] = []
        self._turn_index: int = 0
        self._last_finalized_turn: Optional[VoiceTurnTranscript] = None

        if hasattr(self.transcription_provider, "bind_session"):
            self.transcription_provider.bind_session(self.session_id)

    async def ask_question(self, question_text: str, *, metadata: Optional[Dict[str, Any]] = None) -> PlaybackRequest:
        request = PlaybackRequest(
            session_id=self.session_id,
            text=question_text,
            voice=settings.VOICE_PLAYBACK_VOICE,
            rate=settings.VOICE_PLAYBACK_RATE,
            metadata=metadata or {},
        )
        await self.audio_queue.enqueue(request)
        self.phase = VoiceSessionPhase.QUESTION_PLAYBACK
        self.session.transcript.append(TranscriptEntry(role="examiner", content=question_text))
        self._active_question_text = question_text
        self.transcript_manager.start_turn(question_text, session_id=self.session_id, metadata=metadata)

        playback_request = await self.audio_queue.dequeue()
        await self.tts_provider.speak(playback_request)
        self.phase = VoiceSessionPhase.LISTENING
        self._turn_index += 1
        return playback_request

    async def submit_audio_frame(self, audio_bytes: bytes, *, sequence_number: int, duration_seconds: float | None = None) -> List[TranscriptChunk]:
        async with self._lock:
            audio_frame = AudioFrame(
                session_id=self.session_id,
                sequence_number=sequence_number,
                payload_b64=self._encode_audio(audio_bytes),
                sample_rate_hz=settings.VOICE_SAMPLE_RATE_HZ,
                channels=settings.VOICE_CHANNELS,
            )
            self._pending_audio_frames.append(audio_frame)
            self.phase = VoiceSessionPhase.TRANSCRIBING

            silence_result = self.silence_detector.analyze(audio_bytes, duration_seconds=duration_seconds)
            transcript_chunks = await self.transcription_provider.transcribe_chunk(
                audio_bytes,
                sequence_number=sequence_number,
                is_final=silence_result.should_finalize,
            )
            for chunk in transcript_chunks:
                self.transcript_manager.append_chunk(chunk)

            if silence_result.should_finalize:
                await self._finalize_response_locked(silence_result=silence_result)

            return transcript_chunks

    async def finalize_response(
        self,
        *,
        final_transcript: Optional[FinalTranscript] = None,
        silence_result: Optional[SilenceDetectionResult] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> VoiceTurnTranscript:
        async with self._lock:
            if self._last_finalized_turn is not None and final_transcript is None:
                turn = self._last_finalized_turn
                self._last_finalized_turn = None
                return turn

            return await self._finalize_response_locked(
                final_transcript=final_transcript,
                silence_result=silence_result,
                metadata=metadata,
            )

    def snapshot(self) -> VoiceSessionSnapshot:
        return VoiceSessionSnapshot(
            session_id=self.session_id,
            phase=self.phase,
            active_question=self._active_question_text or None,
            turn_count=len(self.transcript_manager.turn_history()),
            queued_question_count=self.audio_queue.pending_count(),
            completed_turn_count=len(self.transcript_manager.turn_history()),
            pending_audio_frame_count=len(self._pending_audio_frames),
            last_updated=datetime.utcnow(),
            metadata={"session_status": self.session.status},
        )

    async def cleanup(self) -> None:
        await self.transcription_provider.close()
        self.audio_queue.clear()
        self.silence_detector.reset()
        self.phase = VoiceSessionPhase.IDLE

    def _encode_audio(self, audio_bytes: bytes) -> str:
        import base64

        return base64.b64encode(audio_bytes).decode("utf-8")

    async def _finalize_response_locked(
        self,
        *,
        final_transcript: Optional[FinalTranscript] = None,
        silence_result: Optional[SilenceDetectionResult] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> VoiceTurnTranscript:
        self.phase = VoiceSessionPhase.FINALIZING

        if final_transcript is None:
            final_transcript = await self.transcription_provider.finalize_transcript()

        turn = self.transcript_manager.finalize_turn(
            session_id=self.session_id,
            final_transcript=final_transcript,
            silence_detected=bool(silence_result and silence_result.should_finalize),
            metadata=metadata or {
                "turn_index": self._turn_index,
                "pending_audio_frames": len(self._pending_audio_frames),
            },
        )

        self.session.transcript.append(TranscriptEntry(role="student", content=turn.normalized_transcript.normalized_text))
        self.session.status = "active"
        self.phase = VoiceSessionPhase.READY_FOR_MAIN
        self._pending_audio_frames = []
        self._active_question_text = ""

        if self.on_turn_finalized is not None:
            callback_result = self.on_turn_finalized(turn)
            if asyncio.iscoroutine(callback_result):
                await callback_result

        self._last_finalized_turn = turn
        return turn
