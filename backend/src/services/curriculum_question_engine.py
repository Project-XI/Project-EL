"""
Stage 9 - Curriculum + Core Subject Questioning

Deterministically links implementation evidence to foundational subjects.
"""

from typing import Any, Dict, List, Optional, Tuple

from src.models.intelligence_artifact import IntelligenceArtifact
from src.models.stage_7_8_9 import (
    CoreSubject,
    CurriculumQuestion,
    CurriculumTransitionState,
)


class CurriculumQuestionEngine:
    """Implementation-linked curriculum questioning engine."""

    def __init__(self, artifact: IntelligenceArtifact, session_id: str):
        self.artifact = artifact
        self.state = CurriculumTransitionState(session_id=session_id)
        self.question_bank = self._build_question_bank()

    def should_start_transition(self, implementation_turns_completed: int) -> bool:
        """Transition after implementation-aware rounds are complete."""

        return implementation_turns_completed >= 2

    def start_transition(self) -> CurriculumTransitionState:
        self.state.started = True
        return self.state

    def get_next_question(self) -> Optional[CurriculumQuestion]:
        if not self.state.started:
            return None

        for question in self.question_bank:
            if question.question_id not in self.state.asked_questions:
                self.state.asked_questions.append(question.question_id)
                return question

        return None

    def evaluate_answer(self, question: CurriculumQuestion, answer: str) -> Tuple[float, bool]:
        """Return (score, subject_completed)."""

        normalized = answer.lower()
        hits = sum(1 for term in question.expected_coverage if term.lower() in normalized)
        score = round(min(1.0, hits / max(1, len(question.expected_coverage))), 3)

        subject_completed = score >= 0.6
        if subject_completed and question.subject not in self.state.completed_subjects:
            self.state.completed_subjects.append(question.subject)

        return score, subject_completed

    def _build_question_bank(self) -> List[CurriculumQuestion]:
        """Build deterministic curriculum set from implementation signals."""

        questions: List[CurriculumQuestion] = []
        q_index = 0

        backend = {k.lower(): str(v).lower() for k, v in self.artifact.backend_stack.items()}
        execution_text = " ".join(node.implementation_details.lower() for node in self.artifact.execution_graph_nodes)

        if "redis" in " ".join(backend.values()) or "cache" in execution_text:
            questions.append(
                CurriculumQuestion(
                    question_id=f"curr_{q_index}",
                    subject=CoreSubject.OPERATING_SYSTEMS,
                    prompt="Your project uses caching. Explain memory locality and eviction trade-offs relevant to this cache design.",
                    linked_implementation_signal="cache",
                    difficulty="MEDIUM",
                    expected_coverage=["memory", "eviction", "latency", "trade-off"],
                )
            )
            q_index += 1

        if "postgres" in " ".join(backend.values()) or "database" in " ".join(backend.keys()):
            questions.append(
                CurriculumQuestion(
                    question_id=f"curr_{q_index}",
                    subject=CoreSubject.DBMS,
                    prompt="In your database-backed flow, how do indexing and transactions affect consistency and query performance?",
                    linked_implementation_signal="database",
                    difficulty="MEDIUM",
                    expected_coverage=["index", "transaction", "consistency", "query"],
                )
            )
            q_index += 1

        if "async" in execution_text or "queue" in execution_text:
            questions.append(
                CurriculumQuestion(
                    question_id=f"curr_{q_index}",
                    subject=CoreSubject.DSA,
                    prompt="Your runtime path uses asynchronous behavior. Which data structures and scheduling considerations influence throughput under concurrency?",
                    linked_implementation_signal="async",
                    difficulty="HARD",
                    expected_coverage=["queue", "complexity", "concurrency", "throughput"],
                )
            )
            q_index += 1

        if "http" in execution_text or "request" in execution_text:
            questions.append(
                CurriculumQuestion(
                    question_id=f"curr_{q_index}",
                    subject=CoreSubject.COMPUTER_NETWORKS,
                    prompt="Map one request path in your project to HTTP/TCP behavior, including timeout and retry implications.",
                    linked_implementation_signal="networking",
                    difficulty="MEDIUM",
                    expected_coverage=["http", "tcp", "timeout", "retry"],
                )
            )
            q_index += 1

        if "auth" in execution_text or "jwt" in execution_text:
            questions.append(
                CurriculumQuestion(
                    question_id=f"curr_{q_index}",
                    subject=CoreSubject.SOFTWARE_ENGINEERING,
                    prompt="Relate your authentication implementation to secure design principles and boundary placement.",
                    linked_implementation_signal="authentication",
                    difficulty="HARD",
                    expected_coverage=["boundary", "validation", "security", "principle"],
                )
            )
            q_index += 1

        if not questions:
            questions.append(
                CurriculumQuestion(
                    question_id="curr_fallback_0",
                    subject=CoreSubject.SYSTEM_DESIGN,
                    prompt="Explain one architectural trade-off in your implementation and how it impacts runtime behavior.",
                    linked_implementation_signal="architecture",
                    difficulty="MEDIUM",
                    expected_coverage=["trade-off", "architecture", "runtime", "impact"],
                )
            )

        return questions
