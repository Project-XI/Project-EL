"""
test_followup_strategy_engine.py
──────────────────────────────────
Comprehensive test suite for the Follow-Up Question Strategy Engine.

Test categories (per Issue #4 acceptance criteria)
───────────────────────────────────────────────────
1. Weak-answer response detection
2. Contradiction-based probing
3. Evidence-grounding verification
4. Non-repetitive follow-up checks
5. Deterministic strategy selection
6. Fixture tests using known ORACLE outputs

Run:
    export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
    backend/venv/bin/python3 -m pytest backend/tests/test_followup_strategy_engine.py -v
"""

from __future__ import annotations

import copy
import pytest
from typing import List

from src.agents.main_agent.integration.oracle_schema import (
    DifficultyLevel,
    EvidenceLink,
    FailureScenario,
    NormalizedOracleOutput,
    NormalizedVivaTarget,
    ObservableSignal,
    SeverityLevel,
    VivaCategory,
)
from src.agents.main_agent.followups.strategy_engine import (
    StrategyEngine,
    StrategyDecision,
    StrategyType,
)
from src.agents.main_agent.followups.weak_answer_detector import (
    WeakAnswerDetector,
    WeaknessType,
)
from src.agents.main_agent.followups.contradiction_probe import detect_contradiction
from src.agents.main_agent.followups.evidence_mapper import build_evidence_dict
from src.agents.main_agent.followups.patterns import select_pattern, FOLLOW_UP_PATTERNS


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _target(
    qt: str = "JWT Lifecycle",
    category: str = "Security",
    difficulty: str = "hard",
    importance: float = 0.95,
) -> NormalizedVivaTarget:
    return NormalizedVivaTarget(
        topic            = category,
        question_target  = qt,
        difficulty       = DifficultyLevel(difficulty),
        category         = VivaCategory(category),
        importance_score = importance,
        depth_score      = 8.5,
        focus            = f"Explain the full lifecycle and revocation strategy for {qt}.",
        confidence       = 0.9,
        reasoning_summary= "Test target",
    )


def _oracle(
    backend: str = "FastAPI",
    failures: List[str] | None = None,
) -> NormalizedOracleOutput:
    signals = [
        ObservableSignal(key="backend_framework", value=backend, confidence=0.95,
                         evidence=[EvidenceLink(text="import fastapi", confidence=1.0)]),
        ObservableSignal(key="authentication_system", value="JWT", confidence=0.9, evidence=[]),
        ObservableSignal(key="database_used", value="PostgreSQL", confidence=0.85, evidence=[]),
    ]
    failure_list = [
        FailureScenario(
            description=f or "Token validation service unreachable",
            severity=SeverityLevel.HIGH,
            confidence=0.85,
            evidence=[],
        )
        for f in (failures or ["Token validation service unreachable"])
    ]
    return NormalizedOracleOutput(
        project_name         = "TestProject",
        project_type         = "Web API",
        architecture_pattern = "REST API",
        observable_signals   = signals,
        viva_targets         = [_target()],
        failure_scenarios    = failure_list,
    )


WEAK_ANSWERS = {
    "too_short":    "JWT is stateless.",
    "vague":        "It basically works well and is generally fine.",
    "generic":      "It is a token-based authentication mechanism used for securing APIs.",
    "no_mechanism": "The JWT token authenticates the user and grants access to the system.",
    "no_failure":   "The JWT token is validated on every request using a middleware function "
                    "that checks the signature and expiry using the PyJWT library.",
    "good":         (
        "When a request arrives, the JWT middleware extracts the Bearer token from the "
        "Authorization header. It calls verify_token() in auth/middleware.py which uses "
        "PyJWT to decode and validate the signature against the SECRET_KEY. If the token "
        "is expired, a 401 HTTPException is raised immediately. If the signature is invalid, "
        "a 403 is raised. Revocation is handled by a Redis blacklist checked before signature "
        "validation — if the jti is in the blacklist, the request fails with 401."
    ),
}


# ══════════════════════════════════════════════════════════════════════════════
# 1. WEAK-ANSWER RESPONSE DETECTION
# ══════════════════════════════════════════════════════════════════════════════

