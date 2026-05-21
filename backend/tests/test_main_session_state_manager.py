import json
from pathlib import Path

import pytest

from src.agents.main_agent.models import SessionLifecycle
from src.agents.main_agent.session import InMemorySessionStateStorage, SessionStateManager
from src.agents.main_agent.session.persistence import deserialize_state


def test_serialization_deserialization_round_trip_preserves_state():
    manager = SessionStateManager.create("session-1")
    manager.transition_to(SessionLifecycle.ACTIVE)
    first_turn = manager.ask_question("q1", "What does your API cache?")
    second_turn = manager.ask_question("q2", "How do you invalidate it?", follow_up_to_turn_id=first_turn)
    manager.record_response(first_turn, "We cache project metadata.")
    manager.record_response(second_turn, "Invalidation is event driven.")
    manager.add_contradiction(second_turn, "Earlier claimed there is no cache layer.")
    manager.update_weak_area("caching")
    manager.update_topic_coverage("caching", "partial")

    payload = manager.to_json()
    restored = SessionStateManager.from_json(payload)

    assert restored.state.model_dump() == manager.state.model_dump()


def test_question_history_order_and_response_mapping():
    manager = SessionStateManager.create("session-2")
    manager.transition_to(SessionLifecycle.ACTIVE)
    turn_1 = manager.ask_question("q1", "Question 1")
    turn_2 = manager.ask_question("q2", "Question 2")
    turn_3 = manager.ask_question("q3", "Question 3", follow_up_to_turn_id=turn_1)
    manager.record_response(turn_2, "Answer 2")
    manager.record_response(turn_1, "Answer 1")
    manager.record_response(turn_3, "Answer 3")

    assert [item.turn_id for item in manager.state.question_history] == [1, 2, 3]
    assert manager.state.follow_up_chains == {"1": [3]}

    replay = manager.replay_view()
    assert [item["question_text"] for item in replay] == ["Question 1", "Question 2", "Question 3"]
    assert [item["response_text"] for item in replay] == ["Answer 1", "Answer 2", "Answer 3"]


def test_explicit_lifecycle_transitions_and_invalid_transition_blocked():
    manager = SessionStateManager.create("session-3")
    manager.transition_to(SessionLifecycle.ACTIVE)
    manager.transition_to(SessionLifecycle.INTERRUPTED)
    manager.transition_to(SessionLifecycle.ACTIVE)
    manager.transition_to(SessionLifecycle.COMPLETED)

    assert [t.model_dump() for t in manager.state.transitions] == [
        {"from_stage": "initialized", "to_stage": "active"},
        {"from_stage": "active", "to_stage": "interrupted"},
        {"from_stage": "interrupted", "to_stage": "active"},
        {"from_stage": "active", "to_stage": "completed"},
    ]

    with pytest.raises(ValueError):
        manager.transition_to(SessionLifecycle.ACTIVE)


def test_recovery_after_interruption_with_storage():
    storage = InMemorySessionStateStorage()
    manager = SessionStateManager.create("session-4")
    manager.transition_to(SessionLifecycle.ACTIVE)
    manager.ask_question("q1", "Describe your queue strategy.")
    manager.transition_to(SessionLifecycle.INTERRUPTED)
    manager.save(storage)

    recovered = SessionStateManager.recover("session-4", storage)

    assert recovered is not None
    assert recovered.state.lifecycle_stage == SessionLifecycle.INTERRUPTED
    recovered.transition_to(SessionLifecycle.ACTIVE)
    assert recovered.state.lifecycle_stage == SessionLifecycle.ACTIVE


def test_contradiction_history_retained_across_turns():
    manager = SessionStateManager.create("session-5")
    manager.transition_to(SessionLifecycle.ACTIVE)
    turn_1 = manager.ask_question("q1", "How is data encrypted?")
    turn_2 = manager.ask_question("q2", "What algorithm is used?")
    manager.record_response(turn_1, "Data is encrypted.")
    manager.record_response(turn_2, "No encryption is used.")
    manager.add_contradiction(turn_2, "Encryption claim conflicts between turns.")

    payload = manager.to_json()
    restored_state = deserialize_state(payload)

    assert restored_state.contradiction_history[0].model_dump() == {
        "turn_id": 2,
        "detail": "Encryption claim conflicts between turns.",
    }


def test_weak_area_increment_rejects_negative_values():
    manager = SessionStateManager.create("session-6")

    with pytest.raises(ValueError):
        manager.update_weak_area("security", increment=-1)


def test_fixture_replay_consistency():
    fixture_path = Path(__file__).parent / "fixtures" / "session_state_replay.json"
    payload = fixture_path.read_text()
    restored = SessionStateManager.from_json(payload)

    replay = restored.replay_view()

    assert replay == [
        {
            "turn_id": "1",
            "question_id": "q-1",
            "question_text": "Explain your auth flow.",
            "response_text": "JWT was chosen for stateless scaling.",
        },
        {
            "turn_id": "2",
            "question_id": "q-2",
            "question_text": "Why did you choose JWT?",
            "response_text": "It matched existing service boundaries.",
        },
    ]
    assert json.loads(payload)["session_id"] == restored.state.session_id
