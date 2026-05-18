"""
Repository Fixtures: Structured test dataset definitions with expected outputs.

Each fixture defines:
- Repository characteristics (tech stack, patterns, antipatterns)
- Expected observable signals (what SHOULD be detected)
- Expected failure scenarios (propagation paths)
- Expected viva topics (architectural challenges)

Used for validation, stress-testing, and calibration accuracy measurement.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class ExpectedSignal:
    """Definition of an observable signal we expect to find."""
    signal_name: str
    category: str  # error_handling, resilience, observability, etc.
    should_exist: bool
    expected_files: List[str]  # File patterns that should be referenced
    expected_confidence_min: float  # Minimum acceptable confidence
    failure_indicates: str  # What would indicate validation failure


@dataclass
class ExpectedFailureScenario:
    """Definition of a failure scenario propagation path we expect."""
    scenario_name: str
    trigger_pattern: str  # What triggers the failure
    expected_affected_paths: int  # How many execution paths affected
    propagation_risk: str  # critical, high, medium, low
    recovery_possible: bool
    affected_components: List[str]  # Component names in propagation chain


@dataclass
class ExpectedVivaCharacteristic:
    """Characteristics we expect in viva questions for this repo."""
    topic: str
    should_be_grounded_in: str  # What evidence or failure scenario
    difficulty_range: str  # hard, medium, foundational
    should_mention_code_patterns: List[str]


@dataclass
class RepositoryFixture:
    """Complete test fixture for a repository."""
    name: str
    description: str
    repo_type: str  # clean, messy, broken, mixed-framework, partial, dead-code, monorepo, auth-heavy, async-heavy
    tech_stack: Dict[str, str]  # framework -> specific tech
    
    # Structural characteristics
    estimated_modules: int
    async_usage: str  # none, light, heavy
    auth_complexity: str  # none, simple, complex
    error_handling: str  # none, basic, comprehensive
    external_dependencies: List[str]  # APIs, databases, caches
    
    # Expected validation outcomes
    expected_signals: List[ExpectedSignal] = field(default_factory=list)
    expected_failure_scenarios: List[ExpectedFailureScenario] = field(default_factory=list)
    expected_viva_characteristics: List[ExpectedVivaCharacteristic] = field(default_factory=list)
    
    # Stress-test expectations
    adversarial_challenges: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "repo_type": self.repo_type,
            "tech_stack": self.tech_stack,
            "estimated_modules": self.estimated_modules,
            "async_usage": self.async_usage,
            "auth_complexity": self.auth_complexity,
            "error_handling": self.error_handling,
            "external_dependencies": self.external_dependencies,
            "expected_signals": [
                {
                    "signal_name": s.signal_name,
                    "category": s.category,
                    "should_exist": s.should_exist,
                    "expected_confidence_min": s.expected_confidence_min,
                }
                for s in self.expected_signals
            ],
            "expected_failure_scenarios": [
                {
                    "scenario_name": s.scenario_name,
                    "propagation_risk": s.propagation_risk,
                    "recovery_possible": s.recovery_possible,
                }
                for s in self.expected_failure_scenarios
            ],
            "adversarial_challenges": self.adversarial_challenges,
        }


# ============================================================================
# REPOSITORY FIXTURE DEFINITIONS
# ============================================================================

CLEAN_FASTAPI_REST_API = RepositoryFixture(
    name="Clean FastAPI REST API",
    description="Well-structured REST API with comprehensive error handling",
    repo_type="clean",
    tech_stack={"backend": "FastAPI", "database": "PostgreSQL", "cache": "Redis"},
    estimated_modules=8,
    async_usage="heavy",
    auth_complexity="simple",
    error_handling="comprehensive",
    external_dependencies=["PostgreSQL", "Redis", "External REST API"],
    expected_signals=[
        ExpectedSignal(
            signal_name="Async error recovery patterns",
            category="error_handling",
            should_exist=True,
            expected_files=["main.py", "routes/*.py"],
            expected_confidence_min=0.85,
            failure_indicates="Critical missing: no async error handling detected"
        ),
        ExpectedSignal(
            signal_name="Redis cache resilience",
            category="resilience_patterns",
            should_exist=True,
            expected_files=["services/cache.py"],
            expected_confidence_min=0.80,
            failure_indicates="Cache strategy not grounded in actual code"
        ),
        ExpectedSignal(
            signal_name="Request/response observability",
            category="observability",
            should_exist=True,
            expected_files=["middleware/*.py", "main.py"],
            expected_confidence_min=0.75,
            failure_indicates="Logging infrastructure not detected"
        ),
    ],
    expected_failure_scenarios=[
        ExpectedFailureScenario(
            scenario_name="Database connection loss",
            trigger_pattern="PostgreSQL unavailable",
            expected_affected_paths=5,  # All queries fail
            propagation_risk="critical",
            recovery_possible=False,
            affected_components=["queries", "transaction_handlers", "connection_pool"],
        ),
        ExpectedFailureScenario(
            scenario_name="Redis cache failure",
            trigger_pattern="Redis timeout",
            expected_affected_paths=3,
            propagation_risk="high",
            recovery_possible=True,
            affected_components=["cache_layer", "query_fallback"],
        ),
    ],
    expected_viva_characteristics=[
        ExpectedVivaCharacteristic(
            topic="How would you handle database failover?",
            should_be_grounded_in="ExecutionGraphFailureAnalyzer DB failure scenario",
            difficulty_range="hard",
            should_mention_code_patterns=["connection_pool", "retry_logic", "fallback"],
        ),
        ExpectedVivaCharacteristic(
            topic="What's your cache coherency strategy?",
            should_be_grounded_in="ObservableSignalsEngine Redis detection",
            difficulty_range="hard",
            should_mention_code_patterns=["cache_invalidation", "TTL_strategy"],
        ),
    ],
    adversarial_challenges=[
        "Missing proper async context in error handlers",
        "Unhandled timeout cascades",
        "Cache stampede scenarios",
    ],
)

MESSY_STUDENT_PROJECT = RepositoryFixture(
    name="Messy Student Project",
    description="Real student project with mixed patterns, incomplete error handling",
    repo_type="messy",
    tech_stack={"backend": "Flask", "database": "SQLite", "frontend": "React"},
    estimated_modules=15,
    async_usage="none",
    auth_complexity="simple",
    error_handling="basic",
    external_dependencies=["SQLite", "External API (Gmail)"],
    expected_signals=[
        ExpectedSignal(
            signal_name="Synchronous database access",
            category="architecture",
            should_exist=True,
            expected_files=["app.py", "models.py"],
            expected_confidence_min=0.90,
            failure_indicates="Synchronous patterns not detected in Flask app"
        ),
        ExpectedSignal(
            signal_name="Missing connection pooling",
            category="resilience_patterns",
            should_exist=True,
            expected_files=["app.py"],
            expected_confidence_min=0.70,
            failure_indicates="Signal should note absence of pooling, not hallucinate presence"
        ),
        ExpectedSignal(
            signal_name="Inadequate input validation",
            category="error_handling",
            should_exist=True,
            expected_files=["routes.py", "models.py"],
            expected_confidence_min=0.65,
            failure_indicates="Must detect minimal validation patterns"
        ),
    ],
    expected_failure_scenarios=[
        ExpectedFailureScenario(
            scenario_name="SQLite lock timeout",
            trigger_pattern="Concurrent write requests",
            expected_affected_paths=2,
            propagation_risk="high",
            recovery_possible=False,
            affected_components=["database_layer", "request_handler"],
        ),
        ExpectedFailureScenario(
            scenario_name="External API timeout without retry",
            trigger_pattern="Gmail API fails",
            expected_affected_paths=1,
            propagation_risk="medium",
            recovery_possible=False,
            affected_components=["email_service"],
        ),
    ],
    expected_viva_characteristics=[
        ExpectedVivaCharacteristic(
            topic="Why does concurrent database access fail with SQLite?",
            should_be_grounded_in="ObservableSignalsEngine SQLite detection",
            difficulty_range="medium",
            should_mention_code_patterns=["write_locks", "isolation_level"],
        ),
    ],
    adversarial_challenges=[
        "No proper error messages in catch blocks",
        "Silent failures in async-like patterns",
        "Unhandled API integration points",
    ],
)

BROKEN_ASYNC_PROJECT = RepositoryFixture(
    name="Broken Async Project",
    description="Async system with missing awaits, race conditions, deadlocks",
    repo_type="broken",
    tech_stack={"backend": "AsyncIO Python", "message_queue": "RabbitMQ"},
    estimated_modules=10,
    async_usage="heavy",
    auth_complexity="none",
    error_handling="basic",
    external_dependencies=["RabbitMQ", "External worker services"],
    expected_signals=[
        ExpectedSignal(
            signal_name="Missing await statements",
            category="error_handling",
            should_exist=True,
            expected_files=["workers.py", "tasks.py"],
            expected_confidence_min=0.80,
            failure_indicates="Critical: should detect fire-and-forget anti-patterns"
        ),
        ExpectedSignal(
            signal_name="Race condition patterns",
            category="resilience_patterns",
            should_exist=True,
            expected_files=["shared_state.py"],
            expected_confidence_min=0.65,
            failure_indicates="Should detect shared mutable state without locks"
        ),
    ],
    expected_failure_scenarios=[
        ExpectedFailureScenario(
            scenario_name="Deadlock in task coordination",
            trigger_pattern="Circular task dependencies",
            expected_affected_paths=4,
            propagation_risk="critical",
            recovery_possible=False,
            affected_components=["task_queue", "dependency_resolver"],
        ),
        ExpectedFailureScenario(
            scenario_name="Message queue overflow",
            trigger_pattern="Worker failures cascade",
            expected_affected_paths=5,
            propagation_risk="critical",
            recovery_possible=False,
            affected_components=["queue", "workers", "backpressure_handling"],
        ),
    ],
    expected_viva_characteristics=[
        ExpectedVivaCharacteristic(
            topic="How would you prevent task deadlocks in your system?",
            should_be_grounded_in="ExecutionGraphFailureAnalyzer deadlock scenario",
            difficulty_range="hard",
            should_mention_code_patterns=["timeout", "deadlock_detection", "task_ordering"],
        ),
    ],
    adversarial_challenges=[
        "Fire-and-forget task scheduling",
        "Missing timeout on queue operations",
        "Unhandled worker crashes",
        "No circuit breaker for cascading failures",
    ],
)

MONOREPO_WITH_SHARED_STATE = RepositoryFixture(
    name="Monorepo with Shared State",
    description="Monorepo with multiple services sharing database and cache layer",
    repo_type="monorepo",
    tech_stack={
        "backend1": "FastAPI",
        "backend2": "Django",
        "backend3": "Express",
        "database": "PostgreSQL",
        "cache": "Redis",
        "message_queue": "RabbitMQ"
    },
    estimated_modules=40,
    async_usage="heavy",
    auth_complexity="complex",
    error_handling="comprehensive",
    external_dependencies=["PostgreSQL", "Redis", "RabbitMQ", "OAuth providers"],
    expected_signals=[
        ExpectedSignal(
            signal_name="Cross-service auth token validation",
            category="auth_consistency",
            should_exist=True,
            expected_files=["services/*/auth/*.py"],
            expected_confidence_min=0.75,
            failure_indicates="Should detect shared auth patterns across services"
        ),
        ExpectedSignal(
            signal_name="Database connection pooling across services",
            category="operational_dependencies",
            should_exist=True,
            expected_files=["services/*/db_config.py"],
            expected_confidence_min=0.80,
            failure_indicates="Must detect shared resource contention risks"
        ),
    ],
    expected_failure_scenarios=[
        ExpectedFailureScenario(
            scenario_name="Auth service failure cascades across microservices",
            trigger_pattern="Central auth service down",
            expected_affected_paths=8,
            propagation_risk="critical",
            recovery_possible=False,
            affected_components=["auth_service", "service1", "service2", "service3"],
        ),
    ],
    adversarial_challenges=[
        "Duplicate auth implementations with inconsistencies",
        "Cascading service failures through shared DB",
        "Token expiry not synchronized",
    ],
)

# ============================================================================
# TEST DATASET REGISTRY
# ============================================================================

ALL_FIXTURES = [
    CLEAN_FASTAPI_REST_API,
    MESSY_STUDENT_PROJECT,
    BROKEN_ASYNC_PROJECT,
    MONOREPO_WITH_SHARED_STATE,
]

FIXTURE_REGISTRY = {fixture.name: fixture for fixture in ALL_FIXTURES}


def get_fixture_by_type(repo_type: str) -> List[RepositoryFixture]:
    """Get all fixtures matching a specific repository type."""
    return [f for f in ALL_FIXTURES if f.repo_type == repo_type]


def get_fixture_by_name(name: str) -> Optional[RepositoryFixture]:
    """Get fixture by exact name."""
    return FIXTURE_REGISTRY.get(name)
