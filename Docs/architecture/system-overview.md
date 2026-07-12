# ORACLE System Overview

**Version:** 1.0 — Stabilization Phase  
**Architecture Status:** 🔒 Frozen — No new intelligence engines to be added

---

## System Purpose

ORACLE is an **Implementation Familiarity Assessment** system. It is designed to determine whether a candidate has genuine, hands-on familiarity with a codebase — not whether they can recite documentation.

It uses AST-first analysis, evidence-grounded reasoning, and a structured viva protocol to produce auditable, explainable assessments.

---

## Top-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ORACLE Implementation Familiarity System                  │
│                           Architecture v1.0 (Stable)                         │
└─────────────────────────────────────────────────────────────────────────────┘

Browser (ORACLE UI)
      │
      │  WebSocket: ws://localhost:8001/ws/analyze
      ▼
┌─────────────────────────────────────────────────────┐
│                   FastAPI Server                     │
│                   backend/src/main.py                │
└─────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────┐
│                   MainAgent                          │
│  Orchestrates: Gatekeeper → Oracle → Sentinel        │
└─────────────────────────────────────────────────────┘
      │
      ├─── GatekeeperAgent (identity & access validation)
      │
      ├─── OracleAgent (core analysis pipeline)
      │         │
      │         ├── AST Parsing & Execution Graph
      │         ├── ObservableSignalsEngine
      │         ├── ExecutionGraphFailureAnalyzer
      │         ├── EvidenceGroundedVivaGenerator
      │         └── StructuredContext assembly
      │
      └─── SentinelAgent (audit & moderation)
```

---

## Agent Roles

| Agent | Responsibility | File |
|---|---|---|
| **MainAgent** | Orchestrates the full pipeline, manages session flow | `backend/src/agents/main_agent/agent.py` |
| **GatekeeperAgent** | Validates identity context, access permissions | `backend/src/agents/gatekeeper/` |
| **OracleAgent** | Core intelligence — AST, graphs, signals, viva | `backend/src/agents/oracle/agent.py` |
| **SentinelAgent** | Audit logging, moderation, policy enforcement | `backend/src/agents/sentinel/` |

---

## Core Intelligence Modules

### Production (ACTIVE)

| Module | LOC | Purpose |
|---|---|---|
| `viva_session_conductor.py` | 677 | Orchestrate viva sessions, score responses |
| `reasoning_depth_analyzer.py` | 543 | Classify implementation familiarity from indicators |
| `trust_audit.py` | 338 | Verify evidence grounding, detect overconfidence |
| `engineering_review_corpus.py` | 375 | Real engineering review grounding data |
| `failure_corpus.py` | 807 | Failure pattern scenarios (probing targets) |
| `fairness_audit.py` | 350+ | Communication bias & demographic fairness detection |

### Validation Layer

| Module | LOC | Purpose |
|---|---|---|
| `comparative_reasoning_evaluator.py` | 430 | Compare ORACLE outputs vs engineering reviews |
| `comparative_evaluator.py` | 600 | Multi-dimensional comparative analysis |
| `signal_validator.py` | — | Precision/Recall metrics for observable signals |
| `failure_propagation_validator.py` | — | Validates failure scenario propagation paths |
| `viva_quality_validator.py` | — | Rejects generic/textbook questions |
| `confidence_calibrator.py` | — | Calibrates confidence scores to actual accuracy |

### Infrastructure

| Module | LOC | Purpose |
|---|---|---|
| `models.py` | 392 | Core data models |
| `human_evaluator_models.py` | 341 | Human evaluation session models |
| `datasets.py` | 173 | Dataset management |
| `comparative_calibration_runner.py` | 137 | CLI calibration runner |

---

## Data Flow Summary

```
Repository URL (Input)
        ↓
  Git Clone + AST Parse
        ↓
  ExecutionGraph (nodes, edges, types)
        ↓
  ┌─────────────────────────────────┐
  │  Engineering Review Corpus      │──→ CorpusContext
  │  Failure Corpus                 │──→ FailureSignalMap
  └─────────────────────────────────┘
        ↓
  Question Generation (evidence-grounded)
        ↓
  Viva Session (multi-turn Q&A)
        ↓
  Response Evaluation
  (Specificity, Correctness, Quality enum)
        ↓
  Indicator Analysis
  (Understanding vs Memorisation)
        ↓
  Reasoning Pattern Classification
  (DEEP / PRACTICED / INFORMED / LOW / INSUFFICIENT)
        ↓
  Trust Audit + Fairness Audit
        ↓
  FinalAssessment + Evidence Trace (Output)
```

---

## Key Design Principles

1. **AST-First** — All analysis starts from actual code structure, not natural language guesses
2. **Evidence-Grounded** — Every conclusion maps to specific code locations or review evidence
3. **Explainability** — Full indicator trace visible on every assessment
4. **Determinism** — Same inputs → same outputs, no hidden stochastic scoring
5. **Architecture Freeze** — No new intelligence layers; stabilization only

---

## Related Docs

- [Module Inventory](./module-inventory.md) — Detailed LOC breakdown and ownership
- [Data Flow](./data-flow.md) — Full data movement through the system
- [Execution Flow](./execution-flow.md) — Step-by-step pipeline walkthrough
- [Agent Overview](./agent-overview.md) — Per-agent responsibilities and boundaries
