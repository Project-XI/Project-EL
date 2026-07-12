# Data Flow

This document describes how data structures are created, transformed, and passed between modules throughout the ORACLE pipeline.

---

## Request Phase

```
Repository Metadata (URL, branch, concern)
        ↓
┌──────────────────────────────────────────────────────┐
│  Code Parsing                                        │
│  AST → ExecutionGraph                                │
│    nodes: List[GraphNode]                            │
│    edges: List[GraphEdge]                            │
│    node types: ROUTE | MIDDLEWARE | DB_QUERY | ...   │
└──────────────────────────────────────────────────────┘
        ↓
┌──────────────────────────────────────────────────────┐
│  Corpus Loading                                      │
│  EngineeringReviewCorpus → CorpusContext             │
│    reviews: List[EngineeredReviewEntry]              │
│    signals: List[str]                                │
│    concern_match_score: float                        │
└──────────────────────────────────────────────────────┘
        ↓
┌──────────────────────────────────────────────────────┐
│  Failure Mapping                                     │
│  FailureCorpusRepository → FailureSignalMap          │
│    scenarios: List[FailureScenario]                  │
│    severity: HIGH | MEDIUM | LOW                     │
│    propagation_path: List[GraphNode]                 │
└──────────────────────────────────────────────────────┘
```

---

## Session Phase

```
VivaTarget (per question)
    topic: str
    question_target: str
    difficulty: "hard" | "medium" | "foundational"
    importance_score: float
    category: "Architecture" | "Tradeoff" | "Security" | "Scalability" | "Runtime"
    depth_score: float (0–10)
    related_node: str (graph node ID)
    confidence: float (0–1)
    reasoning_summary: str
        ↓
CandidateResponse
    question_id: str
    response_text: str
    turn: int
        ↓
ResponseEvaluation
    specificity_score: float (0–100)
    correctness_score: float (0–100)
    quality: EXCELLENT | GOOD | ADEQUATE | WEAK | EVASIVE | CONTRADICTION
    red_flags: List[str]
```

---

## Analysis Phase

```
IndicatorSet (per response)
    understanding: List[IndicatorType]
    memorisation: List[IndicatorType]
        ↓
ReasoningPatternAssessment
    pattern: DEEP | PRACTICED | INFORMED | LOW | INSUFFICIENT
    implementation_familiarity_score: float (0–1)
    familiarity_confidence: HIGH | MEDIUM | LOW | VERY_HIGH
    indicator_evidence: List[IndicatorEvidence]
        ↓
AggregateProfile
    overall_familiarity: FamiliarityLevel
    overall_confidence: ConfidenceLevel
    red_flags: List[str]
    contradiction_log: List[ContradictionEvent]
        ↓
TrustAuditResult
    is_overconfident: bool
    evidence_grounded: bool
    uncertainty_flags: List[str]
    adjusted_confidence: float
        ↓
FairnessAuditReport
    issues: List[FairnessAuditIssue]
    bias_types: List[BiasType]
    manual_review_recommended: bool
    confidence_adjusted: bool
        ↓
FinalAssessment
    classification: str (DEEP_IMPLEMENTATION_FAMILIARITY | PRACTICED | INFORMED | INSUFFICIENT)
    confidence: str (HIGH | MEDIUM | LOW)
    evidence_trace: List[EvidenceTraceEntry]
    uncertainty_statement: str
    transcript: List[TranscriptEntry]
```

---

## WebSocket Payload (UI → Backend)

```json
{
  "repo_url": "https://github.com/org/repo"
}
```

---

## WebSocket Streaming Messages (Backend → UI)

### Log Message (streaming)
```json
{
  "type": "log",
  "message": "[Oracle] Building execution graph...",
  "log_type": "info"
}
```

`log_type` values: `info` | `warn` | `success` | `error`

---

## WebSocket Result Payload (Backend → UI)

```json
{
  "type": "result",
  "data": {
    "backend_framework": { "value": "FastAPI", "confidence": 0.95, "evidence": [] },
    "architecture_pattern": { "value": "REST + WebSocket", "confidence": 0.88, "evidence": [] },
    "authentication_system": { "value": "JWT Bearer", "confidence": 0.91, "evidence": [] },
    "execution_graph": {
      "nodes": [...],
      "edges": [...]
    },
    "viva_intelligence_targets": [...],
    "runtime_risks": [...],
    "failure_paths": [...],
    "evaluation_metrics": {
      "metrics": { "stack_accuracy": 0.95, "auth_detection_accuracy": 0.91 },
      "mismatches": [],
      "expected": {}
    }
  }
}
```

---

## Model Dependency Map

```
reasoning_depth_analyzer.py
    ├─ No internal HV imports
    └─ Used by: __init__.py, comparative_calibration_runner.py

viva_session_conductor.py
    ├─ Imports: engineering_review_corpus
    └─ Used by: __init__.py, comparative_calibration_runner.py

trust_audit.py
    ├─ No internal HV imports
    └─ Used by: comparative_calibration_runner.py

engineering_review_corpus.py
    ├─ No internal HV imports
    └─ Used by: viva_session_conductor, comparative_reasoning_evaluator

failure_corpus.py
    ├─ No internal HV imports
    └─ Used by: comparative_evaluator, execution_behavior_analysis

fairness_audit.py
    ├─ No internal HV imports
    └─ Used by: comparative_calibration_runner

comparative_reasoning_evaluator.py
    ├─ Imports: engineering_review_corpus, failure_corpus
    └─ Used by: comparative_calibration_runner

⚠️ NEEDS REVIEW:
evaluator.py               → imports human_evaluator_models, models
comparative_evaluator.py   → imports human_evaluator_models, execution_behavior_analysis
execution_behavior_analysis.py → imports models, failure_corpus
```

---

## Related Docs

- [Execution Flow](./execution-flow.md) — Step-by-step pipeline
- [WebSocket API](../api-docs/websocket-api.md) — Full API contract
- [Module Inventory](./module-inventory.md) — Ownership and status
