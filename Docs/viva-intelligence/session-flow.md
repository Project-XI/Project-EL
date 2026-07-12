# Viva Session Flow

This document describes a complete turn-by-turn viva session from the candidate's perspective and the system's internal state.

---

## Session Lifecycle

```
INITIALISED → QUESTION_PRESENTED → RESPONSE_RECEIVED → SCORED
          ↓ (if weak)                                    ↓
      FOLLOW_UP_GENERATED ← ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
                                                         ↓
                                              (after 3–4 turns)
                                                         ↓
                                             ANALYSIS_COMPLETE
                                                         ↓
                                               TRUST_AUDITED
                                                         ↓
                                              FAIRNESS_CHECKED
                                                         ↓
                                             SESSION_CLOSED
```

---

## Turn 1: Opening Question

**System:**
1. Selects the highest-priority VivaTarget from the session plan
2. Presents the question to the candidate
3. Logs: `[Viva] Turn 1 started — category: Architecture — difficulty: hard`

**Example Question:**
> "Your `/checkout` endpoint coordinates with the payment service, inventory check, and order DB write. Walk me through what happens if the payment service times out at step 2."

**Candidate responds.**

**System scores the response:**

| Metric | Score |
|---|---|
| Specificity | 78% |
| Correctness | 85% |
| Quality | GOOD |
| Understanding indicators | EXPLAINS_RATIONALE, HANDLES_EDGE_CASE |
| Memorisation indicators | none |

Quality = GOOD → No follow-up needed. Move to Turn 2.

---

## Turn 2: Second Question

**System:**
1. Checks topic coverage — Architecture covered
2. Selects next VivaTarget from different category (e.g. Security)
3. Presents question

**Example Question:**
> "Your auth middleware is applied globally. How does the system handle routes that need different permission levels — like admin vs. read-only?"

**Candidate responds with a generic answer.**

**System scores:**

| Metric | Score |
|---|---|
| Specificity | 22% |
| Correctness | 45% |
| Quality | WEAK |
| Understanding indicators | none |
| Memorisation indicators | TEXTBOOK_LANGUAGE, GENERIC_ANSWER |

Quality = WEAK → **Follow-up triggered.**

---

## Turn 2 Follow-Up

**FollowUpStrategyEngine:**
1. Detects: WEAK response on Security topic
2. Selects: `implementation_probe` pattern
3. Generates follow-up grounded in execution graph node `auth_middleware_001`

**Follow-Up:**
> "Looking at your middleware code specifically — how does `require_admin` differ from `require_authenticated` in what it checks against the JWT payload?"

**Candidate gives specific answer referencing actual role claims.**

Quality → ADEQUATE → Follow-up depth satisfied.

---

## Turn 3: Edge Case Probe

**System selects:** Failure-Path category question

**Example:**
> "If Redis goes down and your session cache becomes unavailable, what does the `/dashboard` route return to the user?"

**Strong response:** References actual error handling code and fallback path.

Quality → EXCELLENT

---

## Turn 4: Contradiction Check (if triggered)

If the candidate's Turn 3 answer contradicts Turn 1:
1. System logs `ContradictionEvent`
2. Follow-up generated: "Earlier you said X. Just now you described Y. Can you clarify?"
3. Contradiction probe resolves or deepens the contradiction log

---

## Session Termination

The session ends when:
- 3–4 high-quality responses are collected, **OR**
- The maximum turn count is reached (default: 8), **OR**
- Topic coverage across all 6 categories is complete

---

## Post-Session Processing

After session close:
1. `ReasoningDepthAnalyzer` classifies all collected indicators
2. `TrustAuditPipeline` verifies evidence grounding
3. `FairnessAuditor` checks for bias patterns
4. `FinalAssessment` is generated with evidence trace
5. Transcript is serialised and persisted

---

## Session State Object

```json
{
  "session_id": "sess_abc123",
  "stage": "CLOSED",
  "turns": [
    {
      "turn": 1,
      "question": "...",
      "response": "...",
      "quality": "GOOD",
      "indicators": ["EXPLAINS_RATIONALE", "HANDLES_EDGE_CASE"],
      "follow_up_triggered": false
    }
  ],
  "topics_covered": ["Architecture", "Security", "Failure-Path"],
  "contradiction_log": [],
  "fairness_flags": []
}
```

---

## Related Docs

- [Viva Intelligence Overview](./viva-overview.md)
- [Scoring System](./scoring-system.md)
- [Follow-Up Strategy](./follow-up-strategy.md)
- [Analysis Workflow](../user-flows/analysis-workflow.md)
