# ORACLE Documentation

> **ORACLE** — Optimized Repository Analysis & Candidate Learning Engine  
> An evidence-grounded Implementation Familiarity Assessment System

---

## Documentation Index

### 🚀 Getting Started

| Document | Description |
|---|---|
| [README](./getting-started/README.md) | What ORACLE does, quick navigation, system requirements |
| [Installation](./getting-started/installation.md) | Local setup, environment, running the server |

---

### 🏛️ Architecture

| Document | Description |
|---|---|
| [System Overview](./architecture/system-overview.md) | Top-level architecture, agent pipeline, design principles |
| [Module Inventory](./architecture/module-inventory.md) | All modules, LOC, ownership, active/review/archived status |
| [Execution Flow](./architecture/execution-flow.md) | Step-by-step pipeline: repo clone → AST → viva → assessment |
| [Data Flow](./architecture/data-flow.md) | Data structures, transformations, WebSocket payload schemas |
| [Agent Overview](./architecture/agent-overview.md) | Per-agent responsibilities, boundaries, and decision routing |

---

### 🔌 API Reference

| Document | Description |
|---|---|
| [WebSocket API](./api-docs/websocket-api.md) | Full WebSocket protocol, input/output schemas, streaming format |

---

### 🧠 Viva Intelligence

| Document | Description |
|---|---|
| [Viva Overview](./viva-intelligence/viva-overview.md) | How the viva system works, indicators, familiarity levels, examples |
| [Session Flow](./viva-intelligence/session-flow.md) | Turn-by-turn session walkthrough with state and examples |

---

### 🎨 Frontend

| Document | Description |
|---|---|
| [UI Overview](./frontend/ui-overview.md) | Dashboard panels, UI alignment status, known minor issues |

---

### 🚢 Deployment

| Document | Description |
|---|---|
| [Environment Variables](./deployment/environment-variables.md) | All env vars, required scopes, security rules |

---

### ⚙️ CI/CD

| Document | Description |
|---|---|
| [Workflows](./ci-cd/workflows.md) | GitHub Actions workflows: calibration, Discord notify |
| [Discord Notifications](./ci-cd/discord-notifications.md) | Commit-to-Discord bot setup guide |

---

### 🧪 Testing

| Document | Description |
|---|---|
| [Calibration Framework](./testing/calibration.md) | Automated P/R metrics, confidence calibration, CI thresholds |
| [Human Testing Protocol](./testing/human-testing-protocol.md) | 4-phase real-human validation protocol |

---

### 🔐 Security

| Document | Description |
|---|---|
| [Security Overview](./security/overview.md) | Fairness audit, trust audit, overconfidence detection, access control |

---

### ⚠️ Error Handling

| Document | Description |
|---|---|
| [Known Issues](./error-handling/known-issues.md) | Active known issues, error codes, recovery behaviour |
| [Bias Mitigation](./error-handling/bias-mitigation.md) | All 6 FairnessAuditor patterns, mitigation strategies |

---

### 📊 Monitoring & Logging

| Document | Description |
|---|---|
| [Observability](./monitoring-logging/observability.md) | Runtime tracing, WebSocket log streaming, calibration dashboard |

---

### 🤝 Contributing

| Document | Description |
|---|---|
| [Guidelines](./contributing/guidelines.md) | Code standards, PR process, naming conventions, review checklist |
| [MAIN Agent Issues](./contributing/main-agent-issues.md) | 6 pre-scoped contributor issues with file structures |

---

### 🗺️ User Flows

| Document | Description |
|---|---|
| [Analysis Workflow](./user-flows/analysis-workflow.md) | End-to-end user journey: open UI → analyse → review → assess |

---

## Project Phase Status

| Phase | Status |
|---|---|
| Phase 1 – Architecture Assessment & Cleanup | ✅ Complete |
| Phase 2 – Evidence-Grounded Intelligence (3 engines) | ✅ Complete |
| Phase 3.5 – Stabilization & Reality Hardening | 🔄 In Progress |
| Phase 4 – Real Human Testing (10–15 participants) | ⏳ Planned |

---

## Performance Baseline (Phase 2 Calibration)

| Component | Precision | Recall | F1 |
|---|---|---|---|
| Observable Signals | 0.847 | 0.823 | 0.835 |
| Failure Propagation | 0.805 | 0.778 | 0.791 |
| Viva Question Validity | 0.856 | — | — |
| Viva Question Grounding | 0.912 | — | — |
| Confidence Calibration RMSE | — | — | 0.062 ✅ |

---

## Quick Links

- **Run the system:** [Installation Guide](./getting-started/installation.md)
- **Understand the pipeline:** [Execution Flow](./architecture/execution-flow.md)
- **Read the API:** [WebSocket API](./api-docs/websocket-api.md)
- **Run calibration:** [Calibration Framework](./testing/calibration.md)
- **Contribute:** [Contributing Guidelines](./contributing/guidelines.md)
