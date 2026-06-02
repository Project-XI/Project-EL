"""
Integration test for Stages 7-9: SENTINEL, Evaluation loop, Curriculum transition
"""

import asyncio
import json
from datetime import datetime

from src.services.runtime_event_orchestrator import RuntimeEventOrchestrator
from src.services.main_agent_viva_orchestrator import MainAgentVivaOrchestrator
from src.services.sentinel_parallel_monitor import SentinelParallelMonitor
from src.services.main_agent_evaluation_loop import MainAgentEvaluationLoop
from src.services.curriculum_question_engine import CurriculumQuestionEngine
from src.models.intelligence_artifact import IntelligenceArtifact


async def run_test():
    test_session_id = f"test_session_7_8_9_{datetime.utcnow().isoformat()}"
    event_orchestrator = RuntimeEventOrchestrator()

    # Create mock artifact similar to Stage 4
    artifact = IntelligenceArtifact(
        session_id=test_session_id,
        analysis_duration_seconds=1.0,
        project_name="Curriculum Test",
        project_type="Web App",
        backend_stack={"framework": "FastAPI", "database": "PostgreSQL", "cache": "Redis"},
        architecture_pattern="MVC",
        viva_targets=[],
        summary="Test",
        analysis_confidence=0.9,
    )

    main = MainAgentVivaOrchestrator(artifact)
    main.initialize_session(test_session_id)

    # Attach SENTINEL and evaluation loop
    sentinel = SentinelParallelMonitor(test_session_id)
    evaluation = MainAgentEvaluationLoop(main)
    curriculum = CurriculumQuestionEngine(artifact, test_session_id)

    main.attach_sentinel(sentinel)
    main.attach_evaluation_loop(evaluation)
    main.attach_curriculum_engine(curriculum)

    # Simulate a response with sentinel observations
    target_stub = type(
        "T",
        (),
        {
            "target_id": "t1",
            "question": "How do you cache?",
            "category": type("C", (), {"value": "SCALABILITY"}),
            "expected_coverage": ["lock", "evict"],
            "red_flags": [],
            "difficulty": "MEDIUM",
            "depth_score": 5.0,
            "follow_up_paths": ["Explain locking at code level"],
        },
    )
    response = "We use Redis with eviction and locking in critical sections."

    enriched, artifact_eval, follow_up = evaluation.process_finalized_response(1, target_stub, response)
    print(json.dumps(enriched, indent=2, default=str))

    # Start curriculum transition
    if curriculum.should_start_transition(implementation_turns_completed=2):
        curriculum.start_transition()
        q = curriculum.get_next_question()
        print("Curriculum question:", q.prompt)
        score, completed = curriculum.evaluate_answer(q, "Memory eviction and latency trade-off explained with memory considerations.")
        print(score, completed)

    print("SENTINEL events:", len(sentinel.integrity_events))


if __name__ == "__main__":
    asyncio.run(run_test())
