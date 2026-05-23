"""
validation.py
─────────────
Strict schema validation for raw ORACLE payloads.

Responsibilities
────────────────
- Validate that a raw payload dict contains the minimum expected keys.
- Reject clearly malformed payloads with an explicit ValidationError.
- Surface warnings for optional-but-expected fields that are missing.
- Never import StructuredContext directly; only inspect plain dicts.

Rules
─────
- All public functions are pure (no side-effects).
- All failures are explicit — no silent coercion at this layer.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


# ── Required top-level keys ───────────────────────────────────────────────────

_REQUIRED_KEYS: List[str] = [
    "project_name",
    "project_type",
    "backend_framework",
    "frontend_framework",
    "database_used",
    "authentication_system",
    "architecture_pattern",
]

# Keys that should be present and be lists; absence generates a warning, not an error.
_EXPECTED_LIST_KEYS: List[str] = [
    "viva_intelligence_targets",
    "implementation_viva_targets",
    "failure_paths",
    "runtime_risks",
    "inconsistencies",
    "middleware_chain",
    "security_flows",
]


# ── Public exceptions ─────────────────────────────────────────────────────────

class OraclePayloadValidationError(ValueError):
    """Raised when a raw ORACLE payload is structurally invalid."""

    def __init__(self, message: str, missing_keys: List[str] | None = None):
        super().__init__(message)
        self.missing_keys = missing_keys or []


# ── Core validation ───────────────────────────────────────────────────────────

def validate_raw_payload(payload: Any) -> Tuple[bool, List[str]]:
    """
    Validate a raw ORACLE payload dict.

    Returns
    ───────
    (is_valid: bool, warnings: List[str])

    Raises
    ──────
    OraclePayloadValidationError — if the payload is fatally malformed.
    TypeError                    — if the payload is not a dict at all.
    """
    if not isinstance(payload, dict):
        raise TypeError(
            f"ORACLE payload must be a dict, got {type(payload).__name__!r}"
        )

    # ── Fatal checks ──────────────────────────────────────────────────────────
    missing_required: List[str] = [
        key for key in _REQUIRED_KEYS if key not in payload
    ]
    if missing_required:
        raise OraclePayloadValidationError(
            f"ORACLE payload is missing required keys: {missing_required}",
            missing_keys=missing_required,
        )

    # ── Structural checks on required EvidenceModel fields ────────────────────
    for key in _REQUIRED_KEYS:
        field_val = payload[key]
        if not isinstance(field_val, dict):
            raise OraclePayloadValidationError(
                f"Field '{key}' must be an EvidenceModel dict (got {type(field_val).__name__!r}). "
                "Raw ORACLE output may have been pre-processed unexpectedly."
            )
        if "value" not in field_val:
            raise OraclePayloadValidationError(
                f"EvidenceModel for '{key}' is missing the 'value' key."
            )

    # ── Soft checks (generate warnings only) ──────────────────────────────────
    warnings: List[str] = []
    for key in _EXPECTED_LIST_KEYS:
        if key not in payload:
            warnings.append(
                f"Optional list field '{key}' is absent from ORACLE payload. "
                "Defaulting to empty list."
            )
        elif not isinstance(payload[key], list):
            warnings.append(
                f"Field '{key}' is expected to be a list but got "
                f"{type(payload[key]).__name__!r}. It will be treated as empty."
            )

    # ── execution_graph check ─────────────────────────────────────────────────
    eg = payload.get("execution_graph")
    if eg is None:
        warnings.append("'execution_graph' is absent. Graph summary will be zeroed.")
    elif not isinstance(eg, dict):
        warnings.append(
            f"'execution_graph' should be a dict, got {type(eg).__name__!r}. "
            "Graph summary will be zeroed."
        )

    return True, warnings


def validate_evidence_model(raw: Any, field_name: str) -> Dict[str, Any]:
    """
    Ensure a single EvidenceModel dict is sane.

    Returns the dict unchanged if valid, or a safe default if not.
    Never raises — designed for use inside normalizers.
    """
    if not isinstance(raw, dict):
        return {"value": "Unknown", "confidence": 0.0, "evidence": []}
    value = raw.get("value", "Unknown")
    confidence = raw.get("confidence", 0.0)
    evidence = raw.get("evidence", [])
    if not isinstance(evidence, list):
        evidence = []
    if not isinstance(confidence, (int, float)):
        confidence = 0.0
    return {"value": str(value), "confidence": float(confidence), "evidence": evidence}
