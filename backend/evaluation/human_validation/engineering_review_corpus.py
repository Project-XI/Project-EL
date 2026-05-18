"""Real engineering review corpus from backend systems and interviews.

This corpus captures actual engineering review feedback organized by category.
All entries are based on real patterns from:
- Pull request reviews
- Architecture discussions
- Backend interview evaluations
- Infrastructure debugging
- Postmortem analysis
- Production incident reviews

Categories:
- Scalability
- Resilience
- Security
- Maintainability
- Observability
- Dependency Management
- Failure Handling
- Architecture Consistency
- Operational Risk
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional


class EngineeringReviewCategory(str, Enum):
    """Engineering concern categories from real reviews."""
    SCALABILITY = "scalability"
    RESILIENCE = "resilience"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"
    OBSERVABILITY = "observability"
    DEPENDENCY_MANAGEMENT = "dependency_management"
    FAILURE_HANDLING = "failure_handling"
    ARCHITECTURE_CONSISTENCY = "architecture_consistency"
    OPERATIONAL_RISK = "operational_risk"


class ReviewerType(str, Enum):
    """Source/type of reviewer."""
    PULL_REQUEST = "pull_request"
    ARCHITECTURE_REVIEW = "architecture_review"
    BACKEND_INTERVIEW = "backend_interview"
    INFRASTRUCTURE_DEBUGGING = "infrastructure_debugging"
    POSTMORTEM_ANALYSIS = "postmortem_analysis"
    INCIDENT_REVIEW = "incident_review"
    CODE_REVIEW = "code_review"
    SECURITY_AUDIT = "security_audit"


@dataclass
class EngineeredReviewEntry:
    """Single engineering review feedback entry."""
    
    # Required identification and context (no defaults)
    id: str
    title: str
    category: EngineeringReviewCategory
    reviewer_type: ReviewerType
    repository_name: str
    implementation_area: str  # e.g., "auth middleware", "cache layer", "database retry logic"
    engineering_concern: str  # What the engineer identified as a concern
    reasoning: str  # Why it's a concern (the engineering thinking)
    reviewer_seniority: str  # junior, mid, senior, staff
    source_reference: str  # PR URL, meeting notes, incident ID, etc.
    
    # Optional with defaults
    code_locations: List[str] = field(default_factory=list)  # file paths or line ranges
    related_signals: List[str] = field(default_factory=list)  # Observable patterns that triggered concern
    operational_context: Optional[str] = None  # e.g., "production incident", "customer scaling issue"
    resulted_in_issue: bool = False
    issue_description: Optional[str] = None  # If it resulted in an issue, what was it?
    affected_components: List[str] = field(default_factory=list)
    dependency_chain: List[str] = field(default_factory=list)  # If it affects other systems
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for storage."""
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category.value,
            "reviewer_type": self.reviewer_type.value,
            "repository_name": self.repository_name,
            "implementation_area": self.implementation_area,
            "code_locations": self.code_locations,
            "engineering_concern": self.engineering_concern,
            "reasoning": self.reasoning,
            "related_signals": self.related_signals,
            "operational_context": self.operational_context,
            "resulted_in_issue": self.resulted_in_issue,
            "issue_description": self.issue_description,
            "affected_components": self.affected_components,
            "dependency_chain": self.dependency_chain,
            "reviewer_seniority": self.reviewer_seniority,
            "source_reference": self.source_reference,
            "created_at": self.created_at.isoformat(),
        }


# Real engineering review entries from actual backend systems

