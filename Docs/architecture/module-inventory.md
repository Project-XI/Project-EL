# Module Inventory & Ownership

**Total Codebase:** 14 active modules | ~6,800+ LOC  
**Last Updated:** May 2026

---

## Core Analysis Pipeline — 2,740 LOC ← ORACLE Intelligence

| Module | LOC | Purpose | Status |
|---|---|---|---|
| `viva_session_conductor.py` | 677 | Orchestrates viva sessions; scores responses for specificity, correctness, and quality | ✅ ACTIVE |
| `reasoning_depth_analyzer.py` | 543 | Analyzes response patterns; classifies implementation familiarity level | ✅ ACTIVE |
| `trust_audit.py` | 338 | Verifies evidence grounding; detects overconfidence (>0.95); surfaces uncertainty | ✅ ACTIVE |
| `engineering_review_corpus.py` | 375 | Hardcoded fixture of real engineering review data used for grounding | ✅ ACTIVE |
| `failure_corpus.py` | 807 | Failure pattern scenarios used as probing targets in viva sessions | ✅ ACTIVE |
| `fairness_audit.py` | 350+ | Communication style bias detection; demographic fairness audit | ✅ ACTIVE |

---

## Evaluation & Validation — 2,124 LOC

| Module | LOC | Purpose | Status |
|---|---|---|---|
| `comparative_reasoning_evaluator.py` | 430 | Compares ORACLE outputs against engineering reviews (Precision/Recall) | ✅ ACTIVE |
| `comparative_evaluator.py` | 600 | Multi-dimensional comparative analysis | ⚠️ REVIEW — Potential consolidation |
| `execution_behavior_analysis.py` | 466 | Analyzes speculative execution behaviors | ⚠️ REVIEW — Speculative, verify usage |
| `evaluator.py` | 628 | Original evaluator (older pattern) | ⚠️ REVIEW — Usage unknown |

> **Note:** Three competing evaluation systems exist. Consolidation into a single `implementation_familiarity_evaluator.py` is planned for Phase 4.

---

## Infrastructure & Data — 1,043 LOC

| Module | LOC | Purpose | Status |
|---|---|---|---|
| `models.py` | 392 | Core data models: ExecutionGraph, EvidenceModel, VivaTarget, etc. | ⚠️ CONSOLIDATE |
| `human_evaluator_models.py` | 341 | Human evaluator session models | ⚠️ CONSOLIDATE |
| `datasets.py` | 173 | Dataset loading and management | ✅ ACTIVE |
| `comparative_calibration_runner.py` | 137 | CLI test runner for calibration pipeline | ✅ ACTIVE |

> **Note:** Models are split across two files. Consolidation into a single `models.py` with clear sections (CoreModels, SessionModels, EvaluationModels) is planned.

---

## Archived / Dead Code — 449 LOC

| Module | LOC | Issue | Action |
|---|---|---|---|
| `viva_simulation.py` | 449 | Not imported anywhere; duplicates viva_session_conductor | 📌 ARCHIVED — Deprecation notice added |

---

## Intelligence Services — Phase 2

| Module | Path | Purpose | Status |
|---|---|---|---|
| `observable_signals_engine.py` | `services/intelligence/` | Extracts observable facts: error handling, resilience, observability | ✅ ACTIVE |
| `execution_graph_failure_analyzer.py` | `services/intelligence/` | Traces failure scenarios through execution graph | ✅ ACTIVE |
| `evidence_grounded_viva_generator.py` | `services/intelligence/` | Generates interview questions grounded in code evidence | ✅ ACTIVE |

---

## Calibration Framework — `backend/evaluation/calibration/`

| Module | Purpose |
|---|---|
| `repository_fixtures.py` | 4 diverse test case repositories |
| `signal_validator.py` | Precision/Recall metrics for signal detection |
| `failure_propagation_validator.py` | Validates failure propagation path accuracy |
| `viva_quality_validator.py` | Rejects generic/textbook viva questions |
| `confidence_calibrator.py` | Calibrates confidence scores against actual accuracy |
| `observability.py` | Runtime tracing for all reasoning steps |
| `calibration_runner.py` | Orchestrates full calibration + reporting |

---

## Public API Exports (`__init__.py`)

**Current:** 30 exported symbols (reduced from 52 — 47% reduction ✅)

**Core exports:**
- `VivaQuestion`, `CandidateResponse`, `VivaSession`
- `VivaSessionConductor`, `ReasoningDepthAnalyzer`
- `EngineeredReviewEntry`, `FailureCorpusRepository`
- `TrustAuditPipeline`, `FairnessAuditor`
- `ComparativeCalibrationRunner`

---

## Open Issues

| ID | Issue | Priority | Status |
|---|---|---|---|
| #1 | Multiple evaluation systems (3 competing) | 🔴 HIGH | ⚠️ Consolidation planned |
| #2 | Split model definitions (2 files) | 🔴 HIGH | ⚠️ Consolidation planned |
| #3 | Dead code (viva_simulation.py) | 🟠 MEDIUM | ✅ Archived |
| #4 | API bloat (52 → 30 symbols) | 🟠 MEDIUM | ✅ Resolved |

---

## Related Docs

- [Execution Flow](./execution-flow.md) — How modules chain together at runtime
- [Data Flow](./data-flow.md) — How data moves between modules
- [Agent Overview](./agent-overview.md) — Agent-level responsibilities
