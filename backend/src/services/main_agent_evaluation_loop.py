"""
Stage 8 - MAIN Agent Evaluation Loop

Deterministic evaluation loop executed after each finalized response.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from src.models.intelligence_artifact import VivaTarget
from src.models.stage_7_8_9 import ContradictionChainEntry, EvaluationArtifact


class MainAgentEvaluationLoop:
    """Continuous technical evaluation engine for live viva."""

    def __init__(self, main_orchestrator):
        self.main_orchestrator = main_orchestrator
        self.evaluation_history: List[EvaluationArtifact] = []
        self.contradiction_chain: List[ContradictionChainEntry] = []
        self.topic_coverage: Dict[str, float] = {}

    def process_finalized_response(
        self,
        turn_index: int,
        target: VivaTarget,
        response_text: str,
    ) -> Tuple[Dict[str, Any], EvaluationArtifact, Optional[str]]:
        """
        Process full evaluation cycle for one response.

        Flow:
        Question -> Response -> Evaluation -> Session Memory Update ->
        Contradiction Analysis -> Follow-Up Generation
        """

        base_evaluation = self.main_orchestrator.evaluate_answer(response_text, target)

        implementation_specificity = self._score_implementation_specificity(response_text)
        runtime_understanding = self._score_runtime_understanding(response_text)
        operational_reasoning = self._score_operational_reasoning(response_text)
        architectural_understanding = self._score_architectural_understanding(response_text)
        failure_path_awareness = self._score_failure_path_awareness(response_text)
        tradeoff_understanding = self._score_tradeoff_understanding(response_text)
        consistency_score = self._score_consistency(base_evaluation)

        implementation_familiarity = round(
            (
                implementation_specificity
                + runtime_understanding
                + operational_reasoning
                + architectural_understanding
                + failure_path_awareness
                + tradeoff_understanding
                + consistency_score
            )
            / 7.0,
            3,
        )

        category_key = target.category.value
        current_coverage = float(self.topic_coverage.get(category_key, 0.0))
        coverage_increment = float(base_evaluation.get("coverage_score", 0.0))
        self.topic_coverage[category_key] = min(1.0, round(current_coverage + coverage_increment * 0.4, 3))

        for contradiction in base_evaluation.get("contradictions", []):
            self.contradiction_chain.append(
                ContradictionChainEntry(
                    chain_id=f"chain_{self.main_orchestrator.session_state.session_id}_{len(self.contradiction_chain)}",
                    target_id=target.target_id,
                    previous_claim=contradiction.get("previous", "unknown"),
                    current_claim=contradiction.get("current", "unknown"),
                    severity=contradiction.get("severity", "MEDIUM"),
                    turn_index=turn_index,
                )
            )

        follow_up = self._generate_runtime_aware_follow_up(target, response_text, base_evaluation)
        if not follow_up:
            follow_up = self.main_orchestrator.generate_follow_up(base_evaluation, target)

        evaluation_artifact = EvaluationArtifact(
            session_id=self.main_orchestrator.session_state.session_id,
            turn_index=turn_index,
            target_id=target.target_id,
            implementation_specificity=implementation_specificity,
            runtime_understanding=runtime_understanding,
            operational_reasoning=operational_reasoning,
            architectural_understanding=architectural_understanding,
            failure_path_awareness=failure_path_awareness,
            tradeoff_understanding=tradeoff_understanding,
            consistency_score=consistency_score,
            implementation_familiarity=implementation_familiarity,
            topic_coverage=dict(self.topic_coverage),
            weak_areas=list(self.main_orchestrator.weak_areas_detected),
            follow_up_chain=[follow_up] if follow_up else [],
            contradiction_chain=list(self.contradiction_chain),
        )

        self.evaluation_history.append(evaluation_artifact)

        enriched = {
            **base_evaluation,
            "implementation_specificity": implementation_specificity,
            "runtime_understanding": runtime_understanding,
            "operational_reasoning": operational_reasoning,
            "architectural_understanding": architectural_understanding,
            "failure_path_awareness": failure_path_awareness,
            "tradeoff_understanding": tradeoff_understanding,
            "consistency_score": consistency_score,
            "implementation_familiarity": implementation_familiarity,
            "topic_coverage": dict(self.topic_coverage),
            "contradiction_chain_length": len(self.contradiction_chain),
            "evaluated_at": datetime.utcnow().isoformat(),
        }

        return enriched, evaluation_artifact, follow_up

    def _score_implementation_specificity(self, answer: str) -> float:
        keywords = ["middleware", "controller", "service", "repository", "handler", "function"]
        return self._keyword_score(answer, keywords)

    def _score_runtime_understanding(self, answer: str) -> float:
        keywords = ["request", "response", "latency", "concurrent", "queue", "retry"]
        return self._keyword_score(answer, keywords)

    def _score_operational_reasoning(self, answer: str) -> float:
        keywords = ["monitor", "rollback", "deploy", "alert", "incident", "slo"]
        return self._keyword_score(answer, keywords)

    def _score_architectural_understanding(self, answer: str) -> float:
        keywords = ["architecture", "module", "dependency", "layer", "interface", "boundary"]
        return self._keyword_score(answer, keywords)

    def _score_failure_path_awareness(self, answer: str) -> float:
        keywords = ["failure", "fallback", "timeout", "circuit", "error", "exception"]
        return self._keyword_score(answer, keywords)

    def _score_tradeoff_understanding(self, answer: str) -> float:
        keywords = ["trade-off", "tradeoff", "cost", "throughput", "consistency", "availability"]
        return self._keyword_score(answer, keywords)

    def _score_consistency(self, base_evaluation: Dict[str, Any]) -> float:
        contradiction_penalty = min(1.0, 0.25 * len(base_evaluation.get("contradictions", [])))
        red_flag_penalty = min(1.0, 0.1 * len(base_evaluation.get("red_flags", [])))
        return round(max(0.0, 1.0 - contradiction_penalty - red_flag_penalty), 3)

    def _keyword_score(self, answer: str, keywords: List[str]) -> float:
        if not answer.strip():
            return 0.0
        normalized = answer.lower()
        hits = sum(1 for key in keywords if key in normalized)
        return round(min(1.0, hits / max(1, len(keywords) // 2)), 3)

    def _generate_runtime_aware_follow_up(
        self,
        target: VivaTarget,
        answer: str,
        base_evaluation: Dict[str, Any],
    ) -> Optional[str]:
        """Generate technical follow-up with implementation/runtime focus."""

        if base_evaluation.get("depth_level") in {"DEEP", "EXPERT"} and not base_evaluation.get("contradictions"):
            return None

        answer_lower = answer.lower()
        question_lower = target.question.lower()

        if "redis" in answer_lower or "cache" in question_lower:
            return "Where exactly is Redis used in your request lifecycle, and how do you prevent stale cache during rapid updates?"

        if "database" in answer_lower or "db" in answer_lower or "database" in question_lower:
            return "What is the exact failure path when the database call times out, and where is retry or fallback enforced in code?"

        if "jwt" in answer_lower or "auth" in answer_lower or "token" in answer_lower:
            return "Point to the validation boundary for JWT in your flow: middleware, controller, or both, and explain why that placement is safe."

        if base_evaluation.get("contradictions"):
            contradiction = base_evaluation["contradictions"][0]
            return (
                "You stated two different implementation behaviors: "
                f"{contradiction.get('previous')} vs {contradiction.get('current')}. "
                "Which one is accurate in runtime, and where in code is it enforced?"
            )

        return "Describe the exact runtime path for this behavior from entry point to failure handling, including one concrete code-level boundary."
