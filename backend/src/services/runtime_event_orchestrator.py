"""
Runtime Event Flow Orchestrator — Stages 4-6

Comprehensive event emission and coordination for:
- Stage 4: ORACLE Intelligence Handoff
- Stage 5: MAIN Agent Live Viva
- Stage 6: Voice Infrastructure

All events are:
- Deterministic and reproducible
- Audit-safe with timestamps
- Session-bound for traceability
- Explainable with structured payloads
"""

from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from enum import Enum

from src.models.events import EventType, PlatformEvent
from src.models.intelligence_artifact import IntelligenceArtifact
from src.services.storage import FileStorageProvider


class EventEmitter:
    """
    Central event emitter for viva pipeline.

    Coordinates event propagation across all stages.
    """

    def __init__(self, storage_provider: Optional[FileStorageProvider] = None):
        import os
        if storage_provider is None:
            base_path = os.path.join(os.getcwd(), "session_storage", "events")
            os.makedirs(base_path, exist_ok=True)
            storage_provider = FileStorageProvider(base_path)
        self.storage = storage_provider
        self.event_log: List[PlatformEvent] = []
        self.subscribers: Dict[EventType, List[Callable]] = {}

    def subscribe(self, event_type: EventType, callback: Callable) -> None:
        """Subscribe to event type."""

        if event_type not in self.subscribers:
            self.subscribers[event_type] = []

        self.subscribers[event_type].append(callback)

    async def emit(
        self,
        session_id: str,
        event_type: EventType,
        payload: Dict[str, Any],
        agent_name: str = "VivaPipeline",
    ) -> PlatformEvent:
        """
        Emit structured event.

        Performs:
        - Event creation with timestamp
        - Persistence to session storage
        - Callback notifications
        - Event logging for audit trail
        """

        event = PlatformEvent(
            session_id=session_id,
            agent_name=agent_name,
            event_type=event_type,
            payload=payload,
            metadata={
                "timestamp_iso": datetime.utcnow().isoformat(),
                "event_sequence": len(self.event_log),
            },
        )

        # Log event
        self.event_log.append(event)

        # Persist to storage
        await self._persist_event(session_id, event)

        # Notify subscribers
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    await callback(event) if hasattr(callback, "__await__") else callback(event)
                except Exception as e:
                    print(f"Subscriber callback error: {e}")

        return event

    async def _persist_event(self, session_id: str, event: PlatformEvent) -> None:
        """Persist event to session storage."""

        event_data = event.model_dump_json(indent=2)

        event_filename = f"event_{event.event_id}_{event.event_type}.json"

        self.storage.append_artifact(
            session_id=session_id,
            artifact_type="RUNTIME_EVENT",
            payload={
                "event_id": event.event_id,
                "event_type": event.event_type,
                "agent": event.agent_name,
                "timestamp": event.timestamp.isoformat(),
                "payload": event.payload,
            },
        )


class Stage4EventCoordinator:
    """Coordinates event emission for Stage 4: ORACLE → MAIN Handoff."""

    def __init__(self, event_emitter: EventEmitter):
        self.emitter = event_emitter

    async def emit_oracle_analysis_started(self, session_id: str) -> PlatformEvent:
        """ORACLE analysis beginning."""

        return await self.emitter.emit(
            session_id=session_id,
            event_type=EventType.ORACLE_ANALYSIS_STARTED,
            payload={"stage": "4", "status": "starting"},
            agent_name="OracleAgent",
        )

    async def emit_oracle_analysis_complete(
        self, session_id: str, artifact: IntelligenceArtifact
    ) -> PlatformEvent:
        """ORACLE analysis complete, artifact ready."""

        return await self.emitter.emit(
            session_id=session_id,
            event_type=EventType.ORACLE_INTELLIGENCE_READY,
            payload={
                "artifact_id": artifact.artifact_id,
                "project_name": artifact.project_name,
                "num_viva_targets": len(artifact.viva_targets),
                "num_failure_scenarios": len(artifact.failure_scenarios),
                "num_weak_points": len(artifact.weak_points),
                "analysis_confidence": artifact.analysis_confidence,
                "next_stage": "MAIN_AGENT_START_VIVA",
            },
            agent_name="OracleAgent",
        )


