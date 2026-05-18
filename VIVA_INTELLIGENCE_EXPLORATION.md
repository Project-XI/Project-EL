# Viva Intelligence Engine Exploration

## Executive Summary

The Project-EL system has **two parallel viva generation approaches**:
1. **Template-Based** (Primary): `VivaIntelligenceEngine` - Pattern matching on detected technologies
2. **Evidence-Grounded** (Secondary): `EvidenceGroundedVivaGenerator` - Based on actual failure scenarios and observable signals

Both generate `VivaTarget` objects with 7+ attributes. Questions are **ranked by difficulty, topic, and depth keywords**.

---

## 1. Core Classes & Methods

### VivaIntelligenceEngine (viva_intelligence_engine.py)

**Main Entry Point:**
```python
@staticmethod
def generate_targets(detections: Dict[str, Any], arch: EvidenceModel) -> List[VivaTarget]
```

**What it does:**
- Inspects detected technologies (FastAPI, Express, React, SQL, MongoDB, JWT, Redis, etc.)
- Generates 15-25 viva questions across 6 categories:
  - **Architecture**: REST constraints, Microservices boundaries, FastAPI dependency injection
  - **Tradeoffs**: Polyglot persistence, SPA vs SSR, relational vs NoSQL selection
  - **Security**: JWT lifecycle/revocation, auth failure paths, token handling
  - **Scalability**: Database connection pooling, cache eviction, horizontal scaling constraints
  - **Failure-Path**: Cascading failures, auth service unavailability, single points of failure
  - **Runtime**: Async/sync boundaries, event loop blocking, thread pool implications

**Key Methods:**
- `detect_inconsistencies(doc_text, detections)` → Flags mismatches between docs and code (e.g., "Redis mentioned but not detected")
- `detect_complexity_mismatch(arch, detections)` → Identifies claims like "Microservices" with only 1 backend detected

**Confidence & Depth Scoring:**
```python
VivaTarget(
    topic="Security",
    question_target="JWT Lifecycle & Revocation",
    difficulty="hard",
    importance_score=0.95,              # Base importance
    focus="JWT tokens are stateless...", # Question text
    category="Security",
    depth_score=9.5,                     # Engineering depth (0-10)
    related_node="auth_middleware",      # Execution graph node
    confidence=0.97,                     # Engine confidence in relevance
    reasoning_summary="JWT signals detected in middleware chain."
)
```

---

### EvidenceGroundedVivaGenerator (evidence_grounded_viva_generator.py)

**Main Entry Point:**
```python
@staticmethod
def generate_questions(
    failure_scenarios: List[Any],
    observable_signals: Dict[str, List[Any]],
    detections: Dict[str, Any],
    repo_path: str
) -> List[VivaTarget]
```

**What it does:**
- Generates viva questions **grounded in actual code evidence**
- Uses 4 signal categories:
  1. **Failure Scenario Questions** - "Walk me through what happens when {scenario}"
  2. **Observable Signal Questions** - "Your code shows X, how do you handle Y?"
  3. **Technology Questions** - Framework/language-specific patterns
  4. **Architecture Questions** - Observable patterns from signal analysis

**Evidence Tracing:**
- Each question references specific files that prompted the question
- Questions like: "I don't see circuit breaker patterns - how do you prevent cascading failures?"
- Example: If error handling signals show "high" risk, generates hard-difficulty questions

**CodeGroundedVivaQuestion Model:**
```python
@dataclass
class CodeGroundedVivaQuestion:
    topic: str
    question: str
    implementation_context: str  # What code prompted this
    evidence_files: List[str]    # Traceable source files
    expected_knowledge: str      # What engineer should understand
    difficulty: str
```

---

### VivaQuestionRanker (viva_question_ranker.py)

**Scoring Logic:**
```python
@staticmethod
def rank_targets(targets: List[VivaTarget]) -> List[VivaTarget]
```

