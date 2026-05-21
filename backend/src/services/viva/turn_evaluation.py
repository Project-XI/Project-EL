from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from pydantic import BaseModel, Field

from src.models.context import InconsistencyFlag, VivaTarget
from src.services.voice.models.transcript_models import VoiceTurnTranscript


_REQUIRED_DOMAINS = [
    "architecture",
    "runtime",
    "failure-path",
    "scalability",
    "security",
    "tradeoff",
]

_STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "to",
    "of",
    "for",
    "in",
    "on",
    "is",
    "are",
    "with",
    "this",
    "that",
    "your",
    "from",
    "what",
    "when",
    "where",
    "how",
}


class ContradictionEvent(BaseModel):
    concept: str
    previous_claim: str
    current_claim: str
    previous_turn_id: str
    current_turn_id: str
    evidence_previous: str
    evidence_current: str


class FollowUpPlan(BaseModel):
    question: str
    reason: str
    category: str
    parent_turn_id: str


class TurnEvaluationResult(BaseModel):
    session_id: str
    turn_id: str
    question_text: str
    response_text: str
    category: str
    relevance_score: float
    weak_areas: List[str] = Field(default_factory=list)
    contradiction_events: List[ContradictionEvent] = Field(default_factory=list)
    inconsistency_flags: List[InconsistencyFlag] = Field(default_factory=list)
    follow_ups: List[FollowUpPlan] = Field(default_factory=list)
    reasoning_depth_state: str
    implementation_familiarity_state: str
    topic_coverage_delta: Dict[str, int] = Field(default_factory=dict)
    evidence: Dict[str, Any] = Field(default_factory=dict)


class RuntimeVivaState(BaseModel):
    session_id: str
    turn_index: int = 0
    weak_areas: List[str] = Field(default_factory=list)
    contradiction_memory: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    topic_coverage: Dict[str, int] = Field(default_factory=dict)
    follow_up_chain: List[Dict[str, Any]] = Field(default_factory=list)
    asked_questions: List[str] = Field(default_factory=list)
    implementation_familiarity_state: str = "unknown"
    runtime_reasoning_depth_state: str = "unknown"


@dataclass(frozen=True)
class _Claim:
    concept: str
    polarity: str