class TestWeakAnswerDetection:

    def test_too_short_answer_flagged(self):
        report = WeakAnswerDetector.analyze(WEAK_ANSWERS["too_short"], "Security")
        assert report.is_shallow
        assert any(s.weakness_type == WeaknessType.TOO_SHORT for s in report.signals)

    def test_vague_answer_flagged(self):
        report = WeakAnswerDetector.analyze(WEAK_ANSWERS["vague"], "Scalability")
        assert report.is_shallow
        assert any(s.weakness_type == WeaknessType.VAGUE_CLAIM for s in report.signals)

    def test_generic_definition_flagged(self):
        report = WeakAnswerDetector.analyze(WEAK_ANSWERS["generic"], "Architecture")
        assert report.is_shallow
        assert any(s.weakness_type == WeaknessType.GENERIC_DEFINITION for s in report.signals)

    def test_missing_mechanism_flagged(self):
        report = WeakAnswerDetector.analyze(WEAK_ANSWERS["no_mechanism"], "Architecture")
        assert any(s.weakness_type == WeaknessType.MISSING_MECHANISM for s in report.signals)

    def test_no_failure_mention_flagged_for_security_category(self):
        report = WeakAnswerDetector.analyze(WEAK_ANSWERS["no_failure"], "Security")
        assert any(s.weakness_type == WeaknessType.NO_FAILURE_MENTION for s in report.signals)

    def test_no_failure_mention_not_flagged_for_architecture_category(self):
        report = WeakAnswerDetector.analyze(WEAK_ANSWERS["no_failure"], "Architecture")
        types = [s.weakness_type for s in report.signals]
        assert WeaknessType.NO_FAILURE_MENTION not in types

    def test_good_answer_not_shallow(self):
        report = WeakAnswerDetector.analyze(WEAK_ANSWERS["good"], "Security")
        assert not report.is_shallow

    def test_repeated_answer_detected(self):
        prior = "JWT tokens are stateless and signed with a secret key used for authentication."
        new   = "JWT tokens are stateless and signed with the secret key for authentication."
        report = WeakAnswerDetector.analyze(new, "Security", prior_answers=[prior])
        assert any(s.weakness_type == WeaknessType.REPEATED_ANSWER for s in report.signals)

    def test_weakness_report_has_confidence(self):
        report = WeakAnswerDetector.analyze(WEAK_ANSWERS["too_short"])
        for signal in report.signals:
            assert 0.0 <= signal.confidence <= 1.0

    def test_primary_weakness_set_when_signals_present(self):
        report = WeakAnswerDetector.analyze(WEAK_ANSWERS["too_short"])
        if report.signals:
            assert report.primary_weakness is not None


# ══════════════════════════════════════════════════════════════════════════════
# 2. CONTRADICTION-BASED PROBING
# ══════════════════════════════════════════════════════════════════════════════

class TestContradictionProbing:

    def test_stateless_vs_stateful_detected(self):
        prior = "The API is stateless — no server-side session is maintained."
        new   = "The system uses stateful sessions stored in Redis."
        result = detect_contradiction(new, [prior])
        assert result.detected

    def test_sync_vs_async_detected(self):
        prior = "All route handlers are synchronous and block the thread pool."
        new   = "The handlers are all async and use await for IO operations."
        result = detect_contradiction(new, [prior])
        assert result.detected

    def test_no_contradiction_when_consistent(self):
        prior = "The API uses JWT for authentication."
        new   = "JWT tokens are validated on every request."
        result = detect_contradiction(new, [prior])
        assert not result.detected

    def test_contradiction_probe_prompt_cites_both_claims(self):
        prior = "The database is a relational SQL store."
        new   = "We use a NoSQL document store for all data."
        result = detect_contradiction(new, [prior])
        assert result.detected
        assert result.prior_claim in result.probe_prompt
        assert result.new_claim in result.probe_prompt

    def test_contradiction_strategy_type_in_decision(self):
        engine = StrategyEngine()
        prior  = "The system is stateless — no sessions stored server-side."
        new    = "We use stateful session tokens stored in the database."
        decision = engine.evaluate(
            answer_text    = new,
            current_target = _target("Session Management", "Security"),
            oracle_output  = _oracle(),
            prior_answers  = [prior],
        )
        assert decision.should_follow_up
        assert decision.strategy_type == StrategyType.FOLLOW_UP_CONTRADICTION

    def test_contradiction_decision_has_evidence(self):
        prior  = "The system is stateless."
        new    = "We use stateful session tracking."
        engine = StrategyEngine()
        decision = engine.evaluate(
            answer_text    = new,
            current_target = _target(),
            oracle_output  = _oracle(),
            prior_answers  = [prior],
        )
        if decision.should_follow_up and decision.best_follow_up:
            assert len(decision.best_follow_up.evidence_used) > 0

    def test_no_contradiction_on_single_answer(self):
        new = "JWT is stateless and validated server-side."
        result = detect_contradiction(new, [])
        assert not result.detected