**Ranking Formula:**
```
base_score = importance_score

if difficulty == "hard":      +0.3
if topic == "security":       +0.2
if topic == "architecture":   +0.1

if any(depth_keyword in focus):  +0.2
  where depth_keywords = ["middleware", "lifecycle", "flow", "failure", "risk", "tradeoff", "why"]

final_score = min(1.0, score)  # Cap at 1.0
```

**Result:** Sorted descending by importance_score, so highest-value questions appear first.

---

## 2. Data Flow & Context Sources

### What Feeds Into Viva Generation

```
┌─────────────────────────────────────────┐
│ OracleAgent.process()                   │
└────────┬────────────────────────────────┘
         │
    ┌────▼──────────────────────────────────┐
    │ Phase 1: Observable Signals Extraction│
    │ - Error handling patterns             │
    │ - Resilience checks                   │
    │ - Architecture detection              │
    └────┬─────────────────────────────────┘
         │
    ┌────▼──────────────────────────────────┐
    │ Phase 2: Failure Scenario Detection   │
    │ (FailurePathIntelligenceEngine)       │
    │ - Database failures                   │
    │ - Auth service unavailability         │
    │ - Cascading failures                  │
    └────┬─────────────────────────────────┘
         │
    ┌────▼──────────────────────────────────┐
    │ Phase 3: CHOICE OF VIVA GENERATOR     │
    │                                       │
    │ IF failure_scenarios detected:        │
    │   → EvidenceGroundedVivaGenerator     │
    │                                       │
    │ ELSE (fallback):                      │
    │   → VivaIntelligenceEngine            │
    └────┬─────────────────────────────────┘
         │
    ┌────▼──────────────────────────────────┐
    │ Phase 4: Rank Targets                 │
    │ (VivaQuestionRanker)                  │
    │ → Output: Sorted VivaTarget[]         │
    └────────────────────────────────────────┘
```

### Input Data Structure (repo_detections)

```python
repo_detections = {
    "frontend_framework": EvidenceModel(value="React", confidence=0.95),
    "backend_framework": EvidenceModel(value="FastAPI", confidence=0.98),
    "database_used": EvidenceModel(value="SQL", confidence=0.92),
    "authentication_system": EvidenceModel(value="JWT", confidence=0.97),
    "cache_framework": EvidenceModel(value="Redis", confidence=0.85),
    # ... 10+ more detection types
}

arch_inference = EvidenceModel(
    value="REST API + SPA",
    confidence=0.9,
    evidence=["FastAPI routes detected", "React component structure"]
)
```

### Observable Signals (Passed to Evidence-Grounded Generator)

```python
observable_signals = {
    "error_handling": [
        EngineeringSignal(
            signal_name="Centralized Error Handler Detected",
            category="error_handling",
            confidence=0.85,
            evidence_files=["routes/error_handler.py", "middleware/exception.py"],
            description="Centralized error handling middleware found",
            risk_level="N/A"
        )
    ],
    "resilience_patterns": [
        # Circuit breakers, retry logic, timeouts
    ],
    "auth_consistency": [
        # Auth check distribution across endpoints
    ],
    # ... 6 categories total
}
```

### Failure Scenarios

```python
failure_scenarios = [
    {
        "scenario_name": "Database Connection Exhaustion",
        "trigger": "concurrent_requests_triple",
        "propagation_risk": "critical",
        "recovery_possible": True,
        # → Generates question: "How does your system handle this? What's your recovery?"
    },
    # ... 15+ failure modes in corpus
]
```

---

## 3. How Viva Questions Are Currently Generated

### Template-Based Flow (VivaIntelligenceEngine)

**Step 1: Technology Detection**
```python
has_fastapi = any("FastAPI" in str(m.value) for m in detections.values())
has_jwt    = any("JWT" in str(m.value) for m in detections.values())
has_redis  = any("Redis" in str(m.value) for m in detections.values())
# ... check 8 technologies
```