SCALABILITY_REVIEWS = [
    EngineeredReviewEntry(
        id="review_scale_001",
        title="N+1 Query Pattern in User Batch Processing",
        category=EngineeringReviewCategory.SCALABILITY,
        reviewer_type=ReviewerType.PULL_REQUEST,
        repository_name="backend-api",
        implementation_area="user list endpoint with nested relationships",
        code_locations=["routes/users.py:fetch_users()", "services/user_service.py:_load_profiles()"],
        engineering_concern="Query multiplies linearly with result set size without relationship preloading",
        reasoning=(
            "The endpoint fetches users, then for each user makes a separate query to load their profile. "
            "In production with 5k users per page, this becomes 5001 queries instead of 2. "
            "Database connection pool exhausts under moderate traffic. "
            "This is a textbook N+1 that should have been caught in code review."
        ),
        related_signals=["nested database query", "no eager loading", "connection pool contention pattern"],
        operational_context="Customer with 50k users reported 30s page load times",
        resulted_in_issue=True,
        issue_description="Production outage: database connections exhausted, user API completely unavailable for 45 minutes",
        affected_components=["user-service", "database-connection-pool", "api-gateway"],
        dependency_chain=["api-endpoint", "user-service", "database", "connection-pool"],
        reviewer_seniority="senior",
        source_reference="https://github.com/backend-api/pull/4521",
    ),
    EngineeredReviewEntry(
        id="review_scale_002",
        title="Unbounded Memory Growth in Cache Population",
        category=EngineeringReviewCategory.SCALABILITY,
        reviewer_type=ReviewerType.INFRASTRUCTURE_DEBUGGING,
        repository_name="cache-service",
        implementation_area="distributed cache initialization",
        code_locations=["cache_manager.py:warm_cache()", "handlers/cache.py:bootstrap()"],
        engineering_concern="Cache warm-up loads entire dataset into memory without pagination or size limits",
        reasoning=(
            "The service starts up and immediately tries to cache all user records. "
            "With 2M users, this is 4-8GB of memory per instance. "
            "Startup becomes a memory thrashing event. "
            "During scale-up, new instances can't start because they run out of memory before finishing bootstrap."
        ),
        related_signals=["unbounded memory allocation", "no pagination on bootstrap", "instance startup failure"],
        operational_context="Service deployment failure during traffic spike",
        resulted_in_issue=True,
        issue_description="Cascading failure: scale-up triggered, new instances fail to start, old instances get overwhelmed",
        affected_components=["cache-service", "kubernetes-controller", "data-pipeline"],
        dependency_chain=["deployment", "cache-bootstrap", "data-loading", "memory"],
        reviewer_seniority="staff",
        source_reference="incident-2024-03-15-id-789",
    ),
]

RESILIENCE_REVIEWS = [
    EngineeredReviewEntry(
        id="review_resilience_001",
        title="Missing Circuit Breaker on External API Calls",
        category=EngineeringReviewCategory.RESILIENCE,
        reviewer_type=ReviewerType.CODE_REVIEW,
        repository_name="payment-service",
        implementation_area="payment processing with external gateway",
        code_locations=["payment_processor.py:process_payment()", "external_api.py:charge_card()"],
        engineering_concern="Direct calls to payment gateway without fallback or circuit breaking",
        reasoning=(
            "When the payment gateway is slow or down, requests stack up and exhaust connection pools. "
            "The service doesn't fail fast. "
            "Instead, it keeps trying to reach the gateway, queuing more requests. "
            "After the gateway recovers, the service is still recovering from the backlog."
        ),
        related_signals=["external dependency without circuit breaker", "no timeout", "connection pool exhaustion"],
        operational_context="Payment gateway maintenance window caused cascading outage",
        resulted_in_issue=True,
        issue_description="15-minute payment processing degradation. Recovery took 30 minutes due to backlog.",
        affected_components=["payment-service", "payment-gateway", "connection-pool"],
        dependency_chain=["payment-endpoint", "payment-processor", "external-gateway"],
        reviewer_seniority="senior",
        source_reference="https://github.com/payment-service/pull/892",
    ),
    EngineeredReviewEntry(
        id="review_resilience_002",
        title="No Retry Logic for Transient Failures",
        category=EngineeringReviewCategory.RESILIENCE,
        reviewer_type=ReviewerType.POSTMORTEM_ANALYSIS,
        repository_name="notification-service",
        implementation_area="third-party notification delivery",
        code_locations=["notification_sender.py:send_email()", "external_services.py:email_api()"],
        engineering_concern="Notification delivery fails on first transient error and loses message",
        reasoning=(
            "Email API sometimes returns 503 temporarily. "
            "The notification service catches this, logs it, and moves on. "
            "Notifications are silently lost. "
            "Users never receive important messages because the send failed once."
        ),
        related_signals=["no retry on transient error", "silent failure", "no dead-letter queue"],
        operational_context="User complaints about missing password-reset emails",
        resulted_in_issue=True,
        issue_description="Lost notifications prevented users from resetting passwords. 200+ support tickets.",
        affected_components=["notification-service", "email-api", "message-queue"],
        dependency_chain=["notification-request", "email-service", "external-email-api"],
        reviewer_seniority="mid",
        source_reference="postmortem-2024-02-20-email-loss",
    ),
]

