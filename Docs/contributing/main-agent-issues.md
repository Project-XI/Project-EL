# MAIN Agent — Contributor Issue Breakdown

This document defines the 6 pre-scoped contributor issues for the MAIN Agent. Each issue owns exactly one responsibility and must not expand into other agent domains.

> **Rule:** MAIN orchestrates. It does not analyse. All intelligence comes from ORACLE outputs.

---

## Issue 1: Session State Manager

**Goal:** Build a persistent viva session state manager.

### Responsibilities
- Track session lifecycle stages (init → active → complete → closed)
- Store asked question history (ordered)
- Store candidate response history (mapped to correct turns)
- Retain contradiction memory across turns
- Maintain weak-area and topic coverage state
- Track follow-up chains
- Support session recovery after interruption

### Technical Requirements
- JSON serializable state model
- Multi-turn session support
- Deterministic state mutations
- Replay-safe and order-stable
- No database coupling (use storage interface)

### Suggested File Structure
```
backend/src/agents/main_agent/session/
  state.py
  transitions.py
  history.py
  persistence.py

backend/src/agents/main_agent/models/
  session_state.py
  transcript_entry.py
  coverage_state.py
```

### Acceptance Criteria
- Session state can be saved and restored without data loss
- Asked questions preserved in order
- Responses mapped to correct question turns
- Session transitions unit-testable in isolation

---

## Issue 2: Viva Flow Orchestrator

**Goal:** Build the central viva flow orchestrator for session progression.

### Responsibilities
- Sequence viva questions from ORACLE VivaTargets
- Manage pacing and turn progression
- Trigger session state transitions
- Inject follow-up branches when quality is weak
- Balance topic categories across session
- Decide when to terminate the viva
- Keep all decisions deterministic and replayable

### Technical Requirements
- Consumes ORACLE outputs as inputs — does NOT recompute them
- Avoids repetitive questioning
- Deterministic for same state + inputs
- No UI dependencies

### Suggested File Structure
```
backend/src/agents/main_agent/orchestration/
  flow_orchestrator.py
  pacing.py
  termination.py
  branching.py
  category_balancer.py
```

---

## Issue 3: Follow-Up Question Strategy Engine

**Goal:** Build an evidence-grounded follow-up strategy layer.

### Responsibilities
- Detect shallow or generic responses
- Escalate depth when quality is WEAK or ADEQUATE
- Probe implementation familiarity using ORACLE signals
- Challenge contradictions when responses conflict
- Generate operational follow-ups grounded in failure scenarios
- Preserve evidence references for every follow-up generated

### Technical Requirements
- Consumes ORACLE observable signals and failure scenarios
- Follow-up selection deterministic for same inputs
- No textbook-style generic prompts
- No invented facts not present in shared inputs

### Suggested File Structure
```
backend/src/agents/main_agent/followups/
  strategy_engine.py
  patterns.py
  contradiction_probe.py
  weak_answer_detector.py
  evidence_mapper.py
```

---

## Issue 4: Topic Coverage Tracker

**Goal:** Track which implementation domains have been covered to prevent repetitive questioning.

### Responsibilities
- Track architecture coverage
- Track runtime reasoning coverage
- Track failure-analysis coverage
- Track scalability and security coverage
- Detect unanswered or under-covered topics
- Reduce repetitive questioning

### Suggested File Structure
```
backend/src/agents/main_agent/coverage/
  tracker.py
  categories.py
  heuristics.py
  coverage_state.py
```

---

## Issue 5: Transcript Persistence Layer

**Goal:** Persist the full viva transcript for audit, replay, and export.

### Responsibilities
- Store question and answer entries (ordered)
- Log contradiction events with session step reference
- Log fairness events from SentinelAgent annotations
- Support JSON export for downstream tools
- Retain event ordering
- Preserve evidence links

### Technical Requirements
- JSON exportable
- Replay-safe (same turn history from persisted state)
- No UI logic
- Does not mutate viva decisions

### Suggested File Structure
```
backend/src/agents/main_agent/transcript/
  store.py
  serializer.py
  replay.py
  event_log.py
  schemas.py
```

---

## Issue 6: ORACLE Integration Adapter

**Goal:** Create a normalised adapter between ORACLE outputs and MAIN orchestration.

### Responsibilities
- Normalise ORACLE StructuredContext outputs
- Expose stable fields: viva targets, observable signals, failure scenarios
- Validate schema shape (strict, explicit)
- Handle malformed payloads safely
- Be the ONLY place where ORACLE schema differences are handled

### Technical Requirements
- Does NOT duplicate ORACLE analysis logic
- Strict schema validation
- Malformed payloads fail safely (not silently)
- Independently testable

### Suggested File Structure
```
backend/src/agents/main_agent/integration/
  oracle_adapter.py
  oracle_schema.py
  payload_normalizer.py
  validation.py
  compatibility.py
```

---

## Contributor Rules (All Issues)

1. Keep MAIN orchestration-focused — no analysis
2. Preserve evidence grounding at every decision point
3. Do not add speculative AI systems
4. Do not duplicate ORACLE intelligence logic
5. Keep modules small, composable, and independently testable
6. Make every state transition auditable
7. If a change looks like analysis → move to OracleAgent
8. If it looks like moderation → move to SentinelAgent

---

## Review Standard

Before merging any MAIN Agent work:
- [ ] Issue is narrow and non-overlapping
- [ ] Code does not infer hidden reasoning
- [ ] Code uses ORACLE outputs rather than recomputing them
- [ ] Code is deterministic and replayable
- [ ] Code can be explained in one paragraph

---

## Related Docs

- [Agent Overview](../architecture/agent-overview.md) — Agent boundary rules
- [Contributing Guidelines](./guidelines.md) — General contribution standards
