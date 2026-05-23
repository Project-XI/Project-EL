"""Voice infrastructure for turn-based viva sessions.

This package provides deterministic speech capture, transcription,
normalization, playback, and voice-session coordination primitives.
"""

from .models.transcript_models import (
    AudioFrame,
    FinalTranscript,
    NormalizedTranscript,
    PlaybackRequest,
    PlaybackResult,
    SilenceDetectionResult,
    TranscriptChunk,
    TranscriptCorrection,
    VoiceSessionPhase,
    VoiceSessionSnapshot,
    VoiceTurnTranscript,
)
from .playback.audio_queue import AudioQueue
from .playback.tts_provider import BaseTTSProvider, NullTTSProvider, SystemTTSProvider
from .providers.base_provider import BaseTranscriptionProvider
from .providers.deepgram_provider import DeepgramTranscriptionProvider
from .session.voice_session_manager import VoiceSessionManager
from .transcription.silence_detector import SilenceDetector
from .transcription.transcript_manager import TranscriptManager
from .transcription.transcript_normalizer import TranscriptNormalizer
