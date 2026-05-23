"""
compatibility.py
────────────────
Schema compatibility layer between ORACLE output versions and the adapter.

When ORACLE adds, renames, or restructures a field, this file alone is updated.
MAIN Agent and oracle_adapter.py must remain untouched for schema drift.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def _shim_legacy_viva_field(payload: Dict[str, Any]) -> None:
    """Ensure both viva target list keys are present."""
    if "viva_intelligence_targets" not in payload:
        payload["viva_intelligence_targets"] = []
    if "implementation_viva_targets" not in payload:
        payload["implementation_viva_targets"] = []


def _shim_project_graph_to_execution_graph(payload: Dict[str, Any]) -> None:
    """Map old 'project_graph' key to the newer 'execution_graph' shape."""
    if "execution_graph" not in payload and "project_graph" in payload:
        pg = payload["project_graph"]
        payload["execution_graph"] = {
            "nodes": pg.get("nodes", []),
            "edges": pg.get("edges", []),
            "middleware": [],
            "db_calls": [],
            "auth_points": [],
            "risk_flags": [],
            "failure_paths": [],
        }
        logger.debug("[compatibility] Shimmed 'project_graph' → 'execution_graph'")


def _shim_missing_evidence_fields(payload: Dict[str, Any]) -> None:
    """Inject empty evidence lists on EvidenceModel dicts that omit them."""
    for key in [
        "project_name", "project_type", "backend_framework",
        "frontend_framework", "database_used", "authentication_system",
        "architecture_pattern",
    ]:
        field = payload.get(key)
        if isinstance(field, dict) and "evidence" not in field:
            field["evidence"] = []


def _shim_flat_string_failure_paths(payload: Dict[str, Any]) -> None:
    """Coerce List[str] failure_paths to List[EvidenceModel dict]."""
    raw = payload.get("failure_paths", [])
    if not isinstance(raw, list):
        return
    payload["failure_paths"] = [
        {"value": item, "confidence": 0.7, "evidence": []}
        if isinstance(item, str) else item
        for item in raw
    ]


def _shim_runtime_risks_severity(payload: Dict[str, Any]) -> None:
    """Uppercase severity in runtime_risks for enum coercion consistency."""
    risks = payload.get("runtime_risks", [])
    if not isinstance(risks, list):
        return
    for risk in risks:
        if isinstance(risk, dict) and "severity" in risk:
            risk["severity"] = str(risk["severity"]).upper()


_SHIMS = [
    _shim_legacy_viva_field,
    _shim_project_graph_to_execution_graph,
    _shim_missing_evidence_fields,
    _shim_flat_string_failure_paths,
    _shim_runtime_risks_severity,
]


def apply_compatibility_shims(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Apply all registered compatibility shims. Mutates in-place, returns same dict."""
    for shim in _SHIMS:
        try:
            shim(payload)
        except Exception as exc:
            logger.warning("[compatibility] Shim %s raised %s — skipping.", shim.__name__, exc)
    return payload
