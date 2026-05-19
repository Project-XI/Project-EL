# MAIN Agent Issue Breakdown

This document defines a contributor-safe issue set for the ORACLE MAIN Agent. The MAIN Agent is the viva orchestration layer, not a reasoning engine. It must stay deterministic, evidence-grounded, and modular.

## Architecture Boundary

The current codebase routes the overall pipeline through `backend/src/agents/main_agent/agent.py`, which coordinates GATEKEEPER, ORACLE, and SENTINEL. That orchestration role is the correct home for viva session control.

The MAIN Agent must:

- orchestrate the viva flow
- track session state
- persist transcript data
- coordinate ORACLE outputs into questioning decisions
- remain explainable and auditable

The MAIN Agent must not:

- perform deep AST analysis
- duplicate ORACLE implementation logic
- invent speculative reasoning
- hide confidence scoring logic
- behave like a generic chatbot

The issues below are intentionally narrow. Each issue owns one responsibility and must not expand into other agent domains.

---

## Issue 1: Session State Manager

### 1. Title

Build a persistent viva session state manager for the MAIN Agent.

### 2. Purpose

Create the durable session memory layer that lets the MAIN Agent resume, replay, and continue a viva without losing critical state.

### 3. Background Context

The MAIN Agent currently orchestrates the pipeline, but session memory is not yet represented as a clear standalone module. For a viva system, the agent needs a structured state object that survives multiple turns and can be serialized safely.

This is not a reasoning feature. It is a session coordination primitive that the orchestration layer uses to avoid repetition and preserve transcript continuity.

### 4. Responsibilities

- track session lifecycle stages
- store asked question history
- store candidate response history
- retain contradiction memory
- retain weak-area tracking
- maintain topic coverage state
- track follow-up chains
- support session recovery after interruption

### 5. Technical Requirements

- the state model must be JSON serializable
- the state must support multi-turn sessions
- the design must be modular and easy to extend
- the model must be replay-safe and order-stable
- transitions must be explicit rather than inferred
- state mutation must be deterministic
- state objects must be testable without the full viva stack

### 6. Acceptance Criteria

- session state can be saved and restored without data loss
- asked questions are preserved in order
- responses are mapped to the correct question turns
- contradiction history is retained across turns
- weak-area and coverage fields update predictably
- session transitions can be unit tested
- replay from persisted state produces the same session view

### 7. Non-Goals

- no AI reasoning or question generation
- no ORACLE analysis duplication
- no UI rendering logic
- no hidden scoring systems
- no transcript visualization concerns
- no direct database or file system coupling unless abstracted through a storage interface

### 8. Suggested File Structure

```text
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

### 9. Integration Notes

- the state manager should be owned by MAIN only
- ORACLE may feed evidence inputs, but not mutate this state directly
- SENTINEL may read session events for audit purposes, but not own the state
- the state schema should expose stable fields for transcript and coverage tracking
- any schema changes must be backward compatible or explicitly versioned

### 10. Testing Expectations

- unit tests for serialization and deserialization
- unit tests for session recovery
- unit tests for lifecycle transitions
- unit tests for question history ordering
- unit tests for contradiction tracking
- fixture-based tests for replay consistency

---

## Issue 2: Viva Flow Orchestrator

### 1. Title

Build the central viva flow orchestrator for MAIN Agent session progression.

### 2. Purpose

Create the deterministic engine that controls viva progression, pacing, and branching decisions.

### 3. Background Context

The current MAIN Agent is already the entry point that coordinates GATEKEEPER, ORACLE, and SENTINEL. What is missing is a clearly scoped flow orchestrator that owns the sequence of viva actions after initialization.

This issue is about orchestration, not intelligence generation. It should decide when to ask, when to follow up, when to move on, and when to end the session.

### 4. Responsibilities

- sequence viva questions
- manage pacing and turn progression
- trigger session transitions
- inject follow-up branches
- balance topic categories across the session
- decide when to terminate the viva
- keep the flow deterministic across replay

### 5. Technical Requirements

- must consume ORACLE outputs as inputs, not recompute them
- must avoid repetitive questioning
- must support dynamic flow transitions based on session state
- must remain deterministic for the same state and inputs
- must separate sequencing policy from state storage
- must be able to run without UI dependencies
- must not depend on hidden model scores

### 6. Acceptance Criteria

- the orchestrator can run a multi-turn viva end to end
- branching follow-ups are handled correctly
- state updates are reflected in the next decision step
- repeated prompts are reduced when coverage already exists
- replaying the same inputs yields the same orchestration decisions
- session termination conditions are explicit and testable

### 7. Non-Goals

- no AST parsing
- no fairness scoring
- no speculative LLM reasoning
- no transcript rendering
- no direct repository inspection
- no replacement of the ORACLE analysis layer

### 8. Suggested File Structure

```text
backend/src/agents/main_agent/orchestration/
  flow_orchestrator.py
  pacing.py
  termination.py
  branching.py
  category_balancer.py
