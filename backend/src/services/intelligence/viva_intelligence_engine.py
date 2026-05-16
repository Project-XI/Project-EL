from typing import List, Dict, Any
from ...models.context import VivaTarget, InconsistencyFlag, EvidenceModel

class VivaIntelligenceEngine:
    """
    Generates deep engineering viva questions across six categories:
    Architecture, Tradeoff, Security, Scalability, Failure-Path, Runtime.
    """

    @staticmethod
    def generate_targets(detections: Dict[str, Any], arch: EvidenceModel) -> List[VivaTarget]:
        targets = []
        arch_val = arch.value if arch.value else ""

        has_fastapi   = any("FastAPI"   in str(m.value) for m in detections.values())
        has_express   = any("Express"   in str(m.value) for m in detections.values())
        has_react     = any("React"     in str(m.value) for m in detections.values())
        has_sql       = any("SQL"       in str(m.value) for m in detections.values())
        has_mongo     = any("Mongo"     in str(m.value) for m in detections.values())
        has_jwt       = any("JWT"       in str(m.value) or "jwt" in str(m.value) for m in detections.values())
        has_auth      = any("Auth"      in str(m.value) for m in detections.values())
        has_redis     = any("Redis"     in str(m.value) for m in detections.values())
        has_rest      = "REST" in arch_val
        has_micro     = "Microservice" in arch_val

        # ── Architecture ─────────────────────────────────────────────────────
        if has_rest:
            targets.append(VivaTarget(
                topic="Architecture",
                question_target="REST Architectural Constraints",
                difficulty="medium",
                importance_score=0.8,
                focus="Explain each REST constraint (statelessness, uniform interface, layered system) and demonstrate where in this codebase each constraint is satisfied or violated.",
                category="Architecture",
                depth_score=7.5,
                related_node="api_gateway",
                confidence=0.9,
                reasoning_summary="REST API structure detected via route handler patterns in the codebase."
            ))

        if has_micro:
            targets.append(VivaTarget(
                topic="Architecture",
                question_target="Microservices Boundary Design",
                difficulty="hard",
                importance_score=0.9,
                focus="How are service boundaries defined in this system? Walk through the inter-service communication contract and explain how the team would handle eventual consistency.",
                category="Architecture",
                depth_score=9.0,
                related_node="service_layer",
                confidence=0.85,
                reasoning_summary="Microservices pattern inferred from multi-service structure."
            ))

        if has_fastapi:
            targets.append(VivaTarget(
                topic="Architecture",
                question_target="FastAPI Dependency Injection Graph",
                difficulty="medium",
                importance_score=0.85,
                focus="Trace the full FastAPI dependency injection chain from a request entry point to database access. What happens if a dependency resolver raises an exception mid-chain?",
                category="Architecture",
                depth_score=8.0,
                related_node="route_handler",
                confidence=0.95,
                reasoning_summary="FastAPI detected as backend framework; DI patterns are idiomatic to this framework."
            ))

        # ── Tradeoff ──────────────────────────────────────────────────────────
        if has_sql and has_mongo:
            targets.append(VivaTarget(
                topic="Tradeoffs",
                question_target="Polyglot Persistence Decision",
                difficulty="hard",
                importance_score=0.9,
                focus="This architecture uses both a relational and document database. Justify why polyglot persistence was chosen, what the synchronisation strategy is, and what the failure mode is when one store becomes unavailable.",
                category="Tradeoff",
                depth_score=9.2,
                related_node="db_layer",
                confidence=0.88,
                reasoning_summary="Both SQL and MongoDB signals detected simultaneously."
            ))
        elif has_sql:
            targets.append(VivaTarget(
                topic="Tradeoffs",
                question_target="Relational DB vs NoSQL Selection",
                difficulty="medium",
                importance_score=0.75,
                focus="Given the data models in this system, justify why a relational database was selected. Under what read/write patterns would this decision become a bottleneck?",
                category="Tradeoff",
                depth_score=7.0,
                related_node="db_layer",
                confidence=0.85,
                reasoning_summary="SQL-based database detected in dependency graph."
            ))

        if has_fastapi and has_react:
            targets.append(VivaTarget(
                topic="Tradeoffs",
                question_target="SPA vs SSR Trade-off",
                difficulty="medium",
                importance_score=0.8,
                focus="This stack uses a React SPA paired with a REST API. Explain the SEO, TTI (time-to-interactive), and caching trade-offs vs a server-side rendered solution for the same data requirements.",
                category="Tradeoff",
                depth_score=7.8,
                related_node="frontend_layer",
                confidence=0.82,
                reasoning_summary="React SPA + FastAPI API detected — classic SPA pattern."
            ))

        # ── Security ──────────────────────────────────────────────────────────
        if has_jwt:
            targets.append(VivaTarget(
                topic="Security",
                question_target="JWT Lifecycle & Revocation",
                difficulty="hard",
                importance_score=0.95,
                focus="JWT tokens are stateless by design. Explain precisely how this implementation handles token revocation before expiry. What attack vectors does this leave open and how are they mitigated?",
                category="Security",
                depth_score=9.5,
                related_node="auth_middleware",
                confidence=0.97,
                reasoning_summary="JWT authentication signals detected in middleware chain."
            ))

        if has_auth:
            targets.append(VivaTarget(
                topic="Security",
                question_target="Authentication Failure Path",
                difficulty="hard",
                importance_score=0.9,
                focus="Walk through the exact code path when an authentication token is expired, tampered with, or absent. Which HTTP status codes are returned and where is the failure logged?",
                category="Security",
                depth_score=8.8,
                related_node="auth_middleware",
                confidence=0.92,
                reasoning_summary="Authentication middleware identified — failure paths are critical security surface."
            ))

        # ── Scalability ───────────────────────────────────────────────────────
        if has_sql:
            targets.append(VivaTarget(
                topic="Scalability",
                question_target="Database Connection Pooling",
                difficulty="medium",
                importance_score=0.8,
                focus="If concurrent requests triple, how does the database connection pool behave? What is the pool size configuration and what happens to requests when the pool is exhausted?",
                category="Scalability",
                depth_score=8.0,
                related_node="db_layer",
                confidence=0.85,
                reasoning_summary="Relational database under load is a primary scalability bottleneck."
            ))

        if has_redis:
            targets.append(VivaTarget(
                topic="Scalability",
                question_target="Cache Eviction & Invalidation Strategy",
                difficulty="hard",
                importance_score=0.85,
                focus="Explain the cache eviction policy configured in Redis for this system. In a multi-instance deployment, how is cache invalidation kept consistent across instances?",
                category="Scalability",
                depth_score=8.5,
                related_node="cache_layer",
                confidence=0.88,
                reasoning_summary="Redis dependency detected — caching strategy is critical for horizontal scaling."
            ))

        if has_fastapi or has_express:
            targets.append(VivaTarget(
                topic="Scalability",
                question_target="Horizontal Scaling & Stateless Design",
                difficulty="medium",
                importance_score=0.78,
                focus="Describe what would need to change to run three instances of this backend in parallel behind a load balancer. Identify any shared state that would break under horizontal scaling.",
                category="Scalability",
                depth_score=7.5,
                related_node="api_gateway",
                confidence=0.80,
                reasoning_summary="Backend API detected — stateless design is a prerequisite for horizontal scaling."
            ))

        # ── Failure-Path ──────────────────────────────────────────────────────
        targets.append(VivaTarget(
            topic="Failure-Path",
            question_target="Cascading Failure Isolation",
            difficulty="hard",
            importance_score=0.85,
            focus="If the database becomes unavailable for 30 seconds, trace the cascade through the system. Which endpoints degrade gracefully and which throw unhandled 500 errors to the client?",
            category="Failure-Path",
            depth_score=9.0,
            related_node="db_layer",
            confidence=0.85,
            reasoning_summary="All systems with database dependencies have this failure vector."
        ))

        if has_jwt or has_auth:
            targets.append(VivaTarget(
                topic="Failure-Path",
                question_target="Auth Service Unavailability",
                difficulty="hard",
                importance_score=0.9,
                focus="If the token validation service is unreachable, what is the fallback behaviour? Does the system fail open or closed, and is this the correct decision for this application's threat model?",
                category="Failure-Path",
                depth_score=9.3,
                related_node="auth_middleware",
                confidence=0.90,
                reasoning_summary="Auth middleware is a high-criticality single point of failure."
            ))

        # ── Runtime Behavior ──────────────────────────────────────────────────
        if has_fastapi:
            targets.append(VivaTarget(
                topic="Runtime",
                question_target="Async vs Sync Route Handlers",
                difficulty="medium",
                importance_score=0.8,
                focus="This codebase uses FastAPI with both async and sync route handlers. Explain the thread-pool implications of mixing sync handlers in an async event loop and identify any blocking I/O calls that could stall the event loop.",
                category="Runtime",
                depth_score=8.2,
                related_node="route_handler",
                confidence=0.88,
                reasoning_summary="FastAPI async patterns require careful sync/async boundary management."
            ))

        if has_express:
            targets.append(VivaTarget(
                topic="Runtime",
                question_target="Node.js Event Loop Blocking",
                difficulty="hard",
                importance_score=0.85,
                focus="Identify any synchronous CPU-bound operations in this Express.js codebase that could block the Node.js event loop. How would you move them off the main thread?",
                category="Runtime",
                depth_score=8.5,
                related_node="route_handler",
                confidence=0.85,
                reasoning_summary="Express.js single-threaded event loop is vulnerable to CPU-bound blocking."
            ))

        from src.services.intelligence.viva_question_ranker import VivaQuestionRanker
        return VivaQuestionRanker.rank_targets(targets)

    @staticmethod
    def detect_inconsistencies(doc_text: str, detections: Dict[str, Any]) -> list:
        flags = []

        if "redis" in doc_text.lower() and not any("redis" in str(m.value).lower() for m in detections.values()):
            from ...models.context import InconsistencyFlag
            flags.append(InconsistencyFlag(
                issue="Redis mentioned in documentation but absent in repository",
                severity="medium",
                confidence=0.85,
                evidence=["'Redis' keyword found in project report", "No Redis dependency or config found in repo."]
            ))

        if "microservices" in doc_text.lower():
            backend_count = sum(1 for k in detections if "backend" in k and detections[k].value != "Unknown")
            if backend_count <= 1:
                from ...models.context import InconsistencyFlag
                flags.append(InconsistencyFlag(
                    issue="Microservices architecture claimed but monolithic structure detected",
                    severity="high",
                    confidence=0.75,
                    evidence=["'Microservices' mentioned in documentation", "Only a single backend service framework detected."]
                ))

        return flags

    @staticmethod
    def detect_complexity_mismatch(arch: EvidenceModel, detections: Dict[str, Any]) -> EvidenceModel:
        if "Microservices" in arch.value and sum(1 for k in detections if detections[k].value != "Unknown") < 3:
            return EvidenceModel(
                value="High Complexity Claim vs Minimal Implementation",
                confidence=0.7,
                evidence=["Complex architecture pattern claimed", "Very few actual technology components detected."]
            )
        return EvidenceModel(value="No major mismatch detected", confidence=1.0, evidence=[])
