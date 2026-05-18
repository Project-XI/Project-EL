# ORACLE Stabilization & Reality Hardening Phase

## Executive Summary

Transform ORACLE from "advanced intelligence prototype" to "stable, evidence-grounded implementation-aware viva infrastructure."

**Key Principle:** Architecture freeze. No new intelligence engines. Focus on stabilization, clarity, and real-world validation.

---

## Phase 1: Architecture Assessment & Cleanup

### Current State Analysis (May 18, 2026)

**Codebase Size:** 14 modules, 6,356 LOC
```
failure_corpus.py              807 LOC
viva_session_conductor.py      677 LOC
evaluator.py                   628 LOC
comparative_evaluator.py       600 LOC
reasoning_depth_analyzer.py    543 LOC
execution_behavior_analysis.py 466 LOC
viva_simulation.py             449 LOC (⚠️ POTENTIAL DUPLICATE)
comparative_reasoning_evaluator.py 430 LOC
human_evaluator_models.py      341 LOC
trust_audit.py                 338 LOC
models.py                      392 LOC
engineering_review_corpus.py   375 LOC
datasets.py                    173 LOC
comparative_calibration_runner.py 137 LOC
```

### Critical Issues

| Priority | Issue | Impact | Action |
|----------|-------|--------|--------|
| 🔴 HIGH | Multiple evaluation systems (3 modules) | Confusing ownership, duplicated logic | **Consolidate** into single evaluation pipeline |
| 🔴 HIGH | Multiple viva systems (2 modules) | Behavioral divergence, test confusion | **Identify** if viva_simulation.py is dead code |
| 🔴 HIGH | "Builder Detection" terminology | Pseudo-psychological claims | **Rename** to "Implementation Familiarity Analysis" |
| 🟠 MEDIUM | Models scattered (2 files) | Schema inconsistencies, import confusion | **Consolidate** into models.py |
| 🟠 MEDIUM | 52 exported symbols | API bloat, maintenance burden | **Reduce** to <30 core exports |
| 🟠 MEDIUM | No runtime documentation | New contributors lost, unmaintainable | **Create** execution flow + data flow docs |
| 🟡 LOW | viva_simulation.py usage unclear | Possible dead code | **Audit** usage patterns |

---

## Phase 2: Terminology Hardening

### Current Misleading Terms

```
"Builder Detection"              → "Implementation Familiarity Depth Analysis"
"Fake Developer Detection"       → "Surface Knowledge Identification"
"Truth Detection"                → "Reasoning Pattern Analysis"
"Deep Builder"                   → "High Implementation Familiarity"
"Memorizer"                      → "Low Implementation Familiarity"
"Guesser"                        → "Insufficient Evidence"
"Builder Confidence"             → "Familiarity Confidence Score"
"Reasoning Depth"                → "Reasoning Pattern Classification"
```

### Replacement Strategy

1. **reasoning_depth_analyzer.py**
   - Rename `ReasoningDepth` enum values (keep internal, expose neutral names)
   - Rename `builder_confidence` → `implementation_familiarity_score`
   - Rename `overall_reasoning_depth` → `reasoning_pattern_classification`
   - Update assessment language to avoid psychological claims

2. **viva_session_conductor.py**
   - Remove any "detection" language
   - Focus on "assessment patterns" not "detection"

3. **Trust Audit**
   - Expand "overconfidence detection"
   - Flag assessments claiming >90% certainty
   - Require evidence grounding for all claims

---

## Phase 3: End-to-End Workflow Documentation

### Execution Graph

```
┌─────────────────────────────────────────────────────────────────┐
│ ORACLE Implementation Familiarity Assessment Workflow            │
└─────────────────────────────────────────────────────────────────┘

Step 1: Repository Analysis
├─ Parse codebase structure
├─ Extract execution patterns
├─ Identify architecture decisions
├─ Map dependency chains
└─ Output: ExecutionGraph

Step 2: Engineering Review Corpus Loading
├─ Load relevant engineering reviews
├─ Match to repository patterns
├─ Extract implementation signals
└─ Output: CorpusContext

Step 3: Failure Pattern Mapping
├─ Identify potential failure modes
├─ Map to observable signals
├─ Create probing targets
└─ Output: FailureSignalMap

Step 4: Viva Session Planning
├─ Generate opening questions (grounded in reviews + failures)
├─ Prepare follow-up paths
├─ Design evaluation rubric
└─ Output: VivaSessionPlan

Step 5: Live Viva Execution
├─ Present opening question
├─ Evaluate response quality (specificity, correctness, consistency)
├─ Determine follow-up need
├─ Adapt questioning path
└─ Output: ResponseEvaluation

Step 6: Reasoning Pattern Analysis
├─ Analyze understanding indicators (rationale, tradeoffs, edge cases, etc.)
├─ Analyze memorization indicators (textbook language, generic answers, etc.)
├─ Classify reasoning pattern
├─ Compute confidence scores
└─ Output: ReasoningPatternAssessment

Step 7: Fairness & Bias Audit
├─ Check for overconfidence
├─ Verify evidence grounding
├─ Flag edge cases (nervous/confident speakers)
├─ Surface uncertainty
└─ Output: FairnessAuditReport

Step 8: Final Assessment & Explanation
├─ Synthesize all signals
├─ Generate explanation
├─ Surface contradictions
├─ Provide evidence traceability
└─ Output: FinalAssessment + Transcript
```

