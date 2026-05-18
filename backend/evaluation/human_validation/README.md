# ORACLE Human Comparative Validation Framework

## Overview

This framework moves ORACLE from "validated engineering intelligence prototype" to "human-compared implementation reasoning system." 

Instead of asking "Does ORACLE work?" we now ask: **"Does ORACLE reason like experienced engineers?"**

### Key Difference from Phase 2

| Phase 2 | Phase 3 |
|---------|---------|
| ✅ Validation against expected outputs | ✅ Validation against human reviewers |
| ✅ Metrics grounded in test runs | ✅ Metrics grounded in human evaluation |
| ✅ Confidence calibration | ✅ Agreement analysis with humans |
| ✅ Quality checks | ✅ Trustworthiness audit |
| ❌ Human comparison | ✅ **Direct comparison with engineers** |
| ❌ Failure corpus | ✅ **12+ failure modes to detect** |
| ❌ Viva adaptation | ✅ **Simulated weak student responses** |
| ❌ Runtime behavior | ✅ **Execution flow analysis** |

## Architecture

```
┌─────────────────────────────────────────────────┐
│  ORACLE Intelligence Engines (Phase 2)          │
├─────────────────────────────────────────────────┤
│  • ObservableSignalsEngine                      │
│  • ExecutionGraphFailureAnalyzer                │
│  • EvidenceGroundedVivaGenerator                │
└─────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────┐
│  Human Comparative Validation (Phase 3)         │
├─────────────────────────────────────────────────┤
│  • Human Evaluator Models                       │
│  • Failure Corpus Dataset (12+ modes)          │
│  • Viva Session Simulator                       │
│  • Comparative Evaluator                        │
│  • Execution Behavior Analyzer                  │
│  • Trustworthiness Auditor                      │
└─────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────┐
│  Metrics & Dashboards                           │
├─────────────────────────────────────────────────┤
│  • Signal Agreement (Precision/Recall)          │
│  • Failure Realism Scores                       │
│  • Viva Quality Rates                           │
│  • Trust Audit Results                          │
│  • Comparative Dashboard                        │
└─────────────────────────────────────────────────┘
```

## Components

### 1. Human Evaluator Models (`human_evaluator_models.py`)

Structured data models for capturing real human engineering evaluations.

**Key Classes:**

- **HumanSignalEvaluation** - How accurate is a detected signal?
  - `signal_accuracy`: ACCURATE, INCOMPLETE, HALLUCINATED, etc.
  - `realism_score`: How important/realistic is this signal?
  - Evidence references to prove verdict

- **HumanFailureScenarioEvaluation** - Is failure scenario realistic?
  - `human_verdict`: REALISTIC, SPECULATIVE, OVERLY_PESSIMISTIC, etc.
  - `actual_severity`: What humans believe is realistic
  - Propagation and recovery realism scores

- **HumanVivaQuestionEvaluation** - Is viva question good engineering?
  - `human_verdict`: List of quality aspects (TEXTBOOK_GENERIC, IMPLEMENTATION_DEEP_DIVE, etc.)
  - `code_specificity_score`: How specific to this codebase?
  - `distinguishes_senior_engineer`: Would this reveal level differences?

- **ComparativeAgreementMetrics** - Overall agreement statistics
  - Signal precision/recall/F1 vs human
  - Failure realism rates
  - Viva quality rates
  - Trustworthiness score

**Pre-defined Datasets:**

- `GITHUB_PR_REVIEW_DATASET` - Real GitHub PR comments
- `BACKEND_INTERVIEW_DATASET` - Tech interview evaluations
- `ACADEMIC_CODE_REVIEW_DATASET` - Professor evaluations
- `ARCHITECTURE_REVIEW_DATASET` - Architecture discussions

### 2. Failure Corpus Dataset (`failure_corpus.py`)

Intentionally problematic implementations to stress-test ORACLE.

**10 Failure Categories:**

1. **Broken Retry Logic** - Backoff doesn't reset, thundering herd, no jitter
2. **Disconnected Auth Middleware** - Auth verified once, not re-validated
3. **Dead Cache Logic** - Cache invalidation configured but never called
4. **Inconsistent Validation** - Rules differ between layers
5. **Async Race Conditions** - Concurrent requests without synchronization
6. **Missing Timeout Handling** - External calls with no timeout
7. **Duplicated Service Logic** - Business logic copy-pasted across routes
8. **Weak Error Propagation** - Errors caught and swallowed
9. **Missing Fallback Mechanisms** - No graceful degradation
10. **State Consistency Violation** - Microservice updates not synchronized

