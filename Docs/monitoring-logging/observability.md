# Monitoring & Observability

ORACLE includes a runtime observability layer that traces all reasoning steps during analysis — making every decision inspectable and debuggable.

---

## Observability Stack

| Component | Module | Purpose |
|---|---|---|
| Runtime Tracer | `calibration/observability.py` | Records reasoning steps as structured traces |
| Calibration Dashboard | `testing_oracle_ui/calibration_dashboard.html` | Visual trace and metric viewer |
| Calibration Runner | `calibration/calibration_runner.py` | Generates reports with all metric data |
| Log Callback | `main.py` → WebSocket | Real-time terminal streaming |

---

## Runtime Tracing

Every reasoning step in the ORACLE pipeline emits a structured trace record:

```json
{
  "step": "signal_extraction",
  "module": "ObservableSignalsEngine",
  "timestamp": "2026-05-18T12:34:56Z",
  "inputs": { "node_id": "node_042", "node_type": "DB_QUERY" },
  "outputs": { "signal": "Missing error handler on DB call", "severity": "HIGH" },
  "evidence": ["backend/src/routes/users.py:88"],
  "duration_ms": 124
}
```

Trace records are collected during analysis and exported as JSON.

---

## WebSocket Log Streaming

During analysis, progress is streamed to the browser UI in real time:

```
[Gatekeeper] Identity context established
[Oracle] Cloning repository...
[Oracle] AST parsing complete — 142 nodes found
[Oracle] Building execution graph...
[Oracle] Observable signals extraction...
[Oracle] 3 signals detected (HIGH: 1, MEDIUM: 2)
[Oracle] Failure scenario analysis...
[Oracle] 2 failure paths identified
[Oracle] Generating viva questions...
[Oracle] 6 evidence-grounded questions created
[Oracle] Assembling StructuredContext...
[Sentinel] Audit log written
✅ Analysis complete
```

Log types: `info` | `warn` | `success` | `error`

---

## Calibration Dashboard

**File:** `backend/testing_oracle_ui/calibration_dashboard.html`

Open in browser to view:
- Signal precision/recall charts
- Confidence calibration curves
- Viva quality validity scores
- Per-repository fixture performance
- Trend data from multiple runs

---

## Key Metrics to Monitor

| Metric | Target | Action if Below |
|---|---|---|
| Signal Precision | ≥ 0.85 (strict) | Review ObservableSignalsEngine detection logic |
| Signal Recall | ≥ 0.80 (strict) | Check corpus coverage for missing signal types |
| Failure Propagation Precision | ≥ 0.80 | Verify graph edge extraction completeness |
| Viva Validity | ≥ 0.85 | Review EvidenceGroundedVivaGenerator specificity filters |
| Confidence RMSE | ≤ 0.10 | Recalibrate confidence scoring weights |
| Overconfidence instances | 0 | Check TrustAuditPipeline threshold |

---

## Exporting Traces

```bash
cd backend
python -m evaluation.calibration.calibration_runner
```

Output files (generated in `backend/evaluation/results/`):
- `calibration_report_<timestamp>.json` — Full metric report
- `traces_<timestamp>.json` — Raw reasoning trace records
- `validation_report.html` — Human-readable HTML report

---

## What Gets Traced

| Pipeline Step | Traced? |
|---|---|
| Repository clone | ✅ Duration, success/fail |
| AST parsing | ✅ Node count, edge count |
| Observable signal extraction | ✅ Each signal with evidence |
| Failure path analysis | ✅ Each path with propagation chain |
| Viva question generation | ✅ Each question with grounding score |
| Response scoring | ✅ Each response with scores |
| Indicator extraction | ✅ Each indicator detected |
| Fairness audit | ✅ Issues found, patterns triggered |
| Trust audit | ✅ Overconfidence flags, evidence gaps |

---

## Related Docs

- [Calibration Framework](../testing/calibration.md) — How metrics are computed
- [CI/CD Workflows](../ci-cd/workflows.md) — How calibration is automated
- [WebSocket API](../api-docs/websocket-api.md) — Log message format reference
