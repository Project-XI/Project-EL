# Viva Intelligence Overview

The viva system is the heart of ORACLE. It conducts a structured technical interview grounded in actual code evidence — not generic textbook questions.

---

## Core Principle

> ORACLE does not ask "What is JWT?" — it asks "Your `/login` route returns a JWT. How does the system handle token expiry across your microservice calls?"

Every question is anchored to a real node in the execution graph, a real finding from the engineering review corpus, or a real failure scenario detected in the code.

---

## Components

| Component | Module | Purpose |
|---|---|---|
| **Session Conductor** | `viva_session_conductor.py` | Orchestrates questions, scores responses, manages turns |
| **Reasoning Depth Analyzer** | `reasoning_depth_analyzer.py` | Extracts indicators, classifies familiarity level |
| **Viva Generator** | `evidence_grounded_viva_generator.py` | Creates grounded questions from code + corpus |
| **Trust Auditor** | `trust_audit.py` | Verifies all conclusions are evidence-grounded |
| **Fairness Auditor** | `fairness_audit.py` | Prevents communication-style bias |

---

## Familiarity Classification Levels

| Level | Meaning | Indicators |
|---|---|---|
| `DEEP_IMPLEMENTATION_FAMILIARITY` | Candidate built or deeply owns the system | 4+ understanding indicators, 0 memorisation indicators |
| `PRACTICED` | Strong working familiarity, may miss edge cases | 2–3 understanding indicators |
| `INFORMED` | Understands concepts, limited hands-on depth | 1 understanding indicator |
| `LOW` | Primarily surface-level knowledge | 0 understanding + 2+ memorisation indicators |
| `INSUFFICIENT` | Too few signals to classify reliably | < 2 total indicators |

---

## Understanding vs Memorisation Indicators

### Understanding Indicators (positive signals)

| Indicator | What It Looks Like |
|---|---|
| `EXPLAINS_RATIONALE` | "We chose X because Y trade-off" |
| `MENTIONS_TRADEOFFS` | "The downside is that..." |
| `HANDLES_EDGE_CASE` | "What happens when the DB is down is..." |
| `IDENTIFIES_GAPS` | "We never actually solved X cleanly" |
| `ADMITS_UNCERTAINTY` | "I'm not sure of the exact number but..." |
| `INTEGRATES_CONTEXT` | Connects answer to broader system behaviour |
| `CITES_SPECIFIC_IMPLEMENTATION` | References actual file, function, or line |

### Memorisation Indicators (negative signals)

| Indicator | What It Looks Like |
|---|---|
| `TEXTBOOK_LANGUAGE` | "JWT is a stateless authentication mechanism" |
| `GENERIC_ANSWER` | "You'd just use caching for that" |
| `FAILS_FOLLOW_UP` | Cannot explain the same concept differently |
| `CONTRADICTS_SELF` | Earlier answer conflicts with later answer |
| `PARROTS_QUESTION` | Restates the question as the answer |
| `USES_BUZZWORDS` | "We used microservices for scalability" (no specifics) |
| `BLANK_ON_EDGE_CASE` | No answer when asked about a failure or edge condition |

---

## Question Categories

| Category | What It Tests |
|---|---|
| `Architecture` | Design decisions, component relationships, why choices were made |
| `Tradeoff` | Trade-offs made, alternatives considered |
| `Security` | Auth, access control, input validation decisions |
| `Scalability` | Load handling, bottlenecks, performance decisions |
| `Failure-Path` | How the system behaves when components fail |
| `Runtime` | Production behaviour, observability, incident knowledge |

---

## Difficulty Levels

| Level | Typical Question Style |
|---|---|
| `foundational` | "What does this endpoint do?" |
| `medium` | "Why did you structure the auth this way?" |
| `hard` | "Walk me through what happens if Redis goes down during a checkout" |

Questions progress: `foundational` → `medium` → `hard`

---

## Example: Good vs Poor Response

**Question:** "The `/users` endpoint loads 100+ related resources per user. What's the performance concern?"

**High Familiarity Response:**
> "N+1 query. When we first built this, we didn't batch load relationships — each user load hit the DB separately. In production with 50 users it was hitting 2 seconds. We fixed it with SQLAlchemy `joinedload` with pagination — load max 10 per batch. Tradeoff is more complex query logic but sub-100ms now."

**Low Familiarity Response:**
> "Probably an N+1 issue? That's a common database problem. You'd use eager loading. It's a best practice."

| Metric | High | Low |
|---|---|---|
| Specificity | 96% | 18% |
| Correctness | 94% | 55% |
| Quality | EXCELLENT | WEAK |
| Understanding indicators | 4 | 0 |
| Memorisation indicators | 0 | 3 |
| Final classification | DEEP_IMPLEMENTATION_FAMILIARITY | LOW |

---

## Related Docs

- [Session Flow](./session-flow.md) — Turn-by-turn session walkthrough
- [Scoring System](./scoring-system.md) — How responses are scored
- [Follow-Up Strategy](./follow-up-strategy.md) — How follow-ups are triggered
- [Fairness Audit](../security/overview.md) — How bias is prevented
