from __future__ import annotations

import json
import tempfile

from src.agents.main_agent.transcript import (
    FileTranscriptStore,
    TranscriptEventKind,
    TranscriptReplay,
)


def test_transcript_store_exports_json_and_replays_same_turn_history():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = FileTranscriptStore(tmpdir)
        session_id = "transcript_session"
        step_id = "transcript_session:1"

        store.append_event(
            session_id,
            kind=TranscriptEventKind.QUESTION,
            step_id=step_id,
            payload={"question_text": "Explain your JWT authentication flow."},
            evidence_links=["auth_middleware"],
            metadata={"turn_index": 0},
        )
        store.append_event(
            session_id,
            kind=TranscriptEventKind.ANSWER,
            step_id=step_id,
            payload={"normalized_transcript": "When JWT validation fails middleware returns 401."},
            evidence_links=["auth_middleware"],
            metadata={"turn_index": 0},
        )
        store.append_event(
            session_id,
            kind=TranscriptEventKind.CONTRADICTION,
            step_id=step_id,
            payload={
                "concept": "jwt",
                "previous_claim": "present",
                "current_claim": "absent",
                "previous_turn_id": "transcript_session:0",
                "current_turn_id": "transcript_session:1",
            },
            evidence_links=["previous answer", "current answer"],
            metadata={"turn_index": 0},
        )
        store.append_event(
            session_id,
            kind=TranscriptEventKind.FAIRNESS,
            step_id=step_id,
            payload={"annotation": "No fairness issue detected."},
            evidence_links=["audit_note"],
            metadata={"turn_index": 0},
        )
        store.append_event(
            session_id,
            kind=TranscriptEventKind.EVALUATION,
            step_id=step_id,
            payload={"relevance_score": 0.87, "reasoning_depth_state": "moderate"},
            evidence_links=["auth_middleware"],
            metadata={"turn_index": 0},
        )
        store.update_turn(
            session_id,
            turn_id="turn-1",
            question_text="Explain your JWT authentication flow.",
            answer_text="When JWT validation fails middleware returns 401.",
            normalized_answer_text="When JWT validation fails middleware returns 401.",
            evaluation={"relevance_score": 0.87, "reasoning_depth_state": "moderate"},
            contradiction_events=[
                {
                    "concept": "jwt",
                    "previous_claim": "present",
                    "current_claim": "absent",
                }
            ],
            fairness_events=[{"annotation": "No fairness issue detected."}],
            follow_up_questions=["Where is JWT validation enforced in your middleware chain?"],
            evidence_links=["auth_middleware"],
            metadata={"step_id": step_id, "turn_index": 0},
        )

        record = store.load(session_id)
        assert record is not None
        assert record.session_id == session_id
        assert len(record.events) == 5
        assert [event.order_index for event in record.events] == [0, 1, 2, 3, 4]
        assert [event.kind.value for event in record.events] == [
            "question",
            "answer",
            "contradiction",
            "fairness",
            "evaluation",
        ]

        replay_steps = TranscriptReplay.reconstruct(record)
        assert len(replay_steps) == 1
        assert replay_steps[0].question_text == "Explain your JWT authentication flow."
        assert replay_steps[0].answer_text == "When JWT validation fails middleware returns 401."
        assert replay_steps[0].contradiction_events
        assert replay_steps[0].fairness_events
        assert replay_steps[0].follow_up_questions == ["Where is JWT validation enforced in your middleware chain?"]

        exported = store.export_json(session_id)
        exported_payload = json.loads(exported)
        assert exported_payload["session_id"] == session_id
        assert exported_payload["events"][0]["kind"] == "question"
        assert exported_payload["turns"][0]["question_text"] == "Explain your JWT authentication flow."


def test_transcript_store_is_replay_safe_and_overwrites_turn_state_deterministically():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = FileTranscriptStore(tmpdir)
        session_id = "replay_safe_session"
        turn_id = "turn-1"

        store.update_turn(
            session_id,
            turn_id=turn_id,
            question_text="What happens on cache invalidation failure?",
            answer_text="We retry the write path.",
            normalized_answer_text="We retry the write path.",
            evaluation={"relevance_score": 0.5},
            contradiction_events=[],
            fairness_events=[],
            follow_up_questions=[],
            evidence_links=["cache_layer"],
            metadata={"step_id": f"{session_id}:1", "turn_index": 0},
        )
        store.update_turn(
            session_id,
            turn_id=turn_id,
            question_text="What happens on cache invalidation failure?",
            answer_text="We retry the write path.",
            normalized_answer_text="We retry the write path.",
            evaluation={"relevance_score": 0.75},
            contradiction_events=[{"concept": "cache", "previous_claim": "present", "current_claim": "present"}],
            fairness_events=[{"annotation": "stable"}],
            follow_up_questions=["Where exactly is Redis used in your request lifecycle?"],
            evidence_links=["cache_layer"],
            metadata={"step_id": f"{session_id}:1", "turn_index": 0},
        )

        record = store.load(session_id)
        assert record is not None
        assert len(record.turns) == 1
        assert record.turns[0].evaluation["relevance_score"] == 0.75
        assert record.turns[0].contradiction_events[0]["concept"] == "cache"
        assert record.turns[0].fairness_events[0]["annotation"] == "stable"
        assert record.turns[0].follow_up_questions == ["Where exactly is Redis used in your request lifecycle?"]
