# Agent Overview

ORACLE uses a four-agent pipeline. Each agent has a **strictly defined** responsibility boundary. No agent duplicates another's intelligence.

---

## Agent Pipeline

```
Request (repo_url)
      ↓
MainAgent
      ├──→ GatekeeperAgent  (identity + access)
      ├──→ OracleAgent       (analysis + intelligence)
      └──→ SentinelAgent     (audit + moderation)
      ↓
FinalAssessment
```

---

## 1. MainAgent

**File:** `backend/src/agents/main_agent/agent.py`  
**Role:** Viva session orchestrator

### Responsibilities
- Coordinates GatekeeperAgent → OracleAgent → SentinelAgent pipeline
- Manages session lifecycle (init → active → complete → closed)
- Persists viva session state across multiple turns
- Controls question sequencing and pacing
- Routes follow-up decisions to ORACLE outputs — does NOT recompute intelligence
- Maintains topic coverage tracker to avoid repetitive questioning
- Persists full transcript for audit and replay

### MAIN Must NOT
- Perform AST analysis
- Duplicate ORACLE reasoning logic
- Invent speculative questions
- Hide scoring systems
- Behave like a generic chatbot

### Key Sub-Modules (Planned)

```
backend/src/agents/main_agent/
  session/        ← Session state management
  orchestration/  ← Flow control, pacing, branching
  followups/      ← Evidence-grounded follow-up strategy
  coverage/       ← Topic coverage tracker
  transcript/     ← Persistence layer
  integration/    ← ORACLE adapter (normalises outputs)
```

---

## 2. GatekeeperAgent

**File:** `backend/src/agents/gatekeeper/`  
**Role:** Identity context + access validation

### Responsibilities
- Validates the requesting identity
- Establishes access context for the session
- Provides identity metadata to downstream agents
- Returns identity context as input to ORACLE pipeline

### Gatekeeper Must NOT
- Perform code analysis
- Make session decisions
- Modify viva question generation

---

## 3. OracleAgent

**File:** `backend/src/agents/oracle/agent.py`  
**Role:** Core intelligence and analysis engine

### Responsibilities
- Clones repository and builds ExecutionGraph via AST
- Detects backend framework, architecture pattern, authentication system
- Runs ObservableSignalsEngine (error handling, resilience, observability)
- Runs ExecutionGraphFailureAnalyzer (failure propagation paths)
- Runs EvidenceGroundedVivaGenerator (grounded viva questions)
- Conducts viva session scoring (per-response specificity, correctness, quality)
- Classifies reasoning patterns and implementation familiarity
- Runs TrustAuditPipeline and FairnessAuditor
- Assembles and returns StructuredContext

### OracleAgent Pipeline

```
OracleAgent.process()
  ├── Clone + AST Parse → ExecutionGraph
  ├── ObservableSignalsEngine.extract_signals() → observable_signals
  ├── ExecutionGraphFailureAnalyzer.analyze() → failure_paths
  ├── EvidenceGroundedVivaGenerator.generate() → viva_intelligence_targets
  ├── TechDetector → backend_framework, architecture_pattern, auth_system
  ├── OracleEvaluator → evaluation_metrics (benchmarked vs ground truth)
  └── StructuredContext.assemble() → final JSON payload
```

---

## 4. SentinelAgent

**File:** `backend/src/agents/sentinel/`  
**Role:** Audit + moderation layer

### Responsibilities
- Logs audit events for all session decisions
- Enforces moderation policies on outputs
- Appends fairness-related audit annotations to transcripts
- Does NOT own session state — reads only

### Sentinel Must NOT
- Generate questions
- Score candidates
- Override ORACLE assessments without documented policy

---

## Agent Boundaries (Summary)

| Decision | Owner |
|---|---|
| AST analysis, code intelligence | OracleAgent |
| Session flow, turn progression | MainAgent |
| Identity, access | GatekeeperAgent |
| Audit logs, moderation | SentinelAgent |
| Follow-up strategy | MainAgent (consuming ORACLE outputs) |
| Confidence scoring | OracleAgent |
| Fairness detection | OracleAgent (FairnessAuditor) |
| Transcript persistence | MainAgent |

---

## Decision Routing Rule

> If a change starts to look like **analysis** → move it to OracleAgent.  
> If it looks like **moderation** → move it to SentinelAgent.  
> If it looks like **submission validation** → move it to GatekeeperAgent.  
> If it's **orchestration** → it belongs in MainAgent.

---

## Related Docs

- [MAIN Agent Issue Breakdown](../contributing/main-agent-issues.md)
- [Execution Flow](./execution-flow.md)
- [Module Inventory](./module-inventory.md)