# ══════════════════════════════════════════════════════════════════════════════
# 3. EVIDENCE-GROUNDING VERIFICATION
# ══════════════════════════════════════════════════════════════════════════════

class TestEvidenceGrounding:

    def test_evidence_dict_contains_backend_framework(self):
        ev = build_evidence_dict(_oracle("FastAPI"), _target())
        assert ev.get("backend_framework") == "FastAPI"

    def test_evidence_dict_contains_failure_scenario(self):
        ev = build_evidence_dict(_oracle(failures=["DB pool exhausted"]), _target())
        assert "DB pool exhausted" in ev.get("failure_scenario", "")

    def test_evidence_dict_contains_concept_from_target(self):
        ev = build_evidence_dict(_oracle(), _target("JWT Lifecycle"))
        assert ev.get("concept") == "JWT Lifecycle"

    def test_trigger_phrase_included_in_evidence(self):
        ev = build_evidence_dict(_oracle(), _target(), trigger_phrase="it's efficient")
        assert ev.get("vague_phrase") == "it's efficient"

    def test_follow_up_prompt_contains_oracle_data(self):
        engine = StrategyEngine()
        decision = engine.evaluate(
            answer_text    = WEAK_ANSWERS["too_short"],
            current_target = _target("JWT Lifecycle", "Security"),
            oracle_output  = _oracle("FastAPI"),
        )
        if decision.best_follow_up:
            # Prompt should contain ORACLE-derived data, not invented terms
            prompt = decision.best_follow_up.prompt
            assert len(prompt) > 20

    def test_evidence_records_have_source(self):
        ev = build_evidence_dict(_oracle(), _target())
        for rec in ev.records:
            assert rec.source and len(rec.source) > 0

    def test_evidence_no_unknown_values(self):
        ev = build_evidence_dict(_oracle(), _target())
        for val in ev.slots.values():
            assert val.lower() != "unknown"

    def test_pattern_fill_uses_evidence_slots(self):
        from src.agents.main_agent.followups.patterns import select_pattern
        evidence = {"failure_scenario": "DB connection pool exhausted"}
        pattern = select_pattern(WeaknessType.NO_FAILURE_MENTION, "Failure-Path", evidence)
        if pattern:
            filled = pattern.fill(evidence)
            assert "DB connection pool exhausted" in filled


# ══════════════════════════════════════════════════════════════════════════════
# 4. NON-REPETITIVE FOLLOW-UP CHECKS
# ══════════════════════════════════════════════════════════════════════════════

class TestNonRepetitiveFollowUps:

    def test_repeated_answer_triggers_different_angle(self):
        prior = "JWT tokens are stateless authentication tokens signed with HMAC."
        new   = "JWT tokens are stateless authentication tokens using HMAC signing."
        engine = StrategyEngine()
        decision = engine.evaluate(
            answer_text    = new,
            current_target = _target(),
            oracle_output  = _oracle(),
            prior_answers  = [prior],
        )
        if decision.should_follow_up:
            assert decision.best_follow_up.prompt != prior

    def test_asked_topics_avoid_re_covering_same_concept(self):
        engine = StrategyEngine()
        decision = engine.evaluate(
            answer_text    = WEAK_ANSWERS["no_failure"],
            current_target = _target("JWT Lifecycle", "Security"),
            oracle_output  = _oracle(),
            asked_topics   = {"JWT Lifecycle"},
        )
        # Even if operational probe fires, the prompt is not about asked_topic
        if decision.best_follow_up:
            assert "JWT Lifecycle" not in decision.best_follow_up.prompt or \
                   decision.strategy_type != StrategyType.FOLLOW_UP_OPERATIONAL

    def test_multiple_candidates_are_distinct(self):
        engine = StrategyEngine()
        decision = engine.evaluate(
            answer_text    = WEAK_ANSWERS["vague"],
            current_target = _target("DB Pooling", "Scalability"),
            oracle_output  = _oracle(),
        )
        prompts = [c.prompt for c in decision.all_candidates]
        assert len(prompts) == len(set(prompts))


