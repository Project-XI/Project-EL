from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.services.voice.models.transcript_models import (
    FinalTranscript,
    NormalizedTranscript,
    TranscriptChunk,
    VoiceTurnTranscript,
)
from src.services.voice.transcription.transcript_normalizer import TranscriptNormalizer


class TranscriptManager:
    """Aggregate and normalize transcript chunks for a single viva turn."""

    def __init__(self, normalizer: Optional[TranscriptNormalizer] = None):
        self.normalizer = normalizer or TranscriptNormalizer()
        self._turn_history: List[VoiceTurnTranscript] = []
        self._active_turn_id: Optional[str] = None
        self._active_question_text: str = ""
        self._active_chunks: List[TranscriptChunk] = []

    def start_turn(self, question_text: str, *, session_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        self._active_turn_id = str(uuid.uuid4())
        self._active_question_text = question_text
        self._active_chunks = []
        return self._active_turn_id

    def append_chunk(self, chunk: TranscriptChunk) -> TranscriptChunk:
        normalized = self.normalizer.normalize(chunk.raw_text, confidence=chunk.confidence, session_id=chunk.session_id)
        enriched_chunk = chunk.model_copy(
            update={
                "normalized_text": normalized.normalized_text,
                "corrections": normalized.corrections,
                "metadata": {**chunk.metadata, "normalized": True, "applied_rules": normalized.applied_rules},
            }
        )
        self._active_chunks.append(enriched_chunk)
        return enriched_chunk

    def finalize_turn(
        self,
        *,
        session_id: str,
        final_transcript: Optional[FinalTranscript] = None,
        silence_detected: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> VoiceTurnTranscript:
        if self._active_turn_id is None:
            self.start_turn("", session_id=session_id)

        chunks = list(self._active_chunks)
        if final_transcript is not None and final_transcript.raw_text:
            normalized = self.normalizer.normalize(
                final_transcript.raw_text,
                confidence=final_transcript.confidence,
                session_id=session_id,
            )
        else:
            combined_text = " ".join(chunk.normalized_text or chunk.raw_text for chunk in chunks).strip()
            combined_confidence = self._average_confidence(chunks)
            normalized = self.normalizer.normalize(combined_text, confidence=combined_confidence, session_id=session_id)

        turn = VoiceTurnTranscript(
            turn_id=self._active_turn_id or str(uuid.uuid4()),
            session_id=session_id,
            question_text=self._active_question_text,
            raw_transcript=normalized.raw_text,
            normalized_transcript=normalized,
            chunks=chunks,
            silence_detected=silence_detected,
            finalized_at=datetime.utcnow(),
            metadata=metadata or {},
        )
        self._turn_history.append(turn)
        self._active_turn_id = None
        self._active_question_text = ""
        self._active_chunks = []
        return turn

    def current_turn_chunks(self) -> List[TranscriptChunk]:
        return list(self._active_chunks)

    def turn_history(self) -> List[VoiceTurnTranscript]:
        return list(self._turn_history)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "turn_count": len(self._turn_history),
            "active_turn_id": self._active_turn_id,
            "active_question_text": self._active_question_text,
            "active_chunk_count": len(self._active_chunks),
        }

    def reset(self) -> None:
        self._turn_history = []
        self._active_turn_id = None
        self._active_question_text = ""
        self._active_chunks = []

    def _average_confidence(self, chunks: List[TranscriptChunk]) -> float:
        if not chunks:
            return 0.0
        return round(sum(chunk.confidence for chunk in chunks) / len(chunks), 4)
