from __future__ import annotations

import asyncio
import shutil
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from src.core.config import settings
from src.services.voice.models.transcript_models import PlaybackRequest, PlaybackResult


class BaseTTSProvider(ABC):
    @abstractmethod
    async def speak(self, request: PlaybackRequest) -> PlaybackResult:
        raise NotImplementedError


class NullTTSProvider(BaseTTSProvider):
    async def speak(self, request: PlaybackRequest) -> PlaybackResult:
        return PlaybackResult(
            request_id=request.request_id,
            provider="null",
            success=True,
            message="Playback skipped by null provider.",
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow(),
        )


class SystemTTSProvider(BaseTTSProvider):
    """Deterministic local playback provider.

    On macOS, this uses the built-in `say` command with a neutral professional
    voice. It is intentionally simple so playback stays auditable and queue-safe.
    """

    def __init__(self, voice: Optional[str] = None, rate: Optional[int] = None):
        self.voice = voice or settings.VOICE_PLAYBACK_VOICE
        self.rate = rate or settings.VOICE_PLAYBACK_RATE

    async def speak(self, request: PlaybackRequest) -> PlaybackResult:
        if not shutil.which("say"):
            return await NullTTSProvider().speak(request)

        started_at = datetime.utcnow()
        process = await asyncio.create_subprocess_exec(
            "say",
            "-v",
            request.voice or self.voice,
            "-r",
            str(request.rate or self.rate),
            request.text,
        )
        return_code = await process.wait()
        finished_at = datetime.utcnow()

        return PlaybackResult(
            request_id=request.request_id,
            provider="system.say",
            success=return_code == 0,
            message="Playback completed." if return_code == 0 else f"Playback failed with code {return_code}.",
            started_at=started_at,
            finished_at=finished_at,
            metadata={"voice": request.voice or self.voice, "rate": request.rate or self.rate},
        )
