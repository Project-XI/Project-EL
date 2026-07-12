# Known Issues & Error Handling

This document tracks known system limitations, error patterns, and the mitigation strategies in place for each.

---

## Active Known Issues

### Issue 1: Multiple Evaluation Systems (3 Competing)

| Field | Detail |
|---|---|
| **Priority** | 🔴 HIGH |
| **Status** | ⚠️ Consolidation planned — Phase 4 |
| **Impact** | Confusing ownership; possible behavioural divergence |

**Problem:**
Three evaluation modules exist with overlapping purposes:
- `evaluator.py` — Original pattern, usage unknown
- `comparative_evaluator.py` — Newer, multi-dimensional
- `execution_behavior_analysis.py` — Speculative behaviours

**Mitigation (current):** `comparative_reasoning_evaluator.py` is the authoritative path. Others are under review.

**Resolution (planned):** Consolidate into single `implementation_familiarity_evaluator.py`

---

### Issue 2: Split Model Definitions

| Field | Detail |
|---|---|
| **Priority** | 🔴 HIGH |
| **Status** | ⚠️ Consolidation planned — Phase 4 |
| **Impact** | Schema inconsistencies; import confusion |

**Problem:**
Models are split across two files:
- `models.py` → 11 classes (ExecutionGraph, etc.)
- `human_evaluator_models.py` → 16 classes (HumanEvaluationSession, etc.)

**Resolution (planned):** Merge into single `models.py` with sections: `CoreModels`, `SessionModels`, `EvaluationModels`

---

### Issue 3: Difficulty Terminology Mismatch

| Field | Detail |
|---|---|
| **Priority** | 🟡 LOW |
| **Status** | Acceptable — Phase 4 cleanup |
| **Impact** | Cosmetic only |

**Problem:** Agent emits `"foundational"` for viva difficulty; UI `diffTag()` expects `"easy"`.

**Mitigation:** UI handles gracefully with `.tag.pass` CSS fallback.

**Resolution (planned):** Standardise to `"easy|medium|hard"` across all enums in Phase 4.

---

### Issue 4: Observable Signals Not Displayed in UI

| Field | Detail |
|---|---|
| **Priority** | 🟡 LOW |
| **Status** | Enhancement opportunity |
| **Impact** | Data available but unused |

**Problem:** OracleAgent produces `observable_signals` in StructuredContext but the UI doesn't render them.

**Resolution (planned):** Add observable signals visualisation panel to UI in a future enhancement.

---

### Issue 5: Dual Viva Target Field Names

| Field | Detail |
|---|---|
| **Priority** | 🟡 LOW |
| **Status** | Acceptable for legacy support |
| **Impact** | No functional impact |

**Problem:** Agent sets both `implementation_viva_targets` (legacy) and `viva_intelligence_targets` (current). UI reads `viva_intelligence_targets` first with fallback.

**Resolution (planned):** Remove legacy field in Phase 4.

---

### Issue 6: Real Human Testing Not Yet Conducted

| Field | Detail |
|---|---|
| **Priority** | 🔴 HIGH |
| **Status** | Phase 4 planned |
| **Impact** | Accuracy rates unknown on real humans |

**Mitigation:** Automated calibration (Precision ~0.84, RMSE 0.062) provides confidence in component accuracy.

**Resolution:** [4-phase human testing protocol](../testing/human-testing-protocol.md) ready to execute.

---

## Error Recovery Behaviour

### Repository Clone Failure

```
Trigger: Invalid URL, missing GITHUB_TOKEN, private repo without access
Response: WebSocket log error message → connection closed
Recovery: Check GITHUB_TOKEN scope, verify repo URL
```

### AST Parsing Failure

```
Trigger: Unsupported language, malformed code, encrypted files
Response: ExecutionGraph returned with 0 nodes
Recovery: Check language support; ORACLE will still generate corpus-only questions
```

### LLM API Failure

```
Trigger: OPENAI_API_KEY invalid, rate limit, timeout
Response: WebSocket error log → analysis aborted
Recovery: Check API key, retry after rate limit window
```

### Calibration Threshold Failure (CI)

```
Trigger: Metric below threshold (e.g. Precision < 0.75)
Response: CI job fails, PR blocked
Recovery: Fix the regression in the relevant engine before merging
```

---

## Error Codes

| Error Pattern | Likely Cause |
|---|---|
| `Failed to clone repository` | GitHub token missing or insufficient scope |
| `AST parse error` | Unsupported file type or encoding issue |
| `Corpus context empty` | No matching engineering reviews for the concern |
| `Confidence RMSE above threshold` | Calibration regression — check last code change |
| `Overconfidence detected` | Score > 0.95 with < 4 indicators — TrustAudit flagged |
| `Insufficient evidence` | Session too short; < 2 indicators collected |

---

## What to Do When Calibration Fails

1. Run calibration locally and read the full report:
   ```bash
   cd backend
   python -m evaluation.calibration.calibration_runner
   ```

2. Identify which validator failed (Signal, Failure, Viva, Confidence)

3. Check the last code change to that validator's related module

4. Fix the regression and re-run before pushing

---

## Related Docs

- [Calibration Framework](../testing/calibration.md)
- [Bias Mitigation](./bias-mitigation.md)
- [Security Overview](../security/overview.md)
- [Module Inventory](../architecture/module-inventory.md)
