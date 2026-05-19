"""
payload_normalizer.py
─────────────────────
Stateless functions that convert a validated raw ORACLE payload dict
into the stable NormalizedOracleOutput schema.

Rules
─────
- No ORACLE logic is re-implemented here (no AST, no confidence math).
- Every function is pure: same input → same output.
- Missing optional data yields safe defaults; no KeyError is ever raised.
- EvidenceLinks preserve the original evidence strings verbatim.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .oracle_schema import (
    DifficultyLevel,
    EvidenceLink,
    FailureScenario,
    InconsistencySignal,
    NormalizedOracleOutput,
    NormalizedVivaTarget,
    ObservableSignal,
    SeverityLevel,
    VivaCategory,
)
from .validation import validate_evidence_model


# ── Private helpers ───────────────────────────────────────────────────────────

def _evidence_links(raw_evidence: Any) -> List[EvidenceLink]:
    """Convert a raw evidence list (strings or dicts) into EvidenceLink objects."""
    if not isinstance(raw_evidence, list):
        return []
    links: List[EvidenceLink] = []
    for item in raw_evidence:
        if isinstance(item, str) and item.strip():
            links.append(EvidenceLink(text=item.strip(), confidence=1.0))
        elif isinstance(item, dict):
            text = str(item.get("text", item.get("value", ""))).strip()
            confidence = float(item.get("confidence", 1.0))
            if text:
                links.append(EvidenceLink(text=text, confidence=confidence))
    return links


def _safe_float(value: Any, default: float = 0.0, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp a numeric value to [lo, hi]; return default on failure."""
    try:
        return max(lo, min(hi, float(value)))
    except (TypeError, ValueError):
        return default


def _safe_str(value: Any, default: str = "Unknown") -> str:
    s = str(value).strip() if value is not None else ""
    return s if s else default


def _coerce_severity(raw: Any) -> SeverityLevel:
    mapping = {
        "low": SeverityLevel.LOW,
        "medium": SeverityLevel.MEDIUM,
        "high": SeverityLevel.HIGH,
        "critical": SeverityLevel.CRITICAL,
    }
    return mapping.get(str(raw).lower(), SeverityLevel.MEDIUM)


def _coerce_difficulty(raw: Any) -> DifficultyLevel:
    mapping = {
        "easy": DifficultyLevel.EASY,
        "medium": DifficultyLevel.MEDIUM,
        "hard": DifficultyLevel.HARD,
    }
    return mapping.get(str(raw).lower(), DifficultyLevel.MEDIUM)


def _coerce_category(raw: Any) -> VivaCategory:
    mapping = {
        "architecture":  VivaCategory.ARCHITECTURE,
        "tradeoff":      VivaCategory.TRADEOFF,
        "tradeoffs":     VivaCategory.TRADEOFF,
        "security":      VivaCategory.SECURITY,
        "scalability":   VivaCategory.SCALABILITY,
        "failure-path":  VivaCategory.FAILURE_PATH,
        "failure_path":  VivaCategory.FAILURE_PATH,
        "runtime":       VivaCategory.RUNTIME,
    }
    return mapping.get(str(raw).lower(), VivaCategory.ARCHITECTURE)


# ── Observable signals ────────────────────────────────────────────────────────

_SIGNAL_KEYS = [
    "backend_framework",
    "frontend_framework",
    "database_used",
    "authentication_system",
]

def normalize_observable_signals(payload: Dict[str, Any]) -> List[ObservableSignal]:
    """
    Extract the four core observable signals from the ORACLE payload.
    Each maps to an EvidenceModel-shaped dict.
    """
    signals: List[ObservableSignal] = []
    for key in _SIGNAL_KEYS:
        raw = validate_evidence_model(payload.get(key, {}), key)
        if raw["value"] and raw["value"].lower() != "unknown":
            signals.append(ObservableSignal(
                key=key,
                value=_safe_str(raw["value"]),
                confidence=_safe_float(raw["confidence"]),
                evidence=_evidence_links(raw["evidence"]),
            ))
    return signals


# ── Viva targets ──────────────────────────────────────────────────────────────

def normalize_viva_targets(payload: Dict[str, Any]) -> List[NormalizedVivaTarget]:
    """
    Merge both viva target lists (legacy + current) and deduplicate.
    Preserves every evidence link intact.
    """
    raw_targets: List[Any] = []

    legacy = payload.get("viva_intelligence_targets", [])
    current = payload.get("implementation_viva_targets", [])

    if isinstance(legacy, list):
        raw_targets.extend(legacy)
    if isinstance(current, list):
        raw_targets.extend(current)

    seen: set = set()
    results: List[NormalizedVivaTarget] = []

    for raw in raw_targets:
        if not isinstance(raw, dict):
            continue
        question_target = _safe_str(raw.get("question_target"), "Unnamed Target")
        topic           = _safe_str(raw.get("topic"), "General")
        dedup_key = (topic.lower(), question_target.lower())
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        results.append(NormalizedVivaTarget(
            topic            = topic,
            question_target  = question_target,
            difficulty       = _coerce_difficulty(raw.get("difficulty", "medium")),
            category         = _coerce_category(raw.get("category", "Architecture")),
            importance_score = _safe_float(raw.get("importance_score", 0.5)),
            depth_score      = _safe_float(raw.get("depth_score", 5.0), lo=0.0, hi=10.0),
            focus            = _safe_str(raw.get("focus"), ""),
            related_node     = _safe_str(raw.get("related_node"), ""),
            confidence       = _safe_float(raw.get("confidence", 0.8)),
            reasoning_summary= _safe_str(raw.get("reasoning_summary"), ""),
            evidence         = _evidence_links(raw.get("evidence", [])),
        ))

    return results


