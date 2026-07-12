# ORACLE Architecture Documentation

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ORACLE Implementation Familiarity System                  │
│                           Architecture v1.0 (Stable)                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Module Inventory & Ownership

### Core Analysis Pipeline

| Module | LOC | Purpose | Owner | Status |
|--------|-----|---------|-------|--------|
| `viva_session_conductor.py` | 677 | Orchestrate viva sessions, score responses | Core | ✅ ACTIVE |
| `reasoning_depth_analyzer.py` | 543 | Analyze reasoning patterns, classify implementation familiarity | Core | ✅ ACTIVE |
| `trust_audit.py` | 338 | Verify evidence grounding, detect overconfidence | Core | ✅ ACTIVE |
| `engineering_review_corpus.py` | 375 | Real engineering review data (grounding source) | Core | ✅ ACTIVE |
| `failure_corpus.py` | 807 | Failure pattern scenarios (probing targets) | Core | ✅ ACTIVE |

**Total: 2,740 LOC** ← ORACLE core intelligence

### Evaluation & Validation

| Module | LOC | Purpose | Owner | Status |
|--------|-----|---------|-------|--------|
| `comparative_reasoning_evaluator.py` | 430 | Compare ORACLE vs engineering reviews | Validation | ✅ ACTIVE |
| `comparative_evaluator.py` | 600 | Multi-dimensional comparative analysis | Validation | ⚠️ REVIEW |
| `execution_behavior_analysis.py` | 466 | Analyze code execution patterns | Analysis | ⚠️ REVIEW |
| `evaluator.py` | 628 | Initial evaluator (older pattern) | Validation | ⚠️ REVIEW |

**Total: 2,124 LOC** ← Validation layers (3 competing systems)

### Infrastructure & Data

| Module | LOC | Purpose | Owner | Status |
|--------|-----|---------|-------|--------|
| `models.py` | 392 | Core data models | Infrastructure | ⚠️ CONSOLIDATE |
| `human_evaluator_models.py` | 341 | Human evaluator models | Infrastructure | ⚠️ CONSOLIDATE |
| `datasets.py` | 173 | Dataset management | Infrastructure | ✅ ACTIVE |
| `comparative_calibration_runner.py` | 137 | CLI test runner | Infrastructure | ✅ ACTIVE |

**Total: 1,043 LOC** ← Data layer (2 competing model files)

### Dead Code

| Module | LOC | Purpose | Issue | Action |
|--------|-----|---------|-------|--------|
| `viva_simulation.py` | 449 | Simulate student responses | Not imported, duplicates conductor | 📌 ARCHIVE |

**Total: 449 LOC** ← Dead code

---

## Execution Flow

### Happy Path: Generate Assessment

```
Input: Repository + Engineering Concern
  ↓
[1] Load Engineering Review
    ├─ Find relevant reviews (matching concern)
    └─ Extract implementation signals
  ↓
[2] Analyze Failure Patterns
    ├─ Identify potential failure modes
    └─ Map to observable signals
  ↓
[3] Generate Viva Session Plan
    ├─ Create 3-4 opening questions
    │   └─ Evidence-grounded in reviews
    ├─ Prepare follow-up paths
    └─ Design response evaluation rubric
  ↓
[4] Conduct Viva Session (Interactive Loop)
    ├─ Present question
    ├─ Accept response
    ├─ Score response quality
    │   ├─ Specificity (0-100%)
    │   ├─ Correctness (0-100%)
    │   └─ Quality enum (EXCELLENT/GOOD/ADEQUATE/WEAK/EVASIVE/CONTRADICTION)
    ├─ Determine if follow-up needed
    │   └─ If ADEQUATE/WEAK: generate targeted follow-up
    └─ Repeat until 3-4 responses collected
  ↓
[5] Analyze Reasoning Patterns
    ├─ For each response, extract indicators:
    │   ├─ Understanding indicators (7 types):
    │   │   ├─ EXPLAINS_RATIONALE
    │   │   ├─ MENTIONS_TRADEOFFS
    │   │   ├─ HANDLES_EDGE_CASE
    │   │   ├─ IDENTIFIES_GAPS
    │   │   ├─ ADMITS_UNCERTAINTY
    │   │   ├─ INTEGRATES_CONTEXT
    │   │   └─ CITES_SPECIFIC_IMPLEMENTATION
    │   ├─ Memorization indicators (7 types):
    │   │   ├─ TEXTBOOK_LANGUAGE
    │   │   ├─ GENERIC_ANSWER
    │   │   ├─ FAILS_FOLLOW_UP
    │   │   ├─ CONTRADICTS_SELF
    │   │   ├─ PARROTS_QUESTION
    │   │   ├─ USES_BUZZWORDS
    │   │   └─ BLANK_ON_EDGE_CASE
    └─ Classify reasoning pattern (1 of 5 levels)
  ↓
[6] Compute Implementation Familiarity
    ├─ Base classification (DEEP/PRACTICED/INFORMED/LOW/INSUFFICIENT)
    ├─ Confidence score (0-1)
    │   └─ <2 indicators → MEDIUM/LOW confidence
    │   └─ 2-4 indicators → HIGH confidence
    │   └─ >4 indicators → VERY HIGH confidence
    └─ Uncertainty surfaces (e.g., "Based on 1 indicator, insufficient data")
  ↓
[7] Trust Audit
    ├─ Check for overconfidence
    │   └─ Flag any score > 0.95 without 3+ indicators
    ├─ Verify evidence grounding
    │   └─ Every conclusion must map to specific evidence
    ├─ Flag contradictions
    │   └─ When responses diverge, note it
    └─ Surface uncertainty
        └─ Confidence < 0.7 → flag as MEDIUM/LOW
  ↓
[8] Generate Assessment Report
    ├─ Classification: DEEP_IMPLEMENTATION_FAMILIARITY / PRACTICED / INFORMED / INSUFFICIENT
    ├─ Confidence: HIGH/MEDIUM/LOW (reflects signal strength)
    ├─ Evidence trace: Q1→[indicators]→score, Q2→[indicators]→score, ...
    ├─ Uncertainty: "Based on X indicators, confidence Y%"
    └─ Transcript: Full Q&A with evaluation markers

Output: Assessment Report + Transcript + Explainability
```

