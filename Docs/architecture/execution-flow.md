# Execution Flow

This document traces the complete step-by-step pipeline from repository URL input to final assessment output.

---

## Overview

```
Input: Repository URL + Engineering Concern
                   ↓
         [8 Pipeline Steps]
                   ↓
Output: Assessment Report + Transcript + Evidence Trace
```

---

## Step 1: Repository Analysis

```
Input: GitHub Repository URL
    ↓
Git Clone (shallow, --depth 1)
    ↓
AST Parsing (Python AST / language-specific parser)
    ├─ Extract route definitions
    ├─ Extract middleware chains
    ├─ Extract DB query patterns
    ├─ Extract auth handlers
    └─ Extract state store interactions
    ↓
Output: ExecutionGraph (nodes, edges, types, metadata)
```

**Node Types:** `ROUTE`, `MIDDLEWARE`, `DB_QUERY`, `STATE_STORE`, `AUTH_HANDLER`

Each node carries: `file_path`, `line_number`, `snippet`

---

## Step 2: Engineering Review Corpus Loading

```
Input: Engineering Concern (e.g. "auth", "caching", "error handling")
    ↓
Load relevant engineering reviews from corpus
    ├─ Match concern to review topics
    └─ Extract implementation signals from reviews
    ↓
Output: CorpusContext (grounding evidence for questions)
```

---

## Step 3: Failure Pattern Mapping

```
Input: ExecutionGraph
    ↓
FailureCorpusRepository.get_patterns()
    ├─ Identify potential failure modes for this code
    ├─ Map to observable signals (what to look for)
    └─ Create probing targets (which failure paths to question)
    ↓
Output: FailureSignalMap
```

---

## Step 4: Viva Session Planning

```
Input: CorpusContext + FailureSignalMap + ExecutionGraph
    ↓
EvidenceGroundedVivaGenerator
    ├─ Create 3–4 opening questions
    │   └─ Each grounded in specific engineering reviews or code locations
    ├─ Prepare follow-up question paths
    └─ Design response evaluation rubric
    ↓
Output: VivaSessionPlan (VivaTarget list with metadata)
```

Each VivaTarget includes: `topic`, `difficulty`, `category`, `focus`, `depth_score`, `confidence`, `related_node`, `reasoning_summary`

---

## Step 5: Live Viva Execution (Interactive Loop)

```
For each question in VivaSessionPlan:
    ├─ Present question to candidate
    ├─ Accept candidate response (text)
    ├─ VivaSessionConductor.score_response()
    │   ├─ Specificity score (0–100%)
    │   ├─ Correctness score (0–100%)
    │   └─ Quality enum:
    │       EXCELLENT | GOOD | ADEQUATE | WEAK | EVASIVE | CONTRADICTION
    ├─ Determine if follow-up is needed
    │   └─ If ADEQUATE or WEAK → generate targeted follow-up question
    └─ Repeat until 3–4 high-quality responses collected
    ↓
Output: ScoredResponseList
```

---

## Step 6: Reasoning Pattern Analysis

```
Input: ScoredResponseList
    ↓
ReasoningDepthAnalyzer.extract_indicators()
    ├─ Understanding Indicators (7 types):
    │   ├─ EXPLAINS_RATIONALE
    │   ├─ MENTIONS_TRADEOFFS
    │   ├─ HANDLES_EDGE_CASE
    │   ├─ IDENTIFIES_GAPS
    │   ├─ ADMITS_UNCERTAINTY
    │   ├─ INTEGRATES_CONTEXT
    │   └─ CITES_SPECIFIC_IMPLEMENTATION
    └─ Memorisation Indicators (7 types):
        ├─ TEXTBOOK_LANGUAGE
        ├─ GENERIC_ANSWER
        ├─ FAILS_FOLLOW_UP
        ├─ CONTRADICTS_SELF
        ├─ PARROTS_QUESTION
        ├─ USES_BUZZWORDS
        └─ BLANK_ON_EDGE_CASE
    ↓
ReasoningDepthAnalyzer.classify()
    ├─ Reasoning Pattern: DEEP | PRACTICED | INFORMED | LOW | INSUFFICIENT
    ├─ Implementation Familiarity Score (0–1)
    └─ Confidence Level:
        ├─ < 2 indicators → LOW / MEDIUM confidence
        ├─ 2–4 indicators → HIGH confidence
        └─ > 4 indicators → VERY HIGH confidence
    ↓
Output: ReasoningPatternAssessment
```

---

## Step 7: Fairness & Trust Audit

```
Input: ReasoningPatternAssessment + ScoredResponseList
    ↓
FairnessAuditor.audit()
    ├─ Communication style bias (8 patterns)
    ├─ Demographic bias (8 contexts)
    ├─ Nervous developer pattern detection
    ├─ Confident guesser pattern detection
    └─ Non-native speaker separation
    ↓
TrustAuditPipeline.verify()
    ├─ Overconfidence check: Score > 0.95 without 3+ indicators → FLAG
    ├─ Evidence grounding: Every conclusion must link to evidence
    ├─ Contradiction logging
    └─ Uncertainty surfacing: Confidence < 0.7 → MEDIUM/LOW flag
    ↓
Output: FairnessAuditReport + TrustAuditResult
```

---

## Step 8: Final Assessment Generation

```
Input: ReasoningPatternAssessment + FairnessAuditReport + TrustAuditResult
    ↓
Synthesise all signals
    ├─ Classification: DEEP_IMPLEMENTATION_FAMILIARITY | PRACTICED | INFORMED | INSUFFICIENT
    ├─ Confidence: HIGH | MEDIUM | LOW (reflects actual signal strength)
    ├─ Evidence trace: Q1→[indicators]→score, Q2→[indicators]→score, ...
    ├─ Uncertainty: "Based on X indicators, confidence Y%"
    └─ Transcript: Full Q&A with evaluation markers
    ↓
Output: FinalAssessment + Transcript + Explainability
```

---

## Happy Path Summary

| Step | Input | Output |
|---|---|---|
| 1 | Repo URL | ExecutionGraph |
| 2 | Concern | CorpusContext |
| 3 | ExecutionGraph | FailureSignalMap |
| 4 | Corpus + Failures | VivaSessionPlan |
| 5 | Questions + Responses | ScoredResponseList |
| 6 | Scored Responses | ReasoningPatternAssessment |
| 7 | Assessment | Fairness + Trust Audit |
| 8 | All signals | FinalAssessment |

---

## Related Docs

- [Data Flow](./data-flow.md) — How data structures move between modules
- [Module Inventory](./module-inventory.md) — Which file owns each step
- [Viva Session Flow](../viva-intelligence/session-flow.md) — Step 5 in detail