### Data Flow

```
Repository Code
    ↓
ExecutionGraph (AST analysis)
    ↓
Engineering Reviews
+ Failure Corpus
    ↓
Question Generation
    ↓
Viva Session
    ↓
Response Evaluation
(Quality Scoring)
    ↓
Indicator Analysis
(Understanding vs Memorization)
    ↓
Reasoning Pattern Classification
    ↓
Trust Audit
(Overconfidence check)
    ↓
Final Assessment
(with evidence trace + explanation)
```

---

## Phase 4: Real Human Testing Framework

### Test Categories

#### 4.1 Internal Validation (Week 1-2)

| Test | Participants | Goal | Metrics |
|------|-------------|------|---------|
| **Baseline** | 3 developers who built systems | Establish true-positive rate | Correctly identify high familiarity |
| **Adversarial** | 3 who only read code/docs | Establish true-negative rate | Correctly identify low familiarity |
| **Communication** | 1 weak speaker (built), 1 confident (memorized) | Test communication bias | Non-correlated with actual familiarity |
| **Edge Cases** | Nervous developers, non-native speakers, unconventional architects | Reduce false positives | <5% incorrect on edge cases |

#### 4.2 Pilot Human Study (Week 3-4)

**Participants:** 10-15 real people (mix of roles)
- Backend developers (2-3)
- System contributors (2-3)  
- Students/learners (3-4)
- Engineering leads (1-2)
- Cross-team members (2-3)

**Metrics Collected:**
- Familiarity accuracy (true positive, true negative, false positive, false negative)
- Question realism ratings (1-5 Likert)
- Follow-up quality (helpful? confusing? too hard? too easy?)
- Fairness perception (feeling evaluated fairly? biased by communication style?)
- Disagreement patterns (when does ORACLE assessment diverge from reviewer?)

