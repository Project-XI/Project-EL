"""Trust audit pipeline for ORACLE comparative validation.

This module flags unsupported assumptions, speculative reasoning, stale execution
graphs, contradictory evidence, and confidence misuse before outputs are used
in downstream evaluation or surfaced to users.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class TrustAuditSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TrustAuditFinding(BaseModel):
    category: str
    severity: TrustAuditSeverity
    subject: str
    message: str
    evidence: List[str] = Field(default_factory=list)
    recommendation: str


class TrustAuditReport(BaseModel):
    audited_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    overall_score: float
    should_block_output: bool
    findings: List[TrustAuditFinding] = Field(default_factory=list)
    summary: Dict[str, int] = Field(default_factory=dict)
    stale_execution_graph: bool = False
    unsupported_assumption_count: int = 0
    speculative_reasoning_count: int = 0
    contradictory_evidence_count: int = 0
    confidence_misuse_count: int = 0


class TrustAuditPipeline:
    """Deterministic trust audit for ORACLE outputs."""

    SPECULATIVE_MARKERS = (
        "maybe",
        "might",
        "could",
        "probably",
        "possibly",
        "appears to",
        "seems to",
        "likely",
    )
    GENERIC_VIVA_MARKERS = (
        "what is",
        "explain the",
        "how would you",
        "define",
        "describe the concept",
    )

    def __init__(self, stale_graph_age_hours: float = 24.0):
        self.stale_graph_age_hours = stale_graph_age_hours

    def audit(self, oracle_output: Dict[str, Any]) -> TrustAuditReport:
        findings: List[TrustAuditFinding] = []
        category_counts: Counter[str] = Counter()

        signals = self._normalize_claims(oracle_output.get("signals", []))
        failures = self._normalize_claims(oracle_output.get("failure_scenarios", []))
        viva_questions = self._normalize_claims(oracle_output.get("viva_questions", []))
        execution_graph = oracle_output.get("execution_graph", {}) or {}

        unsupported_assumptions = 0
        speculative_reasoning = 0
        contradictory_evidence = 0
        confidence_misuse = 0

        for claim in signals:
            subject = str(claim.get("name") or claim.get("signal_name") or claim.get("signal") or "signal")
            confidence = float(claim.get("confidence") or claim.get("oracle_confidence") or 0.0)
            evidence = self._extract_evidence(claim)
            text = self._claim_text(claim)

            if not evidence:
                unsupported_assumptions += 1
                findings.append(
                    TrustAuditFinding(
                        category="unsupported_assumption",
                        severity=TrustAuditSeverity.HIGH if confidence >= 0.8 else TrustAuditSeverity.MEDIUM,
                        subject=subject,
                        message="Signal lacks explicit evidence references.",
                        evidence=[],
                        recommendation="Attach code locations or execution trace evidence before publishing.",
                    )
                )

            if confidence >= 0.9 and len(evidence) < 2:
                confidence_misuse += 1
                findings.append(
                    TrustAuditFinding(
                        category="confidence_misuse",
                        severity=TrustAuditSeverity.MEDIUM,
                        subject=subject,
                        message="High confidence is not supported by enough evidence.",
                        evidence=evidence,
                        recommendation="Lower confidence or add additional evidence anchors.",
                    )
                )

            if self._contains_speculation(text):
                speculative_reasoning += 1
                findings.append(
                    TrustAuditFinding(
                        category="speculative_reasoning",
                        severity=TrustAuditSeverity.MEDIUM,
                        subject=subject,
                        message="Signal wording contains speculative language.",
                        evidence=evidence,
                        recommendation="Rewrite the claim as an evidence-backed observation.",
                    )
                )

        for claim in failures:
            subject = str(claim.get("name") or claim.get("scenario_name") or claim.get("scenario") or "failure_scenario")
            confidence = float(claim.get("confidence") or claim.get("oracle_confidence") or 0.0)
            evidence = self._extract_evidence(claim)
            text = self._claim_text(claim)

            if not evidence:
                unsupported_assumptions += 1
                findings.append(
                    TrustAuditFinding(
                        category="unsupported_assumption",
                        severity=TrustAuditSeverity.HIGH if confidence >= 0.8 else TrustAuditSeverity.MEDIUM,
                        subject=subject,
                        message="Failure scenario lacks evidence-backed propagation path.",
                        evidence=[],
                        recommendation="Ground the failure in an observed execution path.",
                    )
                )

            if confidence >= 0.9 and len(evidence) < 2:
                confidence_misuse += 1
                findings.append(
                    TrustAuditFinding(
                        category="confidence_misuse",
                        severity=TrustAuditSeverity.MEDIUM,
                        subject=subject,
                        message="Failure severity confidence is not justified by evidence depth.",
                        evidence=evidence,
                        recommendation="Reduce confidence or cite more propagation evidence.",
                    )
                )

            if self._contains_speculation(text):
                speculative_reasoning += 1
                findings.append(
                    TrustAuditFinding(
                        category="speculative_reasoning",
                        severity=TrustAuditSeverity.MEDIUM,
                        subject=subject,
                        message="Failure analysis uses speculative language.",
                        evidence=evidence,
                        recommendation="Replace hypothesis language with execution-graph facts.",
                    )
                )

        for claim in viva_questions:
            subject = str(claim.get("question") or claim.get("question_text") or claim.get("text") or "viva_question")
            evidence = self._extract_evidence(claim)

            if self._is_generic_viva(subject):
                speculative_reasoning += 1
                findings.append(
                    TrustAuditFinding(
                        category="generic_viva_question",
                        severity=TrustAuditSeverity.MEDIUM,
                        subject=subject,
                        message="Viva question is generic and not code-specific.",
                        evidence=evidence,
                        recommendation="Rephrase the question to target execution behavior or a concrete implementation detail.",
                    )
                )

            if not evidence:
                unsupported_assumptions += 1
                findings.append(
                    TrustAuditFinding(
                        category="unsupported_assumption",
                        severity=TrustAuditSeverity.MEDIUM,
                        subject=subject,
                        message="Viva question is not linked to a code location or execution trace.",
                        evidence=[],
                        recommendation="Attach the question to code evidence before using it in evaluation.",
                    )
                )

        if oracle_output.get("contradictions"):
            contradictory_evidence += len(oracle_output.get("contradictions", []))
            for contradiction in oracle_output.get("contradictions", []):
                findings.append(
                    TrustAuditFinding(
                        category="contradictory_evidence",
                        severity=TrustAuditSeverity.HIGH,
                        subject=str(contradiction.get("subject") or contradiction.get("name") or "contradiction"),
                        message=str(contradiction.get("message") or "Contradictory evidence detected."),
                        evidence=[str(item) for item in contradiction.get("evidence", [])],
                        recommendation="Resolve the conflict before output generation.",
                    )
                )

        stale_execution_graph = self._is_stale_execution_graph(oracle_output, execution_graph)
        if stale_execution_graph:
            findings.append(
                TrustAuditFinding(
                    category="stale_execution_graph",
                    severity=TrustAuditSeverity.HIGH,
                    subject="execution_graph",
                    message="Execution graph appears stale relative to the current analysis.",
                    evidence=[str(execution_graph.get("generated_at"))] if execution_graph.get("generated_at") else [],
                    recommendation="Regenerate the execution graph before publishing the analysis.",
                )
            )

        overall_score = self._score(findings)
        should_block_output = overall_score < 0.75 or any(
            finding.severity in {TrustAuditSeverity.HIGH, TrustAuditSeverity.CRITICAL}
            for finding in findings
        )

        category_counts.update(finding.category for finding in findings)
        return TrustAuditReport(
            overall_score=overall_score,
            should_block_output=should_block_output,
            findings=findings,
            summary=dict(category_counts),
            stale_execution_graph=stale_execution_graph,
            unsupported_assumption_count=unsupported_assumptions,
            speculative_reasoning_count=speculative_reasoning,
            contradictory_evidence_count=contradictory_evidence,
            confidence_misuse_count=confidence_misuse,
        )

    @staticmethod
    def _normalize_claims(value: Any) -> List[Dict[str, Any]]:
        if not value:
            return []
        if isinstance(value, dict):
            claims: List[Dict[str, Any]] = []
            for name, payload in value.items():
                if isinstance(payload, dict):
                    claim = dict(payload)
                    claim.setdefault("name", name)
                    claims.append(claim)
                else:
                    claims.append({"name": name, "value": payload})
            return claims
        if isinstance(value, list):
            claims = []
            for item in value:
                if isinstance(item, dict):
                    claims.append(item)
                else:
                    claims.append({"name": item})
            return claims
        return [{"name": value}]

    @staticmethod
    def _extract_evidence(claim: Dict[str, Any]) -> List[str]:
        evidence = claim.get("evidence") or claim.get("evidence_locations") or claim.get("code_evidence") or claim.get("files")
        if evidence is None:
            return []
        if isinstance(evidence, list):
            return [str(item) for item in evidence if str(item).strip()]
        return [str(evidence)] if str(evidence).strip() else []

    @staticmethod
    def _claim_text(claim: Dict[str, Any]) -> str:
        parts = [
            str(claim.get("name") or ""),
            str(claim.get("signal_name") or ""),
            str(claim.get("scenario_name") or ""),
            str(claim.get("question") or ""),
            str(claim.get("question_text") or ""),
            str(claim.get("description") or ""),
            str(claim.get("reasoning") or ""),
        ]
        return " ".join(part for part in parts if part).strip().lower()

    def _contains_speculation(self, text: str) -> bool:
        return any(marker in text for marker in self.SPECULATIVE_MARKERS)

    def _is_generic_viva(self, text: str) -> bool:
        lowered = text.lower()
        return any(marker in lowered for marker in self.GENERIC_VIVA_MARKERS)

    def _is_stale_execution_graph(self, oracle_output: Dict[str, Any], execution_graph: Dict[str, Any]) -> bool:
        graph_generated_at = execution_graph.get("generated_at") or oracle_output.get("execution_graph_generated_at")
        if not graph_generated_at:
            return False

        try:
            graph_time = datetime.fromisoformat(str(graph_generated_at).replace("Z", "+00:00"))
        except ValueError:
            return False

        analysis_generated_at = oracle_output.get("generated_at") or oracle_output.get("analysis_generated_at")
        if analysis_generated_at:
            try:
                analysis_time = datetime.fromisoformat(str(analysis_generated_at).replace("Z", "+00:00"))
            except ValueError:
                analysis_time = datetime.now(timezone.utc)
        else:
            analysis_time = datetime.now(timezone.utc)

        age_hours = max(0.0, (analysis_time - graph_time).total_seconds() / 3600.0)
        return age_hours > self.stale_graph_age_hours

    @staticmethod
    def _score(findings: List[TrustAuditFinding]) -> float:
        score = 1.0
        for finding in findings:
            if finding.severity == TrustAuditSeverity.CRITICAL:
                score -= 0.25
            elif finding.severity == TrustAuditSeverity.HIGH:
                score -= 0.15
            elif finding.severity == TrustAuditSeverity.MEDIUM:
                score -= 0.08
            else:
                score -= 0.03
        return max(0.0, min(1.0, score))
