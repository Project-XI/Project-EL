"""
strategy_engine.py
──────────────────
Central Follow-Up Question Strategy Engine for MAIN Agent.

Responsibilities
────────────────
- Receive a candidate answer + session context + ORACLE output.
- Detect weaknesses and contradictions.
- Select the best follow-up pattern grounded in available evidence.
- Return a StrategyDecision with the follow-up prompt and full audit trail.

Rules
─────
- Stateless class — receives all context as parameters, returns a decision.
- Deterministic: same inputs → same StrategyDecision.
- No LLM calls, no free-form generation, no ORACLE logic re-implementation.
- Every generated prompt is traceable to a weakness signal + evidence record.
- Never invents facts absent from NormalizedOracleOutput.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from src.agents.main_agent.integration.oracle_schema import (
    NormalizedOracleOutput,
    NormalizedVivaTarget,
)
from .contradiction_probe import ContradictionResult, detect_contradiction
from .evidence_mapper import EvidenceDict, build_evidence_dict, evidence_summary
from .patterns import FollowUpPattern, select_pattern
from .weak_answer_detector import WeaknessReport, WeaknessType, WeakAnswerDetector

logger = logging.getLogger(__name__)


# ── Decision types ────────────────────────────────────────────────────────────

class StrategyType(str, Enum):
    FOLLOW_UP_WEAKNESS      = "follow_up_weakness"       # Prompted by weak answer
    FOLLOW_UP_CONTRADICTION = "follow_up_contradiction"  # Prompted by contradiction
    FOLLOW_UP_OPERATIONAL   = "follow_up_operational"    # Operational / runtime probe
    NO_FOLLOW_UP            = "no_follow_up"             # Answer was sufficient


# ── Output contracts ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class FollowUpCandidate:
    """A single candidate follow-up prompt with its evidence audit trail."""
    prompt: str
    strategy_type: StrategyType
    weakness_type: Optional[WeaknessType]
    pattern_name: Optional[str]
    evidence_used: List[str]          # Human-readable evidence references
    confidence: float


@dataclass(frozen=True)
class StrategyDecision:
    """
    The complete output of StrategyEngine.evaluate().

    MAIN Agent acts on `should_follow_up` and presents `best_follow_up.prompt`.
    The full audit trail is in `weakness_report`, `contradiction`, and
    `best_follow_up.evidence_used`.
    """
    should_follow_up: bool
    strategy_type: StrategyType
    best_follow_up: Optional[FollowUpCandidate]
    all_candidates: List[FollowUpCandidate]
    weakness_report: Optional[WeaknessReport]
    contradiction: Optional[ContradictionResult]
    answer_text: str
    is_loggable: bool = True          # Always True — decisions are auditable


# ── Operational probe templates ───────────────────────────────────────────────
# Used when answer is OK but the category warrants a runtime/operational probe.

_OPERATIONAL_PROBES: dict[str, str] = {
    "Security":     (
        "The answer covers the concept. Now address the operational reality: "
        "how would you detect a breach of {concept} in production in this system? "
        "What does your logging and alerting look like?"
    ),
    "Scalability":  (
        "Assuming the answer is correct: at 10× current load, "
        "which component of {concept} becomes the first bottleneck? "
        "What metric would you monitor and what is the remediation?"
    ),
    "Failure-Path": (
        "Good. Now take it further: if {concept} fails silently "
        "(no exception raised), how would an operator discover the failure? "
        "Is there observability in this codebase for that path?"
    ),
    "Runtime":      (
        "Correct. What is the worst-case latency impact of {concept} "
        "on a single request under high concurrency? "
        "Point to where the thread or event-loop boundary sits."
    ),
}


# ── Strategy Engine ───────────────────────────────────────────────────────────

class StrategyEngine:
    """
    Stateless follow-up question strategy engine.

    Usage
    ─────
        engine = StrategyEngine()
        decision = engine.evaluate(
            answer_text     = candidate_answer,
            current_target  = viva_target,
            oracle_output   = normalized_oracle,
            prior_answers   = session_prior_answers,
        )
        if decision.should_follow_up:
            present(decision.best_follow_up.prompt)
    """

    # ── Primary entry point ───────────────────────────────────────────────────

    def evaluate(
        self,
        answer_text: str,
        current_target: NormalizedVivaTarget,
        oracle_output: NormalizedOracleOutput,
        prior_answers: Optional[List[str]] = None,
        asked_topics: Optional[set] = None,
    ) -> StrategyDecision:
        """
        Evaluate a candidate answer and return a StrategyDecision.

        Parameters
        ──────────
        answer_text    : Raw candidate answer string.
        current_target : The NormalizedVivaTarget that was just answered.
        oracle_output  : Full NormalizedOracleOutput for evidence extraction.
        prior_answers  : Earlier answers in this session (for contradiction + repetition).
        asked_topics   : Set of question_targets already covered (avoids repetition).
        """
        prior_answers = prior_answers or []
        asked_topics  = asked_topics or set()
        category      = current_target.category.value

        # ── Step 1: Build evidence dict ───────────────────────────────────────
        weakness_report = WeakAnswerDetector.analyze(
            answer_text      = answer_text,
            question_category= category,
            prior_answers    = prior_answers,
        )
        trigger_phrase = None
        if weakness_report.signals:
            trigger_phrase = weakness_report.signals[0].trigger_phrase

        evidence = build_evidence_dict(
            oracle_output   = oracle_output,
            current_target  = current_target,
            trigger_phrase  = trigger_phrase,
        )

        # ── Step 2: Contradiction check ───────────────────────────────────────
        contradiction = detect_contradiction(answer_text, prior_answers)

        candidates: List[FollowUpCandidate] = []

        # ── Step 3a: Contradiction-driven follow-up (highest priority) ────────
        if contradiction.detected:
            candidates.append(FollowUpCandidate(
                prompt         = contradiction.probe_prompt,
                strategy_type  = StrategyType.FOLLOW_UP_CONTRADICTION,
                weakness_type  = WeaknessType.CONTRADICTS_PRIOR,
                pattern_name   = "contradiction_probe",
                evidence_used  = [
                    f"prior_claim='{contradiction.prior_claim}'",
                    f"new_claim='{contradiction.new_claim}'",
                    f"conflict='{contradiction.conflicting_term}'",
                ],
                confidence     = contradiction.confidence,
            ))

        # ── Step 3b: Weakness-driven follow-ups ───────────────────────────────
        if weakness_report.is_shallow:
            for signal in weakness_report.signals:
                if signal.confidence < 0.70:
                    continue
                pattern = select_pattern(signal.weakness_type, category, evidence.slots)
                if pattern:
                    prompt = pattern.fill(evidence.slots)
                    candidates.append(FollowUpCandidate(
                        prompt         = prompt,
                        strategy_type  = StrategyType.FOLLOW_UP_WEAKNESS,
                        weakness_type  = signal.weakness_type,
                        pattern_name   = pattern.name,
                        evidence_used  = evidence_summary(evidence),
                        confidence     = signal.confidence,
                    ))

        # ── Step 3c: Operational probe (even for OK answers in certain cats) ──
        if not candidates and category in _OPERATIONAL_PROBES:
            concept = evidence.get("concept", current_target.question_target)
            if concept not in asked_topics:
                template = _OPERATIONAL_PROBES[category]
                prompt = template.format(concept=concept)
                candidates.append(FollowUpCandidate(
                    prompt         = prompt,
                    strategy_type  = StrategyType.FOLLOW_UP_OPERATIONAL,
                    weakness_type  = None,
                    pattern_name   = f"operational_{category.lower().replace('-','_')}",
                    evidence_used  = [f"oracle.category={category}", f"concept={concept}"],
                    confidence     = 0.65,
                ))

        # ── Step 4: Sort candidates by confidence descending ──────────────────
        candidates.sort(key=lambda c: -c.confidence)

        # ── Step 5: Build decision ────────────────────────────────────────────
        if candidates:
            best = candidates[0]
            logger.debug(
                "[StrategyEngine] follow-up selected: strategy=%s pattern=%s conf=%.2f",
                best.strategy_type, best.pattern_name, best.confidence,
            )
            return StrategyDecision(
                should_follow_up = True,
                strategy_type    = best.strategy_type,
                best_follow_up   = best,
                all_candidates   = candidates,
                weakness_report  = weakness_report,
                contradiction    = contradiction if contradiction.detected else None,
                answer_text      = answer_text,
            )

        logger.debug("[StrategyEngine] no follow-up warranted for category=%s", category)
        return StrategyDecision(
            should_follow_up = False,
            strategy_type    = StrategyType.NO_FOLLOW_UP,
            best_follow_up   = None,
            all_candidates   = [],
            weakness_report  = weakness_report,
            contradiction    = None,
            answer_text      = answer_text,
        )