**Each Repository Fixture Includes:**

```python
FailureCorpusRepository(
    id="corpus_001",
    name="Broken Exponential Backoff Retry",
    category=FailureCorpusCategory.RETRY_LOGIC,
    
    # What's wrong
    problems=[
        "Retry count not reset",
        "Exponential multiplier persists",
        "No jitter, causes thundering herd",
    ],
    
    # What ORACLE should find
    expected_signals=[
        {"signal": "Retry pattern detected", "confidence_min": 0.85},
        {"signal": "No jitter in backoff", "confidence_min": 0.80},
    ],
    
    expected_failure_scenarios=[
        {
            "scenario": "Database temporarily unavailable",
            "propagation_path": ["retry_handler", "connection_pool", "app"],
            "risk_severity": "high",
        }
    ],
    
    # Ways ORACLE might get confused
    adversarial_challenges=[
        "Retry logic might be split across decorator and handler",
        "Backoff might be in separate service",
    ],
)
```

### 3. Viva Session Simulator (`viva_simulation.py`)

Simulates adaptive viva interviews with realistic student responses.

**Simulated Response Types:**

- **CORRECT** - Knows implementation and can explain
- **TEXTBOOK** - Recites generic concepts, no codebase context
- **PARTIAL** - Correct but missing important details
- **CONTRADICTORY** - Says conflicting things
- **MISUNDERSTANDING** - Wrong assumptions about code
- **WEAK_EXPLANATION** - Right answer, unclear reasoning

**Follow-up Quality Metrics:**

- `PROBING` - Targets revealed weakness
- `CLARIFYING` - Asks for elaboration
- `DEEPENING` - Pushes understanding deeper
- `GENERIC` - Could apply to any codebase
- `IRRELEVANT` - Doesn't relate to response

**Usage:**

```python
simulator = AdaptiveVivaSimulator()

# Simulate sessions for different student levels
sessions = simulator.simulate_session(
    repository_name="Project-EL",
    initial_questions=questions,
    student_level="intermediate"  # junior, intermediate, senior
)

# Evaluate ORACLE's follow-up questions
metrics = simulator.evaluate_follow_up_set(
    sessions,
    oracle_follow_ups,
)

# Check probing rate: Did ORACLE target weaknesses?
print(f"Probing rate: {metrics['probing_rate']:.1%}")
print(f"Generic rate: {metrics['generic_rate']:.1%}")
```

### 4. Comparative Evaluator (`comparative_evaluator.py`)

Orchestrates comparison between ORACLE and human reviewers.

**Three Specialized Evaluators:**

- **ComparativeSignalEvaluator**
  - Compares ORACLE signals against human assessments
  - Calculates precision/recall/agreement rates
  - Identifies hallucinations

- **ComparativeFailureEvaluator**
  - Compares failure scenarios against human judgments
  - Measures realism rate and severity alignment
  - Checks propagation path accuracy

- **ComparativeVivaEvaluator**
  - Compares viva questions against quality assessments
  - Detects textbook/generic patterns
  - Measures code specificity

- **TrustworthinessAuditor**
  - Audits for hallucinations and speculation
  - Flags weak reasoning
  - Generates comprehensive trust score

### 5. Dataset Storage (`datasets.py`)

Stores and loads structured human review data without inventing values.

- `HumanReviewDataset` JSON for bundled corpora
- `HumanReviewDatapoint` JSONL for append-friendly exports
- Source manifests for PR reviews, interviews, maintainer feedback, and architecture reviews

### 6. Trust Audit Pipeline (`trust_audit.py`)

Deterministically flags weak reasoning before outputs are surfaced:

- Unsupported assumptions
- Speculative reasoning
- Generic viva phrasing
- Contradictory evidence
- Stale execution graphs
- Confidence misuse

### 7. Comparative Calibration Runner (`comparative_calibration_runner.py`)

Runs the full human-comparison flow from disk-backed inputs.

```bash
python -m evaluation.human_validation.comparative_calibration_runner \
    --repository-name Project-EL \
    --oracle-analysis path/to/oracle_analysis.json \
    --human-dataset path/to/human_reviews.json
```

The runner writes a report to `evaluation/human_validation/results/`.

**Usage:**