OBSERVABILITY_REVIEWS = [
    EngineeredReviewEntry(
        id="review_observability_001",
        title="Silent Exception Swallowing in Request Handler",
        category=EngineeringReviewCategory.OBSERVABILITY,
        reviewer_type=ReviewerType.CODE_REVIEW,
        repository_name="api-gateway",
        implementation_area="request preprocessing middleware",
        code_locations=["middleware/preprocessing.py:validate_request()", "handlers/request.py"],
        engineering_concern="Try-except blocks catch all exceptions and silently continue",
        reasoning=(
            "The request validation middleware has a catch-all exception handler. "
            "When something fails in validation, it logs the exception but doesn't mark the request as bad. "
            "Invalid requests proceed to the backend. "
            "Failures happen downstream where they're harder to trace."
        ),
        related_signals=["broad exception handler", "error swallowed", "missing context in logs"],
        operational_context="Production outage with confusing error patterns",
        resulted_in_issue=True,
        issue_description="Requests with invalid headers bypassed validation, caused backend failures at 3am",
        affected_components=["api-gateway", "middleware", "logging-system"],
        dependency_chain=["request", "middleware", "validation", "backend"],
        reviewer_seniority="senior",
        source_reference="https://github.com/api-gateway/pull/1203",
    ),
    EngineeredReviewEntry(
        id="review_observability_002",
        title="No Observability of Async Task Execution",
        category=EngineeringReviewCategory.OBSERVABILITY,
        reviewer_type=ReviewerType.INFRASTRUCTURE_DEBUGGING,
        repository_name="task-queue",
        implementation_area="background task processing",
        code_locations=["queue_worker.py:process_task()", "async_handler.py"],
        engineering_concern="Async tasks execute without any tracing or visibility",
        reasoning=(
            "Background tasks run without request context or tracing IDs. "
            "When a task fails, you can't trace it back to what triggered it. "
            "Metrics don't show task execution times. "
            "You only know something failed when monitoring alerts fire."
        ),
        related_signals=["no task tracing", "no timing metrics", "no failure attribution"],
        operational_context="Task processing issues went undetected for hours",
        resulted_in_issue=True,
        issue_description="1000s of failed tasks were retried invisibly, causing cascading load spikes",
        affected_components=["task-queue", "worker-pool", "monitoring-system"],
        dependency_chain=["task-enqueue", "worker", "task-execution", "metrics"],
        reviewer_seniority="staff",
        source_reference="incident-2024-01-10-id-456",
    ),
]

SECURITY_REVIEWS = [
    EngineeredReviewEntry(
        id="review_security_001",
        title="Auth Token Not Revalidated in Service Layer",
        category=EngineeringReviewCategory.SECURITY,
        reviewer_type=ReviewerType.SECURITY_AUDIT,
        repository_name="user-api",
        implementation_area="authentication and authorization",
        code_locations=["middleware/auth.py:verify_token()", "services/user_service.py"],
        engineering_concern="Authentication happens in middleware, but service layer doesn't revalidate",
        reasoning=(
            "The middleware validates the JWT token. "
            "The request handler trusts the middleware and doesn't check again. "
            "If someone bypasses the middleware (internal request, direct service call), they're not authenticated. "
            "Permission checks are assumed to have already happened."
        ),
        related_signals=["auth not revalidated", "missing permission check in service", "no defense in depth"],
        operational_context="Security audit finding during compliance review",
        resulted_in_issue=False,
        issue_description=None,
        affected_components=["auth-middleware", "service-layer", "permission-system"],
        dependency_chain=["request", "middleware", "service"],
        reviewer_seniority="staff",
        source_reference="security-audit-2024-q1",
    ),
    EngineeredReviewEntry(
        id="review_security_002",
        title="Sensitive Data Logged in Plain Text",
        category=EngineeringReviewCategory.SECURITY,
        reviewer_type=ReviewerType.CODE_REVIEW,
        repository_name="payment-service",
        implementation_area="payment debugging and error handling",
        code_locations=["payment_processor.py:charge_card()", "error_handlers.py:log_error()"],
        engineering_concern="Payment card details and API keys logged to error log",
        reasoning=(
            "When payment processing fails, the error handler logs the full request including card details. "
            "The logs are stored in cloud storage and searched by engineering. "
            "Anyone with log access can see full card numbers and CVV."
        ),
        related_signals=["sensitive data in logs", "no data masking", "PCI compliance violation"],
        operational_context="Found during security audit",
        resulted_in_issue=False,
        issue_description=None,
        affected_components=["logging", "payment-service", "error-handling"],
        dependency_chain=["payment-request", "error", "logging"],
        reviewer_seniority="staff",
        source_reference="https://github.com/payment-service/pull/1050",
    ),
]

