# Contributing to ORACLE

Thank you for contributing. ORACLE is a precision tool — contributions must maintain evidence-grounding, determinism, and architectural clarity.

---

## Before You Start

Read these docs first:

1. [System Overview](../architecture/system-overview.md) — Understand what ORACLE does
2. [Agent Overview](../architecture/agent-overview.md) — Know which agent owns what
3. [Module Inventory](../architecture/module-inventory.md) — Check if your feature already exists

---

## Architecture Boundary Rules

### OracleAgent owns:
- AST parsing and execution graph construction
- Observable signals extraction
- Failure scenario analysis
- Viva question generation
- Response scoring and familiarity classification
- Fairness and trust auditing

### MainAgent owns:
- Viva session lifecycle and state
- Question sequencing and pacing
- Follow-up strategy (consuming ORACLE outputs — NOT recomputing them)
- Transcript persistence
- Topic coverage tracking

### Never:
- Add speculative AI reasoning to any agent
- Duplicate analysis from one agent into another
- Create new intelligence engines without architecture review
- Add new exports to `__init__.py` without discussion

---

## Code Standards

### Python

- Python 3.10+
- Type hints on all public functions and class attributes
- Pydantic models for all data structures passed between modules
- No bare `except:` clauses
- All public functions must have docstrings

### Module Design

- One module = one responsibility
- Prefer small, composable files over monolithic logic
- Every state transition must be auditable (loggable and replayable)
- Every conclusion must have a traceable evidence link

### Naming Conventions

Use evidence-grounded terminology — no pseudo-psychological framing:

| ❌ Don't Use | ✅ Use Instead |
|---|---|
| "Builder Detection" | "Implementation Familiarity Analysis" |
| "Deep Builder" | "High Implementation Familiarity" |
| "Memorizer" | "Low Implementation Familiarity" |
| "Builder Confidence" | "Implementation Familiarity Score" |
| "Fake Developer" | "Surface Knowledge Identification" |
| "Reasoning Depth" | "Reasoning Pattern Classification" |

---

## Submitting a Pull Request

1. **Branch from `main`**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Keep scope narrow** — one issue, one PR

3. **Run calibration before pushing**
   ```bash
   cd backend
   python evaluation/check_calibration_thresholds.py
   ```

4. **Write tests** for any new module or logic change

5. **Update Docs/** if your change affects architecture, APIs, or agent behaviour

6. **PR title format:** `[Agent] Brief description`  
   Examples: `[Oracle] Add token expiry signal detector`, `[Main] Session state serializer`

---

## PR Review Checklist

Before requesting review, confirm:

- [ ] The issue is narrow and non-overlapping with existing modules
- [ ] The code does not perform hidden reasoning or scoring
- [ ] The code uses ORACLE outputs — not recomputed intelligence
- [ ] The code is deterministic and replayable
- [ ] All new conclusions have evidence links
- [ ] Terminology uses the evidence-grounded naming convention
- [ ] Tests pass locally
- [ ] Calibration thresholds pass
- [ ] Docs are updated if behaviour changed

---

## Reviewer Expectations

Before merging any PR, reviewers confirm:

- The code does not look like a generic chat assistant
- The code does not infer hidden reasoning
- The change belongs in the right agent (Oracle vs Main vs Gatekeeper vs Sentinel)
- The change can be explained by a contributor in one paragraph
- No pseudo-psychological language remains

---

## Issue Reporting

When filing a bug or feature request:

1. **Title:** Brief, specific description
2. **Context:** What agent/module is affected?
3. **Expected behaviour:** What should happen?
4. **Actual behaviour:** What happens instead?
5. **Evidence:** Log output, test case, or code reference

---

## Related Docs

- [MAIN Agent Issue Breakdown](./main-agent-issues.md) — Pre-scoped contributor issues
- [Module Inventory](../architecture/module-inventory.md) — Ownership reference
- [Testing Framework](../testing/human-testing-protocol.md) — How to validate changes
