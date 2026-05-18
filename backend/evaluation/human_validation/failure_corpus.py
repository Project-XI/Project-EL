"""Failure Corpus Dataset: Intentionally Problematic Implementations for Stress-Testing

This module defines a collection of "problematic" repositories designed to test whether
ORACLE can identify and characterize real failure modes that engineers encounter.

Each repository fixture includes:
- Intentional implementation problems
- Expected ORACLE signals (what should be detected)
- Expected failure scenarios (what can go wrong)
- Expected viva targets (what engineers would question)
- Adversarial challenges (edge cases ORACLE might miss)
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class FailureCorpusCategory(str, Enum):
    """Categories of failure modes in corpus"""
    RETRY_LOGIC = "broken_retry_logic"
    AUTH_MIDDLEWARE = "disconnected_auth_middleware"
    CACHE_LOGIC = "dead_cache_logic"
    VALIDATION = "inconsistent_validation"
    ASYNC_RACE = "async_race_condition"
    TIMEOUT = "missing_timeout_handling"
    DUPLICATION = "duplicated_service_logic"
    ERROR_PROPAGATION = "weak_error_propagation"
    FALLBACK = "missing_fallback_mechanisms"
    STATE_CONSISTENCY = "state_consistency_violation"
    DEPENDENCY_INJECTION = "broken_dependency_injection"
    RESOURCE_LEAK = "resource_leak"
    CASCADING_FAILURE = "cascading_failure_not_handled"
    STALE_DATA = "stale_data_not_detected"
    TRANSACTION_ISOLATION = "transaction_isolation_violation"


class FailureCorpusRepository(BaseModel):
    """Repository fixture with intentional failures for testing"""
    id: str
    name: str
    category: FailureCorpusCategory
    description: str
    
    # Code characteristics
    framework: str  # FastAPI, Django, Flask, etc
    async_patterns: bool
    external_services: List[str]  # Redis, PostgreSQL, Elasticsearch, etc
    
    # Intentional problems
    problems: List[str]  # Plain English description of each problem
    problem_severity: str  # low, medium, high, critical
    problem_likelihood_in_production: float  # 0-1 how likely this is real?
    
    # Expected detections
    expected_signals: List[Dict[str, Any]] = []  # What ORACLE should find
    expected_failure_scenarios: List[Dict[str, Any]] = []  # What failures should be identified
    expected_viva_targets: List[Dict[str, Any]] = []  # What should be questioned
    
    # Adversarial challenges
    adversarial_challenges: List[str] = []  # Ways ORACLE might get confused
    hallucination_risks: List[str] = []  # What ORACLE might wrongly detect?
    edge_cases: List[str] = []  # Subtle cases that are hard to spot
    
    # Test data
    test_code_locations: List[str]  # Where to find the problems in code
    related_test_cases: List[str] = []  # Test files that expose the problem
    real_world_examples: List[str] = []  # Real CVEs/issues this relates to


# Failure Corpus: 15+ problem categories with expected detections

BROKEN_RETRY_LOGIC = FailureCorpusRepository(
    id="corpus_001",
    name="Broken Exponential Backoff Retry",
    category=FailureCorpusCategory.RETRY_LOGIC,
    description="Exponential backoff that doesn't properly reset, leading to long retry windows",
    framework="FastAPI",
    async_patterns=True,
    external_services=["PostgreSQL", "Redis"],
    problems=[
        "Retry count not reset across different request types",
        "Exponential backoff multiplier persists across failures",
        "No jitter, causing thundering herd",
        "Max backoff not capped",
    ],
    problem_severity="high",
    problem_likelihood_in_production=0.75,
    expected_signals=[
        {"signal": "Retry pattern detected", "confidence_min": 0.85, "files": ["retry_handler.py"]},
        {"signal": "No jitter in backoff", "confidence_min": 0.80, "files": ["retry_handler.py"]},
        {"signal": "Unbounded backoff risk", "confidence_min": 0.75, "files": ["retry_handler.py"]},
    ],
    expected_failure_scenarios=[
        {
            "scenario": "Database temporarily unavailable",
            "trigger": "PostgreSQL connection timeout",
            "propagation_path": ["retry_handler", "connection_pool", "application"],
            "risk_severity": "high",
            "recovery": "Eventual recovery after max retries, but with long delay",
        },
    ],
    adversarial_challenges=[
        "Retry logic might be split across decorator and handler",
        "Backoff calculation might be in separate service",
        "Jitter might be applied elsewhere",
    ],
    hallucination_risks=[
        "Claiming jitter exists when it doesn't",
        "Misidentifying static backoff as exponential",
    ],
    edge_cases=[
        "What happens after max retries on cascade?",
        "How does connection pool behave under retry storm?",
    ],
    test_code_locations=[
        "retry_handler.py:ExponentialBackoff.calculate_wait_time()",
        "retry_handler.py:ConnectionRetryManager.retry()",
    ],
)

DISCONNECTED_AUTH_MIDDLEWARE = FailureCorpusRepository(
    id="corpus_002",
    name="Auth Middleware Disconnected from Service Layer",
    category=FailureCorpusCategory.AUTH_MIDDLEWARE,
    description="Authentication verified in middleware but not re-validated in service, allowing logic bypass",
    framework="FastAPI",
    async_patterns=True,
    external_services=["PostgreSQL"],
    problems=[
        "Auth token validated only in middleware, not in service layer",
        "Permission checks don't match endpoint restrictions",
        "User context can be modified after auth check",
        "No re-validation on sensitive operations",
    ],
    problem_severity="critical",
    problem_likelihood_in_production=0.60,
    expected_signals=[
        {"signal": "Permission verification in middleware", "confidence_min": 0.90, "files": ["middleware/auth.py"]},
        {"signal": "No re-validation in service", "confidence_min": 0.80, "files": ["services/user_service.py"]},
        {"signal": "User context mutable after auth", "confidence_min": 0.75, "files": ["models/context.py"]},
    ],
    expected_failure_scenarios=[
        {
            "scenario": "Privilege escalation via context mutation",
            "trigger": "Authenticated user modifies own permission context",
            "propagation_path": ["request_handler", "service_layer", "database"],
            "risk_severity": "critical",
            "recovery": "Manual audit and permission reset required",
        },
    ],
    adversarial_challenges=[
        "Auth might be split across multiple decorators",
        "Permission model might be complex with roles/scopes",
    ],
    hallucination_risks=[
        "Claiming deep permission checking when there's only surface validation",
    ],
    edge_cases=[
        "What about background jobs that don't go through middleware?",
        "How are permissions checked in batch operations?",
    ],
    test_code_locations=[
        "middleware/auth.py:AuthMiddleware.verify_token()",
        "services/user_service.py:UserService.update_user()",
    ],
)

DEAD_CACHE_LOGIC = FailureCorpusRepository(
    id="corpus_003",
    name="Dead Cache Invalidation Logic",
    category=FailureCorpusCategory.CACHE_LOGIC,
    description="Cache invalidation configured but never triggered, causing stale data issues",
    framework="FastAPI",
    async_patterns=True,
    external_services=["Redis", "PostgreSQL"],
    problems=[
        "Cache invalidation only called in error cases, not success path",
        "TTL set but no active invalidation",
        "Dependent caches not invalidated together",
        "Race condition between write and invalidation",
    ],
    problem_severity="high",
    problem_likelihood_in_production=0.80,
    expected_signals=[
        {"signal": "Cache usage detected", "confidence_min": 0.90, "files": ["cache_manager.py"]},
        {"signal": "Invalidation on write", "confidence_min": 0.70, "files": ["cache_manager.py"]},
        {"signal": "Stale data risk without TTL", "confidence_min": 0.75, "files": ["cache_manager.py"]},
    ],
    expected_failure_scenarios=[
        {
            "scenario": "Cached data becomes stale after update",
            "trigger": "Update succeeds but cache not invalidated",
            "propagation_path": ["write_operation", "cache_miss", "stale_read"],
            "risk_severity": "medium",
            "recovery": "Stale data served until TTL expires or manual intervention",
        },
    ],
    adversarial_challenges=[
        "Invalidation might be async in background task",
        "Cache might be wrapped in abstraction layer",
    ],
    hallucination_risks=[
        "Claiming cache coherency when invalidation is missing",
    ],
    edge_cases=[
        "What about dependent resource caches?",
        "How does read-heavy workload expose stale data?",
    ],
    test_code_locations=[
        "cache_manager.py:CacheManager.set()",
        "cache_manager.py:CacheManager.invalidate()",
    ],
)

INCONSISTENT_VALIDATION = FailureCorpusRepository(
    id="corpus_004",
    name="Inconsistent Input Validation",
    category=FailureCorpusCategory.VALIDATION,
    description="Validation rules differ between endpoints, database models, and service layer",
    framework="FastAPI",
    async_patterns=False,
    external_services=["PostgreSQL"],
    problems=[
        "Request validation in endpoint but different rules in service",
        "Database constraints differ from API validation",
        "Business rules not enforced at all layers",
        "No common validation schema",
    ],
    problem_severity="medium",
    problem_likelihood_in_production=0.85,
    expected_signals=[
        {"signal": "Input validation in routes", "confidence_min": 0.85, "files": ["routes/*.py"]},
        {"signal": "Different validation in services", "confidence_min": 0.75, "files": ["services/*.py"]},
        {"signal": "Validation inconsistency flag", "confidence_min": 0.70, "files": ["models.py"]},
    ],
    expected_failure_scenarios=[
        {
            "scenario": "Invalid data accepted by service but rejected by DB",
            "trigger": "Service layer bypassed with direct DB access",
            "propagation_path": ["endpoint", "service", "database"],
            "risk_severity": "medium",
            "recovery": "Transaction rollback, but user sees inconsistent error",
        },
    ],
    adversarial_challenges=[
        "Validation might be in Pydantic model, service, and database",
    ],
    hallucination_risks=[
        "Claiming consistent validation when rules differ",
    ],
    edge_cases=[
        "What about migrations that change validation rules?",
    ],
    test_code_locations=[
        "models.py:User model validation",
        "services/user_service.py:validate_user_data()",
    ],
)

ASYNC_RACE_CONDITION = FailureCorpusRepository(
    id="corpus_005",
    name="Async Race Condition in Concurrent Requests",
    category=FailureCorpusCategory.ASYNC_RACE,
    description="Concurrent async operations race on shared state without proper synchronization",
    framework="FastAPI",
    async_patterns=True,
    external_services=["PostgreSQL", "Redis"],
    problems=[
        "Multiple awaits accessing same resource without locking",
        "Shared state modified in concurrent handlers",
        "Database operations not serialized when needed",
        "Cache read-then-write pattern without atomicity",
    ],
    problem_severity="high",
    problem_likelihood_in_production=0.70,
    expected_signals=[
        {"signal": "Concurrent async handlers", "confidence_min": 0.85, "files": ["routes/*.py"]},
        {"signal": "Shared state access without locking", "confidence_min": 0.80, "files": ["services/*.py"]},
        {"signal": "Race condition risk", "confidence_min": 0.75, "files": ["handlers.py"]},
    ],
    expected_failure_scenarios=[
        {
            "scenario": "Lost update in concurrent requests",
            "trigger": "Two concurrent requests read-modify-write same resource",
            "propagation_path": ["request_handler_1", "request_handler_2", "shared_state"],
            "risk_severity": "high",
            "recovery": "Data inconsistency, requires manual correction",
        },
    ],
    adversarial_challenges=[
        "Locking might be implemented via database transactions (hard to detect)",
        "Race might only manifest under high load",
    ],
    hallucination_risks=[
        "Claiming proper synchronization when there's just sequential logic",
    ],
    edge_cases=[
        "What about distributed systems with multiple processes?",
        "How does this interact with background tasks?",
    ],
    test_code_locations=[
        "handlers.py:handle_concurrent_update()",
        "services/transaction_service.py:update_with_concurrency()",
    ],
)

MISSING_TIMEOUT_HANDLING = FailureCorpusRepository(
    id="corpus_006",
    name="Missing Timeout on External Service Calls",
    category=FailureCorpusCategory.TIMEOUT,
    description="Calls to external services (API, DB, cache) without timeout configuration",
    framework="FastAPI",
    async_patterns=True,
    external_services=["PostgreSQL", "Redis", "External API"],
    problems=[
        "Database queries without timeout",
        "HTTP requests to external APIs with no timeout",
        "Cache operations without timeout",
        "Cumulative timeouts in request chain",
    ],
    problem_severity="high",
    problem_likelihood_in_production=0.90,
    expected_signals=[
        {"signal": "External service calls", "confidence_min": 0.90, "files": ["services/*.py"]},
        {"signal": "No timeout configuration", "confidence_min": 0.85, "files": ["services/*.py", "db/*.py"]},
        {"signal": "Unbounded wait risk", "confidence_min": 0.80, "files": ["services/*.py"]},
    ],
    expected_failure_scenarios=[
        {
            "scenario": "Slow external service blocks entire application",
            "trigger": "External API hangs or is unreachable",
            "propagation_path": ["endpoint", "service", "external_call", "waiting"],
            "risk_severity": "critical",
            "recovery": "Server eventually times out at OS level after 30min+",
        },
    ],
    adversarial_challenges=[
        "Timeout might be set at library level (aiohttp defaults)",
        "Timeout might be different for different operations",
    ],
    hallucination_risks=[
        "Claiming timeout exists when it's just the default",
    ],
    edge_cases=[
        "What about connection pool timeout vs request timeout?",
        "How do timeouts cascade in dependent calls?",
    ],
    test_code_locations=[
        "services/external_api.py:make_request()",
        "db/connection.py:execute_query()",
    ],
)

DUPLICATED_SERVICE_LOGIC = FailureCorpusRepository(
    id="corpus_007",
    name="Duplicated Service Logic Across Endpoints",
    category=FailureCorpusCategory.DUPLICATION,
    description="Business logic duplicated in multiple endpoints instead of centralized in service",
    framework="FastAPI",
    async_patterns=False,
    external_services=["PostgreSQL"],
    problems=[
        "Create/update logic duplicated across endpoints",
        "Validation rules copy-pasted in multiple places",
        "Error handling different per endpoint",
        "Changes require multiple updates",
    ],
    problem_severity="medium",
    problem_likelihood_in_production=0.95,
    expected_signals=[
        {"signal": "Logic duplication detected", "confidence_min": 0.80, "files": ["routes/*.py"]},
        {"signal": "Multiple implementations of same operation", "confidence_min": 0.75, "files": ["routes/*.py"]},
    ],
    expected_failure_scenarios=[
        {
            "scenario": "Inconsistent behavior across endpoints",
            "trigger": "Bug fix applied to one endpoint but not others",
            "propagation_path": ["endpoint_1", "endpoint_2", "divergent_logic"],
            "risk_severity": "medium",
            "recovery": "Manual discovery and multi-endpoint patch",
        },
    ],
    adversarial_challenges=[
        "Duplication might be in helper functions (harder to detect)",
    ],
    hallucination_risks=[],
    edge_cases=[
        "What about intentional variations?",
    ],
    test_code_locations=[
        "routes/users.py:create_user()",
        "routes/admin.py:create_admin_user()",
    ],
)

WEAK_ERROR_PROPAGATION = FailureCorpusRepository(
    id="corpus_008",
    name="Weak Error Propagation Through Layers",
    category=FailureCorpusCategory.ERROR_PROPAGATION,
    description="Errors caught and swallowed instead of propagated with context",
    framework="FastAPI",
    async_patterns=True,
    external_services=["PostgreSQL"],
    problems=[
        "Try-except blocks that catch all exceptions silently",
        "Errors logged but not raised",
        "Error context lost in exception handler",
        "Generic 500 errors with no details",
    ],
    problem_severity="high",
    problem_likelihood_in_production=0.75,
    expected_signals=[
        {"signal": "Broad exception handlers", "confidence_min": 0.85, "files": ["handlers.py"]},
        {"signal": "Error swallowing pattern", "confidence_min": 0.80, "files": ["services/*.py"]},
        {"signal": "Missing error context", "confidence_min": 0.75, "files": ["error_handlers.py"]},
    ],
    expected_failure_scenarios=[
        {
            "scenario": "Database error silently ignored, stale data served",
            "trigger": "Database write fails but error is caught",
            "propagation_path": ["request", "database_write", "exception_caught", "silent_failure"],
            "risk_severity": "high",
            "recovery": "Data inconsistency, no logging of what happened",
        },
    ],
    adversarial_challenges=[
        "Errors might be re-raised after logging (correct pattern)",
    ],
    hallucination_risks=[
        "Claiming error propagation when it's just logged",
    ],
    edge_cases=[
        "What about expected errors that should be caught?",
    ],
    test_code_locations=[
        "error_handlers.py:handle_exception()",
        "services/user_service.py:try-except blocks",
    ],
)

MISSING_FALLBACK_MECHANISMS = FailureCorpusRepository(
    id="corpus_009",
    name="Missing Fallback for Degraded Service",
    category=FailureCorpusCategory.FALLBACK,
    description="No fallback strategy when dependent service fails",
    framework="FastAPI",
    async_patterns=True,
    external_services=["PostgreSQL", "Redis", "Search Service"],
    problems=[
        "Search service down = entire API down",
        "Cache failure causes direct DB hammer",
        "No circuit breaker pattern",
        "No graceful degradation",
    ],
    problem_severity="high",
    problem_likelihood_in_production=0.80,
    expected_signals=[
        {"signal": "Dependency on external service", "confidence_min": 0.90, "files": ["services/*.py"]},
        {"signal": "No fallback pattern", "confidence_min": 0.80, "files": ["services/*.py"]},
        {"signal": "Cascading failure risk", "confidence_min": 0.75, "files": ["services/*.py"]},
    ],
    expected_failure_scenarios=[
        {
            "scenario": "External service failure cascades to application",
            "trigger": "Redis/Search service becomes unavailable",
            "propagation_path": ["search_request", "external_service_down", "application_degraded"],
            "risk_severity": "high",
            "recovery": "Wait for external service recovery or manual intervention",
        },
    ],
    adversarial_challenges=[
        "Fallback might be implicit (return empty results)",
    ],
    hallucination_risks=[],
    edge_cases=[
        "What about partial degradation?",
    ],
    test_code_locations=[
        "services/search_service.py:search()",
        "handlers/search_handler.py:handle_search()",
    ],
)

STATE_CONSISTENCY_VIOLATION = FailureCorpusRepository(
    id="corpus_010",
    name="State Consistency Violation Across Microservices",
    category=FailureCorpusCategory.STATE_CONSISTENCY,
    description="Updates to state in multiple services not kept in sync",
    framework="FastAPI",
    async_patterns=True,
    external_services=["PostgreSQL", "Message Queue"],
    problems=[
        "Service A updates state, message send fails",
        "Service B doesn't receive update notification",
        "No distributed transaction coordination",
        "No compensating transactions",
    ],
    problem_severity="critical",
    problem_likelihood_in_production=0.65,
    expected_signals=[
        {"signal": "Multiple service dependency", "confidence_min": 0.90, "files": ["services/*.py"]},
        {"signal": "Async state update pattern", "confidence_min": 0.85, "files": ["services/*.py"]},
        {"signal": "No transaction coordination", "confidence_min": 0.80, "files": ["services/*.py"]},
    ],
    expected_failure_scenarios=[
        {
            "scenario": "Distributed transaction partially completes",
            "trigger": "Service A succeeds, Service B fails to receive update",
            "propagation_path": ["update_request", "service_a_updated", "message_send_fails", "service_b_stale"],
            "risk_severity": "critical",
            "recovery": "Manual reconciliation between services",
        },
    ],
    adversarial_challenges=[
        "Transaction might be wrapped in saga pattern (harder to detect)",
    ],
    hallucination_risks=[],
    edge_cases=[
        "What about eventual consistency guarantees?",
    ],
    test_code_locations=[
        "services/order_service.py:update_order()",
        "services/inventory_service.py:update_inventory()",
    ],
)

# Additional failure modes from expanded corpus

RETRY_EXHAUSTION_WITHOUT_BACKOFF = FailureCorpusRepository(
    id="corpus_retry_exhaustion",
    name="Retry Exhaustion Without Exponential Backoff",
    category=FailureCorpusCategory.RETRY_LOGIC,
    description="Retry logic retries immediately in tight loop without backoff, exhausting downstream resources",
    
    framework="FastAPI",
    async_patterns=True,
    external_services=["PostgreSQL", "Redis"],
    
    problems=[
        "Retry attempts made immediately without delay",
        "No exponential backoff multiplier",
        "Retry count limit too high (100+)",
        "Upstream service gets hammered during outage",
    ],
    problem_severity="HIGH",
    problem_likelihood_in_production=0.85,
    
    expected_signals=[
        {"name": "tight_retry_loop", "confidence": 0.9},
        {"name": "missing_backoff_strategy", "confidence": 0.85},
        {"name": "high_retry_attempt_count", "confidence": 0.8},
    ],
    
    expected_failure_scenarios=[
        {"name": "connection_pool_exhaustion", "severity": "HIGH"},
        {"name": "cascading_timeout_storm", "severity": "CRITICAL"},
        {"name": "load_spike_on_upstream", "severity": "HIGH"},
    ],
    
    expected_viva_targets=[
        {"question": "How does your retry mechanism handle exponential backoff?"},
        {"question": "What's the maximum retry count and total timeout you enforce?"},
        {"question": "Have you tested retry behavior under database outage?"},
    ],
    
    hallucination_risks=[],
    edge_cases=[
        "What if backoff exceeds total timeout?",
        "Circuit breaker vs retry backoff interaction",
    ],
    test_code_locations=[
        "services/database_client.py:execute_with_retry()",
        "handlers/retry_policy.py:apply_retry()",
    ],
)

STALE_CACHE_WITHOUT_TTL = FailureCorpusRepository(
    id="corpus_stale_cache",
    name="Stale Cache Without TTL or Invalidation",
    category=FailureCorpusCategory.CACHE_LOGIC,
    description="Cache entries remain indefinitely without TTL or invalidation mechanism",
    
    framework="FastAPI",
    async_patterns=False,
    external_services=["Redis"],
    
    problems=[
        "Cache entries have no TTL (time to live)",
        "No invalidation mechanism when source data changes",
        "Manual cache clear operations are inconsistent",
        "No versioning of cached data",
    ],
    problem_severity="HIGH",
    problem_likelihood_in_production=0.8,
    
    expected_signals=[
        {"name": "cache_without_ttl", "confidence": 0.9},
        {"name": "missing_cache_invalidation", "confidence": 0.85},
        {"name": "unbounded_cache_lifetime", "confidence": 0.8},
    ],
    
    expected_failure_scenarios=[
        {"name": "stale_user_profile", "severity": "MEDIUM"},
        {"name": "permission_divergence", "severity": "HIGH"},
        {"name": "config_change_not_propagated", "severity": "HIGH"},
    ],
    
    expected_viva_targets=[
        {"question": "What's your cache TTL strategy and how is it enforced?"},
        {"question": "How do you handle cache invalidation on source data changes?"},
        {"question": "What's your plan if cache and database diverge?"},
    ],
    
    hallucination_risks=[],
    edge_cases=[
        "TTL too short causes cache thrashing",
        "TTL too long causes stale data",
    ],
    test_code_locations=[
        "services/cache_layer.py:get_cached()",
        "services/cache_layer.py:set_cached()",
    ],
)

SILENT_EXCEPTION_IN_BACKGROUND_TASK = FailureCorpusRepository(
    id="corpus_silent_exception",
    name="Silent Exception Swallowing in Background Task",
    category=FailureCorpusCategory.ERROR_PROPAGATION,
    description="Background task exceptions are caught and swallowed without logging or alerting",
    
    framework="FastAPI",
    async_patterns=True,
    external_services=["RabbitMQ"],
    
    problems=[
        "Background tasks have broad exception handlers",
        "Exceptions logged at debug level (never read)",
        "No alert on task failure",
        "No dead-letter queue for failed messages",
        "Task failure doesn't propagate to monitoring",
    ],
    problem_severity="CRITICAL",
    problem_likelihood_in_production=0.9,
    
    expected_signals=[
        {"name": "broad_exception_handler", "confidence": 0.85},
        {"name": "no_error_alerting", "confidence": 0.8},
        {"name": "no_dead_letter_queue", "confidence": 0.75},
    ],
    
    expected_failure_scenarios=[
        {"name": "silent_email_failure", "severity": "CRITICAL"},
        {"name": "lost_notifications", "severity": "CRITICAL"},
        {"name": "unrecorded_billing", "severity": "CRITICAL"},
    ],
    
    expected_viva_targets=[
        {"question": "How do you monitor background task failures?"},
        {"question": "What happens when a task fails - is it retried or logged?"},
        {"question": "How would you detect 1000 failed notifications?"},
    ],
    
    hallucination_risks=[],
    edge_cases=[
        "Distinguishing transient from permanent failures",
        "Retry strategy for background tasks",
    ],
    test_code_locations=[
        "background_tasks.py:send_email_task()",
        "background_tasks.py:process_notification()",
    ],
)

BROKEN_MIDDLEWARE_ORDERING = FailureCorpusRepository(
    id="corpus_middleware_order",
    name="Broken Middleware Ordering and Execution",
    category=FailureCorpusCategory.AUTH_MIDDLEWARE,
    description="Middleware executes in wrong order, causing auth/validation to be skipped or applied out of sequence",
    
    framework="FastAPI",
    async_patterns=False,
    external_services=[],
    
    problems=[
        "Middleware ordered such that auth runs after business logic",
        "Validation middleware runs after transformation",
        "Logging middleware before rate limiting",
        "Error handling middleware doesn't catch errors from other middleware",
    ],
    problem_severity="HIGH",
    problem_likelihood_in_production=0.75,
    
    expected_signals=[
        {"name": "middleware_execution_order_issue", "confidence": 0.85},
        {"name": "auth_after_business_logic", "confidence": 0.8},
        {"name": "validation_order_dependency", "confidence": 0.75},
    ],
    
    expected_failure_scenarios=[
        {"name": "auth_bypass", "severity": "CRITICAL"},
        {"name": "invalid_data_accepted", "severity": "HIGH"},
        {"name": "rate_limit_ineffective", "severity": "MEDIUM"},
    ],
    
    expected_viva_targets=[
        {"question": "What's your middleware execution order and why?"},
        {"question": "How do you ensure auth middleware runs before business logic?"},
        {"question": "Have you documented middleware dependencies?"},
    ],
    
    hallucination_risks=[],
    edge_cases=[
        "Conditional middleware execution",
        "Middleware that modifies request context",
    ],
    test_code_locations=[
        "main.py:app.add_middleware()",
        "middleware/__init__.py",
    ],
)

CASCADING_DEPENDENCY_FAILURE = FailureCorpusRepository(
    id="corpus_cascading_deps",
    name="Cascading Dependency Failure Without Circuit Breaker",
    category=FailureCorpusCategory.CASCADING_FAILURE,
    description="Service A depends on B, B depends on C; when C fails, B times out, then A gets overwhelmed",
    
    framework="FastAPI",
    async_patterns=True,
    external_services=["ServiceB", "ServiceC", "PostgreSQL"],
    
    problems=[
        "No circuit breaker between services",
        "Timeout configured independently per service",
        "No timeout escalation strategy",
        "Falling back to stale data not implemented",
        "Requests queue up waiting for failing downstream service",
    ],
    problem_severity="CRITICAL",
    problem_likelihood_in_production=0.88,
    
    expected_signals=[
        {"name": "cascading_timeout_pattern", "confidence": 0.9},
        {"name": "no_circuit_breaker", "confidence": 0.85},
        {"name": "request_queue_backpressure", "confidence": 0.8},
    ],
    
    expected_failure_scenarios=[
        {"name": "connection_pool_exhaustion", "severity": "CRITICAL"},
        {"name": "timeout_accumulation", "severity": "CRITICAL"},
        {"name": "cascading_service_failure", "severity": "CRITICAL"},
    ],
    
    expected_viva_targets=[
        {"question": "How do you handle cascading failures across dependencies?"},
        {"question": "What's your circuit breaker strategy?"},
        {"question": "How do you set timeout values considering dependency chains?"},
        {"question": "What fallback mechanisms exist when downstream fails?"},
    ],
    
    hallucination_risks=[],
    edge_cases=[
        "Partial failure of dependent service",
        "Degraded mode with partial fallback",
    ],
    test_code_locations=[
        "services/service_client.py:call_service_b()",
        "services/service_b_client.py:call_service_c()",
    ],
)

# Container for all failure corpus repositories
FAILURE_CORPUS = [
    BROKEN_RETRY_LOGIC,
    DISCONNECTED_AUTH_MIDDLEWARE,
    DEAD_CACHE_LOGIC,
    INCONSISTENT_VALIDATION,
    ASYNC_RACE_CONDITION,
    MISSING_TIMEOUT_HANDLING,
    DUPLICATED_SERVICE_LOGIC,
    WEAK_ERROR_PROPAGATION,
    MISSING_FALLBACK_MECHANISMS,
    STATE_CONSISTENCY_VIOLATION,
    RETRY_EXHAUSTION_WITHOUT_BACKOFF,
    STALE_CACHE_WITHOUT_TTL,
    SILENT_EXCEPTION_IN_BACKGROUND_TASK,
    BROKEN_MIDDLEWARE_ORDERING,
    CASCADING_DEPENDENCY_FAILURE,
]

def get_corpus_by_category(category: FailureCorpusCategory) -> Optional[FailureCorpusRepository]:
    """Get corpus repository by failure category"""
    for repo in FAILURE_CORPUS:
        if repo.category == category:
            return repo
    return None

def get_corpus_by_severity(severity: str) -> List[FailureCorpusRepository]:
    """Get all corpus repositories of a given severity level"""
    return [repo for repo in FAILURE_CORPUS if repo.problem_severity == severity]

def get_corpus_by_framework(framework: str) -> List[FailureCorpusRepository]:
    """Get corpus repositories for a specific framework"""
    return [repo for repo in FAILURE_CORPUS if repo.framework == framework]