# ── Failure scenarios ─────────────────────────────────────────────────────────

def normalize_failure_scenarios(payload: Dict[str, Any]) -> List[FailureScenario]:
    """
    Merge failure_paths, runtime_risks, and execution_graph.failure_paths
    into a single flat list of FailureScenario objects.
    """
    results: List[FailureScenario] = []

    # From failure_paths (List[EvidenceModel])
    for raw in payload.get("failure_paths", []):
        if not isinstance(raw, dict):
            continue
        desc = _safe_str(raw.get("value"), "")
        if not desc:
            continue
        results.append(FailureScenario(
            description = desc,
            severity    = SeverityLevel.MEDIUM,
            confidence  = _safe_float(raw.get("confidence", 0.7)),
            evidence    = _evidence_links(raw.get("evidence", [])),
        ))

    # From runtime_risks (List[RuntimeRisk])
    for raw in payload.get("runtime_risks", []):
        if not isinstance(raw, dict):
            continue
        desc = _safe_str(raw.get("value"), "")
        if not desc:
            continue
        results.append(FailureScenario(
            description = desc,
            severity    = _coerce_severity(raw.get("severity", "medium")),
            confidence  = _safe_float(raw.get("confidence", 0.7)),
            evidence    = _evidence_links(raw.get("evidence", [])),
        ))

    # From execution_graph.risk_flags / failure_paths (plain strings)
    eg = payload.get("execution_graph", {})
    if isinstance(eg, dict):
        for label in eg.get("risk_flags", []):
            results.append(FailureScenario(
                description = _safe_str(label),
                severity    = SeverityLevel.MEDIUM,
                confidence  = 0.75,
                evidence    = [],
            ))
        for label in eg.get("failure_paths", []):
            results.append(FailureScenario(
                description = _safe_str(label),
                severity    = SeverityLevel.HIGH,
                confidence  = 0.80,
                evidence    = [],
            ))

    return results


# ── Inconsistencies ───────────────────────────────────────────────────────────

def normalize_inconsistencies(payload: Dict[str, Any]) -> List[InconsistencySignal]:
    results: List[InconsistencySignal] = []
    for raw in payload.get("inconsistencies", []):
        if not isinstance(raw, dict):
            continue
        issue = _safe_str(raw.get("issue"), "")
        if not issue:
            continue
        results.append(InconsistencySignal(
            issue      = issue,
            severity   = _coerce_severity(raw.get("severity", "medium")),
            confidence = _safe_float(raw.get("confidence", 0.7)),
            evidence   = _evidence_links(raw.get("evidence", [])),
        ))
    return results


# ── Execution graph summary ───────────────────────────────────────────────────

def normalize_execution_graph_summary(payload: Dict[str, Any]) -> Dict[str, int]:
    """Return a minimal int-only summary of the execution graph for MAIN."""
    eg = payload.get("execution_graph", {})
    if not isinstance(eg, dict):
        return {"node_count": 0, "edge_count": 0, "middleware_count": 0, "auth_point_count": 0}
    return {
        "node_count":      len(eg.get("nodes", [])),
        "edge_count":      len(eg.get("edges", [])),
        "middleware_count":len(eg.get("middleware", [])),
        "auth_point_count":len(eg.get("auth_points", [])),
    }


# ── Full payload normalization ────────────────────────────────────────────────

def normalize_payload(validated_payload: Dict[str, Any], warnings: List[str] | None = None) -> NormalizedOracleOutput:
    """
    Convert a *validated* raw ORACLE payload dict into NormalizedOracleOutput.

    This is the primary entry-point called by OracleAdapter.
    `warnings` is the list returned by validate_raw_payload().
    """
    warnings = warnings or []

    pn  = validate_evidence_model(validated_payload.get("project_name", {}), "project_name")
    pt  = validate_evidence_model(validated_payload.get("project_type", {}), "project_type")
    ap  = validate_evidence_model(validated_payload.get("architecture_pattern", {}), "architecture_pattern")

    graph_summary = normalize_execution_graph_summary(validated_payload)

    cm = validated_payload.get("complexity_mismatch")
    cm_detected = False
    cm_note = ""
    if isinstance(cm, dict):
        cm_note = _safe_str(cm.get("value"), "")
        cm_detected = bool(cm_note and "no major" not in cm_note.lower())

    return NormalizedOracleOutput(
        project_name          = _safe_str(pn["value"]),
        project_type          = _safe_str(pt["value"]),
        architecture_pattern  = _safe_str(ap["value"]),
        observable_signals    = normalize_observable_signals(validated_payload),
        viva_targets          = normalize_viva_targets(validated_payload),
        failure_scenarios     = normalize_failure_scenarios(validated_payload),
        inconsistencies       = normalize_inconsistencies(validated_payload),
        execution_node_count  = graph_summary["node_count"],
        execution_edge_count  = graph_summary["edge_count"],
        middleware_count      = graph_summary["middleware_count"],
        auth_point_count      = graph_summary["auth_point_count"],
        complexity_mismatch_detected = cm_detected,
        complexity_mismatch_note     = cm_note,
        adapter_warnings      = warnings,
    )
