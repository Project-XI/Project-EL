from __future__ import annotations

import base64
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class VoiceSessionPhase(str, Enum):
    IDLE = "idle"
    QUESTION_PLAYBACK = "question_playback"
    LISTENING = "listening"
    TRANSCRIBING = "transcribing"
    FINALIZING = "finalizing"
    READY_FOR_MAIN = "ready_for_main"
    COMPLETED = "completed"
    ERROR = "error"


class TranscriptCorrection(BaseModel):
    source_text: str
    normalized_text: str
    reason: str
    rule_name: str


class AudioFrame(BaseModel):
    session_id: str
    sequence_number: int
    payload_b64: str
    sample_rate_hz: int = 16000
    channels: int = 1
    mime_type: str = "audio/l16"
    is_final: bool = False
    captured_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_bytes(self) -> bytes:
        return base64.b64decode(self.payload_b64)


class TranscriptChunk(BaseModel):
    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    sequence_number: int
    raw_text: str
    confidence: float = 0.0
    is_final: bool = False
    provider: str = "deepgram"
    normalized_text: Optional[str] = None
    corrections: List[TranscriptCorrection] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FinalTranscript(BaseModel):
    session_id: str
    raw_text: str
    confidence: float = 0.0
    provider: str = "deepgram"
    chunk_count: int = 0
    is_final: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    finalized_at: datetime = Field(default_factory=datetime.utcnow)


class NormalizedTranscript(BaseModel):
    session_id: str
    raw_text: str
    normalized_text: str
    confidence: float = 0.0
    normalized_confidence: float = 0.0
    corrections: List[TranscriptCorrection] = Field(default_factory=list)
    applied_rules: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    normalized_at: datetime = Field(default_factory=datetime.utcnow)


class PlaybackRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    text: str
    voice: str = "Samantha"
    rate: int = 180
    enqueued_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PlaybackResult(BaseModel):
    request_id: str
    provider: str
    success: bool = True
    message: str = ""
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    audio_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SilenceDetectionResult(BaseModel):
    is_silent: bool
    rms: float
    duration_seconds: float
    accumulated_silence_seconds: float
    threshold_rms: float
    should_finalize: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VoiceTurnTranscript(BaseModel):
    turn_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    question_text: str
    raw_transcript: str
    normalized_transcript: NormalizedTranscript
    chunks: List[TranscriptChunk] = Field(default_factory=list)
    silence_detected: bool = False
    finalized_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VoiceSessionSnapshot(BaseModel):
    session_id: str
    phase: VoiceSessionPhase
    active_question: Optional[str] = None
    turn_count: int = 0
    queued_question_count: int = 0
    completed_turn_count: int = 0
    pending_audio_frame_count: int = 0
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