**Step 2: Pattern Matching → Question Generation**
```python
if has_fastapi:
    targets.append(VivaTarget(
        topic="Architecture",
        question_target="FastAPI Dependency Injection Graph",
        difficulty="medium",
        importance_score=0.85,
        focus="Trace the full FastAPI dependency injection chain from request to database access..."
    ))

if has_jwt:
    targets.append(VivaTarget(
        topic="Security",
        question_target="JWT Lifecycle & Revocation",
        difficulty="hard",
        importance_score=0.95,
        focus="JWT tokens are stateless. Explain how this implementation handles token revocation..."
    ))
```

**Step 3: Ranking**
- All targets passed to `VivaQuestionRanker.rank_targets()`
- Scoring boosts hard-difficulty, security, and depth-keyword questions
- Returns sorted list by `importance_score` (descending)

### Evidence-Grounded Flow (EvidenceGroundedVivaGenerator)

**Step 1: Analyze Failure Scenarios**
```python
for scenario in failure_scenarios:
    if scenario.propagation_risk == "critical":
        question_text = f"Walk me through what happens when {scenario.trigger.lower()}..."
        questions.append(VivaTarget(
            topic=scenario.scenario_name,
            difficulty="hard",
            importance_score=0.95,  # High for critical failures
            focus=question_text
        ))
```

**Step 2: Analyze Observable Signals**
```python
# If auth signals don't show centralized checking:
if not any("Centralized" in str(s.signal_name) for s in auth_signals):
    question = VivaTarget(
        topic="Authentication",
        question_target="Auth Consistency",
        difficulty="hard",
        importance_score=0.9,
        focus="I see auth checks scattered across your codebase. How do you ensure..."
    )
```

**Step 3: Technology-Specific Questions**
- Questions tailored to detected tech: FastAPI patterns, Express blocking, React SSR tradeoffs

---

## 4. Multi-Turn / Follow-Up Logic

### VivaSession Simulation Framework (viva_simulation.py)

**Architecture:**
```python
class VivaSession(BaseModel):
    initial_question: str
    student_responses: List[SimulatedStudentResponse] = []
    follow_up_questions: List[VivaFollowUpQuestion] = []
    weakness_probing_rate: float  # % of follow-ups targeting revealed weaknesses
    generic_question_rate: float  # % of follow-ups that are generic
```

**Student Response Types:**
- `CORRECT`: Knows implementation and reasoning
- `TEXTBOOK`: Generic concepts, not codebase-specific
- `PARTIAL`: Correct but incomplete
- `CONTRADICTORY`: Internally inconsistent
- `MISUNDERSTANDING`: Wrong assumptions
- `WEAK_EXPLANATION`: Right answer, unclear reasoning

**Follow-Up Question Quality Assessment:**
```python
class FollowUpQuestionQuality(str, Enum):
    GENERIC = "generic"          # Could apply to any codebase
    PROBING = "probing"          # Tests specific weakness
    IRRELEVANT = "irrelevant"    # Doesn't relate to prior answer
    CLARIFYING = "clarifying"    # Good clarification
    DEEPENING = "deepening"      # Pushes deeper
    CONTRADICTING = "contradicting"  # Points out inconsistency
```

**Current Status:**
- Follow-up framework is defined but **NOT YET INTEGRATED** into OracleAgent
- System can simulate follow-ups but doesn't auto-generate them in live ORACLE flow
- Evaluation harness exists: `evaluate_follow_up()` method in viva_simulation.py

---

## 5. Viva Question Scoring & Evaluation

### ComparativeVivaEvaluator (comparative_evaluator.py)

**Single Question Evaluation:**
```python
def compare_viva_question(
    self,
    oracle_question: str,
    human_evaluations: List[HumanVivaQuestionEvaluation]
) -> ComparativeVivaAnalysis
```

**Metrics Generated:**
- **quality_rate**: % of humans who rated question as non-generic
- **code_specificity**: Average specificity score (0-1)
- **distinguishes_levels**: % saying question would distinguish senior from junior engineers
- **would_ask_in_interview**: % saying they'd ask this in a real interview

**Verdict Logic:**
```
if generic_count / total_humans >= 0.75:
    → "Question detected as textbook/generic"
    → oracle_question_good = False

elif quality_rate >= 0.7:
    → "Good question"
    → oracle_question_good = True

else:
    → "Mixed quality evaluation"
```

