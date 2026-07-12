# Bias Mitigation

ORACLE is built to prevent systematic bias in implementation familiarity assessments. This document explains the bias risks, detection mechanisms, and mitigation strategies.

---

## What Bias Looks Like in ORACLE

Without bias mitigation, an assessment system can:

- Mark a **nervous but knowledgeable** engineer as LOW familiarity (False Positive)
- Mark a **confident but shallow** speaker as HIGH familiarity (False Negative)
- Systematically underestimate **non-native English speakers** who have deep technical knowledge
- Favour **conventional coding styles** over equally valid unconventional approaches

These are not hypothetical risks — they are documented patterns in interview assessment research.

---

## Mitigation Layer: FairnessAuditor

**Module:** `fairness_audit.py`  
**Integrated into:** OracleAgent pipeline (after TrustAudit, before FinalAssessment)

The FairnessAuditor runs 6 detection patterns on every session.

### Pattern 1: Nervous Developer False Positive

| Aspect | Detail |
|---|---|
| **Risk** | Builder marked LOW due to hedging communication, not lack of knowledge |
| **Detection** | Nervous language + high understanding indicators + low memorisation indicators |
| **Action** | Manual review recommended; score not automatically penalised |
| **Output** | `FairnessAuditIssue(type="NERVOUS_DEVELOPER", severity="MEDIUM")` |

---

### Pattern 2: Confident Guesser False Negative

| Aspect | Detail |
|---|---|
| **Risk** | Non-builder marked HIGH due to confident delivery and buzzword fluency |
| **Detection** | High surface confidence + TEXTBOOK_LANGUAGE + USES_BUZZWORDS + zero understanding indicators |
| **Action** | Familiarity confidence score reduced; false negative risk flagged |
| **Output** | `FairnessAuditIssue(type="CONFIDENT_GUESSER", severity="HIGH")` |

---

### Pattern 3: Overconfidence Correction

| Aspect | Detail |
|---|---|
| **Risk** | System claims >95% confidence with insufficient evidence |
| **Detection** | `implementation_familiarity_score > 0.95` with fewer than 4 indicators |
| **Action** | Score reduced to ≤ 0.85; flagged as CRITICAL |
| **Output** | `TrustAuditResult(overconfident=True, adjusted_score=0.85)` |

---

### Pattern 4: Insufficient Evidence Correction

| Aspect | Detail |
|---|---|
| **Risk** | HIGH/MEDIUM confidence on thin evidence (< 2 indicators) |
| **Detection** | Confidence MEDIUM or HIGH with < 2 total indicators |
| **Action** | Confidence reduced to LOW; marked INSUFFICIENT_DATA |
| **Output** | `TrustAuditResult(insufficient_evidence=True, adjusted_confidence="LOW")` |

---

### Pattern 5: Demographic Bias

| Aspect | Detail |
|---|---|
| **Risk** | Non-native speaker, neurodivergent, or early-career communicators systematically underscored |
| **Detection** | Response contains demographic communication markers; score correlates with communication style |
| **Action** | Manual review recommended; fluency explicitly separated from technical depth in report |
| **Output** | `FairnessAuditIssue(type="DEMOGRAPHIC_BIAS", context="non_native_speaker")` |

---

### Pattern 6: Communication Style Correlation

| Aspect | Detail |
|---|---|
| **Risk** | Statistically significant correlation between communication traits and familiarity score |
| **Detection** | Communication style features correlate with final score above threshold |
| **Action** | Bias surfaced explicitly in report; score adjusted if correlation exceeds threshold |
| **Output** | `FairnessAuditIssue(type="COMMUNICATION_BIAS", severity="HIGH")` |

---

## Separation of Fluency from Familiarity

ORACLE is explicitly designed to score **content**, not **delivery**:

| What We Score | What We Do NOT Score |
|---|---|
| Specific implementation references | Eloquence or vocabulary |
| Mention of actual tradeoffs | Accent or phrasing |
| Knowledge of production incidents | Speed of response |
| Correct edge case identification | Confidence level of delivery |
| Ability to cite specific files or decisions | Grammar correctness |

---

## Fairness Audit Report Schema

```json
{
  "issues": [
    {
      "type": "NERVOUS_DEVELOPER",
      "severity": "MEDIUM",
      "description": "Candidate shows understanding indicators despite nervous delivery",
      "recommendation": "Manual review recommended — do not penalise for communication style"
    }
  ],
  "manual_review_recommended": true,
  "confidence_adjusted": false,
  "bias_types_detected": ["COMMUNICATION_STYLE"]
}
```

---

## Validation Results (Phase 1 Testing)

| Test Case | Expected | Actual | Pass? |
|---|---|---|---|
| Nervous builder → HIGH familiarity | Detects nervous pattern, manual review | ✅ Correct | ✅ |
| Confident guesser → LOW familiarity | Detects false negative risk | ✅ Correct | ✅ |
| Non-native speaker builder | Flags demographic bias, separates fluency | ✅ Correct | ✅ |

---

## Fairness Audit Checklist

Run before every production release:

- [ ] FairnessAuditor runs on 100% of sessions
- [ ] Overconfidence threshold (>0.95) not disabled
- [ ] Nervous developer pattern detection active
- [ ] Confident guesser pattern detection active
- [ ] Demographic bias flags generating correctly
- [ ] Manual review recommendations surfaced in report
- [ ] Communication style does not correlate with score in test set

---

## Related Docs

- [Security Overview](../security/overview.md) — Trust audit + access control
- [Human Testing Protocol](../testing/human-testing-protocol.md) — How bias is measured empirically
- [Viva Intelligence](../viva-intelligence/viva-overview.md) — How indicators are designed to separate understanding from style
