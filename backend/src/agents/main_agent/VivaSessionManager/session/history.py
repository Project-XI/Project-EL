"""
SessionHistory — ordered, deterministic history for questions and
candidate responses.

Question order is preserved exactly (no resorting, no duplicate re-keying).
Responses are keyed to the correct turn index. The data structure is
pickle- and json-safe by design.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

from vsm.models.session_state import (
    FollowUpRecord,
    RecordedQuestion,
    RecordedResponse,
)


class SessionHistory:
    """
    Thin wrapper around ordered containers that guarantees the same
    turn order on every replay.

    Parameters
    ----------
    session_id:
        Identifier used for audit / logging purposes.
    """

    def __init__(self, session_id: str) -> None:
        self.session_id: str = session_id
        self._questions: OrderedDict[int, RecordedQuestion] = OrderedDict()
        self._responses: OrderedDict[int, RecordedResponse] = OrderedDict()
        self._follow_up_chains: Dict[int, FollowUpRecord] = {}

    # ---- Question operations ------------------------------------------------

    def record_question(self, question: RecordedQuestion) -> int:
        """Append a question; returns its assigned turn index."""
        turn = len(self._questions)
        question.turn_index = turn
        self._questions[turn] = question
        return turn

    def get_question(self, turn_index: int) -> Optional[RecordedQuestion]:
        return self._questions.get(turn_index)

    def get_questions(self) -> List[RecordedQuestion]:
        return list(self._questions.values())

    def get_question_count(self) -> int:
        return len(self._questions)

    # ---- Response operations ------------------------------------------------

    def record_response(self, response: RecordedResponse) -> int:
        """Append a candidate response; returns its turn index."""
        turn = response.turn_index
        if turn not in self._responses:
            self._responses[turn] = response
        return turn

    def get_response(self, turn_index: int) -> Optional[RecordedResponse]:
        return self._responses.get(turn_index)

    def get_responses(self) -> List[RecordedResponse]:
        return list(self._responses.values())

    # ---- Q/A pairs ----------------------------------------------------------

    def get_qa_pairs(
        self,
    ) -> List[Tuple[RecordedQuestion, Optional[RecordedResponse]]]:
        pairs: List[Tuple[RecordedQuestion, Optional[RecordedResponse]]] = []
        for turn, question in self._questions.items():
            response = self._responses.get(turn)
            pairs.append((question, response))
        return pairs

    # ---- Follow-up chain operations ------------------------------------------

    def start_follow_up_chain(self, origin_turn_index: int) -> None:
        if origin_turn_index not in self._follow_up_chains:
            self._follow_up_chains[origin_turn_index] = FollowUpRecord(
                origin_turn_index=origin_turn_index,
            )

    def advance_follow_up_chain(self, origin_turn_index: int, turn_index: int) -> None:
        chain = self._follow_up_chains.get(origin_turn_index)
        if chain:
            chain.add_turn(turn_index)

    def get_follow_up_chains(self) -> List[FollowUpRecord]:
        return list(self._follow_up_chains.values())

    # ---- Serialisation -------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "questions": [q.to_dict() for q in self._questions.values()],
            "responses": [r.to_dict() for r in self._responses.values()],
            "follow_up_chains": [c.to_dict() for c in self._follow_up_chains.values()],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionHistory":
        self = cls(session_id=data.get("session_id", ""))
        for qd in data.get("questions", []):
            q = RecordedQuestion(
                turn_index=qd["turn_index"],
                question_text=qd["question_text"],
                topic=qd.get("topic"),
                difficulty=qd.get("difficulty"),
                target_category=qd.get("target_category"),
                asked_at=qd.get("asked_at"),
                is_follow_up=qd.get("is_follow_up", False),
                parent_turn_index=qd.get("parent_turn_index"),
            )
            self._questions[q.turn_index] = q

        for rd in data.get("responses", []):
            r = RecordedResponse(
                turn_index=rd["turn_index"],
                response_text=rd["response_text"],
                quality_score=rd.get("quality_score"),
                detected_at=rd.get("detected_at"),
            )
            self._responses[r.turn_index] = r

        for cd in data.get("follow_up_chains", []):
            chain = FollowUpRecord(
                origin_turn_index=cd["origin_turn_index"],
                chain_depth=cd.get("chain_depth", 0),
                is_exhausted=cd.get("is_exhausted", False),
                follow_up_indices=cd.get("follow_up_indices", []),
            )
            self._follow_up_chains[chain.origin_turn_index] = chain

        return self

    def __repr__(self) -> str:
        return (
            f"SessionHistory(session_id={self.session_id!r}, "
            f"questions={len(self._questions)}, "
            f"responses={len(self._responses)})"
        )