```python
runner = ComparativeEvaluationRunner()

metrics = runner.run_comparative_evaluation(
    repository_name="Project-EL",
    oracle_analysis=oracle_output,
    human_evaluation_dataset=human_datapoints,
)

print(f"Signal Precision: {metrics.signal_precision:.1%}")
print(f"Failure Realism: {metrics.failure_precision:.1%}")
print(f"Viva Quality: {metrics.viva_quality_rate:.1%}")
print(f"Trust Score: {metrics.oracle_trustworthiness:.1%}")
```

### 5. Execution Behavior Analyzer (`execution_behavior_analysis.py`)

Expands ORACLE's analysis beyond static structure to runtime behavior.

**Analyzes:**

- **Request Lifecycle** - Complete trace through middleware, services, DB
- **Dependency Interactions** - Service chains and cascade effects
- **Async Execution** - Race conditions and ordering issues
- **State Propagation** - How state mutates through execution
- **Failure Impact** - What happens when components fail
- **Consistency Models** - Strong vs eventual consistency

**Key Output:**

```python
RequestLifecycleTrace(
    route="/api/users",
    
    # Node-by-node execution
    execution_sequence=["middleware_auth", "route_handler", "service_layer", "db_query"],
    
    # State changes
    state_mutations=[
        {"step": "service_layer", "mutation": "user_context_set"},
    ],
    
    # Database operations in order
    db_operations=[
        {"operation": "SELECT * FROM users", "transaction_id": "tx_001"},
    ],
    
    # Async tasks spawned
    async_tasks=[
        {"task": "audit_log_write", "background": True},
    ],
    
    # Where failures can occur
    failure_points=[
        {"failure_point": "db_query", "propagates": True},
        {"failure_point": "auth_check", "propagates": True},
    ],
)
```

## Metrics & Agreements

### Signal Detection Agreement

- **Precision** = TP / (TP + FP) - % of ORACLE signals that humans agree with
- **Recall** = TP / (TP + FN) - % of human-identified signals that ORACLE found
- **F1 Score** = Harmonic mean

**Interpreting Results:**
- Precision 0.85+: Few hallucinations
- Recall 0.80+: Finding most signals humans see
- Both 0.80+: Good signal detection overall

### Failure Scenario Agreement

- **Realism Rate** - % of scenarios humans find realistic
- **Severity Alignment** - Does ORACLE severity match human judgment?
- **Propagation Accuracy** - Are execution paths correct?
- **Recovery Accuracy** - Are recovery strategies grounded?

**Interpreting Results:**
- Realism 0.75+: Most scenarios are realistic
- Alignment 0.70+: Severity judgments reasonable
- Propagation 0.80+: Paths through code accurate

### Viva Question Quality

- **Quality Rate** - % of questions humans rate as good
- **Code Specificity** - How specific to this codebase?
- **Distinguishes Levels** - Would this reveal junior vs senior?
- **Textbook Detection** - Flags generic/memorizable questions

**Interpreting Results:**
- Quality 0.80+: Most questions are good
- Specificity 0.75+: Questions are codebase-specific
- Distinguishes 0.70+: Questions probe real understanding

### Trustworthiness Score

Composite score combining:
- Signal audit (no hallucinations, good calibration)
- Failure audit (realistic scenarios, good propagation)
- Viva audit (specific questions, no generic patterns)
- Execution audit (correct runtime modeling)

**Score Interpretation:**
- 0.90+: Excellent, fully production-ready
- 0.80-0.90: Good, ready for production with monitoring
- 0.70-0.80: Fair, needs refinement before production
- <0.70: Not ready, needs significant work

## Running Comparative Validation

### Step 1: Prepare Human Evaluations

Populate human evaluation datasets with real data:

```python
from human_evaluator_models import (
    HumanReviewDatapoint,
    ReviewerRole,
    HumanSignalEvaluation,
)

datapoint = HumanReviewDatapoint(
    source_type="pr_review",
    source_reference="https://github.com/...",
    reviewer_role=ReviewerRole.SENIOR_BACKEND_ENGINEER,
    repository_name="Project-EL",
    human_observations="Good error handling, but missing timeout on external calls",
    identified_signals=["Error recovery patterns", "No timeout handling"],
)
```

### Step 2: Run ORACLE Analysis

Get ORACLE's analysis output:

```python
from src.agents.oracle.agent import OracleAgent

oracle = OracleAgent()
analysis = oracle.process(project_graph, execution_graph)

oracle_output = {
    "signals": {signal.name: signal.confidence for signal in analysis.observable_signals},
    "failure_scenarios": {s.name: s.risk_severity for s in analysis.failure_scenarios},
    "viva_questions": [q.question_text for q in analysis.viva_intelligence_targets],
}
```

### Step 3: Run Comparative Evaluation

```python
from human_validation.comparative_calibration_runner import ComparativeCalibrationRunner

runner = ComparativeCalibrationRunner()
report_path = runner.run_from_paths(
    repository_name="Project-EL",
    oracle_analysis_path="path/to/oracle_analysis.json",
    dataset_paths=["path/to/human_reviews.json"],
)

print(f"Saved comparative calibration report to: {report_path}")
```

### Step 4: Check Dashboard

Open the comparative dashboard to visualize results:

```bash
open backend/testing_oracle_ui/comparative_validation_dashboard.html
```

## Key Constraints (No New Speculation)

This framework maintains ORACLE's evidence-grounded principles:

✅ **What We Compare:**
- ORACLE signals against human signal evaluations
- ORACLE failure scenarios against human realism assessments
- ORACLE viva questions against human quality ratings
- ORACLE execution modeling against human understanding

❌ **What We Don't Do:**
- No new ML models or pattern matching
- No confidence inflation or arbitrary scoring
- No generic templates for comparison
- No speculative reasoning about what humans would say

✅ **All Metrics:**
- Based on real human evaluations
- Tied to actual code evidence
- Explainable and deterministic
- Come from pre-existing datasets

## Data Conventions

- Store real human review exports as `HumanReviewDataset` JSON.
- Store append-only comparisons as `HumanReviewDatapoint` JSONL.
- Use `datasets.py` to export a source manifest before evaluation runs.
- Do not fabricate agreement scores, trust scores, or reviewer responses.

## Expected Improvements Over Phase 2

### Before Phase 3
- ✅ Validated against test fixtures
- ✅ Signals grounded in code
- ✅ Failure scenarios traced through execution graph
- ✅ Viva questions checked for genericity
- ✅ Confidence scores calibrated
- ❌ No human comparison

### After Phase 3
- ✅ Validated against test fixtures
- ✅ Validated against human engineers
- ✅ Hallucinations identified and removed
- ✅ Speculative reasoning flagged
- ✅ Failure realism confirmed by humans
- ✅ Viva question quality rated by experts
- ✅ Execution behavior validated against human understanding
- ✅ Trustworthiness audited comprehensively
- ✅ Production-ready with human confidence

## Dashboard Tabs

### Overview
- Overall trustworthiness score
- Coverage metrics (repos, reviewers, datapoints)
- Agreement by category (signals, failures, viva)
- Trends over time

### Signal Agreement
- Precision/Recall metrics
- False positive analysis
- Confidence calibration quality
- Hallucinated vs strong signals

### Failure Analysis
- Realism agreement rates
- Propagation accuracy
- Severity alignment
- Speculative scenarios flagged

### Viva Questions
- Quality distribution
- Code specificity scores
- Level-distinguishing ability
- Generic patterns detected

### Trustworthiness
- Overall trust score
- Trust enablers (what's working)
- Trust gaps (what needs work)
- Hallucination detection
- Speculative reasoning detection

### Execution Behavior
- Request lifecycle traces
- Async race conditions
- Cascading failure paths
- State consistency analysis

## Production Readiness Criteria

ORACLE is production-ready when:

- ✅ Signal precision ≥ 0.85
- ✅ Signal recall ≥ 0.82
- ✅ Hallucinations < 5% of signals
- ✅ Failure realism agreement ≥ 0.80
- ✅ Viva quality rate ≥ 0.85
- ✅ Viva specificity ≥ 0.75
- ✅ Trustworthiness score ≥ 0.80
- ✅ No speculative reasoning in failure scenarios
- ✅ No speculative reasoning in viva questions
- ✅ Execution behavior correctly modeled

## Next Steps

1. **Populate Human Datasets** - Add real PR reviews, interview data, architecture discussions
2. **Run Comparative Evaluation** - Compare ORACLE against all datasets
3. **Review Audit Results** - Identify and fix hallucinations/speculation
4. **Monitor Dashboard** - Track metrics over time
5. **Iterate Based on Feedback** - Refine algorithms based on human input
6. **Deploy to Production** - Use in real code review workflows

---

**ORACLE Human Comparative Validation** | Evidence-Grounded | Human-Validated | Production-Ready