### Viva Question Quality Enum

```python
class VivaQuestionQuality(str, Enum):
    TEXTBOOK_GENERIC = "textbook_generic"
    IMPLEMENTATION_DEEP_DIVE = "implementation_deep_dive"
    ARCHITECTURAL_INSIGHT = "architectural_insight"
    TOO_SIMPLE = "too_simple"
    TOO_VAGUE = "too_vague"
    CONTEXT_APPROPRIATE = "context_appropriate"
    DISTINGUISHES_ENGINEER_LEVEL = "distinguishes_engineer_level"
```

### Dataset Metrics (Full Batch Evaluation)

```python
def evaluate_viva_questions(
    self,
    oracle_questions: List[str],
    human_question_evaluations: Dict[str, List[HumanVivaQuestionEvaluation]]
) -> Tuple[List[ComparativeVivaAnalysis], Dict[str, Any]]

# Returns:
metrics = {
    "total_questions": N,
    "quality_questions": count of good questions,
    "generic_questions": count flagged as generic,
    "avg_quality_rate": 0.0-1.0,
    "avg_code_specificity": 0.0-1.0,
    "avg_distinguish_levels": 0.0-1.0,
}
```

---

## 6. Current Viva Capabilities Summary

### What ORACLE Can Do ✅

1. **Generate 15-25 viva questions per repo** (template-based or evidence-grounded)
2. **Categorize questions** across 6 engineering domains
3. **Assign difficulty levels** (easy, medium, hard)
4. **Score by importance** (0-1 scale, ranked)
5. **Rank by engineering depth** (depth_score 0-10, difficulty boost, keyword analysis)
6. **Ground in observable code patterns** (if evidence-grounded)
7. **Detect inconsistencies** (doc claims vs actual code)
8. **Identify complexity mismatches** (e.g., "microservices" with 1 backend)

### What ORACLE Cannot Do (Yet) ❌

1. **Generate true multi-turn follow-ups** - Framework exists but not integrated
2. **Adapt questions in real-time** - Based on student response quality
3. **Score student answers** - Only infrastructure for human evaluation exists
4. **Update question difficulty** - Based on initial response
5. **Surface follow-up follow-ups** - Only one level of follow-ups planned

---

## 7. Key Data Structures

### VivaTarget (models/context.py)

```python
class VivaTarget(BaseModel):
    topic: str                          # Architecture, Security, Scalability, etc.
    question_target: str                # Specific topic (e.g., "JWT Lifecycle")
    difficulty: str                     # easy, medium, hard
    importance_score: float             # 0.0-1.0, boosted by ranker
    focus: str                          # Full question text
    
    # Extended Intelligence
    category: str                       # Same as topic, for filtering
    depth_score: float                  # 0-10 engineering depth
    related_node: str                   # Execution graph node (e.g., "auth_middleware")
    confidence: float                   # 0.0-1.0, engine confidence
    reasoning_summary: str              # Why this question was generated
```

### HumanVivaQuestionEvaluation (human_evaluator_models.py)

```python
class HumanVivaQuestionEvaluation(BaseModel):
    question_text: str
    human_verdict: List[VivaQuestionQuality]  # Multiple verdicts possible
    code_specificity_score: float              # 0.0-1.0
    distinguishes_senior_engineer: bool       # Would this screen out juniors?
    technical_accuracy: bool
    suggested_follow_up: Optional[str]
```

### ComparativeVivaAnalysis (comparative_evaluator.py)

```python
class ComparativeVivaAnalysis(BaseModel):
    question_text: str
    human_evaluations: List[HumanVivaQuestionEvaluation]
    
    # Metrics
    quality_rate: float                 # % rated as good
    code_specificity: float             # Average specificity
    distinguishes_levels: float         # % say it distinguishes levels
    would_ask_in_interview: float       # % say they'd ask this
    
    # Verdict
    oracle_question_good: bool
    textbook_pattern_detected: bool
    consensus: str
```

---

## 8. File Map

