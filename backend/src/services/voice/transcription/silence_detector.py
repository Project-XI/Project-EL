from __future__ import annotations

import math
import struct
from dataclasses import dataclass

from src.core.config import settings
from src.services.voice.models.transcript_models import SilenceDetectionResult


@dataclass
class SilenceDetectorState:
    accumulated_silence_seconds: float = 0.0


class SilenceDetector:
    """Deterministic silence detector for turn-based viva responses."""

    def __init__(
        self,
        threshold_rms: int | None = None,
        min_silence_seconds: float | None = None,
        sample_rate_hz: int | None = None,
        channels: int | None = None,
        sample_width_bytes: int = 2,
    ):
        self.threshold_rms = threshold_rms or settings.VOICE_SILENCE_RMS_THRESHOLD
        self.min_silence_seconds = min_silence_seconds or settings.VOICE_SILENCE_SECONDS
        self.sample_rate_hz = sample_rate_hz or settings.VOICE_SAMPLE_RATE_HZ
        self.channels = channels or settings.VOICE_CHANNELS
        self.sample_width_bytes = sample_width_bytes
        self._state = SilenceDetectorState()

    def reset(self) -> None:
        self._state = SilenceDetectorState()

    def analyze(self, pcm_bytes: bytes, *, duration_seconds: float | None = None) -> SilenceDetectionResult:
        if not pcm_bytes:
            duration = duration_seconds or 0.0
            self._state.accumulated_silence_seconds += duration
            return SilenceDetectionResult(
                is_silent=True,
                rms=0.0,
                duration_seconds=duration,
                accumulated_silence_seconds=self._state.accumulated_silence_seconds,
                threshold_rms=float(self.threshold_rms),
                should_finalize=self._state.accumulated_silence_seconds >= self.min_silence_seconds,
            )

        rms = self._calculate_rms(pcm_bytes)
        duration = duration_seconds
        if duration is None:
            frame_count = len(pcm_bytes) / (self.sample_width_bytes * max(self.channels, 1))
            duration = frame_count / float(self.sample_rate_hz)

        is_silent = rms <= self.threshold_rms
        if is_silent:
            self._state.accumulated_silence_seconds += duration
        else:
            self._state.accumulated_silence_seconds = 0.0

        return SilenceDetectionResult(
            is_silent=is_silent,
            rms=rms,
            duration_seconds=duration,
            accumulated_silence_seconds=self._state.accumulated_silence_seconds,
            threshold_rms=float(self.threshold_rms),
            should_finalize=self._state.accumulated_silence_seconds >= self.min_silence_seconds,
        )

    def _calculate_rms(self, pcm_bytes: bytes) -> float:
        if self.sample_width_bytes != 2:
            raise ValueError("VoiceInfrastructureV1 currently expects 16-bit PCM audio chunks.")

        usable_length = len(pcm_bytes) - (len(pcm_bytes) % self.sample_width_bytes)
        if usable_length <= 0:
            return 0.0

        total = 0.0
        sample_count = 0
        for (sample,) in struct.iter_unpack("<h", pcm_bytes[:usable_length]):
            total += float(sample * sample)
            sample_count += 1

        if sample_count == 0:
            return 0.0

        return math.sqrt(total / sample_count)
