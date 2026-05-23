from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .schemas import TranscriptRecord


@dataclass(frozen=True)
class ReplayStep:
    order_index: int
    step_id: str
    question_text: str
    answer_text: Optional[str]
    evaluation: Optional[Dict[str, Any]]
    contradiction_events: List[Dict[str, Any]]
    fairness_events: List[Dict[str, Any]]
    follow_up_questions: List[str]
    evidence_links: List[str]


class TranscriptReplay:
    """Reconstructs ordered viva steps from a transcript record."""

    @staticmethod
    def reconstruct(record: TranscriptRecord) -> List[ReplayStep]:
        steps: List[ReplayStep] = []
        for turn in sorted(record.turns, key=lambda item: (item.order_index, item.created_at)):
            steps.append(
                ReplayStep(
                    order_index=turn.order_index,
                    step_id=turn.step_id,
                    question_text=turn.question_text,
                    answer_text=turn.normalized_answer_text or turn.answer_text,
                    evaluation=turn.evaluation,
                    contradiction_events=list(turn.contradiction_events),
                    fairness_events=list(turn.fairness_events),
                    follow_up_questions=list(turn.follow_up_questions),
                    evidence_links=list(turn.evidence_links),
                )
            )
        return steps

    @staticmethod
    def export_replay_payload(record: TranscriptRecord) -> Dict[str, Any]:
        return {
            "schema_version": record.schema_version,
            "session_id": record.session_id,
            "turns": [
                {
                    "order_index": step.order_index,
                    "step_id": step.step_id,
                    "question_text": step.question_text,
                    "answer_text": step.answer_text,
                    "evaluation": step.evaluation,
                    "contradiction_events": step.contradiction_events,
                    "fairness_events": step.fairness_events,
                    "follow_up_questions": step.follow_up_questions,
                    "evidence_links": step.evidence_links,
                }
                for step in TranscriptReplay.reconstruct(record)
            ],
            "events": [event.model_dump(mode="json") for event in sorted(record.events, key=lambda event: event.order_index)],
        }