---

## Data Flow

### Request Phase
```
Repository Metadata
    ↓
Code Structure → ExecutionGraph
Engineering Reviews (Corpus) → CorpusContext
Failure Patterns (Corpus) → FailureSignalMap
```

### Session Phase
```
Question Plan
    ↓
Candidate Response
    ↓
ResponseEvaluation
    ├─ Specificity score
    ├─ Correctness score
    ├─ Quality enum
    └─ Red flags
    ↓
IndicatorExtraction
    ├─ Understanding indicators
    └─ Memorization indicators
```

### Analysis Phase
```
Indicator Data (per response)
    ↓
ReasoningPatternClassification
    ├─ Score calculation
    ├─ Depth classification
    └─ Confidence computation
    ↓
AggregateProfile
    ├─ Overall familiarity
    ├─ Overall confidence
    └─ Red flags
    ↓
TrustAudit
    └─ Overconfidence check
    └─ Evidence verification
    ↓
FinalAssessment
    ├─ Grounded classification
    ├─ Confidence (reflects uncertainty)
    └─ Explainability trace
```

---

## Module Dependencies

### Import Graph

```
reasoning_depth_analyzer.py
├─ Imports from: (no other HV modules)
├─ Used by: __init__.py, comparative_calibration_runner.py
└─ Data source: VivaSession (external)

viva_session_conductor.py
├─ Imports from: engineering_review_corpus
├─ Used by: __init__.py, comparative_calibration_runner.py
└─ Data source: CandidateResponse (external)

trust_audit.py
├─ Imports from: (no other HV modules)
├─ Used by: comparative_calibration_runner.py
└─ Data source: Various (flexible)

engineering_review_corpus.py
├─ Imports from: (no other HV modules)
├─ Used by: viva_session_conductor.py, comparative_reasoning_evaluator.py
└─ Data source: Hardcoded fixture

failure_corpus.py
├─ Imports from: (no other HV modules)
├─ Used by: comparative_evaluator.py, execution_behavior_analysis.py
└─ Data source: Hardcoded fixture

comparative_reasoning_evaluator.py
├─ Imports from: engineering_review_corpus, failure_corpus
├─ Used by: comparative_calibration_runner.py
└─ Data source: VivaSession, assessment report

⚠️ COMPLEX DEPENDENCIES:

evaluator.py
├─ Imports from: human_evaluator_models, models
├─ Used by: [unknown]
└─ Status: REVIEW NEEDED

comparative_evaluator.py
├─ Imports from: human_evaluator_models, execution_behavior_analysis
├─ Used by: comparative_calibration_runner.py
└─ Status: REVIEW NEEDED (3 competing evaluation systems)

execution_behavior_analysis.py
├─ Imports from: models, failure_corpus
├─ Used by: comparative_evaluator.py
└─ Status: REVIEW NEEDED (speculative behavior analysis)

models.py
├─ Imports from: (no other HV modules)
├─ Imported by: execution_behavior_analysis.py
└─ Status: CONSOLIDATE with human_evaluator_models.py

human_evaluator_models.py
├─ Imports from: (no other HV modules)
├─ Imported by: evaluator.py, comparative_evaluator.py
└─ Status: CONSOLIDATE with models.py
```

