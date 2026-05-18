"""
Context-Aware Tradeoff Reasoning Engine: Generates implementation-specific engineering tradeoff analysis.
Moves beyond template-based reasoning to actual implementation context.
"""

from typing import Dict, Any, List
from ...models.context import EvidenceModel, ImplementationReasoning


class ContextAwareTradeoffEngine:
    """
    Generates context-aware tradeoff analysis based on:
    - Actual implementation patterns detected
    - Operational environment and constraints
    - Quality analysis findings
    - Failure scenarios
    - Project purpose and scale expectations
    """

    @staticmethod
    def generate_context_aware_reasoning(
        detections: Dict[str, Any],
        quality_analysis: Dict[str, EvidenceModel],
        context_enrichment: Dict[str, Any],
        failure_analysis: Dict[str, EvidenceModel]
    ) -> List[ImplementationReasoning]:
        """
        Generate sophisticated, context-aware reasoning for detected technologies.
        """
        reasonings = []

        # Analyze backend framework choice
        backend_tech = detections.get("backend_framework")
        if backend_tech:
            reasoning = ContextAwareTradeoffEngine._reason_backend_choice(
                backend_tech, detections, quality_analysis, context_enrichment
            )
            if reasoning:
                reasonings.append(reasoning)

        # Analyze database choice
        db_tech = detections.get("database_used")
        if db_tech:
            reasoning = ContextAwareTradeoffEngine._reason_database_choice(
                db_tech, detections, quality_analysis, context_enrichment
            )
            if reasoning:
                reasonings.append(reasoning)

        # Analyze caching strategy
        cache_quality = quality_analysis.get("cache_management")
        if cache_quality and "No caching" not in cache_quality.value:
            reasoning = ContextAwareTradeoffEngine._reason_caching_strategy(
                detections, quality_analysis, context_enrichment
            )
            if reasoning:
                reasonings.append(reasoning)

        # Analyze authentication approach
        auth_quality = quality_analysis.get("authentication_consistency")
        if auth_quality:
            reasoning = ContextAwareTradeoffEngine._reason_auth_strategy(
                detections, quality_analysis, context_enrichment
            )
            if reasoning:
                reasonings.append(reasoning)

        # Analyze async processing strategy
        resilience_quality = quality_analysis.get("resilience_patterns")
        if resilience_quality:
            reasoning = ContextAwareTradeoffEngine._reason_async_strategy(
                detections, quality_analysis, context_enrichment
            )
            if reasoning:
                reasonings.append(reasoning)

        return reasonings

    @staticmethod
    def _reason_backend_choice(
        backend_tech: EvidenceModel,
        detections: Dict[str, Any],
        quality_analysis: Dict[str, EvidenceModel],
        context_enrichment: Dict[str, Any]
    ) -> ImplementationReasoning:
        """Generate context-aware reasoning for backend framework choice."""
        tech_name = backend_tech.value
        probable_reasoning = []
        confidence = 0.7

        # Get operational context
        scale_expectations = context_enrichment.get("scalability_expectations", {})
        project_purpose = context_enrichment.get("project_purpose", {})

        # FastAPI-specific reasoning
        if "FastAPI" in tech_name:
            probable_reasoning = [
                f"Async I/O capabilities align with {scale_expectations.get('value', 'medium')} scale expectations",
                "Pydantic integration provides type-safe request validation matching quality: " + 
                quality_analysis.get("api_design_quality", EvidenceModel(value="", confidence=0.0, evidence=[])).value,
                "Automatic OpenAPI documentation supports: " + 
                context_enrichment.get("documentation_quality", EvidenceModel(value="", confidence=0.0, evidence=[])).value
            ]
            confidence = 0.85

        # Django-specific reasoning
        elif "Django" in tech_name:
            probable_reasoning = [
                "Full-featured framework chosen over minimalist approach for rapid development",
                "Built-in ORM matches database: " + detections.get("database_used", EvidenceModel(value="Unknown", confidence=0.0, evidence=[])).value,
                "Admin panel and built-in auth support project maturity: " + 
                quality_analysis.get("architecture_separation", EvidenceModel(value="", confidence=0.0, evidence=[])).value
            ]
            confidence = 0.75

        # Express.js-specific reasoning
        elif "Express" in tech_name:
            probable_reasoning = [
                "Minimalist approach allows custom middleware for specific scale needs",
                "Lightweight overhead suits " + context_enrichment.get("operational_environment", {}).get("value", "standard") + " deployments",
                "Flexible routing matches API design quality: " + 
                quality_analysis.get("api_design_quality", EvidenceModel(value="", confidence=0.0, evidence=[])).value
            ]
            confidence = 0.75

        # Spring Boot-specific reasoning
        elif "Spring" in tech_name:
            probable_reasoning = [
                "Enterprise ecosystem matches infrastructure maturity: " + 
                context_enrichment.get("infrastructure_maturity", {}).get("value", "unknown"),
                "Built-in dependency injection supports: " + 
                quality_analysis.get("architecture_separation", EvidenceModel(value="", confidence=0.0, evidence=[])).value,
                "Rich ecosystem for resilience patterns: " + 
                quality_analysis.get("resilience_patterns", EvidenceModel(value="", confidence=0.0, evidence=[])).value
            ]
            confidence = 0.8

        return ImplementationReasoning(
            technology=tech_name,
            probable_reasoning=probable_reasoning,
            confidence=confidence,
            evidence=backend_tech.evidence
        )

    @staticmethod
    def _reason_database_choice(
        db_tech: EvidenceModel,
        detections: Dict[str, Any],
        quality_analysis: Dict[str, EvidenceModel],
        context_enrichment: Dict[str, Any]
    ) -> ImplementationReasoning:
        """Generate context-aware reasoning for database choice."""
        tech_name = db_tech.value
        probable_reasoning = []
        confidence = 0.7

        scale = context_enrichment.get("scalability_expectations", {}).get("value", "unknown")

        # PostgreSQL reasoning
        if "PostgreSQL" in tech_name:
            probable_reasoning = [
                f"ACID compliance chosen for {scale} scale with strict data consistency needs",
                "Complex relational queries support detected architecture: " + 
                quality_analysis.get("architecture_separation", EvidenceModel(value="", confidence=0.0, evidence=[])).value,
                "Advanced features (JSON, full-text search) enable rich queries"
            ]
            confidence = 0.85

        # MongoDB reasoning
        elif "MongoDB" in tech_name:
            probable_reasoning = [
                "Schema flexibility chosen for rapid iteration and evolving data models",
                "Horizontal sharding capability matches: " + scale + " scale expectations",
                "Document model simplifies: " + 
                quality_analysis.get("api_design_quality", EvidenceModel(value="", confidence=0.0, evidence=[])).value + " responses"
            ]
            confidence = 0.75

        # MySQL reasoning
        elif "MySQL" in tech_name:
            probable_reasoning = [
                "Traditional RDBMS chosen for ecosystem maturity and reliability",
                "Wide hosting support in: " + context_enrichment.get("operational_environment", {}).get("value", "standard") + " environments",
                "Suitable for: " + context_enrichment.get("project_purpose", {}).get("value", "general") + " projects"
            ]
            confidence = 0.7

        # Redis reasoning (if listed as primary storage)
        elif "Redis" in tech_name:
            probable_reasoning = [
                f"In-memory store chosen to reduce latency for {scale} concurrent users",
                "Used primarily for: " + 
                quality_analysis.get("cache_management", EvidenceModel(value="", confidence=0.0, evidence=[])).value,
                "Persistence likely handled by secondary database"
            ]
            confidence = 0.65

        return ImplementationReasoning(
            technology=tech_name,
            probable_reasoning=probable_reasoning,
            confidence=confidence,
            evidence=db_tech.evidence
        )

    @staticmethod
    def _reason_caching_strategy(
        detections: Dict[str, Any],
        quality_analysis: Dict[str, EvidenceModel],
        context_enrichment: Dict[str, Any]
    ) -> ImplementationReasoning:
        """Generate context-aware reasoning for caching strategy."""
        cache_quality = quality_analysis.get("cache_management", EvidenceModel(value="", confidence=0.0, evidence=[]))
        probable_reasoning = []
        confidence = 0.7

        scale = context_enrichment.get("scalability_expectations", {}).get("value", "medium")

        if "Redis" in cache_quality.value:
            probable_reasoning = [
                f"Redis reduces repeated database hits for {scale} scale demands",
                "Improves response time for high-frequency endpoints detected in code",
            ]
            
            if "Cache invalidation" in cache_quality.value:
                probable_reasoning.append("Explicit invalidation patterns maintain data freshness")
            else:
                probable_reasoning.append("WARNING: No cache invalidation pattern detected - risk of stale data")
            
            confidence = 0.8

        if "Local caching" in cache_quality.value:
            probable_reasoning.append("In-process caching reduces network latency for frequently accessed data")
            confidence = 0.7

        return ImplementationReasoning(
            technology="Caching Strategy",
            probable_reasoning=probable_reasoning,
            confidence=confidence,
            evidence=cache_quality.evidence
        )

    @staticmethod
    def _reason_auth_strategy(
        detections: Dict[str, Any],
        quality_analysis: Dict[str, EvidenceModel],
        context_enrichment: Dict[str, Any]
    ) -> ImplementationReasoning:
        """Generate context-aware reasoning for authentication approach."""
        auth_quality = quality_analysis.get("authentication_consistency", EvidenceModel(value="", confidence=0.0, evidence=[]))
        probable_reasoning = []
        confidence = 0.7

        if "JWT" in str(detections.get("authentication_system", EvidenceModel(value="", confidence=0.0, evidence=[])).value):
            probable_reasoning = [
                "JWT enables stateless authentication for horizontal scaling",
                "Cross-domain support suits: " + context_enrichment.get("operational_environment", {}).get("value", "standard") + " deployments"
            ]
            
            if "Centralized auth" in auth_quality.value:
                probable_reasoning.append("Centralized middleware ensures consistent token validation across endpoints")
            
            if "RBAC" in auth_quality.value:
                probable_reasoning.append("Role-based access control provides granular permission management")
            
            confidence = 0.85

        elif "Session" in auth_quality.value:
            probable_reasoning = [
                "Session-based authentication provides stateful security model",
                "Simpler revocation compared to token-based approaches",
                "Suitable for: " + context_enrichment.get("project_purpose", {}).get("value", "general") + " applications"
            ]
            confidence = 0.7

        return ImplementationReasoning(
            technology="Authentication Strategy",
            probable_reasoning=probable_reasoning,
            confidence=confidence,
            evidence=auth_quality.evidence
        )

    @staticmethod
    def _reason_async_strategy(
        detections: Dict[str, Any],
        quality_analysis: Dict[str, EvidenceModel],
        context_enrichment: Dict[str, Any]
    ) -> ImplementationReasoning:
        """Generate context-aware reasoning for async processing strategy."""
        resilience_quality = quality_analysis.get("resilience_patterns", EvidenceModel(value="", confidence=0.0, evidence=[]))
        probable_reasoning = []
        confidence = 0.6

        scale = context_enrichment.get("scalability_expectations", {}).get("value", "medium")

        if "Retry" in resilience_quality.value or "Circuit breaker" in resilience_quality.value:
            probable_reasoning = [
                f"Resilience patterns chosen for {scale} scale reliability requirements",
            ]
            
            if "Retry" in resilience_quality.value:
                probable_reasoning.append("Automatic retries handle transient failures in external dependencies")
            
            if "Circuit breaker" in resilience_quality.value:
                probable_reasoning.append("Circuit breakers prevent cascading failures to dependent systems")
            
            if "Timeout" in resilience_quality.value:
                probable_reasoning.append("Request timeouts prevent resource exhaustion from slow services")
            
            confidence = 0.8

        return ImplementationReasoning(
            technology="Resilience/Async Strategy",
            probable_reasoning=probable_reasoning,
            confidence=confidence,
            evidence=resilience_quality.evidence
        )

    @staticmethod
    def generate_tradeoff_analysis(
        detections: Dict[str, Any],
        quality_analysis: Dict[str, EvidenceModel],
        context_enrichment: Dict[str, Any],
        failure_analysis: Dict[str, EvidenceModel]
    ) -> List[EvidenceModel]:
        """
        Generate engineering-level tradeoff analysis.
        """
        tradeoffs = []

        # Database vs. cache consistency tradeoff
        db = detections.get("database_used", EvidenceModel(value="", confidence=0.0, evidence=[]))
        cache = quality_analysis.get("cache_management", EvidenceModel(value="", confidence=0.0, evidence=[]))
        
        if "Redis" in cache.value or "Memcached" in cache.value:
            if "MongoDB" in db.value:
                tradeoffs.append(EvidenceModel(
                    value="NoSQL + Caching: Flexibility vs. Consistency Complexity",
                    confidence=0.8,
                    evidence=[
                        "MongoDB schema flexibility enables rapid evolution",
                        "Cache layer adds invalidation complexity",
                        "Risk: Stale cache + schema changes may cause subtle bugs"
                    ]
                ))
            elif "PostgreSQL" in db.value or "MySQL" in db.value:
                tradeoffs.append(EvidenceModel(
                    value="RDBMS + Caching: Strong Consistency vs. Cache Overhead",
                    confidence=0.8,
                    evidence=[
                        "Database provides ACID guarantees",
                        "Cache requires careful invalidation to maintain consistency",
                        "Benefit: Reduced database load for high-frequency queries"
                    ]
                ))

        # Async processing tradeoff
        resilience = quality_analysis.get("resilience_patterns", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Retry" in resilience.value or "Circuit breaker" in resilience.value:
            tradeoffs.append(EvidenceModel(
                value="Resilience Patterns: Safety vs. Complexity",
                confidence=0.75,
                evidence=[
                    "Retries and circuit breakers prevent cascading failures",
                    "Added complexity in error handling and recovery logic",
                    "Benefit: System resilience to transient failures"
                ]
            ))

        # Auth centralization tradeoff
        auth = quality_analysis.get("authentication_consistency", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Centralized auth" in auth.value:
            tradeoffs.append(EvidenceModel(
                value="Centralized Auth: Security vs. Single Point of Failure",
                confidence=0.8,
                evidence=[
                    "Centralized middleware ensures consistent policy enforcement",
                    "Risk: Auth middleware failure blocks all requests",
                    "Mitigation: Requires fallback or redundancy strategy"
                ]
            ))

        # Scale expectations vs. simplicity
        scale = context_enrichment.get("scalability_expectations", {}).get("value", "medium")
        if "High-scale" in scale or "Enterprise" in scale:
            if "Minimal" in str(quality_analysis.get("resilience_patterns", EvidenceModel(value="", confidence=0.0, evidence=[])).value):
                tradeoffs.append(EvidenceModel(
                    value="High-Scale Ambitions vs. Minimal Resilience Implementation",
                    confidence=0.75,
                    evidence=[
                        "Project targets high scale but lacks resilience patterns",
                        "Risk: May fail under load or dependency failures",
                        "Recommendation: Implement circuit breakers, retries, timeouts"
                    ]
                ))

        return tradeoffs if tradeoffs else [
            EvidenceModel(
                value="Standard architectural tradeoffs detected",
                confidence=0.5,
                evidence=["No major tradeoff misalignments identified"]
            )
        ]
