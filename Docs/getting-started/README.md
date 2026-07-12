# Getting Started with ORACLE

ORACLE (Optimized Repository Analysis & Candidate Learning Engine) is an evidence-grounded Implementation Familiarity Assessment system. It analyzes a GitHub repository and conducts a structured viva (technical interview) to measure a candidate's real implementation familiarity — not memorised knowledge.

---

## What ORACLE Does

1. **Clones and parses** a repository via AST analysis
2. **Builds an execution graph** tracing routes, middleware, DB calls, auth, and state
3. **Extracts observable signals** — error handling, resilience patterns, observability hooks
4. **Detects failure scenarios** by traversing the execution graph
5. **Generates grounded viva questions** from real code evidence
6. **Conducts a viva session** evaluating depth of understanding vs. surface-level recitation
7. **Produces a trust-audited assessment** with confidence scores and full evidence traces

---

## Quick Navigation

| Where do you want to go? | Link |
|---|---|
| Set up locally in 5 minutes | [Installation Guide](./installation.md) |
| Understand the full architecture | [Architecture Overview](../architecture/system-overview.md) |
| Run the calibration pipeline | [Calibration Quickstart](../testing/calibration.md) |
| Understand the viva session flow | [Viva Intelligence](../viva-intelligence/viva-overview.md) |
| Read the API contracts | [API Docs](../api-docs/websocket-api.md) |
| Contribute to the project | [Contributing Guide](../contributing/guidelines.md) |

---

## System Requirements

| Requirement | Minimum |
|---|---|
| Python | 3.10+ |
| Node.js | 18+ (for dashboard UI) |
| RAM | 4 GB |
| OS | macOS / Linux / WSL2 |
| GitHub Access | Personal Access Token (for private repos) |

---

## High-Level Architecture

```
Browser (ORACLE UI)
      ↓ WebSocket
FastAPI Backend (main.py :8001)
      ↓
MainAgent → GatekeeperAgent → OracleAgent → SentinelAgent
                                    ↓
                         Intelligence Pipeline
                    ┌────────────────────────────┐
                    │ Observable Signals Engine   │
                    │ Execution Graph Failure     │
                    │ Evidence-Grounded Viva Gen  │
                    └────────────────────────────┘
                                    ↓
                         StructuredContext (JSON)
                                    ↓
                            WebSocket Result
```

---

## Project Status

| Phase | Status |
|---|---|
| Phase 1 – Architecture Assessment & Cleanup | ✅ Complete |
| Phase 2 – Evidence-Grounded Intelligence | ✅ Complete |
| Phase 3.5 – Stabilization & Reality Hardening | 🔄 In Progress |
| Phase 4 – Real Human Testing | ⏳ Planned |

---

## Next Step

→ [Installation Guide](./installation.md)
