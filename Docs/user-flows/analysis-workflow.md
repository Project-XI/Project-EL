# Analysis Workflow (User Flow)

This document walks through the complete ORACLE analysis workflow from a user's perspective.

---

## Step 1: Open the ORACLE UI

Open `frontend/index.html` in your browser.

The interface shows:
- An input field for the repository URL
- An animated orb (processing indicator)
- A terminal log panel
- An empty dashboard (ready to populate)

---

## Step 2: Enter a Repository URL

Enter the full GitHub URL of the repository to analyse:

```
https://github.com/your-org/your-repo
```

Click **Analyze** (or press Enter).

---

## Step 3: Watch the Analysis Stream

The terminal panel shows real-time progress:

```
[Gatekeeper] Identity context established
[Oracle] Cloning repository...
[Oracle] AST parsing complete — 142 nodes found
[Oracle] Building execution graph...
[Oracle] Extracting observable signals...
[Oracle] 3 signals detected (HIGH: 1, MEDIUM: 2)
[Oracle] Tracing failure paths...
[Oracle] 2 failure paths identified
[Oracle] Generating viva questions...
[Oracle] 6 evidence-grounded questions created
[Sentinel] Audit complete
✅ Analysis complete
```

This takes approximately **20–40 seconds** depending on repository size.

---

## Step 4: Review the Dashboard

When analysis is complete, four panel sections populate:

### Framework Detection Cards
Shows detected: Backend Framework · Architecture Pattern · Auth System

Each card shows a `value` and `confidence` score.

### Execution Graph
An interactive node graph showing how the codebase is connected:
- Routes → Middleware → DB Queries
- Auth handlers
- State stores

Click any node to see: `file_path`, `line_number`, `code snippet`

### Viva Intelligence Questions
A list of evidence-grounded interview questions. Each card shows:
- Category badge (Architecture / Security / Runtime / etc.)
- Difficulty tag (hard / medium / foundational)
- The question text
- Depth score and confidence
- Which execution graph node it targets
- Reasoning summary (why this question was generated)

### Anomalies & Failure Paths
Shows:
- Runtime risks (severity: HIGH / MEDIUM / LOW)
- Failure propagation paths (what breaks when a component fails)

---

## Step 5: Conduct the Viva

Take the generated questions from the Viva Intelligence panel and use them in a real interview session with the candidate.

For each question:
1. Present the question to the candidate
2. Record their response
3. Submit the response to ORACLE for scoring (if using the interactive mode)
4. ORACLE evaluates: specificity, correctness, quality (EXCELLENT / GOOD / ADEQUATE / WEAK / EVASIVE)
5. If quality is ADEQUATE or WEAK → ORACLE generates a follow-up question
6. Continue for 3–4 exchanges

---

## Step 6: Review the Assessment

After the viva, ORACLE generates a final assessment:

```
Classification: DEEP_IMPLEMENTATION_FAMILIARITY
Confidence: HIGH (based on 4 understanding indicators)
Evidence Trace:
  Q1 → [EXPLAINS_RATIONALE, MENTIONS_TRADEOFFS] → score: 0.89
  Q2 → [CITES_SPECIFIC_IMPLEMENTATION] → score: 0.92
  Q3 → [HANDLES_EDGE_CASE, INTEGRATES_CONTEXT] → score: 0.94
Fairness Audit: No issues detected
Trust Audit: Evidence grounding verified, no overconfidence
```

---

## Step 7: Export / Record

Export the transcript as JSON from the transcript persistence layer for:
- Candidate records
- HR documentation
- Bias audit review
- Team disagreement analysis

---

## Related Docs

- [Viva Intelligence Overview](../viva-intelligence/viva-overview.md)
- [Session Flow](../viva-intelligence/session-flow.md)
- [WebSocket API](../api-docs/websocket-api.md)
- [Frontend UI Overview](../frontend/ui-overview.md)