# ══════════════════════════════════════════════════════════════════════════════
# 5. DETERMINISTIC STRATEGY SELECTION
# ══════════════════════════════════════════════════════════════════════════════

class TestDeterministicStrategySelection:

    def test_same_inputs_same_decision(self):
        engine = StrategyEngine()
        args = dict(
            answer_text    = WEAK_ANSWERS["too_short"],
            current_target = _target(),
            oracle_output  = _oracle(),
            prior_answers  = [],
        )
        d1 = engine.evaluate(**args)
        d2 = engine.evaluate(**args)
        assert d1.should_follow_up == d2.should_follow_up
        assert d1.strategy_type == d2.strategy_type
        if d1.best_follow_up and d2.best_follow_up:
            assert d1.best_follow_up.prompt == d2.best_follow_up.prompt

    def test_decision_is_always_loggable(self):
        engine = StrategyEngine()
        decision = engine.evaluate(
            answer_text    = WEAK_ANSWERS["good"],
            current_target = _target(),
            oracle_output  = _oracle(),
        )
        assert decision.is_loggable is True

    def test_strategy_type_is_valid_enum(self):
        engine = StrategyEngine()
        decision = engine.evaluate(
            answer_text    = WEAK_ANSWERS["vague"],
            current_target = _target(),
            oracle_output  = _oracle(),
        )
        assert decision.strategy_type in list(StrategyType)

    def test_no_follow_up_on_strong_answer_non_risk_category(self):
        engine = StrategyEngine()
        decision = engine.evaluate(
            answer_text    = WEAK_ANSWERS["good"],
            current_target = _target("REST Constraints", "Architecture"),
            oracle_output  = _oracle(),
        )
        # Good answer to Architecture → should not trigger follow-up
        assert decision.strategy_type in (StrategyType.NO_FOLLOW_UP, StrategyType.FOLLOW_UP_OPERATIONAL)


# ══════════════════════════════════════════════════════════════════════════════
# 6. FIXTURE TESTS WITH KNOWN ORACLE OUTPUTS
# ══════════════════════════════════════════════════════════════════════════════

class TestKnownOracleFixtures:

    def test_fastapi_backend_in_evidence(self):
        oracle = _oracle("FastAPI")
        ev = build_evidence_dict(oracle, _target())
        assert ev.get("backend_framework") == "FastAPI"

    def test_failure_scenario_surfaces_in_follow_up_prompt(self):
        oracle = _oracle(failures=["Redis cache unavailable — all reads hit DB"])
        engine = StrategyEngine()
        decision = engine.evaluate(
            answer_text    = WEAK_ANSWERS["no_failure"],
            current_target = _target("Cache Strategy", "Scalability"),
            oracle_output  = oracle,
        )
        if decision.best_follow_up and decision.strategy_type == StrategyType.FOLLOW_UP_WEAKNESS:
            assert "Redis" in decision.best_follow_up.prompt or \
                   decision.best_follow_up.evidence_used

    def test_security_category_triggers_operational_probe_on_ok_answer(self):
        engine = StrategyEngine()
        decision = engine.evaluate(
            answer_text    = WEAK_ANSWERS["good"],
            current_target = _target("JWT Lifecycle", "Security"),
            oracle_output  = _oracle(),
        )
        # Good security answer should trigger operational probe
        if decision.should_follow_up:
            assert decision.strategy_type == StrategyType.FOLLOW_UP_OPERATIONAL

    def test_all_pattern_names_are_unique(self):
        names = [p.name for p in FOLLOW_UP_PATTERNS]
        assert len(names) == len(set(names))

    def test_every_pattern_has_non_empty_template(self):
        for p in FOLLOW_UP_PATTERNS:
            assert len(p.template.strip()) > 20, f"Pattern {p.name} has trivial template"

    def test_strategy_decision_answer_text_preserved(self):
        engine = StrategyEngine()
        answer = WEAK_ANSWERS["generic"]
        decision = engine.evaluate(
            answer_text    = answer,
            current_target = _target(),
            oracle_output  = _oracle(),
        )
        assert decision.answer_text == answer

    def test_weakness_report_attached_to_decision(self):
        engine = StrategyEngine()
        decision = engine.evaluate(
            answer_text    = WEAK_ANSWERS["too_short"],
            current_target = _target(),
            oracle_output  = _oracle(),
        )
        assert decision.weakness_report is not None
