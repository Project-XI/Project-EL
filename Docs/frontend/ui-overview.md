# Frontend & UI Overview

ORACLE has two UI surfaces: the main Analysis Dashboard and the Calibration Dashboard.

---

## Main Analysis Dashboard

**File:** `frontend/index.html` (also mirrored in `Docs/index.html`)  
**Style:** `frontend/style.css`  
**Logic:** `frontend/app.js`  
**Orb Animation:** `frontend/orb.js`

### What It Shows

| Panel | Data Source | Description |
|---|---|---|
| **Backend Framework Card** | `payload.backend_framework.value` | Detected framework (e.g. FastAPI) |
| **Architecture Pattern Card** | `payload.architecture_pattern.value` | Detected architecture (e.g. REST + WebSocket) |
| **Authentication System Card** | `payload.authentication_system.value` | Detected auth (e.g. JWT Bearer) |
| **Graph Integrity Card** | `payload.execution_graph.nodes.length` | Number of graph nodes found |
| **Execution Graph** | `payload.execution_graph` | Interactive node/edge diagram (Mermaid) |
| **Viva Intelligence List** | `payload.viva_intelligence_targets` | Evidence-grounded interview questions |
| **Anomalies & Failure Paths** | `payload.runtime_risks` + `payload.failure_paths` | Risk severity and propagation paths |
| **Benchmark Results Table** | `payload.evaluation_metrics` | Accuracy vs ground truth |
| **Terminal Log Panel** | WebSocket `type: "log"` messages | Real-time streaming agent progress |

---

## UI → Backend Connection

```
Browser opens WebSocket: ws://localhost:8001/ws/analyze
        ↓
User enters repo URL, clicks Analyze
        ↓
UI sends: { "repo_url": "https://github.com/..." }
        ↓
Backend streams: { "type": "log", ... } (many messages)
        ↓
Backend sends: { "type": "result", "data": {...} }
        ↓
UI renders all panels from data
```

---

## Viva Intelligence Card Rendering

Each viva target renders as a card with:

| Field | Display |
|---|---|
| `category` | Badge (Architecture / Security / Runtime / etc.) |
| `difficulty` | Coloured tag (hard = red / medium = yellow / foundational = green) |
| `topic` | Card title |
| `question_target` | Full question text |
| `depth_score` | Score bar (0–10) |
| `confidence` | Percentage shown |
| `reasoning_summary` | Evidence summary text |
| `related_node` | Graph node ID link |

> ⚠️ **Minor Alignment Note:** The agent may emit `"foundational"` for difficulty, while the UI `diffTag()` function expects `"easy"`. The UI fallback handles this gracefully with a `.tag.pass` class — no functional impact. Standardisation to `"easy|medium|hard"` is planned for Phase 4.

---

## Execution Graph Visualisation

Rendered using Mermaid.js from the `execution_graph` payload:

```javascript
// Node types map to shapes:
ROUTE         → rounded rectangle
MIDDLEWARE    → parallelogram
DB_QUERY      → cylinder
STATE_STORE   → database shape
AUTH_HANDLER  → hexagon
```

Each node is clickable and shows: `file_path`, `line_number`, `snippet`

---

## Calibration Dashboard

**File:** `backend/testing_oracle_ui/calibration_dashboard.html`

Open directly in browser (no server required). Displays:
- Signal precision/recall bar charts
- Confidence calibration curve (expected vs actual accuracy)
- Viva question validity scores
- Per-repository fixture breakdown

---

## UI Alignment Status (Phase 3.5 Audit)

| Component | Status | Notes |
|---|---|---|
| WebSocket connection | ✅ ALIGNED | Endpoint, input format, output format |
| Dashboard cards | ✅ ALIGNED | All EvidenceModel fields match |
| Execution graph | ✅ ALIGNED | Nodes, edges, types, metadata |
| Viva intelligence output | ✅ ALIGNED | All VivaTarget fields match (minor difficulty terminology note) |
| Anomalies & failure paths | ✅ ALIGNED | runtime_risks and failure_paths populated |
| Benchmark results table | ✅ ALIGNED | evaluation_metrics from OracleEvaluator |
| Terminal logs | ✅ ALIGNED | log_type colouring works |
| Observable signals panel | 🟡 UNUSED | Data available but not displayed; enhancement opportunity |

---

## Known Minor Issues

| Issue | Impact | Resolution |
|---|---|---|
| Difficulty: `"foundational"` vs `"easy"` | Cosmetic only — UI handles gracefully | Standardise to `"easy"` in Phase 4 |
| Observable signals not displayed | Data available, no rendering | Add signals panel in future enhancement |
| Dual viva target field names | No impact — UI reads both | Consolidate to single field in Phase 4 |

---

## Related Docs

- [WebSocket API](../api-docs/websocket-api.md) — Full payload schema
- [Data Flow](../architecture/data-flow.md) — How data reaches the UI
- [Deployment](../deployment/local-setup.md) — How to run the UI locally