```

### 9. Integration Notes

- the orchestrator should consume session state plus ORACLE viva targets
- it should not infer implementation facts on its own
- it should emit decisions that can be logged and replayed
- any change to session transition semantics should be coordinated with the session state manager
- if a new question type is needed, define it as an orchestration concern, not a reasoning engine

### 10. Testing Expectations

- deterministic orchestration tests
- follow-up branching tests
- pacing and termination tests
- coverage-aware sequencing tests
- replay consistency tests
- regression tests for repetitive question avoidance

---

## Issue 3: Follow-Up Question Strategy Engine

### 1. Title

Build an evidence-grounded follow-up question strategy engine for MAIN Agent.

### 2. Purpose

Create the strategy layer that determines how the MAIN Agent probes shallow answers, contradictions, and implementation gaps.

### 3. Background Context

The viva should not feel like a generic chatbot loop. It should challenge implementation understanding using evidence from ORACLE outputs such as viva targets, observable signals, and failure scenarios.

This engine is responsible for strategy, not creativity. It should choose from deterministic follow-up patterns based on structured evidence.

### 4. Responsibilities

- detect shallow or generic responses
- escalate depth when an answer is weak
- probe implementation familiarity
- challenge contradictions
- generate operational follow-ups
- remain grounded in available evidence only

### 5. Technical Requirements

- the engine must consume ORACLE signals and failure scenarios
- follow-up selection must be deterministic for the same inputs
- it must avoid textbook-style generic prompts
- it must support contradiction-driven probing
- it must preserve evidence references for each follow-up
- it must not invent facts not present in shared inputs

### 6. Acceptance Criteria

- weak answers trigger meaningful follow-ups
- follow-ups remain implementation-specific
- operational and runtime questions are preferred over generic theory
- contradiction probing works when prior answers conflict
- repeated prompts are avoided when a topic was already covered
- generated follow-ups can be traced back to evidence inputs

### 7. Non-Goals

- no free-form hallucinated questioning
- no generic chatbot behavior
- no ORACLE logic duplication
- no AI memory beyond the approved session state
- no broad conversation generation outside viva purpose

### 8. Suggested File Structure

```text
backend/src/agents/main_agent/followups/
  strategy_engine.py
  patterns.py
  contradiction_probe.py
  weak_answer_detector.py
  evidence_mapper.py
```

### 9. Integration Notes

- inputs should come from ORACLE outputs and MAIN session state
- the strategy engine should not parse source code directly
- each follow-up should cite the evidence or gap that triggered it
- if a future enhancement needs new evidence fields, update shared schemas first
- strategy decisions should be loggable for replay and review

### 10. Testing Expectations

- weak-answer response tests
- contradiction-based probing tests
- evidence-grounding tests
- non-repetitive follow-up tests
- deterministic strategy selection tests
- fixture tests using known ORACLE outputs

---

## Issue 4: Topic Coverage Tracker

### 1. Title

Build a topic coverage tracker for viva breadth and gap detection.

### 2. Purpose

Track which implementation domains have been covered so the MAIN Agent can avoid repetitive questioning and can intentionally close gaps.

### 3. Background Context

The MAIN Agent should not just ask questions. It should manage coverage across architecture, runtime behavior, failure analysis, and tradeoffs. A topic coverage tracker makes the viva more structured and prevents over-focusing on one area.

### 4. Responsibilities

- track architecture coverage
- track runtime reasoning coverage
- track failure-analysis coverage
- track scalability and security coverage
- detect unanswered or under-covered topics
- reduce repetitive questioning

### 5. Technical Requirements

- coverage state should be lightweight
- topic tagging must be supported
- updates must be deterministic
- coverage fields should be easy to serialize
- the tracker must integrate with session state
- it must be simple enough for contributors to extend safely

### 6. Acceptance Criteria

- topic coverage updates correctly after each turn
- missing-topic detection works consistently
- repeated questioning is reduced when a topic is already covered
- topic tags can be added without rewriting the tracker
- coverage data can be displayed or exported without changing core logic

### 7. Non-Goals

- no reasoning about code correctness
- no ORACLE replacement logic
- no UI-specific rendering concerns
- no hidden policy engine
- no autonomous grading of candidate quality

### 8. Suggested File Structure

```text
backend/src/agents/main_agent/coverage/
  tracker.py
  categories.py
  heuristics.py
  coverage_state.py
