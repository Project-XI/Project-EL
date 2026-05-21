from __future__ import annotations

import asyncio
from typing import List, Optional

from src.services.voice.models.transcript_models import PlaybackRequest


class AudioQueue:
    """Queue-safe playback buffer for viva questions."""

    def __init__(self):
        self._queue: asyncio.Queue[PlaybackRequest] = asyncio.Queue()
        self._current_item: Optional[PlaybackRequest] = None

    async def enqueue(self, request: PlaybackRequest) -> None:
        await self._queue.put(request)

    async def dequeue(self) -> PlaybackRequest:
        request = await self._queue.get()
        self._current_item = request
        return request

    async def drain(self) -> List[PlaybackRequest]:
        drained: List[PlaybackRequest] = []
        while not self._queue.empty():
            drained.append(self._queue.get_nowait())
        return drained

    def clear(self) -> None:
        while not self._queue.empty():
            self._queue.get_nowait()
        self._current_item = None

    def pending_count(self) -> int:
        return self._queue.qsize()

    def current_item(self) -> Optional[PlaybackRequest]:
        return self._current_item
