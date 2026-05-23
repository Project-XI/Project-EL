import tempfile

import pytest

from src.agents.main_agent.agent import MainAgent
from src.core.config import settings
from src.models.context import EvidenceModel, StructuredContext, VivaTarget
from src.services.storage import FileStorageProvider
from src.services.viva.turn_evaluation import DeterministicTurnEvaluator, RuntimeVivaState
from src.services.voice.models.transcript_models import NormalizedTranscript, VoiceTurnTranscript
from src.services.voice.playback.tts_provider import NullTTSProvider


def _build_context() -> StructuredContext:
    return StructuredContext(
        project_name=EvidenceModel(value="Project-EL", confidence=1.0, evidence=["test"]),
        project_type=EvidenceModel(value="API", confidence=1.0, evidence=["test"]),
        frontend_framework=EvidenceModel(value="React", confidence=0.8, evidence=["pkg"]),
        backend_framework=EvidenceModel(value="FastAPI", confidence=0.9, evidence=["pkg"]),
        database_used=EvidenceModel(value="PostgreSQL", confidence=0.8, evidence=["pkg"]),
        authentication_system=EvidenceModel(value="JWT", confidence=0.9, evidence=["code"]),
        architecture_pattern=EvidenceModel(value="REST", confidence=0.8, evidence=["routes"]),
        implementation_viva_targets=[
            VivaTarget(
                topic="Security",
                question_target="Explain your JWT authentication flow.",
                difficulty="hard",
                importance_score=0.95,
                focus="Trace validation and failure behavior in middleware.",
                category="Security",
                depth_score=9.0,
                related_node="auth_middleware",
                confidence=0.9,
                reasoning_summary="JWT found in stack",
            )
        ],
    )


@pytest.mark.asyncio
async def test_closed_loop_voice_viva_with_mock_response_persists_artifacts():
    with tempfile.TemporaryDirectory() as tmpdir:
        settings.TRANSCRIPT_STORAGE_PATH = tmpdir

        agent = MainAgent()
        agent._tts_provider = NullTTSProvider()
        agent.storage = FileStorageProvider(tmpdir)

        context = _build_context()
        await agent._conduct_voice_viva(
            "voice_test_session",
            {
                "enable_voice": True,
                "voice_max_turns": 3,
                "mock_responses": ["When JWT validation fails middleware returns 401."],
            },
            context,
        )

        record = agent.storage.get_session_record("voice_test_session")
        artifacts = record.get("artifacts", [])
        transitions = record.get("state_transitions", [])

        assert artifacts, "Expected persisted artifacts"
        assert transitions, "Expected persisted state transitions"

        eval_artifacts = [a for a in artifacts if a.get("artifact_type") == "turn_evaluation"]
        assert eval_artifacts, "Expected turn evaluation artifact"

        payload = eval_artifacts[0]["payload"]
        assert payload["reasoning_depth_state"] in {"moderate", "deep", "shallow"}
        assert payload["topic_coverage_delta"].get("security", 0) == 1
        assert any("JWT validation" in f["question"] for f in payload.get("follow_ups", []))


def test_turn_evaluator_is_deterministic_for_same_input():
    evaluator = DeterministicTurnEvaluator()

    target = VivaTarget(
        topic="Security",
        question_target="Explain your JWT authentication flow.",
        difficulty="hard",
        importance_score=0.95,
        focus="Trace validation and failure behavior in middleware.",
        category="Security",
        depth_score=9.0,
        related_node="auth_middleware",
        confidence=0.9,
        reasoning_summary="JWT found in stack",
    )

    turn = VoiceTurnTranscript(
        session_id="determinism_session",
        question_text=target.question_target,
        raw_transcript="When JWT validation fails middleware returns 401.",
        normalized_transcript=NormalizedTranscript(
            session_id="determinism_session",
            raw_text="When JWT validation fails middleware returns 401.",
            normalized_text="When JWT validation fails middleware returns 401.",
            confidence=0.95,
            normalized_confidence=0.95,
        ),
    )

    state_a = RuntimeVivaState(session_id="determinism_session")
    state_b = RuntimeVivaState(session_id="determinism_session")

    result_a, next_a = evaluator.evaluate_turn(state=state_a, target=target, turn=turn)
    result_b, next_b = evaluator.evaluate_turn(state=state_b, target=target, turn=turn)

    assert result_a.relevance_score == result_b.relevance_score
    assert [f.question for f in result_a.follow_ups] == [f.question for f in result_b.follow_ups]
    assert result_a.reasoning_depth_state == result_b.reasoning_depth_state
    assert next_a.topic_coverage == next_b.topic_coverage