class DeterministicTurnEvaluator:
    """Deterministic turn evaluator for closed-loop technical viva orchestration."""

    def evaluate_turn(
        self,
        *,
        state: RuntimeVivaState,
        target: VivaTarget,
        turn: VoiceTurnTranscript,
        inconsistency_flags: Optional[Sequence[InconsistencyFlag]] = None,
    ) -> Tuple[TurnEvaluationResult, RuntimeVivaState]:
        response_text = (turn.normalized_transcript.normalized_text or "").strip()
        category = (target.category or target.topic or "runtime").strip().lower()
        relevance_score, overlap = self._relevance_score(target=target, response_text=response_text)

        weak_areas = list(state.weak_areas)
        target_area = (target.question_target or target.topic or "runtime_behavior").strip()
        if relevance_score < 0.45 and target_area not in weak_areas:
            weak_areas.append(target_area)

        contradiction_events, contradiction_memory = self._detect_contradictions(
            prior_memory=state.contradiction_memory,
            response_text=response_text,
            turn_id=turn.turn_id,
        )

        topic_coverage = dict(state.topic_coverage)
        topic_coverage[category] = topic_coverage.get(category, 0) + 1

        reasoning_depth_state = self._reasoning_depth_state(response_text)
        familiarity_state = self._implementation_familiarity_state(response_text)

        follow_ups = self._generate_followups(
            target=target,
            turn=turn,
            response_text=response_text,
            relevance_score=relevance_score,
            contradiction_events=contradiction_events,
            asked_questions=state.asked_questions,
        )

        state_updates = RuntimeVivaState(
            session_id=state.session_id,
            turn_index=state.turn_index + 1,
            weak_areas=weak_areas,
            contradiction_memory=contradiction_memory,
            topic_coverage=topic_coverage,
            follow_up_chain=state.follow_up_chain
            + [
                {
                    "turn_id": turn.turn_id,
                    "question": turn.question_text,
                    "follow_ups": [f.model_dump() for f in follow_ups],
                }
            ],
            asked_questions=state.asked_questions + [turn.question_text],
            implementation_familiarity_state=familiarity_state,
            runtime_reasoning_depth_state=reasoning_depth_state,
        )

        result = TurnEvaluationResult(
            session_id=state.session_id,
            turn_id=turn.turn_id,
            question_text=turn.question_text,
            response_text=response_text,
            category=category,
            relevance_score=relevance_score,
            weak_areas=weak_areas,
            contradiction_events=contradiction_events,
            inconsistency_flags=list(inconsistency_flags or []),
            follow_ups=follow_ups,
            reasoning_depth_state=reasoning_depth_state,
            implementation_familiarity_state=familiarity_state,
            topic_coverage_delta={category: 1},
            evidence={
                "keyword_overlap": overlap,
                "required_domains": _REQUIRED_DOMAINS,
            },
        )

        return result, state_updates

    def missing_domains(self, state: RuntimeVivaState) -> List[str]:
        return [d for d in _REQUIRED_DOMAINS if state.topic_coverage.get(d, 0) == 0]

    def _relevance_score(self, *, target: VivaTarget, response_text: str) -> Tuple[float, List[str]]:
        target_text = " ".join(
            [
                target.topic or "",
                target.question_target or "",
                target.focus or "",
                target.category or "",
            ]
        ).lower()
        target_tokens = self._tokens(target_text)
        response_tokens = self._tokens(response_text.lower())
        if not target_tokens:
            return 0.0, []

        overlap = sorted(target_tokens.intersection(response_tokens))
        score = len(overlap) / max(1, min(10, len(target_tokens)))
        return round(min(1.0, score), 4), overlap

    def _tokens(self, text: str) -> set[str]:
        parts = re.findall(r"[a-zA-Z0-9_]+", text)
        return {p for p in parts if len(p) >= 4 and p not in _STOPWORDS}

    def _detect_contradictions(
        self,
        *,
        prior_memory: Dict[str, Dict[str, str]],
        response_text: str,
        turn_id: str,
    ) -> Tuple[List[ContradictionEvent], Dict[str, Dict[str, str]]]:
        memory = dict(prior_memory)
        contradictions: List[ContradictionEvent] = []

        claims = self._extract_claims(response_text)
        for claim in claims:
            previous = memory.get(claim.concept)
            if previous and previous.get("polarity") != claim.polarity:
                contradictions.append(
                    ContradictionEvent(
                        concept=claim.concept,
                        previous_claim=previous.get("polarity", "unknown"),
                        current_claim=claim.polarity,
                        previous_turn_id=previous.get("turn_id", "unknown"),
                        current_turn_id=turn_id,
                        evidence_previous=previous.get("evidence", ""),
                        evidence_current=response_text,
                    )
                )

            memory[claim.concept] = {
                "polarity": claim.polarity,
                "turn_id": turn_id,
                "evidence": response_text,
            }

        return contradictions, memory

    def _extract_claims(self, response_text: str) -> List[_Claim]:
        text = response_text.lower()
        concepts = [
            "jwt",
            "redis",
            "cache",
            "middleware",
            "database",
            "authentication",
            "auth",
            "transaction",
            "retry",
        ]
        claims: List[_Claim] = []

        for concept in concepts:
            if concept not in text:
                continue

            absent_patterns = [
                f"no {concept}",
                f"without {concept}",
                f"{concept} is not",
                f"{concept} isn't",
                f"{concept} not",
                f"does not use {concept}",
                f"doesn't use {concept}",
            ]
            polarity = "absent" if any(p in text for p in absent_patterns) else "present"
            claims.append(_Claim(concept=concept, polarity=polarity))

        return claims

    def _reasoning_depth_state(self, response_text: str) -> str:
        lower = response_text.lower()
        words = len(response_text.split())
        causal_markers = ["because", "when", "if", "fails", "failure", "path", "middleware", "request", "response"]
        markers = sum(1 for m in causal_markers if m in lower)
        if words >= 25 and markers >= 2:
            return "deep"
        if words >= 12 and markers >= 1:
            return "moderate"
        return "shallow"

    def _implementation_familiarity_state(self, response_text: str) -> str:
        lower = response_text.lower()
        specific_markers = ["middleware", "handler", "route", "function", "class", "module", "line", "endpoint", "401", "403", "500"]
        marker_hits = sum(1 for m in specific_markers if m in lower)
        if marker_hits >= 3:
            return "grounded"
        if marker_hits >= 1:
            return "partial"
        return "unclear"

    def _generate_followups(
        self,
        *,
        target: VivaTarget,
        turn: VoiceTurnTranscript,
        response_text: str,
        relevance_score: float,
        contradiction_events: Sequence[ContradictionEvent],
        asked_questions: Sequence[str],
    ) -> List[FollowUpPlan]:
        lower = response_text.lower()
        category = (target.category or target.topic or "runtime").lower()
        candidates: List[Tuple[str, str]] = []

        if "redis" in lower or "cache" in lower:
            candidates.extend(
                [
                    (
                        "Where exactly is Redis used in your request lifecycle?",
                        "Need concrete cache placement evidence.",
                    ),
                    (
                        "What happens if cache invalidation fails during concurrent writes?",
                        "Need failure-path clarity for cache coherence.",
                    ),
                ]
            )

        if "jwt" in lower or "auth" in lower or "authentication" in lower:
            candidates.extend(
                [
                    (
                        "Where is JWT validation enforced in your middleware chain?",
                        "Need exact validation point in execution path.",
                    ),
                    (
                        "What is the exact request lifecycle when JWT validation fails and returns 401?",
                        "Need deterministic failure path from token check to response.",
                    ),
                ]
            )

        if not candidates and (relevance_score < 0.45 or contradiction_events):
            by_category = {
                "architecture": "Trace the exact request path from entry route to persistence for this feature.",
                "runtime": "What blocks runtime execution in this path, and how is that prevented?",
                "failure-path": "If this component fails at runtime, what fallback path executes first?",
                "scalability": "Under 3x concurrent load, which resource saturates first and why?",
                "security": "Which code path returns security failure responses, and what evidence logs are emitted?",
                "tradeoff": "What measurable production cost did this design tradeoff introduce?",
            }
            candidates.append(
                (
                    by_category.get(category, "Show the concrete runtime path for this implementation detail."),
                    "Need implementation-specific runtime grounding.",
                )
            )

        followups: List[FollowUpPlan] = []
        for question, reason in candidates:
            if question in asked_questions:
                continue
            followups.append(
                FollowUpPlan(
                    question=question,
                    reason=reason,
                    category=category,
                    parent_turn_id=turn.turn_id,
                )
            )
            if len(followups) >= 2:
                break

        return followups
