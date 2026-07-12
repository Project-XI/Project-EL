# WebSocket API Reference

ORACLE communicates with the browser UI via a persistent WebSocket connection.

**Endpoint:** `ws://localhost:8001/ws/analyze`  
**Protocol:** JSON messages over WebSocket  
**Server:** FastAPI + `python-multipart`, `uvicorn`

---

## Connection Flow

```
Browser                          FastAPI Server
  │                                   │
  │──── ws://localhost:8001/ws/analyze ──→│
  │                                   │
  │──── { "repo_url": "..." } ────────→│
  │                                   │
  │←─── { "type": "log", ... } ───────│  (streaming)
  │←─── { "type": "log", ... } ───────│  (streaming)
  │        ... many log messages ...   │
  │←─── { "type": "result", ... } ────│  (final payload)
  │                                   │
  │──── close ────────────────────────│
```

---

## Input Message

Sent once after WebSocket connection is established.

```json
{
  "repo_url": "https://github.com/org/repo-name"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `repo_url` | `string` | ✅ Yes | Full HTTPS GitHub URL of the repository to analyse |

---

## Streaming Messages (Backend → UI)

Sent continuously during analysis. Used to update the terminal log panel.

```json
{
  "type": "log",
  "message": "[Oracle] Building execution graph...",
  "log_type": "info"
}
```

| Field | Type | Values | Description |
|---|---|---|---|
| `type` | `string` | `"log"` | Always `"log"` for streaming messages |
| `message` | `string` | Any | Human-readable progress message |
| `log_type` | `string` | `info` \| `warn` \| `success` \| `error` | Controls colour in terminal panel |

---

## Final Result Payload (Backend → UI)

Sent once when analysis is complete.

```json
{
  "type": "result",
  "data": { ... }
}
```

### `data` Object Schema

#### Framework Detection

```json
"backend_framework": {
  "value": "FastAPI",
  "confidence": 0.95,
  "evidence": ["backend/src/main.py:12 — @app.get('/health')"]
}
```

| Field | Type | Description |
|---|---|---|
| `value` | `string` | Detected framework name |
| `confidence` | `float` | Detection confidence (0–1) |
| `evidence` | `List[string]` | Code locations that support detection |

Same schema applies to:
- `architecture_pattern` — e.g. "REST + WebSocket"
- `authentication_system` — e.g. "JWT Bearer"

---

#### Execution Graph

```json
"execution_graph": {
  "nodes": [
    {
      "id": "node_001",
      "label": "GET /users",
      "type": "ROUTE",
      "metadata": {
        "file_path": "backend/src/main.py",
        "line_number": 42,
        "snippet": "@app.get('/users')"
      }
    }
  ],
  "edges": [
    {
      "source": "node_001",
      "target": "node_002",
      "relationship": "calls"
    }
  ]
}
```

**Node types:** `ROUTE` | `MIDDLEWARE` | `DB_QUERY` | `STATE_STORE` | `AUTH_HANDLER`

---

#### Viva Intelligence Targets

```json
"viva_intelligence_targets": [
  {
    "topic": "N+1 Query in /users endpoint",
    "question_target": "What performance concern does the /users endpoint have?",
    "difficulty": "hard",
    "importance_score": 0.95,
    "category": "Architecture",
    "depth_score": 8.5,
    "related_node": "node_001",
    "confidence": 0.88,
    "reasoning_summary": "Endpoint loads 100+ related resources without batching"
  }
]
```

**Difficulty values:** `"hard"` | `"medium"` | `"foundational"`  
**Category values:** `"Architecture"` | `"Tradeoff"` | `"Security"` | `"Scalability"` | `"Failure-Path"` | `"Runtime"`

---

#### Runtime Risks

```json
"runtime_risks": [
  {
    "severity": "HIGH",
    "value": "Unhandled async exception in payment service",
    "confidence": 0.87,
    "evidence": ["backend/src/services/payment.py:88"]
  }
]
```

---

#### Failure Paths

```json
"failure_paths": [
  {
    "value": "DB connection loss causes cascading timeout in /checkout",
    "confidence": 0.82,
    "evidence": ["backend/src/routes/checkout.py:55"]
  }
]
```

---

#### Evaluation Metrics

```json
"evaluation_metrics": {
  "metrics": {
    "stack_accuracy": 0.95,
    "auth_detection_accuracy": 0.91
  },
  "mismatches": [],
  "expected": {
    "expected_stack": "FastAPI + PostgreSQL",
    "expected_protected_routes": ["/admin", "/dashboard"],
    "expected_architecture": "Layered REST"
  }
}
```

---

## Error Handling

If analysis fails, the backend sends:

```json
{
  "type": "log",
  "message": "[Oracle] ERROR: Failed to clone repository. Check GITHUB_TOKEN.",
  "log_type": "error"
}
```

The WebSocket connection is then closed.

---

## Backend Source Reference

- Handler: `backend/src/main.py` — `websocket_analyze()` at line 42
- OracleAgent: `backend/src/agents/oracle/agent.py`
- StructuredContext model: `backend/src/models/`

---

## Related Docs

- [Payload Schemas](./payload-schemas.md) — Full Pydantic model reference
- [Data Flow](../architecture/data-flow.md) — How data is assembled
- [UI Overview](../frontend/ui-overview.md) — How the UI consumes this payload