class Stage5EventCoordinator:
    """Coordinates event emission for Stage 5: MAIN Agent Live Viva."""

    def __init__(self, event_emitter: EventEmitter):
        self.emitter = event_emitter

    async def emit_viva_session_started(self, session_id: str) -> PlatformEvent:
        """Viva session started."""

        return await self.emitter.emit(
            session_id=session_id,
            event_type=EventType.VIVA_SESSION_STARTED,
            payload={
                "stage": "5",
                "status": "started",
                "timestamp": datetime.utcnow().isoformat(),
            },
            agent_name="MainAgent",
        )

    async def emit_question_asked(
        self, session_id: str, target_id: str, question: str, difficulty: str
    ) -> PlatformEvent:
        """Question asked to student."""

        return await self.emitter.emit(
            session_id=session_id,
            event_type=EventType.VIVA_QUESTION_ASKED,
            payload={
                "target_id": target_id,
                "question": question,
                "difficulty": difficulty,
            },
            agent_name="MainAgent",
        )

    async def emit_response_received(
        self, session_id: str, target_id: str, response_text: str
    ) -> PlatformEvent:
        """Student response received."""

        return await self.emitter.emit(
            session_id=session_id,
            event_type=EventType.VIVA_RESPONSE_RECEIVED,
            payload={
                "target_id": target_id,
                "response_length": len(response_text),
                "timestamp": datetime.utcnow().isoformat(),
            },
            agent_name="MainAgent",
        )

    async def emit_evaluation_complete(
        self,
        session_id: str,
        target_id: str,
        depth_level: str,
        coverage_score: float,
        red_flags: List[str],
    ) -> PlatformEvent:
        """Answer evaluation complete."""

        return await self.emitter.emit(
            session_id=session_id,
            event_type=EventType.VIVA_EVALUATION_COMPLETE,
            payload={
                "target_id": target_id,
                "depth_level": depth_level,
                "coverage_score": coverage_score,
                "red_flags_count": len(red_flags),
                "has_red_flags": len(red_flags) > 0,
            },
            agent_name="MainAgent",
        )

    async def emit_follow_up_generated(
        self, session_id: str, target_id: str, follow_up_question: str
    ) -> PlatformEvent:
        """Adaptive follow-up generated."""

        return await self.emitter.emit(
            session_id=session_id,
            event_type=EventType.VIVA_FOLLOW_UP_GENERATED,
            payload={
                "target_id": target_id,
                "follow_up": follow_up_question,
            },
            agent_name="MainAgent",
        )

    async def emit_contradiction_detected(
        self,
        session_id: str,
        target_id: str,
        previous_claim: str,
        current_claim: str,
        severity: str,
    ) -> PlatformEvent:
        """Contradiction detected."""

        return await self.emitter.emit(
            session_id=session_id,
            event_type=EventType.VIVA_CONTRADICTION_DETECTED,
            payload={
                "target_id": target_id,
                "previous_claim": previous_claim,
                "current_claim": current_claim,
                "severity": severity,
            },
            agent_name="MainAgent",
        )

    async def emit_topic_escalated(
        self, session_id: str, topic: str, reason: str
    ) -> PlatformEvent:
        """Topic escalated to deeper questioning."""

        return await self.emitter.emit(
            session_id=session_id,
            event_type=EventType.VIVA_TOPIC_ESCALATED,
            payload={
                "topic": topic,
                "reason": reason,
                "increased_difficulty": True,
            },
            agent_name="MainAgent",
        )

    async def emit_viva_session_completed(
        self, session_id: str, summary: Dict[str, Any]
    ) -> PlatformEvent:
        """Viva session completed."""

        return await self.emitter.emit(
            session_id=session_id,
            event_type=EventType.VIVA_SESSION_COMPLETED,
            payload={
                "total_questions": summary.get("total_questions"),
                "average_depth_score": summary.get("average_depth_score"),
                "contradictions_found": summary.get("contradictions_found"),
                "weak_areas": summary.get("weak_areas"),
                "strong_areas": summary.get("strong_areas"),
            },
            agent_name="MainAgent",
        )


class Stage6EventCoordinator:
    """Coordinates event emission for Stage 6: Voice Infrastructure."""

    def __init__(self, event_emitter: EventEmitter):
        self.emitter = event_emitter

    async def emit_voice_session_started(self, session_id: str) -> PlatformEvent:
        """Voice viva session started."""

        return await self.emitter.emit(
            session_id=session_id,
            event_type=EventType.VOICE_SESSION_STARTED,
            payload={"stage": "6", "status": "started"},
            agent_name="VoiceInfrastructure",
        )

    async def emit_question_played(
        self, session_id: str, turn_number: int, duration_seconds: float
    ) -> PlatformEvent:
        """Question played via TTS."""

        return await self.emitter.emit(
            session_id=session_id,
            event_type=EventType.VOICE_QUESTION_PLAYED,
            payload={
                "turn_number": turn_number,
                "tts_duration_seconds": duration_seconds,
                "provider": "system_tts",
            },
            agent_name="VoiceInfrastructure",
        )

    async def emit_listening_started(self, session_id: str, turn_number: int) -> PlatformEvent:
        """Started listening for student response."""

        return await self.emitter.emit(
            session_id=session_id,
            event_type=EventType.VOICE_LISTENING_STARTED,
            payload={"turn_number": turn_number},
            agent_name="VoiceInfrastructure",
        )

    async def emit_listening_stopped(
        self, session_id: str, turn_number: int, duration_seconds: float
    ) -> PlatformEvent:
        """Stopped listening (silence detected)."""

        return await self.emitter.emit(
            session_id=session_id,
            event_type=EventType.VOICE_LISTENING_STOPPED,
            payload={
                "turn_number": turn_number,
                "recording_duration_seconds": duration_seconds,
            },
            agent_name="VoiceInfrastructure",
        )

    async def emit_transcription_received(
        self,
        session_id: str,
        turn_number: int,
        transcript_raw: str,
        confidence: float,
    ) -> PlatformEvent:
        """Speech transcription received."""

        return await self.emitter.emit(
            session_id=session_id,
            event_type=EventType.VOICE_TRANSCRIPTION_RECEIVED,
            payload={
                "turn_number": turn_number,
                "transcript_length": len(transcript_raw),
                "stt_confidence": confidence,
                "provider": "mock_stt",
            },
            agent_name="VoiceInfrastructure",
        )

    async def emit_transcription_normalized(
        self,
        session_id: str,
        turn_number: int,
        technical_terms: List[str],
    ) -> PlatformEvent:
        """Transcript normalized with technical terminology."""

        return await self.emitter.emit(
            session_id=session_id,
            event_type=EventType.VOICE_TRANSCRIPTION_NORMALIZED,
            payload={
                "turn_number": turn_number,
                "technical_terms_corrected": technical_terms,
            },
            agent_name="VoiceInfrastructure",
        )

    async def emit_voice_session_ended(self, session_id: str, total_turns: int) -> PlatformEvent:
        """Voice viva session ended."""

        return await self.emitter.emit(
            session_id=session_id,
            event_type=EventType.VOICE_SESSION_ENDED,
            payload={
                "total_voice_turns": total_turns,
                "status": "completed",
            },
            agent_name="VoiceInfrastructure",
        )