**Outputs:**
- Confusion cases (where ORACLE misclassified)
- False-positive patterns (who was mislabeled?)
- False-negative patterns (who should have been identified but wasn't?)
- Bias patterns (communication style, accent, confidence, experience level)

---

## Phase 5: False Positive & Bias Reduction

### Known Risk Patterns

| Risk | Evidence | Mitigation |
|------|----------|-----------|
| **Weak Communicators** | Good technical knowledge but vague explanations | Reweight indicators: require >2 understanding indicators, not just 1 |
| **Confident Guessers** | Sound authoritative despite guessing | Flag buzzwords without specifics, probe follow-ups |
| **Non-Native Speakers** | Fluency ≠ familiarity | Separate "communication quality" from "technical depth" |
| **Nervous Candidates** | Knowledge is real but responses rambling | Penalize less for "WEAK" responses, more for "EVASIVE" |
| **Unconventional Architects** | Different approach but valid reasoning | Require evidence, not style matching |

### Fairness Audit Checklist

- [ ] Assessment doesn't over-reward confidence (trait bias)
- [ ] Assessment doesn't penalize communication style (demographic bias)
- [ ] Uncertainty is surfaced honestly (no false precision)
- [ ] Follow-ups probe actual knowledge, not communication ability
- [ ] Evidence grounding is verified (no "intuitive" conclusions)

---

## Phase 6: Viva UX & Interaction Improvements

### Current Issues

| Issue | Current Behavior | Desired Behavior |
|-------|------------------|------------------|
| **Pacing** | No pacing control | 10-15 min opening session, optional follow-ups |
| **Question Order** | Static order | Adaptive: sequence based on response quality |
| **Follow-up Timing** | Immediate | Grouped: collect 3-4 responses, then targeted follow-ups |
| **Feedback** | Silent scoring | Real-time indicators (question difficulty, relevance) |
| **Transcript** | Stored, not visible | Live transcript with evidence markers |

### Proposed UX Improvements

1. **Opening Phase (3-4 questions, ~10 min)**
   - Question difficulty: EASY → MEDIUM → HARD
   - Each grounded in actual engineering reviews
   - Candidate sees question, timer (optional)

2. **Evaluation Phase (LIVE)**
   - Response quality shown (specificity %, correctness %, consistency)
   - Evidence markers visible (code ref, timeline, tradeoff discussion)

3. **Follow-up Phase (2-3 follow-ups)**
   - Only if response quality < GOOD
   - Adaptive: probe actual gaps, not generic depth
   - Surface contradictions gently

4. **Transcript (Exportable)**
   - Q&A pairs with evaluations
   - Evidence markers hyperlinked
   - Final assessment with confidence/uncertainty

---

## Phase 7: Trustworthiness Reinforcement

### Trust Audit Expansion

Current trust audit detects:
- Unsupported conclusions
- Overconfident judgments
- Weak contradiction evidence

**New detections needed:**

1. **Overconfidence Threshold**
   - Flag any single indicator with >85% weight
   - Flag familiarity_confidence_score > 0.95 without 3+ indicators
   - Flag 0.0 scores as "insufficient evidence" not "confirmed false"

2. **Evidence Traceability**
   - Every conclusion must link to specific evidence
   - Show what was said + why it matters
   - Show what contradictions exist

3. **Uncertainty Surfacing**
   - "Insufficient evidence for determination" > guessing
   - Confidence scores must reflect actual signal strength
   - "MEDIUM" certainty for <2 indicators

---

## Implementation Roadmap

### Week 1: Architecture & Cleanup
- [x] Assess current state
- [ ] Identify dead code (viva_simulation.py)
- [ ] Consolidate duplicate evaluation systems
- [ ] Consolidate model classes
- [ ] Reduce exports to <30 core symbols
- [ ] Document architecture freeze

### Week 2: Terminology Hardening
- [ ] Rename reasoning_depth_analyzer.py concepts
- [ ] Update all assessment language
- [ ] Expand trust audit for overconfidence
- [ ] Audit all output strings for "detection" language

### Week 3: Documentation
- [ ] Create execution flow diagrams
- [ ] Create data flow documentation
- [ ] Create module dependency map
- [ ] Document actual runtime behavior

### Week 4: Real Testing Framework
- [ ] Build test harness for real humans
- [ ] Create fairness audit checklist
- [ ] Document false-positive patterns
- [ ] Plan pilot study

### Week 5-6: Hardening & Validation
- [ ] Run internal validation tests
- [ ] Fix identified false positives
- [ ] Pilot with real humans (10-15 people)
- [ ] Collect disagreement cases

### Week 7: UX Improvements
- [ ] Implement adaptive question sequencing
- [ ] Add real-time response quality feedback
- [ ] Create exportable transcripts
- [ ] Improve follow-up UX

### Week 8: Final Validation
- [ ] End-to-end workflow test
- [ ] Trust audit verification
- [ ] Performance benchmarks
- [ ] Documentation completeness

---

## Success Criteria

### Stability Metrics
- [ ] All modules have clear purpose and ownership
- [ ] <30 exported symbols (down from 52)
- [ ] Zero dead code
- [ ] <5% test flakiness
- [ ] All workflows end-to-end tested

### Reality Metrics
- [ ] <5% false positive rate on real humans
- [ ] <10% false negative rate on real humans
- [ ] Zero pseudo-psychological claims
- [ ] 100% evidence traceability
- [ ] Fairness audit pass: no communication-style bias

### Trustworthiness Metrics
- [ ] All conclusions flagged with confidence
- [ ] Overconfidence detection active (0 >0.95 scores)
- [ ] Uncertainty surfaced when evidence <2 indicators
- [ ] All contradictions logged and explained

### Documentation Metrics
- [ ] Execution flow documented
- [ ] Data flow documented
- [ ] Module dependency map created
- [ ] Fairness audit checklist published

---

## Non-Goals (Architecture Freeze)

❌ DO NOT add:
- New intelligence engines
- New reasoning layers
- New behavioral models
- Speculative AI features
- Additional abstraction layers

✅ DO maintain:
- AST-first architecture
- Execution graph foundation
- Explainability
- Deterministic behavior
- Calibration systems

---

## References

- [VIVA_INTELLIGENCE_EXPLORATION.md](VIVA_INTELLIGENCE_EXPLORATION.md) — Previous exploration
- [ORACLE_PHASE_2_SUMMARY.md](ORACLE_PHASE_2_SUMMARY.md) — Phase 2 outcomes
