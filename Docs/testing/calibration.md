# Calibration Framework

ORACLE's intelligence outputs are validated through a comprehensive calibration pipeline. This ensures confidence scores reflect actual accuracy — not just internal self-assessments.

---

## Why Calibration Matters

> If ORACLE says "95% confident" but is only 60% accurate, that is worse than useless.

Calibration ensures:
- Precision/Recall metrics are tracked per component
- Confidence scores map to real accuracy curves
- Hallucinations (evidence that doesn't exist) are caught
- Regressions are blocked by CI/CD thresholds

---

## Framework Location

```
backend/evaluation/calibration/
  ├── __init__.py                     ← Framework overview
  ├── repository_fixtures.py          ← 4 diverse test repositories
  ├── signal_validator.py             ← Observable signal P/R metrics
  ├── failure_propagation_validator.py← Failure path validation
  ├── viva_quality_validator.py       ← Viva question specificity check
  ├── confidence_calibrator.py        ← Score vs accuracy calibration
  ├── observability.py                ← Runtime tracing
  ├── calibration_runner.py           ← Orchestration + report generation
  ├── README.md                       ← Detailed framework docs
  ├── SYSTEM_OVERVIEW.md              ← Architecture concepts
  └── INTEGRATION_GUIDE.md            ← Integration instructions

backend/evaluation/
  ├── check_calibration_thresholds.py ← Quality gate (CI use)
  ├── validate_oracle_analysis.py     ← Validation wrapper
  └── CALIBRATION_QUICKSTART.md       ← 5-minute reference
```

---

## Test Repository Fixtures

4 stress-test repositories with known expected outputs:

| Fixture | Type | Tests |
|---|---|---|
| Clean FastAPI REST API | Well-structured | Baseline accuracy |
| Messy student project | Unstructured | Noise tolerance |
| Broken async system | Partial failures | Failure path detection |
| Monorepo with shared state | Complex | Graph traversal |

---

## Validators

### Signal Validator

Tests that observable signals are correctly detected.

```bash
cd backend
python -m evaluation.calibration.calibration_runner
```

**Metrics:**
- **Precision** = Detected signals that actually exist
- **Recall** = Actual signals that were detected
- **F1 Score** = Harmonic mean of P and R

**Baseline:**

| Component | Precision | Recall | F1 |
|---|---|---|---|
| Observable Signals | 0.847 | 0.823 | 0.835 |
| Failure Propagation | 0.805 | 0.778 | 0.791 |
| Viva Quality (Validity) | 0.856 | — | — |
| Viva Grounding Score | 0.912 | — | — |
| Confidence Calibration RMSE | — | — | 0.062 |

---

### Failure Propagation Validator

Tests that failure scenarios correctly trace through the execution graph.

**Pass criteria:**
- Propagation paths must exist as actual edges in the graph
- Recovery strategies must reference real code locations
- Risk severity must be justified by path count

---

### Viva Quality Validator

Ensures generated viva questions are specific and grounded — not generic textbook questions.

**Rejects:**
- "What is FastAPI?" (generic)
- "How would you add machine learning?" (speculative)
- "Describe the MVC pattern" (textbook)

**Accepts:**
- "Your `/checkout` route has no timeout handler. Walk me through what happens when Stripe's API hangs."

---

### Confidence Calibrator

Maps confidence score buckets to actual precision/recall:

```
If ORACLE says 0.9 confidence → actual accuracy should be ~90%
If ORACLE says 0.6 confidence → actual accuracy should be ~60%
```

**Metric:** RMSE (Root Mean Squared Error between stated confidence and actual accuracy)

**Target:** RMSE < 0.10 (current baseline: 0.062 ✅)

---

## Running Calibration

### Full calibration run

```bash
cd backend
python -m evaluation.calibration.calibration_runner
```

### Threshold check (CI/CD quality gate)

```bash
cd backend
python evaluation/check_calibration_thresholds.py
```

Exit code `0` = PASSED, `1` = FAILED

### Validate against fixtures

```bash
cd backend
python evaluation/validate_oracle_analysis.py
```

### View dashboard

Open `backend/testing_oracle_ui/calibration_dashboard.html` in browser.

---

## CI/CD Integration

The GitHub Actions workflow runs calibration on every PR:

```yaml
# .github/workflows/calibration.yml
jobs:
  calibration:
    - name: Run calibration thresholds
      run: python evaluation/check_calibration_thresholds.py
```

**Strict mode** (main branch): Higher thresholds  
**Standard mode** (feature branches): Reasonable thresholds

---

## Threshold Reference

| Metric | Standard Mode | Strict Mode (main) |
|---|---|---|
| Signal Precision | ≥ 0.75 | ≥ 0.85 |
| Signal Recall | ≥ 0.70 | ≥ 0.80 |
| Failure Precision | ≥ 0.70 | ≥ 0.80 |
| Viva Validity | ≥ 0.80 | ≥ 0.85 |
| Confidence RMSE | ≤ 0.15 | ≤ 0.10 |

---

## Hallucination Prevention

Validators catch:
- **Signal hallucinations** — Signals that reference non-existent code locations
- **Failure hallucinations** — Failure paths through edges that don't exist in graph
- **Question hallucinations** — Viva questions referencing functionality not in the repo

---

## Related Docs

- [Human Testing Protocol](./human-testing-protocol.md)
- [Observability & Runtime Tracing](../monitoring-logging/runtime-tracing.md)
- [CI/CD Workflows](../ci-cd/workflows.md)
