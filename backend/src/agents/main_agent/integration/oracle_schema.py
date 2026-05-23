"""
oracle_schema.py
────────────────
Stable, versioned data contracts that MAIN Agent consumes.

These models are the *only* shapes MAIN should ever reference.
They must never import StructuredContext or any ORACLE-internal model directly.
Adapter-layer (oracle_adapter.py) is responsible for populating them.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Schema version ───────────────────────────────────────────────────────────

ADAPTER_SCHEMA_VERSION = "1.0.0"


# ── Enumerations ─────────────────────────────────────────────────────────────

class VivaCategory(str, Enum):
    ARCHITECTURE  = "Architecture"
    TRADEOFF      = "Tradeoff"
    SECURITY      = "Security"
    SCALABILITY   = "Scalability"
    FAILURE_PATH  = "Failure-Path"
    RUNTIME       = "Runtime"


class DifficultyLevel(str, Enum):
    EASY   = "easy"
    MEDIUM = "medium"
    HARD   = "hard"


class SeverityLevel(str, Enum):
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"


# ── Atomic building blocks ────────────────────────────────────────────────────

class EvidenceLink(BaseModel):
    """A single piece of traceable evidence backing a claim."""
    text: str
    confidence: float = Field(ge=0.0, le=1.0)


class ObservableSignal(BaseModel):
    """
    A normalized, observable property of the analysed project.
    MAIN uses these to drive orchestration decisions (e.g. question difficulty,
    persona tone, session length).
    """
    key: str                             # e.g. "backend_framework", "auth_system"
    value: str                           # e.g. "FastAPI", "JWT"
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[EvidenceLink] = []


class NormalizedVivaTarget(BaseModel):
    """A single viva question target ready for MAIN orchestration."""
    topic: str
    question_target: str
    difficulty: DifficultyLevel
    category: VivaCategory
    importance_score: float = Field(ge=0.0, le=1.0)
    depth_score: float      = Field(ge=0.0, le=10.0)
    focus: str
    related_node: str       = ""
    confidence: float       = Field(ge=0.0, le=1.0)
    reasoning_summary: str  = ""
    evidence: List[EvidenceLink] = []


class FailureScenario(BaseModel):
    """A single normalized failure path or risk flag from ORACLE."""
    description: str
    severity: SeverityLevel
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[EvidenceLink] = []


class InconsistencySignal(BaseModel):
    """A doc-vs-code inconsistency detected by ORACLE."""
    issue: str
    severity: SeverityLevel
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[EvidenceLink] = []


# ── Top-level normalized output ───────────────────────────────────────────────

class NormalizedOracleOutput(BaseModel):
    """
    The single, stable output contract between ORACLE and MAIN Agent.

    MAIN must only ever read fields defined here.
    No internal ORACLE types should leak past this boundary.
    """
    schema_version: str = ADAPTER_SCHEMA_VERSION

    # Project identity
    project_name: str    = "Unknown"
    project_type: str    = "Unknown"
    architecture_pattern: str = "Unknown"

    # Core intelligence surfaces
    observable_signals:  List[ObservableSignal]    = []
    viva_targets:        List[NormalizedVivaTarget] = []
    failure_scenarios:   List[FailureScenario]      = []
    inconsistencies:     List[InconsistencySignal]  = []

    # Execution graph summary (MAIN never touches graph internals)
    execution_node_count: int = 0
    execution_edge_count: int = 0
    middleware_count:     int = 0
    auth_point_count:     int = 0

    # Complexity signal
    complexity_mismatch_detected: bool  = False
    complexity_mismatch_note:     str   = ""

    # Adapter metadata
    adapter_warnings: List[str] = []