class Stage7EventCoordinator:
    """Coordinates SENTINEL integrity events emission for Stage 7."""

    def __init__(self, event_emitter: EventEmitter):
        self.emitter = event_emitter

    async def emit_integrity_alert(self, session_id: str, alert_payload: Dict[str, Any]) -> PlatformEvent:
        return await self.emitter.emit(
            session_id=session_id,
            event_type=EventType.INTEGRITY_ALERT_GENERATED,
            payload=alert_payload,
            agent_name="Sentinel",
        )

class Stage8EventCoordinator:
    """Coordinates evaluation loop events for Stage 8."""

    def __init__(self, event_emitter: EventEmitter):
        self.emitter = event_emitter

    async def emit_implementation_familiarity_updated(self, session_id: str, payload: Dict[str, Any]) -> PlatformEvent:
        return await self.emitter.emit(
            session_id=session_id,
            event_type=EventType.IMPLEMENTATION_FAMILIARITY_UPDATED,
            payload=payload,
            agent_name="MainAgentEvaluation",
        )

    async def emit_contradiction_chain_updated(self, session_id: str, payload: Dict[str, Any]) -> PlatformEvent:
        return await self.emitter.emit(
            session_id=session_id,
            event_type=EventType.CONTRADICTION_CHAIN_UPDATED,
            payload=payload,
            agent_name="MainAgentEvaluation",
        )

class Stage9EventCoordinator:
    """Coordinates curriculum transition events for Stage 9."""

    def __init__(self, event_emitter: EventEmitter):
        self.emitter = event_emitter

    async def emit_curriculum_transition_started(self, session_id: str, payload: Dict[str, Any]) -> PlatformEvent:
        return await self.emitter.emit(
            session_id=session_id,
            event_type=EventType.CURRICULUM_TRANSITION_STARTED,
            payload=payload,
            agent_name="CurriculumEngine",
        )

    async def emit_curriculum_topic_completed(self, session_id: str, payload: Dict[str, Any]) -> PlatformEvent:
        return await self.emitter.emit(
            session_id=session_id,
            event_type=EventType.CURRICULUM_TOPIC_COMPLETED,
            payload=payload,
            agent_name="CurriculumEngine",
        )


class RuntimeEventOrchestrator:
    """
    Master orchestrator for all runtime events across Stages 4-6.

    Provides unified interface for event emission and subscription.
    """

    def __init__(self, storage_provider: Optional[FileStorageProvider] = None):
        self.emitter = EventEmitter(storage_provider)
        self.stage4 = Stage4EventCoordinator(self.emitter)
        self.stage5 = Stage5EventCoordinator(self.emitter)
        self.stage6 = Stage6EventCoordinator(self.emitter)
        self.stage7 = Stage7EventCoordinator(self.emitter)
        self.stage8 = Stage8EventCoordinator(self.emitter)
        self.stage9 = Stage9EventCoordinator(self.emitter)

    def subscribe(self, event_type: EventType, callback: Callable) -> None:
        """Subscribe to specific event type."""

        self.emitter.subscribe(event_type, callback)

    def get_event_log(self) -> List[PlatformEvent]:
        """Get complete event log for audit/replay."""

        return self.emitter.event_log

    def get_events_for_session(self, session_id: str) -> List[PlatformEvent]:
        """Get all events for a specific session."""

        return [e for e in self.emitter.event_log if e.session_id == session_id]

    def get_events_by_type(self, event_type: EventType) -> List[PlatformEvent]:
        """Get all events of a specific type."""

        return [e for e in self.emitter.event_log if e.event_type == event_type]
