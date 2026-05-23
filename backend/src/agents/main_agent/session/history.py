from typing import Dict, List

from src.agents.main_agent.models import SessionState


def build_replay_view(state: SessionState) -> List[Dict[str, str]]:
    response_by_turn = {entry.turn_id: entry.response_text for entry in state.response_history}
    replay: List[Dict[str, str]] = []
    for question in state.question_history:
        replay.append(
            {
                "turn_id": str(question.turn_id),
                "question_id": question.question_id,
                "question_text": question.question_text,
                "response_text": response_by_turn.get(question.turn_id, ""),
            }
        )
    return replay

