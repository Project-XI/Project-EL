# ORACLE Real Human Testing Framework

## Testing Protocol

### Phase 1: Internal Validation (Week 1-2)

#### 1.1 True Positive Test: High Implementation Familiarity

**Participants:** 3 developers who built the actual systems

**Requirement:** Participants have:
- Direct implementation experience (6+ months on the system)
- Can explain design decisions
- Know about production incidents
- Can discuss tradeoffs and limitations

**Test Procedure:**
1. Conduct full viva session (3-4 questions, 10-15 min)
2. Questions drawn from engineering review corpus
3. Collect responses
4. Run implementation familiarity analysis
5. Record assessment

**Expected Outcome:**
- Classification: HIGH_IMPLEMENTATION_FAMILIARITY or better
- Confidence: HIGH
- Indicators: 3+ understanding indicators

**Pass Criteria:**
- ✅ All 3 participants classified as HIGH/PRACTICED
- ✅ Confidence >= MEDIUM
- ✅ <1 false uncertainty issue

---

#### 1.2 True Negative Test: Low Implementation Familiarity

**Participants:** 3 who only read code/documentation (no hands-on experience)

**Requirement:** Participants have:
- Studied code but never built/deployed
- Can recite concepts
- Know theory but not practice
- Cannot discuss production incidents

**Test Procedure:**
1. Conduct full viva session (same questions as 1.1)
2. Collect responses
3. Run implementation familiarity analysis
4. Record assessment

**Expected Outcome:**
- Classification: LOW_IMPLEMENTATION_FAMILIARITY or INSUFFICIENT
- Confidence: HIGH
- Indicators: 2+ memorization indicators, 0 understanding indicators

**Pass Criteria:**
- ✅ All 3 participants classified as LOW/INSUFFICIENT
- ✅ Confidence >= MEDIUM
- ✅ No false positives marking them as HIGH

---

#### 1.3 Communication Style Bias Test

**Participants:**
- 1 builder who communicates poorly (nervous, hedging, unsure tone)
- 1 non-builder who communicates confidently (confident tone, buzzwords)

**Test Procedure:**
1. Run same viva session as 1.1/1.2
2. Compare communication style markers vs familiarity assessment
3. Verify FairnessAuditor detects patterns

**Expected Outcome:**
- Builder classified HIGH despite nervous communication
- Non-builder classified LOW despite confident communication
- FairnessAuditReport flags communication style bias

**Pass Criteria:**
- ✅ Nervous builder not penalized for communication
- ✅ Confident guesser not rewarded for delivery
- ✅ Assessment based on content, not style

---

#### 1.4 Edge Cases

**Participants:**
- 1 weak non-native English speaker who is a builder
- 1 unconventional (non-OOP, non-standard) but valid engineer
- 1 nervous but knowledgeable candidate

**Test Procedure:**
1. Run viva sessions
2. Collect assessments
3. Flag any problematic conclusions

**Expected Outcome:**
- Fairness audit catches potential bias
- Manual review recommended for edge cases
- Confidence marked as MEDIUM (not HIGH)

**Pass Criteria:**
- ✅ No wrong classifications
- ✅ Uncertainty surfaced honestly
- ✅ Manual review recommended

---

### Phase 2: Pilot Human Study (Week 3-4)

#### 2.1 Participant Recruitment

**Total:** 10-15 real people

**Mix:**
- Backend developers who built systems (2-3)
- System contributors (2-3)
- Engineering leads (1-2)
- Students/learners (3-4)
- Cross-team members (2-3)

**Inclusion Criteria:**
- Willing to participate in 20-30 min viva session
- OK with recording/analyzing responses
- Willing to provide feedback on assessment accuracy

---

#### 2.2 Session Procedure

For each participant:

1. **Pre-Session Survey** (5 min)
   - Background: role, experience, how long on this system?
   - Communication style: comfortable in technical interviews? Nervous? Confident?
   - Demographics: first language? Neurodivergent?

2. **Viva Session** (15-20 min)
   - 3-4 opening questions
   - Optional follow-ups based on response quality
   - Record all responses

3. **Assessment** (automated)
   - VivaSessionConductor scores responses
   - ReasoningDepthAnalyzer classifies familiarity
   - FairnessAuditor checks for bias
   - TrustAudit verifies evidence grounding

4. **Post-Session Survey** (5 min)
   - How accurate was the assessment? (1-5 scale)
   - Which questions were: too easy / too hard / just right?
   - Did you feel evaluated fairly? Any biases?
   - Would you recommend this for hiring/evaluation?

5. **Interviewer Notes** (written)
   - Technical depth impression
   - Communication observations
   - Any contradictions/confusion?
   - Confidence in assessment

---

#### 2.3 Data Collection

**Metrics Collected:**

```
For each participant:
├─ demographics (role, exp_years, first_language, etc.)
├─ responses (text, quality_score, correctness_score, etc.)
├─ assessment (classification, confidence, indicators)
├─ fairness_audit (issues found, recommendations)
├─ accuracy (participant self-report: 1-5 scale)
├─ feedback (too easy? fair? recommendations?)
└─ interviewer_notes (text observations)
```

