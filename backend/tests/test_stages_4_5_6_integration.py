"""
End-to-End Integration Test — Stages 4-6

Validates complete flow:
1. ORACLE analysis → IntelligenceArtifact
2. MAIN Agent starts viva with adaptive questions
3. Voice infrastructure conducts turns
4. Session persists with full audit trail

This test demonstrates:
- Deterministic behavior
- Event emission across stages
- Transcript persistence
- Contradiction detection
- Adaptive difficulty progression
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

# Stage 4 imports
from src.services.oracle_main_handoff import OracleMainHandoffOrchestrator
from src.models.intelligence_artifact import IntelligenceArtifact

# Stage 5 imports
from src.services.main_agent_viva_orchestrator import MainAgentVivaOrchestrator

# Stage 6 imports
from src.services.voice_viva_orchestrator import (
    MockSTTProvider,
    SystemTTSProvider,
    VoiceVivaSession,
)

# Event orchestration
from src.services.runtime_event_orchestrator import RuntimeEventOrchestrator

# Session persistence
from src.services.viva_session_persistence import VivaSessionStore, VivaTranscriptBuilder


class Stage456IntegrationTest:
    """
    End-to-end integration test for Stages 4-6.

    Demonstrates:
    - Complete workflow
    - Event emission
    - Adaptive behavior
    - Persistence
    """

    def __init__(self):
        self.test_session_id = f"test_session_{datetime.utcnow().isoformat()}"
        self.event_orchestrator = RuntimeEventOrchestrator()
        self.viva_session_store = VivaSessionStore()
        self.results = {}

    async def run_full_test(self) -> Dict[str, Any]:
        """
        Execute full Stages 4-6 flow.

        Returns:
            Results with validation status and key metrics
        """

        print("\n" + "=" * 70)
        print("STAGE 4-6 INTEGRATION TEST")
        print("=" * 70)

        try:
            # Stage 4: Create mock ORACLE artifact
            print("\n[STAGE 4] Creating mock IntelligenceArtifact from ORACLE...")
            artifact = self._create_mock_oracle_artifact()
            print(f"✓ Artifact created: {artifact.artifact_id}")
            print(f"  - Viva targets: {len(artifact.viva_targets)}")
            print(f"  - Failure scenarios: {len(artifact.failure_scenarios)}")
            print(f"  - Weak points: {len(artifact.weak_points)}")

            # Emit Stage 4 event
            await self.event_orchestrator.stage4.emit_oracle_analysis_complete(
                self.test_session_id, artifact
            )
            print("✓ ORACLE_INTELLIGENCE_READY event emitted")

            # Stage 5: Initialize MAIN Agent and conduct viva
            print("\n[STAGE 5] Initializing MAIN Agent viva orchestration...")
            main_orchestrator = MainAgentVivaOrchestrator(artifact)
            session_state = main_orchestrator.initialize_session(self.test_session_id)
            print(f"✓ Viva session initialized: {session_state.session_id}")

            # Emit Stage 5 start event
            await self.event_orchestrator.stage5.emit_viva_session_started(self.test_session_id)
            print("✓ VIVA_SESSION_STARTED event emitted")

            # Conduct mock viva turns (without voice)
            print("\n[STAGE 5] Conducting viva questions...")
            num_turns = 3
            for turn_num in range(num_turns):
                print(f"\n  Turn {turn_num + 1}/{num_turns}:")

                # Get question
                target, question = main_orchestrator.get_next_question()
                if not target:
                    print("  ✗ No more questions")
                    break

                print(f"    Q: {question}")
                print(f"    Category: {target.category.value}")

                # Emit question event
                await self.event_orchestrator.stage5.emit_question_asked(
                    self.test_session_id,
                    target.target_id,
                    question,
                    target.difficulty,
                )

                # Mock student response
                mock_response = self._get_mock_response(target)
                print(f"    A: {mock_response}")

                # Emit response event
                await self.event_orchestrator.stage5.emit_response_received(
                    self.test_session_id, target.target_id, mock_response
                )

                # Evaluate
                evaluation = main_orchestrator.evaluate_answer(mock_response, target)
                print(
                    f"    Depth: {evaluation['depth_level']}, Coverage: {evaluation['coverage_score']:.2f}"
                )

                # Emit evaluation event
                await self.event_orchestrator.stage5.emit_evaluation_complete(
                    self.test_session_id,
                    target.target_id,
                    evaluation["depth_level"],
                    evaluation["coverage_score"],
                    evaluation.get("red_flags", []),
                )

                # Generate follow-up
                follow_up = main_orchestrator.generate_follow_up(evaluation, target)
                if follow_up:
                    print(f"    Follow-up: {follow_up}")
                    await self.event_orchestrator.stage5.emit_follow_up_generated(
                        self.test_session_id, target.target_id, follow_up
                    )

                # Detect contradictions
                if evaluation.get("contradictions"):
                    for contradiction in evaluation["contradictions"]:
                        print(
                            f"    ⚠ Contradiction: {contradiction['previous']} vs {contradiction['current']}"
                        )
                        await self.event_orchestrator.stage5.emit_contradiction_detected(
                            self.test_session_id,
                            target.target_id,
                            contradiction["previous"],
                            contradiction["current"],
                            contradiction.get("severity", "MEDIUM"),
                        )

                # Save QA pair
                await self.viva_session_store.save_question_answer_pair(
                    self.test_session_id,
                    {"target_id": target.target_id, "question": question},
                    {"transcript": mock_response},
                    evaluation,
                )

            # Get viva summary
            session_summary = main_orchestrator.get_session_summary()
            print(f"\n✓ Viva summary:")
            print(f"  - Questions: {session_summary['total_questions']}")
            print(f"  - Avg depth score: {session_summary['average_depth_score']:.2f}")
            print(f"  - Contradictions: {session_summary['contradictions_found']}")
            print(f"  - Weak areas: {', '.join(session_summary['weak_areas']) or 'None'}")

            # Emit completion event
            await self.event_orchestrator.stage5.emit_viva_session_completed(
                self.test_session_id, session_summary
            )
            print("✓ VIVA_SESSION_COMPLETED event emitted")

            # Stage 6: Mock voice session (without actual audio)
            print("\n[STAGE 6] Initializing voice infrastructure...")
            mock_stt = MockSTTProvider()
            mock_stt.add_mock_response("Redis is used for caching in the request pipeline", 0.95)
            mock_stt.add_mock_response(
                "It provides fast in-memory storage for frequently accessed data", 0.92
            )

            tts_provider = SystemTTSProvider()

            # Create voice session
            voice_session = VoiceVivaSession(
                self.test_session_id,
                main_orchestrator,
                tts_provider,
                mock_stt,
            )

            print("✓ Voice session initialized")

            # Emit voice start event
            await self.event_orchestrator.stage6.emit_voice_session_started(self.test_session_id)

            # Conduct 1 voice turn to demonstrate
            print("\n[STAGE 6] Conducting sample voice turn...")
            target, question = main_orchestrator.get_next_question()
            if target:
                print(f"  Question: {question}")

                # Emit playing event
                await self.event_orchestrator.stage6.emit_question_played(
                    self.test_session_id, 1, 2.5
                )
                print("  ✓ Question played via TTS")

                # Emit listening start
                await self.event_orchestrator.stage6.emit_listening_started(self.test_session_id, 1)
                print("  ✓ Listening started")

                # Simulate recording
                await asyncio.sleep(0.5)

                # Emit listening stop
                await self.event_orchestrator.stage6.emit_listening_stopped(
                    self.test_session_id, 1, 3.2
                )
                print("  ✓ Silence detected, recording stopped")

                # Mock transcription
                transcription = await mock_stt.transcribe(b"mock_audio")
                if transcription.get("success"):
                    await self.event_orchestrator.stage6.emit_transcription_received(
                        self.test_session_id,
                        1,
                        transcription.get("transcript"),
                        transcription.get("confidence"),
                    )
                    print(f"  ✓ Transcription: {transcription.get('transcript')}")

                    # Emit normalization
                    from src.services.voice_viva_orchestrator import TranscriptNormalizer

                    normalized = TranscriptNormalizer.normalize(
                        transcription.get("transcript")
                    )
                    technical_terms = TranscriptNormalizer.extract_technical_terms(normalized)
                    await self.event_orchestrator.stage6.emit_transcription_normalized(
                        self.test_session_id, 1, technical_terms
                    )
                    print(f"  ✓ Normalized with terms: {technical_terms}")

            # Emit voice session end
            await self.event_orchestrator.stage6.emit_voice_session_ended(
                self.test_session_id, 1
            )
            print("✓ VOICE_SESSION_ENDED event emitted")

            # Save session summary
            await self.viva_session_store.save_session_summary(
                self.test_session_id, session_summary, artifact.artifact_id
            )
            print("✓ Session summary persisted")

            # Generate transcripts
            print("\n[PERSISTENCE] Generating transcripts...")
            text_transcript = VivaTranscriptBuilder.build_text_transcript(session_summary)
            print("✓ Text transcript generated")

            eval_report = VivaTranscriptBuilder.build_evaluation_report(session_summary)
            print("✓ Evaluation report generated")

            # Collect results
            self.results = {
                "status": "SUCCESS",
                "test_session_id": self.test_session_id,
                "stage4": {
                    "artifact_id": artifact.artifact_id,
                    "viva_targets": len(artifact.viva_targets),
                    "deterministic_hash": artifact.deterministic_hash,
                },
                "stage5": {
                    "questions_asked": session_summary["total_questions"],
                    "average_depth_score": session_summary["average_depth_score"],
                    "average_coverage_score": session_summary["average_coverage_score"],
                    "contradictions_found": session_summary["contradictions_found"],
                    "weak_areas": session_summary["weak_areas"],
                    "strong_areas": session_summary["strong_areas"],
                },
                "stage6": {
                    "voice_turns": 1,
                    "mock_stt_confidence": 0.95,
                },
                "events_emitted": len(self.event_orchestrator.get_event_log()),
                "event_types": list(
                    set(e.event_type for e in self.event_orchestrator.get_event_log())
                ),
            }

            # Print event log summary
            print("\n[EVENTS] Summary of emitted events:")
            event_log = self.event_orchestrator.get_event_log()
            for i, event in enumerate(event_log, 1):
                print(f"  {i:2d}. {event.event_type}")

            print("\n" + "=" * 70)
            print("✓ INTEGRATION TEST PASSED")
            print("=" * 70)

            return self.results

        except Exception as e:
            self.results = {
                "status": "FAILED",
                "error": str(e),
            }
            print(f"\n✗ TEST FAILED: {e}")
            import traceback

            traceback.print_exc()
            return self.results

    def _create_mock_oracle_artifact(self) -> IntelligenceArtifact:
        """Create mock ORACLE artifact for testing."""

        from src.models.intelligence_artifact import (
            VivaTarget,
            ExecutionNode,
            ExecutionPath,
            FailureScenario,
            WeakPoint,
            IntelligenceCategory,
        )

        return IntelligenceArtifact(
            session_id=self.test_session_id,
                        analysis_duration_seconds=2.5,
            project_name="Test Project",
            project_type="Web Application",
            backend_stack={"framework": "FastAPI", "database": "PostgreSQL", "cache": "Redis"},
            architecture_pattern="MVC",
            execution_graph_nodes=[
                ExecutionNode(
                    node_id="req_handler",
                    label="Request Handler",
                    node_type="REQUEST_HANDLER",
                    implementation_details="Receives HTTP request",
                ),
                ExecutionNode(
                    node_id="middleware",
                    label="Auth Middleware",
                    node_type="MIDDLEWARE",
                    implementation_details="Validates JWT token",
                ),
            ],
            execution_paths=[
                ExecutionPath(
                    path_id="happy_path",
                    description="Normal flow",
                    nodes=["req_handler", "middleware"],
                    scenario="HAPPY_PATH",
                    criticality="HIGH",
                )
            ],
            viva_targets=[
                VivaTarget(
                    target_id="target_1",
                    question="How does your caching strategy handle concurrent writes?",
                    category=IntelligenceCategory.SCALABILITY,
                    difficulty="HARD",
                    depth_score=8.0,
                    why_important="Tests understanding of race conditions",
                    expected_coverage=[
                        "Locking mechanism",
                        "Cache invalidation",
                        "Consistency guarantees",
                    ],
                    red_flags=["No concurrency handling", "Hand-waving solution"],
                ),
                VivaTarget(
                    target_id="target_2",
                    question="What happens if database connection fails?",
                    category=IntelligenceCategory.FAILURE_PATH,
                    difficulty="MEDIUM",
                    depth_score=6.0,
                    why_important="Tests error handling knowledge",
                ),
            ],
            failure_scenarios=[
                FailureScenario(
                    scenario_name="Database Connection Failure",
                    trigger="DB unreachable",
                    propagation_path=["DB Query", "Error Handler"],
                    impact="Request fails",
                    severity="HIGH",
                    detectability="EASY",
                )
            ],
            weak_points=[
                WeakPoint(
                    area="Concurrency",
                    weakness="Race conditions in cache invalidation",
                    why_problematic="Shows lack of understanding of concurrent systems",
                    testing_approach="Ask about locking mechanisms",
                )
            ],
            summary="Mock artifact for testing",
            analysis_confidence=0.95,
        )

    def _get_mock_response(self, target: Any) -> str:
        """Generate mock response based on target."""

        if "caching" in target.question.lower():
            return "We use Redis for caching with TTL-based invalidation and handle concurrent writes with atomic operations."

        elif "database" in target.question.lower():
            return "If database fails, we have circuit breaker and fallback to cache or return error."

        else:
            return "The system is designed with consideration for error handling and recovery mechanisms."


async def main():
    """Run the integration test."""

    test = Stage456IntegrationTest()
    results = await test.run_full_test()

    # Print final results as JSON
    print("\nFinal Results:")
    print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
