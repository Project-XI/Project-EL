"""
oracle_adapter.py
─────────────────
Public entry point — the ONLY class MAIN Agent should import from this package.

Usage
─────
    from src.agents.main_agent.integration import OracleAdapter, NormalizedOracleOutput

    # From a live StructuredContext object
    output: NormalizedOracleOutput = OracleAdapter.from_context(context)

    # From a raw dict (e.g. WebSocket payload)
    output: NormalizedOracleOutput = OracleAdapter.from_dict(raw_dict)

Contract
────────
- Never raises on malformed input; returns a safe fallback NormalizedOracleOutput.
- All validation errors are captured in output.adapter_warnings.
- MAIN must never import StructuredContext or any ORACLE-internal model.
"""

from __future__ import annotations

import copy
import logging
from typing import Any, Dict

from src.models.context import StructuredContext

from .compatibility import apply_compatibility_shims
from .oracle_schema import NormalizedOracleOutput
from .payload_normalizer import normalize_payload
from .validation import OraclePayloadValidationError, validate_raw_payload

logger = logging.getLogger(__name__)


class OracleAdapter:
    """
    Converts ORACLE output (StructuredContext or raw dict) into
    a stable NormalizedOracleOutput for MAIN Agent consumption.

    All methods are classmethods — no instantiation needed.
    """

    # ── Primary entry points ──────────────────────────────────────────────────

    @classmethod
    def from_context(cls, context: StructuredContext) -> NormalizedOracleOutput:
        """
        Convert a live StructuredContext object into NormalizedOracleOutput.

        Serialises the context to dict first so the rest of the pipeline
        stays fully decoupled from ORACLE internal types.
        """
        try:
            raw = context.model_dump()
        except AttributeError:
            raw = context.dict()  # pydantic v1 fallback
        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, raw: Any) -> NormalizedOracleOutput:
        """
        Convert a raw ORACLE payload dict into NormalizedOracleOutput.

        Never raises — all failures produce a safe fallback with populated
        adapter_warnings so MAIN can log and handle degraded state.
        """
        if not isinstance(raw, dict):
            logger.error("[OracleAdapter] Received non-dict payload: %s", type(raw).__name__)
            return cls._safe_fallback(
                [f"Payload must be a dict, got {type(raw).__name__!r}"]
            )

        # Work on a deep copy so we never mutate the caller's object.
        payload: Dict[str, Any] = copy.deepcopy(raw)

        # 1. Apply compatibility shims (handles schema evolution silently).
        apply_compatibility_shims(payload)

        # 2. Validate — collect warnings, reject fatally malformed payloads.
        warnings: list[str] = []
        try:
            _, warnings = validate_raw_payload(payload)
        except (OraclePayloadValidationError, TypeError) as exc:
            logger.warning("[OracleAdapter] Validation failed: %s", exc)
            return cls._safe_fallback([str(exc)])

        if warnings:
            for w in warnings:
                logger.debug("[OracleAdapter] Warning: %s", w)

        # 3. Normalize.
        try:
            return normalize_payload(payload, warnings)
        except Exception as exc:  # noqa: BLE001
            logger.error("[OracleAdapter] Normalization error: %s", exc, exc_info=True)
            return cls._safe_fallback(
                [f"Normalization failed: {exc}"] + warnings
            )

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _safe_fallback(warnings: list[str]) -> NormalizedOracleOutput:
        """Return a fully-initialized, zeroed NormalizedOracleOutput with warnings."""
        return NormalizedOracleOutput(adapter_warnings=warnings)