**Output Files:**
- `viva_session_[participant_id].json` (session recording)
- `assessment_[participant_id].json` (classification + evidence)
- `fairness_audit_[participant_id].json` (bias check results)
- `participant_feedback_[participant_id].json` (survey responses)

---

#### 2.4 Disagreement Analysis

**Find cases where:**
1. ORACLE says HIGH but interviewer says LOW (possible false positive)
2. ORACLE says LOW but interviewer says HIGH (possible false negative)
3. ORACLE HIGH but participant self-reports LOW (overconfidence?)
4. ORACLE LOW but participant self-reports HIGH (underconfidence?)

**For each disagreement, analyze:**
- What signals did ORACLE use?
- Did fairness audit catch issues?
- Was evidence insufficient?
- Did communication style affect assessment?
- What should have happened?

---

### Phase 3: Error Analysis & Hardening (Week 5)

#### 3.1 False Positive Analysis

**Question:** When did ORACLE mark someone as non-familiar when they actually were?

**Analysis:**
- Which communication patterns triggered false positives?
- Were fairness audit issues correctly flagged?
- Should confidence be reduced? Recommendations added?
- What follow-ups would have helped?

**Output:** False positive patterns document

---

#### 3.2 False Negative Analysis

**Question:** When did ORACLE mark someone as familiar when they actually weren't?

**Analysis:**
- Which confidence indicators were misleading?
- How many memorization indicators were missed?
- Did confident delivery trick the system?
- Should follow-ups probe deeper?

**Output:** False negative patterns document

---

#### 3.3 Bias Pattern Analysis

**Question:** Did certain demographics get systematically misclassified?

**Analysis by demographic:**
- Non-native speakers: under/over represented in misclassifications?
- Early career: systematic bias?
- Non-traditional background: systematic bias?
- Communication style: correlation with accuracy?

**Output:** Bias analysis report

---

### Phase 4: System Improvements (Week 6-7)

Based on findings from Phase 2-3:

1. **Adjust indicator weights** if communication style bias detected
2. **Add new follow-up patterns** if certain misclassifications repeat
3. **Improve fairness audit** if certain biases not caught
4. **Reduce confidence scores** if overconfidence detected
5. **Retrain on test cases** if patterns are systematic

---

## Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| True Positive Rate | 90%+ | % of HIGH-familiarity test cases correctly identified |
| True Negative Rate | 90%+ | % of LOW-familiarity test cases correctly identified |
| False Positive Rate | <10% | % of non-familiar marked as familiar |
| False Negative Rate | <10% | % of familiar marked as non-familiar |
| Communication Bias | <5% | Correlation between communication style and assessment |
| Demographic Bias | <5% | Systematic bias by demographic |
| Fairness Audit Effectiveness | 80%+ | % of problems caught by fairness audit |
| Participant Accuracy Self-Report | 4+/5 avg | Mean participant satisfaction |
| Evidence Grounding | 100% | All conclusions have evidence trace |

---

## Testing Checklist

### Before Phase 1:
- [ ] Define test case library (questions to ask)
- [ ] Recruit 6 internal testers (3 builders, 3 non-builders)
- [ ] Create feedback template
- [ ] Set baseline metrics

### Before Phase 2:
- [ ] Recruit 10-15 external participants
- [ ] Create pre/post surveys
- [ ] Set up recording infrastructure
- [ ] Train facilitators

### After Phase 2-3:
- [ ] Analyze all disagreement cases
- [ ] Categorize false positives/negatives
- [ ] Identify bias patterns
- [ ] Create improvement plan

### After Phase 4:
- [ ] Implement improvements
- [ ] Re-test on sample of failures
- [ ] Document learnings
- [ ] Generate final report

---

## Sample Test Case

**Participant:** Backend developer, 3 years on project X

**Question 1:** "The API endpoint for user list loads 100+ related resources per user. What's the performance concern and how would you fix it?"

**Good Response (HIGH familiarity):**
> "N+1 query problem. When we first built this, we didn't batch load relationships, so each user load triggered a separate query. We discovered this in production when response time hit 2 seconds for 10 users. We fixed it using SQLAlchemy's joinedload with batch pagination - we load at most 10 related records per batch. Tradeoff is complexity in query construction, but we get sub-100ms responses now."

**Poor Response (LOW familiarity):**
> "Um, probably an N+1 query issue? That's like a common database pattern problem. You'd use eager loading to fix it, I think. That's a best practice in database design."

**Expected Difference in Assessment:**
- Good response: HIGH_FAMILIARITY, HIGH confidence, 3+ understanding indicators
- Poor response: LOW_FAMILIARITY, HIGH confidence, 2+ memorization indicators

---

## Documentation Output

- `TESTING_RESULTS_PHASE1.md` - Internal validation results
- `TESTING_RESULTS_PHASE2.md` - Pilot study results + feedback
- `DISAGREEMENT_ANALYSIS.md` - False positive/negative patterns
- `BIAS_ANALYSIS.md` - Demographic bias findings
- `IMPROVEMENTS_APPLIED.md` - Changes made based on testing

---

## Next Actions

1. [ ] Finalize test case library
2. [ ] Recruit internal testers
3. [ ] Create feedback templates
4. [ ] Schedule Phase 1 (Week 1-2)
5. [ ] Recruit external participants
6. [ ] Schedule Phase 2 (Week 3-4)