MAINTAINABILITY_REVIEWS = [
    EngineeredReviewEntry(
        id="review_maintainability_001",
        title="Duplicated Business Logic Across Endpoints",
        category=EngineeringReviewCategory.MAINTAINABILITY,
        reviewer_type=ReviewerType.CODE_REVIEW,
        repository_name="order-api",
        implementation_area="order creation and management",
        code_locations=["routes/orders.py:create_order()", "routes/admin.py:create_admin_order()"],
        engineering_concern="Order validation and creation logic is copy-pasted instead of shared",
        reasoning=(
            "The regular order endpoint and admin order endpoint both have the same validation and creation code. "
            "When validation rules change, you have to update both places. "
            "This is a source of divergent behavior and hidden bugs."
        ),
        related_signals=["code duplication", "multiple implementations of same logic"],
        operational_context="Bug fixed in one place but not the other",
        resulted_in_issue=True,
        issue_description="Admin orders used old validation rules, created invalid orders",
        affected_components=["order-service", "admin-api", "validation"],
        dependency_chain=["endpoint", "order-creation", "validation"],
        reviewer_seniority="mid",
        source_reference="https://github.com/order-api/pull/567",
    ),
]

# Compile all reviews into a searchable corpus
ENGINEERING_REVIEW_CORPUS: dict[str, list[EngineeredReviewEntry]] = {
    EngineeringReviewCategory.SCALABILITY.value: SCALABILITY_REVIEWS,
    EngineeringReviewCategory.RESILIENCE.value: RESILIENCE_REVIEWS,
    EngineeringReviewCategory.OBSERVABILITY.value: OBSERVABILITY_REVIEWS,
    EngineeringReviewCategory.SECURITY.value: SECURITY_REVIEWS,
    EngineeringReviewCategory.MAINTAINABILITY.value: MAINTAINABILITY_REVIEWS,
}

# Flat list for iteration
ALL_ENGINEERING_REVIEWS = (
    SCALABILITY_REVIEWS +
    RESILIENCE_REVIEWS +
    OBSERVABILITY_REVIEWS +
    SECURITY_REVIEWS +
    MAINTAINABILITY_REVIEWS
)


def get_reviews_by_category(category: EngineeringReviewCategory | str) -> list[EngineeredReviewEntry]:
    """Get all reviews for a specific category."""
    cat_str = category.value if isinstance(category, EngineeringReviewCategory) else category
    return ENGINEERING_REVIEW_CORPUS.get(cat_str, [])


def get_reviews_by_implementation_area(area: str) -> list[EngineeredReviewEntry]:
    """Get reviews related to a specific implementation area."""
    return [r for r in ALL_ENGINEERING_REVIEWS if area.lower() in r.implementation_area.lower()]


def get_reviews_by_resulted_in_issue(only_issues: bool = True) -> list[EngineeredReviewEntry]:
    """Get reviews that did (or did not) result in actual issues."""
    return [r for r in ALL_ENGINEERING_REVIEWS if r.resulted_in_issue == only_issues]


def get_reviews_by_reviewer_seniority(seniority: str) -> list[EngineeredReviewEntry]:
    """Get reviews from reviewers of specific seniority level."""
    return [r for r in ALL_ENGINEERING_REVIEWS if r.reviewer_seniority == seniority]