---

## Critical Issues Summary

### 🔴 Issue 1: Multiple Evaluation Systems

**Problem:** Three competing evaluation approaches
```
evaluator.py                    ← Original pattern, usage unknown
comparative_evaluator.py        ← Newer, multi-dimensional
execution_behavior_analysis.py  ← Speculative behaviors
```

**Impact:** 
- Confusing maintenance burden
- Potential behavioral divergence
- Unclear which is "source of truth"

**Resolution:**
- [ ] Audit which is actually used
- [ ] Consolidate into single `implementation_familiarity_evaluator.py`
- [ ] Document clear ownership

---

### 🔴 Issue 2: Split Model Definitions

**Problem:** Models scattered across two files
```
models.py                    → 11 classes (ExecutionGraph, etc.)
human_evaluator_models.py   → 16 classes (HumanEvaluationSession, etc.)
```

**Impact:**
- Schema inconsistencies
- Import confusion
- Maintenance overhead

**Resolution:**
- [ ] Consolidate into single `models.py`
- [ ] Create clear sections: CoreModels, SessionModels, EvaluationModels

---

### 🟠 Issue 3: Dead Code

**Problem:** viva_simulation.py not imported anywhere
```
viva_simulation.py (449 LOC)  ← Designed for simulating students
viva_session_conductor.py     ← Active, production use
```

**Impact:**
- Confusing for new developers
- Maintenance burden
- Dead code in repository

**Resolution:**
- [ ] Document as "archived/deprecated"
- [ ] Keep in repo with clear deprecation notice
- [ ] Potential future use for unit testing

---

### 🟠 Issue 4: API Bloat

**Problem:** 52 exported symbols from __init__.py

**Impact:**
- Confusing public API
- Hard to find what to use
- Maintenance overhead

**Resolution:**
- [ ] Reduce to ~20 core exports:
  - Core models: VivaQuestion, CandidateResponse, VivaSession
  - Core analyzers: VivaSessionConductor, ReasoningDepthAnalyzer
  - Core data: EngineeredReviewEntry, FailureCorpusRepository
  - Evaluation: TrustAuditPipeline
  - Main runner: ComparativeCalibrationRunner

---

## Terminology Mapping (Hardening)

### Before (Pseudo-Psychological)
```
"Builder Detection"
"Fake Developer Detection"
"Deep Builder"
"Memorizer"
"Builder Confidence"
"Reasoning Depth"
```

### After (Evidence-Grounded)
```
"Implementation Familiarity Analysis"
"Surface Knowledge Identification"
"High Implementation Familiarity"
"Low Implementation Familiarity"
"Implementation Familiarity Confidence Score"
"Reasoning Pattern Classification"
```

---

## Testing Strategy

### Unit Tests (Per Module)
- VivaSessionConductor: Question generation, response scoring
- ReasoningDepthAnalyzer: Indicator detection, classification
- TrustAuditPipeline: Overconfidence detection, evidence tracing

### Integration Tests
- End-to-end: Repository → Assessment Report
- Fairness: Edge cases (weak speakers, confident guessers, etc.)
- Bias: Communication style doesn't affect classification

### Real Human Testing
- Internal validation (3 builders, 3 non-builders)
- Pilot study (10-15 real people)
- Error case collection (misclassifications)

---

## Success Criteria

| Criterion | Target | Current | Status |
|-----------|--------|---------|--------|
| Module clarity | <3 competing systems | 3 evaluation systems | ⚠️ TODO |
| Dead code | 0% | viva_simulation.py | ⚠️ TODO |
| Export bloat | <20 core symbols | 52 symbols | ⚠️ TODO |
| False positive rate | <5% on real humans | Unknown | ❌ TEST |
| Fairness bias | 0 communication-style correlation | Unknown | ❌ TEST |
| Evidence tracing | 100% traceable | ~90% | ⚠️ TODO |
| Documentation | Complete | 0% | ❌ TODO |

---

## Next Steps

1. **Week 1**: Audit and consolidate evaluation systems
2. **Week 2**: Rename terminology throughout codebase
3. **Week 3**: Implement fairness audit framework
4. **Week 4**: Real human testing framework
5. **Week 5+**: Validation and hardening
