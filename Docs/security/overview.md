# Security & Fairness Architecture

ORACLE is designed with security and fairness as first-class architectural concerns. This document covers the fairness audit framework, trust audit pipeline, overconfidence detection, and access control.

---

## Fairness Audit Framework

**Module:** `backend/src/agents/oracle/` → `fairness_audit.py` (350+ LOC)

### Purpose

Ensure that ORACLE's implementation familiarity assessments are not influenced by:
- Communication style (nervousness, confidence, verbosity)
- Demographics (non-native English speakers, early career, neurodivergence)
- Delivery style (accent, phrasing, hedging language)

### Key Classes

| Class | Purpose |
|---|---|
| `FairnessAuditor` | Main auditing engine — runs all checks |
| `FairnessAuditReport` | Comprehensive audit output with all issues found |
| `FairnessAuditIssue` | Individual bias or false-positive issue record |

---

## False Positive / Negative Detection Patterns

ORACLE detects 6 systematic risk patterns that can corrupt assessments:

### Pattern 1: Nervous Developer
> Builder with genuine knowledge but hesitant, hedging communication style.

| Field | Value |
|---|---|
| Detection | Nervous hedging language + low memorisation indicators + high understanding indicators |
| Risk | False negative — marked LOW familiarity despite actual knowledge |
| Action | Manual review recommended; **not penalised** |

---

### Pattern 2: Confident Guesser
> Non-builder with authoritative delivery and textbook buzzwords.

| Field | Value |
|---|---|
| Detection | High surface confidence + zero understanding indicators + TEXTBOOK_LANGUAGE |
| Risk | False positive — marked HIGH familiarity without genuine knowledge |
| Action | Confidence score reduced; false negative risk flagged |

---

### Pattern 3: Overconfidence
> System assigns >95% confidence without sufficient evidence.

| Field | Value |
|---|---|
| Detection | `implementation_familiarity_score > 0.95` with fewer than 4 indicators |
| Risk | Misleading assessment presented as near-certain |
| Action | Score reduced to ≤ 0.85; flagged as CRITICAL |

---

### Pattern 4: Insufficient Evidence
> System assigns MEDIUM/HIGH confidence with too few data points.

| Field | Value |
|---|---|
| Detection | Confidence HIGH/MEDIUM with fewer than 2 indicators |
| Risk | Overconfident classification on thin evidence |
| Action | Confidence reduced to LOW; marked INSUFFICIENT_DATA |

---

### Pattern 5: Demographic Bias
> Non-native speaker, early career, or neurodivergent communication style affecting scores.

| Field | Value |
|---|---|
| Detection | Response contains non-native phrasing, early-career uncertainty markers, or non-standard explanation style |
| Risk | Fluency correlated with familiarity score |
| Action | Manual review recommended; fluency explicitly separated from technical depth |

---

### Pattern 6: Communication Style Bias
> General correlation between communication traits and familiarity score.

| Field | Value |
|---|---|
| Detection | Statistically significant correlation between communication style features and final score |
| Risk | Systematic unfairness to certain communication styles |
| Action | Bias surfaced explicitly; score adjusted if correlation detected |

---

## Trust Audit Pipeline

**Module:** `trust_audit.py`  
**Called by:** `comparative_calibration_runner.py`

### Checks Performed

| Check | Trigger | Action |
|---|---|---|
| Overconfidence | Score > 0.95 without 3+ indicators | Flag and reduce confidence |
| Single indicator dominance | Any single indicator >85% weight | Flag for review |
| Evidence grounding | Conclusion without evidence link | Reject and surface gap |
| Contradiction logging | Two responses contradict each other | Log contradiction event |
| Uncertainty surfacing | Confidence < 0.7 | Surface as MEDIUM/LOW |
| Zero-score interpretation | Score = 0.0 | Treat as INSUFFICIENT, not CONFIRMED FALSE |

---

## Access Control & API Security

### GitHub Token

ORACLE requires a `GITHUB_TOKEN` to clone repositories. Rules:
- Store **only** in `.env` (never commit)
- Minimum required scope: `repo:read`
- Rotate tokens if accidentally exposed

### WebSocket Security

- WebSocket endpoint is unauthenticated by default for local development
- In production, implement session token validation middleware on `/ws/analyze`
- Never log full `repo_url` with embedded tokens

### Environment Variables

```env
GITHUB_TOKEN=ghp_...      # Never expose
OPENAI_API_KEY=sk-...     # Never expose
DISCORD_WEBHOOK_URL=...   # Never expose
```

All sensitive config MUST use GitHub Secrets for CI/CD. See [Discord Bot Setup](../ci-cd/discord-notifications.md).

---

## Fairness Audit Checklist (Pre-Release)

- [ ] Assessment does not over-reward confident delivery (trait bias)
- [ ] Assessment does not penalise nervous or hedging communication
- [ ] Uncertainty is surfaced honestly — no false precision
- [ ] Follow-ups probe actual knowledge, not communication ability
- [ ] All conclusions have a traceable evidence link
- [ ] Demographic patterns do not systematically bias scores
- [ ] Overconfidence threshold (>0.95) has not been disabled
- [ ] FairnessAuditReport is generated for every session

---

## Validation Results (Phase 1)

| Test Case | Input | System Output | Pass? |
|---|---|---|---|
| Nervous Builder (HIGH familiarity) | Hesitant delivery | Detects bias, recommends review | ✅ YES |
| Confident Guesser (LOW familiarity) | Confident buzzwords | Detects false negative risk | ✅ YES |
| Non-native Speaker (HIGH familiarity) | Technical depth, non-native phrasing | Flags demographic bias risk | ✅ YES |

---

## Related Docs

- [Trust Audit Deep Dive](./trust-audit.md)
- [Fairness Audit Module](./fairness-audit.md)
- [Testing Framework](../testing/human-testing-protocol.md)
- [Error Handling & Bias Mitigation](../error-handling/bias-mitigation.md)