| File | Purpose |
|------|---------|
| `viva_intelligence_engine.py` | Template-based viva generation (primary) |
| `evidence_grounded_viva_generator.py` | Evidence-grounded viva generation (secondary) |
| `viva_question_ranker.py` | Ranks/scores viva targets |
| `implementation_flow_engine.py` | Orchestrates analysis, attaches viva targets |
| `observable_signals_engine.py` | Extracts engineering signals for evidence-grounding |
| `viva_simulation.py` | Simulates viva sessions with follow-up logic |
| `comparative_evaluator.py` | Evaluates viva questions against human assessments |
| `agents/oracle/agent.py` | Main orchestrator calling viva generators |
| `models/context.py` | VivaTarget, StructuredContext data models |

---

## 9. Integration Points (OracleAgent Flow)

```python
# File: backend/src/agents/oracle/agent.py, line 140-170

# Phase 1: Extract signals & failures
grounded_viva_targets = EvidenceGroundedVivaGenerator.generate_questions(
    failure_scenarios,
    observable_signals,
    repo_detections,
    repo_path
)

# Phase 2: Fallback viva generation
viva_targets = VivaIntelligenceEngine.generate_targets(
    repo_detections,
    arch_inference
)

# Phase 3: Use evidence-grounded if available, else fallback
final_viva_targets = grounded_viva_targets if grounded_viva_targets else viva_targets

# Phase 4: Attach to context
context.viva_intelligence_targets = final_viva_targets

# Phase 5: Implementation flow analysis (adds more viva targets)
context = ImplementationFlowEngine.analyze_implementation(repo_path, structure, context)
# This adds: context.implementation_viva_targets (basic, hardcoded for now)
```

---

## 10. Future Enhancement Opportunities

### Short Term
1. **Wire follow-up generation into OracleAgent** - Use VivaSession simulation in live flow
2. **Auto-score student responses** - Integrate LLM evaluation for answer quality
3. **Adaptive difficulty** - Re-rank questions based on response quality
4. **Rich follow-up feedback** - Surface why question was asked and what weakness it targets

### Medium Term
5. **Multi-turn conversations** - Chain 3-5 follow-ups before judging competency
6. **Personalized question selection** - Pick questions matching student's tech stack
7. **Failure scenario drills** - "Walk me through your system when X fails" - auto-scored
8. **Peer comparison** - Show how student's answers compare to engineering review corpus

### Long Term
9. **Active learning** - Questions that maximize information gain about candidate
10. **Calibration** - Learn which questions best distinguish senior vs junior engineers
11. **Competency profiling** - Map responses to specific engineering competencies
12. **Career progression tracking** - See how candidate's knowledge evolves over time

---

## 11. Known Limitations

1. **No true semantic understanding** - Pattern matching, not semantic viva question generation
2. **Hardcoded follow-ups** - Implementation flow engine adds basic, fixed follow-ups
3. **Single-pass ranking** - Doesn't re-rank based on interdependencies
4. **No context from prior answers** - Each question generated independently
5. **Generic fallback** - If no evidence available, falls back to template-based
6. **Limited failure corpus** - Only 15 canned failure scenarios
7. **No student model** - Can't track student's knowledge over time within session

---

## 12. Key Insights from Codebase

### Design Philosophy
- **Evidence-first**: Questions should be grounded in observable code patterns
- **No speculative scoring**: Avoid arbitrary confidence inflation
- **Failure-driven**: Generate questions that probe likely failure modes
- **Comparative assessment**: Evaluate against human engineering reviews, not rubrics

### Architecture Strengths
- Clean separation between template-based and evidence-grounded approaches
- Modular signal extraction (error handling, resilience, auth, observability)
- Ranked output (easy to filter by difficulty/importance)
- Rich metadata (depth_score, related_node, confidence, reasoning)

### Open Questions for Phase 3+
- Should follow-ups be generated online (during interview) or precomputed?
- How to prevent questions from being "asked before" in industry interviews?
- Should we learn from student responses to update question quality metrics?
- How to calibrate importance_score against real interview outcomes?
