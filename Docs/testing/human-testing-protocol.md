# Human Testing Protocol

ORACLE's accuracy is validated through a structured 4-phase real human testing protocol. This document defines the full protocol.

---

## Why Human Testing Matters

Automated metrics alone cannot validate an implementation familiarity assessment system. We must verify:

1. Does ORACLE correctly identify people who built systems? (True Positive Rate)
2. Does ORACLE correctly identify people who only read code? (True Negative Rate)
3. Does ORACLE penalise nervous communicators unfairly? (False Positive Risk)
4. Does ORACLE reward confident speakers unfairly? (False Negative Risk)
5. Are there demographic patterns in misclassifications? (Bias Risk)

---

## Phase 1: Internal Validation (Weeks 1–2)

**Participants:** 6 total (controlled group)

### Test 1.1 — True Positive (High Familiarity)

| Attribute | Detail |
|---|---|
| Participants | 3 developers who built the actual systems |
| Requirement | 6+ months direct implementation experience |
| Expected Classification | HIGH_IMPLEMENTATION_FAMILIARITY or PRACTICED |
| Expected Confidence | HIGH |
| Pass Criteria | All 3 correct, ≥ MEDIUM confidence, < 1 false uncertainty |

### Test 1.2 — True Negative (Low Familiarity)

| Attribute | Detail |
|---|---|
| Participants | 3 who only read code/docs, no hands-on experience |
| Expected Classification | LOW_IMPLEMENTATION_FAMILIARITY or INSUFFICIENT |
| Expected Confidence | HIGH |
| Pass Criteria | All 3 correct, no false positives |

### Test 1.3 — Communication Style Bias

| Attribute | Detail |
|---|---|
| Participants | 1 builder (nervous communicator) + 1 non-builder (confident communicator) |
| Expected Outcome | Nervous builder classified HIGH; confident non-builder classified LOW |
| Pass Criteria | Assessment based on content, NOT delivery style |

### Test 1.4 — Edge Cases

| Attribute | Detail |
|---|---|
| Participants | 1 non-native English speaker (builder), 1 unconventional engineer, 1 nervous candidate |
| Expected Outcome | Fairness audit catches bias; manual review recommended |
| Pass Criteria | No wrong classifications; uncertainty surfaced; manual review recommended |

---

## Phase 2: Pilot Human Study (Weeks 3–4)

**Participants:** 10–15 real people across roles

| Role | Count |
|---|---|
| Backend developers who built the system | 2–3 |
| System contributors | 2–3 |
| Engineering leads | 1–2 |
| Students / learners | 3–4 |
| Cross-team members | 2–3 |

### Session Procedure (Per Participant)

1. **Pre-Session Survey (5 min)**
   - Role, experience, time on this system
   - Communication style self-assessment
   - Demographics (optional: first language, neurodivergence)

2. **Viva Session (15–20 min)**
   - 3–4 opening questions (grounded in code evidence)
   - Follow-ups based on response quality
   - All responses recorded

3. **Automated Assessment**
   - `VivaSessionConductor` scores responses
   - `ReasoningDepthAnalyzer` classifies familiarity
   - `FairnessAuditor` checks for bias
   - `TrustAuditPipeline` verifies evidence grounding

4. **Post-Session Survey (5 min)**
   - Assessment accuracy (1–5 scale)
   - Question difficulty rating (too easy / too hard / just right)
   - Fairness perception
   - Recommendation for hiring use

5. **Interviewer Notes**
   - Technical depth impression
   - Communication observations
   - Any contradictions or confusion noticed
   - Confidence in ORACLE assessment

### Data Collected Per Participant

```
├─ demographics (role, exp_years, first_language)
├─ responses (text, quality_score, correctness_score)
├─ assessment (classification, confidence, indicators)
├─ fairness_audit (issues found, recommendations)
├─ accuracy (participant self-report: 1–5 scale)
├─ feedback (too easy? fair? recommendations?)
└─ interviewer_notes (text observations)
```

---

## Phase 3: Error Analysis & Hardening (Week 5)

### Disagreement Analysis

Find cases where:
- ORACLE says HIGH but interviewer says LOW → **possible false positive**
- ORACLE says LOW but interviewer says HIGH → **possible false negative**
- ORACLE HIGH but participant self-reports LOW → **overconfidence?**
- ORACLE LOW but participant self-reports HIGH → **underconfidence?**

For each disagreement:
- What signals did ORACLE use?
- Was evidence sufficient?
- Did communication style affect the result?
- What should have happened?

### False Positive Analysis
- Which communication patterns triggered wrong HIGH classifications?
- Were FairnessAuditor issues correctly flagged?

### False Negative Analysis
- Which memorisation indicators were missed?
- Did confident delivery override evidence signals?

### Bias Pattern Analysis
- Non-native speakers: systematically over/under-represented in misclassifications?
- Early career: systematic underestimation?
- Communication style correlation with accuracy?

---

## Phase 4: System Improvements (Weeks 6–7)

Based on findings from Phases 2–3:

1. Adjust indicator weights if communication bias detected
2. Add new follow-up patterns if certain misclassifications repeat
3. Improve `FairnessAuditor` rules if biases slip through
4. Reduce confidence thresholds if overconfidence is systematic
5. Retrain on new failure cases if patterns are consistent

---

## Target Metrics

| Metric | Target |
|---|---|
| True Positive Rate | ≥ 90% |
| True Negative Rate | ≥ 90% |
| False Positive Rate | < 10% |
| False Negative Rate | < 10% |
| Communication Bias Correlation | < 5% |
| Demographic Bias | < 5% |
| Fairness Audit Effectiveness | ≥ 80% issues caught |
| Participant Accuracy Self-Report | ≥ 4/5 average |
| Evidence Grounding | 100% |

---

## Output Documents

| Document | Purpose |
|---|---|
| `TESTING_RESULTS_PHASE1.md` | Internal validation results |
| `TESTING_RESULTS_PHASE2.md` | Pilot study results + feedback |
| `DISAGREEMENT_ANALYSIS.md` | False positive/negative patterns |
| `BIAS_ANALYSIS.md` | Demographic bias findings |
| `IMPROVEMENTS_APPLIED.md` | Changes made based on testing |

---

## Related Docs

- [Calibration Framework](./calibration.md) — Automated metrics
- [Fairness Audit](../security/overview.md) — Bias detection system
- [Viva Intelligence](../viva-intelligence/viva-overview.md) — What is being tested
