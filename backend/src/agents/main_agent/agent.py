import asyncio
from collections import deque

from typing import Any, Dict, List, Optional
from src.agents.base import BaseAgent
from src.models.context import EvidenceModel, StructuredContext, VivaTarget
from src.models.session import VivaSession
from src.agents.gatekeeper.agent import GatekeeperAgent
from src.agents.oracle.agent import OracleAgent
from src.agents.sentinel.agent import SentinelAgent
from src.services.storage import FileStorageProvider
from src.services.intelligence.viva_intelligence_engine import VivaIntelligenceEngine
from src.services.viva.turn_evaluation import DeterministicTurnEvaluator, RuntimeVivaState
from src.agents.main_agent.transcript import FileTranscriptStore, TranscriptEventKind, TranscriptTurnRecord

# Voice integration imports (kept optional and pluggable)
from src.core.config import settings
from src.services.voice.session.voice_session_manager import VoiceSessionManager
from src.services.voice.providers.deepgram_provider import DeepgramTranscriptionProvider
from src.services.voice.playback.tts_provider import SystemTTSProvider, NullTTSProvider
from src.services.voice.transcription.transcript_normalizer import TranscriptNormalizer
from src.services.voice.models.transcript_models import FinalTranscript, VoiceSessionPhase

class MainAgent(BaseAgent):
    def __init__(self, prompt_version: str = "v2"):
        super().__init__(name="MainAgent")
        self.prompt_version = prompt_version
        self.gatekeeper = GatekeeperAgent()
        self.oracle = OracleAgent()
        self.sentinel = SentinelAgent()
        self.storage = FileStorageProvider(settings.TRANSCRIPT_STORAGE_PATH)
        self.transcript_store = FileTranscriptStore(settings.TRANSCRIPT_STORAGE_PATH)
        self.turn_evaluator = DeterministicTurnEvaluator()
        self._runtime_viva_states: Dict[str, RuntimeVivaState] = {}
        # voice playback is optional and activated per-session
        self._tts_provider = SystemTTSProvider() if SystemTTSProvider else NullTTSProvider()

    async def process(self, session_id: str, input_data: Dict[str, Any], log_callback=None) -> StructuredContext:
        """
        Orchestrates the project intelligence pipeline according to the defined agent roles.
        """
        async def send_log(msg: str, type: str = "info"):
            if log_callback:
                await log_callback({"message": msg, "type": type})

        self.log_info(f"MainAgent starting analysis for session {session_id}")
        
        # Agent 2 (GATEKEEPER) — Identity + Session Agent (Placeholder)
        gatekeeper_output = await self.gatekeeper.process(session_id, input_data, log_callback)
        
        # Agent 1 (ORACLE) — Submission Intelligence Agent
        oracle_output = await self.oracle.process(session_id, gatekeeper_output, log_callback)
        
        # Optional voice-enabled deterministic viva loop
        enable_voice = bool(input_data.get("enable_voice", False))
        if enable_voice:
            try:
                await self._conduct_voice_viva(session_id, input_data, oracle_output, log_callback)
            except Exception as e:
                await send_log(f"[MainAgent] Voice viva failed: {e}", "error")

        # Agent 3 (SENTINEL) — Behaviour Analysis Agent (Placeholder)
        final_context = await self.sentinel.process(session_id, oracle_output, log_callback)

        self.log_info(f"MainAgent finished analysis for session {session_id}")
        await send_log("[MainAgent] Analysis complete.", "success")
        
        return final_context

    async def _conduct_voice_viva(self, session_id: str, input_data: Dict[str, Any], oracle_output: StructuredContext, log_callback=None) -> None:
        """Deterministic closed-loop voice viva orchestration.

        Loop:
        question -> playback -> transcript finalize -> evaluation -> state update
        -> contradiction checks -> follow-up generation -> next turn.
        """

        async def _log(msg: str, level: str = "info"):
            if log_callback:
                await log_callback({"message": msg, "type": level})

        await _log(f"[MainAgent] event=voice_viva.started session_id={session_id}")

        viva_targets = getattr(oracle_output, "implementation_viva_targets", None) or []
        if not viva_targets:
            await _log("[MainAgent] No viva targets from ORACLE; skipping voice viva.")
            return

        # Choose transcription provider: Deepgram if configured, otherwise use a local test harness
        transcription_provider = None
        if settings.DEEPGRAM_API_KEY:
            transcription_provider = DeepgramTranscriptionProvider(api_key=settings.DEEPGRAM_API_KEY)
        else:
            # Fallback testing provider: implement a tiny provider that returns supplied mock text
            class _MockProvider(DeepgramTranscriptionProvider):
                async def connect(self):
                    return None
                async def transcribe_chunk(self, audio_bytes: bytes, *, sequence_number: int, is_final: bool = False):
                    # No-op; real audio capture will be done externally in production
                    return []
                async def finalize_transcript(self):
                    return FinalTranscript(session_id=session_id, raw_text="", confidence=0.0, provider="mock", chunk_count=0)
                async def close(self):
                    return None

            transcription_provider = _MockProvider(api_key=None)

        tts_provider = self._tts_provider or NullTTSProvider()

        session = VivaSession(
            session_id=session_id,
            student_id=str(input_data.get("student_id", "unknown")),
            status="active",
        )

        # Create a voice session manager dedicated to this MainAgent session
        voice_manager = VoiceSessionManager(
            transcription_provider=transcription_provider,
            tts_provider=tts_provider,
            session=session,
            normalizer=TranscriptNormalizer(),
        )

        # For deterministic runs, we may accept a list of mock responses (strings)
        mock_responses: Optional[List[str]] = input_data.get("mock_responses")
        mock_iter = iter(mock_responses) if isinstance(mock_responses, list) else None

        runtime_state = self._runtime_viva_states.get(session_id) or RuntimeVivaState(session_id=session_id)
        turn_queue = deque(viva_targets)
        max_turns = int(input_data.get("voice_max_turns", max(1, len(viva_targets) * 2)))
        processed_turns = 0

        try:
            while turn_queue and processed_turns < max_turns:
                target = turn_queue.popleft()
                question_text = getattr(target, "question_target", None) or getattr(target, "topic", "Explain this area.")
                if question_text in runtime_state.asked_questions:
                    continue

                step_id = f"{session_id}:{processed_turns + 1}"

                await _log(
                    f"[MainAgent] event=question.playback.started session_id={session_id} turn={processed_turns + 1} category={target.category} question={question_text}"
                )
                self.transcript_store.append_event(
                    session_id,
                    kind=TranscriptEventKind.QUESTION,
                    step_id=step_id,
                    payload={
                        "question_text": question_text,
                        "category": target.category,
                        "focus": target.focus,
                        "target_topic": target.topic,
                        "related_node": target.related_node,
                    },
                    evidence_links=[link for link in [target.related_node] if link],
                    metadata={"turn_index": processed_turns},
                )
                await voice_manager.ask_question(question_text, metadata={"category": target.category, "focus": target.focus})

                turn = None

                # Deterministic mock-response path for tests
                if mock_iter is not None:
                    try:
                        mock_text = next(mock_iter)
                    except StopIteration:
                        mock_text = ""

                    if not mock_text:
                        await _log("[MainAgent] event=turn.skipped reason=empty_mock_response", "warn")
                        continue

                    final = FinalTranscript(
                        session_id=session_id,
                        raw_text=mock_text,
                        confidence=0.95,
                        provider="mock",
                        chunk_count=1,
                    )
                    turn = await voice_manager.finalize_response(final_transcript=final)
                else:
                    # External capture pipeline should finalize and move manager to READY_FOR_MAIN.
                    timeout = float(input_data.get("voice_turn_timeout_seconds", 30))
                    waited = 0.0
                    poll_interval = 0.5
                    while voice_manager.phase != VoiceSessionPhase.READY_FOR_MAIN and waited < timeout:
                        await asyncio.sleep(poll_interval)
                        waited += poll_interval

                    if voice_manager.phase != VoiceSessionPhase.READY_FOR_MAIN:
                        await _log("[MainAgent] event=turn.timeout reason=finalized_transcript_not_ready", "error")
                        continue

                    turn = await voice_manager.finalize_response()

                processed_turns += 1
                await _log(
                    f"[MainAgent] event=turn.finalized session_id={session_id} turn_id={turn.turn_id} text={turn.normalized_transcript.normalized_text}"
                )

                self.transcript_store.append_event(
                    session_id,
                    kind=TranscriptEventKind.ANSWER,
                    step_id=step_id,
                    payload={
                        "turn_id": turn.turn_id,
                        "raw_transcript": turn.raw_transcript,
                        "normalized_transcript": turn.normalized_transcript.normalized_text,
                        "silence_detected": turn.silence_detected,
                        "confidence": turn.normalized_transcript.confidence,
                    },
                    evidence_links=list(turn.normalized_transcript.metadata.get("evidence_links", [])),
                    metadata={"turn_index": processed_turns},
                )

                # Existing contradiction hook: compare transcript claims against detected stack/context.
                repo_detections = self._build_detection_map_from_context(oracle_output)
                inconsistency_flags = VivaIntelligenceEngine.detect_inconsistencies(
                    turn.normalized_transcript.normalized_text,
                    repo_detections,
                )

                # Deterministic evaluation and runtime state transition.
                evaluation_result, new_state = self.turn_evaluator.evaluate_turn(
                    state=runtime_state,
                    target=target,
                    turn=turn,
                    inconsistency_flags=inconsistency_flags,
                )

                await _log(
                    "[MainAgent] event=turn.evaluated "
                    f"turn_id={turn.turn_id} relevance={evaluation_result.relevance_score} "
                    f"depth={evaluation_result.reasoning_depth_state} familiarity={evaluation_result.implementation_familiarity_state}"
                )

                self.transcript_store.append_event(
                    session_id,
                    kind=TranscriptEventKind.EVALUATION,
                    step_id=step_id,
                    payload=evaluation_result.model_dump(mode="json"),
                    evidence_links=[link for link in [target.related_node] if link],
                    metadata={"turn_index": processed_turns},
                )

                if evaluation_result.contradiction_events:
                    await _log(
                        f"[MainAgent] event=contradiction.analysis contradictions={len(evaluation_result.contradiction_events)}",
                        "warn",
                    )
                    for contradiction in evaluation_result.contradiction_events:
                        self.transcript_store.append_event(
                            session_id,
                            kind=TranscriptEventKind.CONTRADICTION,
                            step_id=step_id,
                            payload=contradiction.model_dump(mode="json"),
                            evidence_links=[contradiction.evidence_previous, contradiction.evidence_current],
                            metadata={"turn_index": processed_turns},
                        )

                # Adaptive follow-up generation reuses target category and runtime evidence.
                follow_up_questions: List[str] = []
                for followup in evaluation_result.follow_ups:
                    follow_target = VivaTarget(
                        topic=f"Follow-up: {target.topic}",
                        question_target=followup.question,
                        difficulty=target.difficulty,
                        importance_score=target.importance_score,
                        focus=followup.reason,
                        category=target.category,
                        depth_score=target.depth_score,
                        related_node=target.related_node,
                        confidence=target.confidence,
                        reasoning_summary=f"Follow-up from turn {turn.turn_id}",
                    )
                    turn_queue.appendleft(follow_target)
                    follow_up_questions.append(followup.question)

                if follow_up_questions:
                    self.transcript_store.append_event(
                        session_id,
                        kind=TranscriptEventKind.FOLLOW_UP,
                        step_id=step_id,
                        payload={
                            "source_turn_id": turn.turn_id,
                            "follow_up_questions": follow_up_questions,
                        },
                        evidence_links=[link for link in [target.related_node] if link],
                        metadata={"turn_index": processed_turns},
                    )

                missing_domains = self.turn_evaluator.missing_domains(new_state)
                await _log(
                    "[MainAgent] event=topic.coverage.updated "
                    f"coverage={new_state.topic_coverage} missing={missing_domains}"
                )

                self.transcript_store.append_event(
                    session_id,
                    kind=TranscriptEventKind.TOPIC_COVERAGE,
                    step_id=step_id,
                    payload={
                        "coverage": new_state.topic_coverage,
                        "missing_domains": missing_domains,
                    },
                    metadata={"turn_index": processed_turns},
                )

                self.transcript_store.append_event(
                    session_id,
                    kind=TranscriptEventKind.STATE_TRANSITION,
                    step_id=step_id,
                    payload={
                        "from_state": runtime_state.model_dump(mode="json"),
                        "to_state": new_state.model_dump(mode="json"),
                    },
                    metadata={"turn_index": processed_turns},
                )

                self.transcript_store.update_turn(
                    session_id,
                    turn.turn_id,
                    question_text=question_text,
                    answer_text=turn.raw_transcript,
                    normalized_answer_text=turn.normalized_transcript.normalized_text,
                    evaluation=evaluation_result.model_dump(mode="json"),
                    contradiction_events=[event.model_dump(mode="json") for event in evaluation_result.contradiction_events],
                    fairness_events=[],
                    follow_up_questions=follow_up_questions,
                    evidence_links=[link for link in [target.related_node] if link],
                    metadata={
                        "step_id": step_id,
                        "turn_index": processed_turns,
                        "category": target.category,
                    },
                )

                # Backward-compatible sidecar writes for older session tooling.
                self.storage.append_artifact(
                    session_id,
                    "turn_evaluation",
                    evaluation_result.model_dump(mode="json"),
                )
                self.storage.append_artifact(
                    session_id,
                    "turn_transcript",
                    turn.model_dump(mode="json"),
                )
                self.storage.append_state_transition(
                    session_id,
                    {
                        "turn_id": turn.turn_id,
                        "from_state": runtime_state.model_dump(mode="json"),
                        "to_state": new_state.model_dump(mode="json"),
                    },
                )

                # Persist transcript/session artifacts/state transitions for replay-safe audit.
                self.storage.save_session(voice_manager.session)

                runtime_state = new_state
                self._runtime_viva_states[session_id] = runtime_state

            # Persist a stable export snapshot for downstream tooling.
            record = self.transcript_store.load(session_id)
            if record is not None:
                record.session_state = runtime_state.model_dump(mode="json")
                record.export_metadata = {
                    "exported_by": "MainAgent",
                    "session_id": session_id,
                    "turns_processed": processed_turns,
                }
                self.transcript_store.save(record)

            await _log(
                f"[MainAgent] event=voice_viva.completed session_id={session_id} turns={processed_turns} final_state={runtime_state.model_dump(mode='json')}"
            )
        finally:
            await voice_manager.cleanup()

    def _build_detection_map_from_context(self, context: StructuredContext) -> Dict[str, EvidenceModel]:
        """Build minimal detection map for reuse of existing inconsistency hooks."""
        return {
            "frontend_framework": context.frontend_framework,
            "backend_framework": context.backend_framework,
            "database_used": context.database_used,
            "authentication_system": context.authentication_system,
            "architecture_pattern": context.architecture_pattern,
        }