```

### 9. Integration Notes

- coverage should be updated from question issuance and response completion events
- category definitions should remain stable across the viva lifecycle
- the tracker should consume session state rather than duplicating it
- ORACLE evidence can inform the initial topic map, but not the tracker logic itself

### 10. Testing Expectations

- coverage update tests
- missing-topic detection tests
- category tagging tests
- repetitive question reduction tests
- deterministic update tests
- serialization tests

---

## Issue 5: Transcript Persistence Layer

### 1. Title

Build a transcript persistence layer for explainable viva records.

### 2. Purpose

Persist the full viva transcript and related audit events so the session can be reviewed, replayed, and exported.

### 3. Background Context

The MAIN Agent needs a durable record of questions, answers, contradiction events, and fairness-related annotations. This record is a core engineering artifact, not a UI artifact.

The transcript must support explanation and replay. It should be easy for contributors to inspect and hard to misuse.

### 4. Responsibilities

- store question and answer entries
- log contradiction events
- log fairness events
- support replay export
- retain event ordering
- preserve evidence links

### 5. Technical Requirements

- transcript data must be JSON exportable
- storage structure must be replay-safe
- formatting must remain explainability-friendly
- the layer should not require UI logic
- the layer should not mutate viva decisions
- the persisted format should be stable enough for downstream tools

### 6. Acceptance Criteria

- sessions export correctly to JSON
- transcript replay reconstructs the same turn history
- contradiction and fairness events remain linked to the right session step
- the persistence layer can be exercised in isolation
- exported records remain readable by contributors

### 7. Non-Goals

- no question generation
- no assessment scoring
- no visualization logic
- no ORACLE analysis duplication
- no hidden state outside the transcript contract

### 8. Suggested File Structure

```text
backend/src/agents/main_agent/transcript/
  store.py
  serializer.py
  replay.py
  event_log.py
  schemas.py
```

### 9. Integration Notes

- transcript writes should be driven by session events, not ad hoc writes
- the persistence layer should be compatible with the session state manager
- SENTINEL events may be appended as audit annotations, but not interpreted here
- if file storage is used, keep it behind a storage interface

### 10. Testing Expectations

- JSON export tests
- replay reconstruction tests
- event ordering tests
- contradiction log tests
- fairness log tests
- storage abstraction tests

---

## Issue 6: ORACLE Integration Adapter

### 1. Title

Build a normalized ORACLE integration adapter for the MAIN Agent.

### 2. Purpose

Create the adapter that converts ORACLE outputs into stable inputs the MAIN Agent can safely use for orchestration.

### 3. Background Context

The MAIN Agent must never duplicate ORACLE analysis. It should only consume normalized ORACLE outputs such as viva targets, observable signals, failure scenarios, and evidence traces.

This adapter is the contract boundary between the intelligence layer and the orchestration layer. It should absorb schema variability and expose safe, versioned fields to MAIN.

### 4. Responsibilities

- normalize ORACLE outputs
- expose viva targets
- expose observable signals
- expose failure scenarios
- validate schema shape
- handle malformed payloads safely

### 5. Technical Requirements

- the adapter must not duplicate ORACLE logic
- schema validation must be strict and explicit
- malformed payloads must fail safely
- normalized outputs should be simple for MAIN to consume
- the adapter should remain modular and independently testable
- if schemas evolve, the adapter should be the first compatibility layer updated

### 6. Acceptance Criteria

- integration remains stable across expected ORACLE output shapes
- malformed payloads are rejected or normalized safely
- MAIN receives normalized interfaces only
- evidence links remain intact after normalization
- adapter behavior is deterministic and auditable

### 7. Non-Goals

- no ORACLE implementation duplication
- no AST parsing
- no viva orchestration logic
- no hidden confidence calculation
- no candidate response scoring

### 8. Suggested File Structure

```text
backend/src/agents/main_agent/integration/
  oracle_adapter.py
  oracle_schema.py
  payload_normalizer.py
  validation.py
  compatibility.py
```

### 9. Integration Notes

- the adapter should sit between ORACLE output models and MAIN orchestration logic
- the adapter should be the only place where ORACLE payload shape differences are handled
- if ORACLE adds a new field, update the adapter and shared schema intentionally
- do not let MAIN reach into ORACLE internals directly

### 10. Testing Expectations

- valid payload normalization tests
- malformed payload rejection tests
- schema compatibility tests
- regression tests for evidence mapping
- deterministic output tests
- adapter isolation tests

---

## Contributor Guidance

When implementing any of these issues, contributors must follow these rules:

- keep the MAIN Agent orchestration-focused
- preserve evidence grounding at every decision point
- do not add speculative AI systems
- do not duplicate ORACLE intelligence logic
- keep new modules modular and independently testable
- prefer small, composable files over monolithic logic
- make every state transition auditable

If a change starts to look like analysis, move it to ORACLE. If it starts to look like moderation, move it to SENTINEL. If it starts to look like submission validation, move it to GATEKEEPER.

## Recommended Review Standard

Before merging any MAIN Agent work, reviewers should confirm:

- the issue is narrow and non-overlapping
- the code does not infer hidden reasoning
- the code does not read like a generic chat assistant
- the code uses ORACLE outputs rather than recomputing them
- the code remains deterministic and replayable
- the code can be explained by a contributor in one paragraph
