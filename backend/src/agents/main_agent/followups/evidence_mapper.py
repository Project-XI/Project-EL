"""
evidence_mapper.py
──────────────────
Maps ORACLE outputs and session state into the evidence dict consumed by patterns.

Responsibilities
────────────────
- Extract named evidence slots from NormalizedOracleOutput.
- Construct an EvidenceDict (plain str→str) for pattern template substitution.
- Ensure every slot defaults safely — never raises KeyError downstream.
- Preserve traceability: EvidenceRecord logs the source of each slot.

Rules
─────
- No inference or scoring — only extraction and mapping.
- No ORACLE logic duplicated — reads NormalizedOracleOutput fields only.
- Pure functions; no side effects.
- Deterministic: same oracle output → same evidence dict.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.agents.main_agent.integration.oracle_schema import (
    FailureScenario,
    NormalizedOracleOutput,
    NormalizedVivaTarget,
    ObservableSignal,
)


# ── Evidence record ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class EvidenceRecord:
    """
    A single slot in the evidence dict with its traceability source.
    Allows follow-ups to be audited back to the ORACLE signal that triggered them.
    """
    key: str
    value: str
    source: str          # e.g. "oracle.failure_scenarios[0]", "oracle.observable_signals.backend_framework"
    confidence: float    # Inherited from the ORACLE signal


@dataclass
class EvidenceDict:
    """
    A flat, auditable evidence dictionary ready for pattern substitution.

    The `slots` dict is what gets passed to FollowUpPattern.fill().
    The `records` list is what gets logged for traceability.
    """
    slots: Dict[str, str] = field(default_factory=dict)
    records: List[EvidenceRecord] = field(default_factory=list)

    def add(self, key: str, value: str, source: str, confidence: float = 1.0) -> None:
        if value:
            self.slots[key] = value
            self.records.append(EvidenceRecord(
                key=key, value=value, source=source, confidence=confidence
            ))

    def get(self, key: str, default: str = "") -> str:
        return self.slots.get(key, default)

    def has(self, key: str) -> bool:
        return key in self.slots


# ── Signal extractors ─────────────────────────────────────────────────────────

def _extract_signal_value(signals: List[ObservableSignal], key: str) -> Optional[ObservableSignal]:
    return next((s for s in signals if s.key == key), None)


def _top_failure(failures: List[FailureScenario]) -> Optional[FailureScenario]:
    if not failures:
        return None
    return sorted(failures, key=lambda f: -f.confidence)[0]


# ── Primary builder ───────────────────────────────────────────────────────────

def build_evidence_dict(
    oracle_output: NormalizedOracleOutput,
    current_target: Optional[NormalizedVivaTarget] = None,
    trigger_phrase: Optional[str] = None,
) -> EvidenceDict:
    """
    Build a fully populated EvidenceDict from a NormalizedOracleOutput.

    All slots are optional — missing data yields empty strings, never errors.

    Slot catalogue
    ──────────────
    backend_framework    : e.g. "FastAPI"
    frontend_framework   : e.g. "React"
    database             : e.g. "PostgreSQL"
    auth_system          : e.g. "JWT"
    architecture         : e.g. "REST API"
    concept              : current question target text
    scenario             : current question focus (condensed)
    trigger_event        : the event or action being examined
    failure_scenario     : top ORACLE failure scenario description
    vague_phrase         : the vague term the candidate used
    project_name         : project name from ORACLE
    """
    ev = EvidenceDict()

    # ── Observable signals ────────────────────────────────────────────────────
    sig_map = {s.key: s for s in oracle_output.observable_signals}

    for slot, oracle_key in [
        ("backend_framework",  "backend_framework"),
        ("frontend_framework", "frontend_framework"),
        ("database",           "database_used"),
        ("auth_system",        "authentication_system"),
    ]:
        sig = sig_map.get(oracle_key)
        if sig and sig.value and sig.value.lower() != "unknown":
            ev.add(
                key        = slot,
                value      = sig.value,
                source     = f"oracle.observable_signals.{oracle_key}",
                confidence = sig.confidence,
            )

    # ── Architecture ──────────────────────────────────────────────────────────
    if oracle_output.architecture_pattern and oracle_output.architecture_pattern != "Unknown":
        ev.add("architecture", oracle_output.architecture_pattern,
               source="oracle.architecture_pattern")

    # ── Project name ──────────────────────────────────────────────────────────
    if oracle_output.project_name and oracle_output.project_name != "Unknown":
        ev.add("project_name", oracle_output.project_name,
               source="oracle.project_name")

    # ── Current target context ────────────────────────────────────────────────
    if current_target:
        ev.add("concept", current_target.question_target,
               source="current_target.question_target")

        # Condense focus to a trigger event phrase (first sentence)
        focus_sentences = current_target.focus.split(".")
        trigger = focus_sentences[0].strip() if focus_sentences else current_target.focus
        ev.add("trigger_event", trigger, source="current_target.focus")
        ev.add("scenario", trigger, source="current_target.focus")

    # ── Top failure scenario ──────────────────────────────────────────────────
    top_failure = _top_failure(oracle_output.failure_scenarios)
    if top_failure:
        ev.add(
            key        = "failure_scenario",
            value      = top_failure.description,
            source     = "oracle.failure_scenarios[0]",
            confidence = top_failure.confidence,
        )

    # ── Vague phrase (from detector trigger) ──────────────────────────────────
    if trigger_phrase:
        ev.add("vague_phrase", trigger_phrase, source="weak_answer_detector.trigger_phrase")

    return ev


def evidence_summary(ev: EvidenceDict) -> List[str]:
    """
    Return a list of human-readable evidence strings for logging / audit.
    """
    return [
        f"[{r.source}] {r.key}={r.value!r} (conf={r.confidence:.2f})"
        for r in ev.records
    ]
