"""
Architecture Quality Scorer: Evaluates implementation quality across engineering dimensions.
Provides detailed scores for architecture, maintainability, resilience, observability, security, and scalability.
"""

from typing import Dict, Any
from ...models.context import EvidenceModel


class ArchitectureQualityScorer:
    """
    Scores implementation quality across 7 engineering dimensions.
    """

    DIMENSION_WEIGHTS = {
        "architecture_quality": 0.2,
        "maintainability": 0.15,
        "resilience": 0.2,
        "observability": 0.15,
        "security_consistency": 0.15,
        "scalability_readiness": 0.1,
        "implementation_depth": 0.05,
    }

    @staticmethod
    def score_architecture_quality(
        quality_analysis: Dict[str, EvidenceModel],
        context_enrichment: Dict[str, Any],
        failure_analysis: Dict[str, EvidenceModel],
        detections: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Comprehensive quality scoring across 7 dimensions.
        Returns dict with individual scores, detailed explanations, and overall score.
        """
        scores = {}

        # 1. Architecture Quality (20%)
        scores["architecture_quality"] = ArchitectureQualityScorer._score_architecture_quality(quality_analysis)

        # 2. Maintainability (15%)
        scores["maintainability"] = ArchitectureQualityScorer._score_maintainability(quality_analysis, context_enrichment)

        # 3. Resilience (20%)
        scores["resilience"] = ArchitectureQualityScorer._score_resilience(quality_analysis, failure_analysis)

        # 4. Observability (15%)
        scores["observability"] = ArchitectureQualityScorer._score_observability(quality_analysis, context_enrichment)

        # 5. Security Consistency (15%)
        scores["security_consistency"] = ArchitectureQualityScorer._score_security(quality_analysis, detections)

        # 6. Scalability Readiness (10%)
        scores["scalability_readiness"] = ArchitectureQualityScorer._score_scalability(quality_analysis, context_enrichment)

        # 7. Implementation Depth (5%)
        scores["implementation_depth"] = ArchitectureQualityScorer._score_implementation_depth(quality_analysis)

        # Calculate weighted overall score
        overall_score = sum(
            scores[dimension]["score"] * ArchitectureQualityScorer.DIMENSION_WEIGHTS[dimension]
            for dimension in scores
        )

        return {
            "dimensions": scores,
            "overall_score": round(overall_score, 2),
            "overall_grade": ArchitectureQualityScorer._grade_from_score(overall_score),
            "summary": ArchitectureQualityScorer._generate_quality_summary(scores),
        }

    @staticmethod
    def _score_architecture_quality(quality_analysis: Dict[str, EvidenceModel]) -> Dict[str, Any]:
        """Score 0-100: Architecture design and separation of concerns."""
        score = 0
        feedback = []

        # Clear layer separation
        separation = quality_analysis.get("architecture_separation", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Clear layered structure" in separation.value:
            score += 30
            feedback.append("✓ Clear layered architecture detected")
        elif "Partial layering" in separation.value:
            score += 15
            feedback.append("⚠ Partial layer separation - room for improvement")
        else:
            feedback.append("✗ No clear architecture layers detected")

        # Separation of concerns
        if "separation of concerns" in separation.value.lower():
            score += 20
            feedback.append("✓ Good separation of concerns")
        else:
            feedback.append("⚠ Separation of concerns could be clearer")
            score += 5

        # API design
        api = quality_analysis.get("api_design_quality", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Swagger" in api.value or "OpenAPI" in api.value:
            score += 15
            feedback.append("✓ API documented with Swagger/OpenAPI")
        elif "API documentation" in api.value:
            score += 10
            feedback.append("✓ API documentation present")
        else:
            feedback.append("⚠ API design documentation missing")
            score += 3

        # Error handling
        error = quality_analysis.get("error_handling_maturity", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Centralized error handling" in error.value:
            score += 15
            feedback.append("✓ Centralized error handling")
        else:
            feedback.append("⚠ Error handling could be more centralized")

        # Code reuse
        reuse = quality_analysis.get("code_duplication", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Good code reuse" in reuse.value:
            score += 10
            feedback.append("✓ Good code reuse and utilities extraction")
        else:
            feedback.append("⚠ Potential code duplication issues")

        # Fallback handling
        fallback = quality_analysis.get("fallback_handling", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Fallback strategies" in fallback.value or "Feature flags" in fallback.value:
            score += 5
            feedback.append("✓ Graceful degradation strategies")

        return {
            "score": min(100, score),
            "max_score": 100,
            "feedback": feedback,
            "percentage": min(100, score),
        }

    @staticmethod
    def _score_maintainability(quality_analysis: Dict[str, EvidenceModel], context_enrichment: Dict[str, Any]) -> Dict[str, Any]:
        """Score 0-100: Code maintainability and documentation."""
        score = 0
        feedback = []

        # Code reuse
        reuse = quality_analysis.get("code_duplication", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Good code reuse" in reuse.value:
            score += 25
            feedback.append("✓ Excellent code reuse patterns")
        elif "Partial reuse" in reuse.value:
            score += 15
            feedback.append("⚠ Moderate code reuse")
        else:
            feedback.append("✗ Code duplication indicates poor maintainability")

        # Documentation quality
        doc = context_enrichment.get("documentation_quality", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Well-documented" in doc.value:
            score += 25
            feedback.append("✓ Well-documented project")
        elif "Partially documented" in doc.value:
            score += 15
            feedback.append("⚠ Partial documentation")
        else:
            feedback.append("✗ Minimal documentation - onboarding challenge")

        # Error handling
        error = quality_analysis.get("error_handling_maturity", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Comprehensive try-catch" in error.value and "Error logging" in error.value:
            score += 20
            feedback.append("✓ Comprehensive error handling and logging")
        elif "Basic exception handling" in error.value:
            score += 10
            feedback.append("⚠ Basic error handling")
        else:
            feedback.append("⚠ Error handling needs improvement")

        # Architecture separation
        sep = quality_analysis.get("architecture_separation", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Clear layered" in sep.value:
            score += 15
            feedback.append("✓ Clear architecture aids maintainability")
        else:
            feedback.append("⚠ Architecture clarity affects maintainability")
            score += 5

        # Dependency management
        dep = quality_analysis.get("dependency_management", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Lock files" in dep.value:
            score += 10
            feedback.append("✓ Dependency versions locked")
        else:
            feedback.append("⚠ No dependency version locking")

        # Constants/config centralization
        if "Centralized constants" in str(quality_analysis.get("code_duplication", EvidenceModel(value="", confidence=0.0, evidence=[])).value):
            score += 5
            feedback.append("✓ Centralized configuration")

        return {
            "score": min(100, score),
            "max_score": 100,
            "feedback": feedback,
            "percentage": min(100, score),
        }

    @staticmethod
    def _score_resilience(quality_analysis: Dict[str, EvidenceModel], failure_analysis: Dict[str, EvidenceModel]) -> Dict[str, Any]:
        """Score 0-100: System resilience and failure handling."""
        score = 0
        feedback = []

        # Resilience patterns
        resilience = quality_analysis.get("resilience_patterns", EvidenceModel(value="", confidence=0.0, evidence=[]))
        patterns_found = sum([
            "Retry" in resilience.value,
            "Circuit breaker" in resilience.value,
            "Timeout" in resilience.value,
            "Connection pooling" in resilience.value,
        ])

        if patterns_found >= 3:
            score += 30
            feedback.append("✓ Comprehensive resilience patterns (retries, CB, timeouts)")
        elif patterns_found >= 2:
            score += 20
            feedback.append("⚠ Partial resilience patterns")
        else:
            feedback.append("✗ Minimal resilience patterns detected")

        # Graceful degradation
        fallback = quality_analysis.get("fallback_handling", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Fallback" in fallback.value or "Feature flags" in fallback.value:
            score += 20
            feedback.append("✓ Graceful degradation implemented")
        else:
            feedback.append("⚠ No graceful degradation strategy")

        # Database failure protection
        db_risk = failure_analysis.get("database_failure_risk", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "LOW" in str(db_risk.value):
            score += 25
            feedback.append("✓ Low database failure risk")
        elif "MEDIUM" in str(db_risk.value):
            score += 15
            feedback.append("⚠ Moderate database failure risk")
        else:
            feedback.append("✗ High database failure risk")

        # Recovery mechanisms
        recovery = failure_analysis.get("recovery_mechanisms", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Automatic retries" in recovery.value or "Circuit breaker recovery" in recovery.value:
            score += 15
            feedback.append("✓ Automatic recovery mechanisms")
        else:
            feedback.append("⚠ Limited automatic recovery")

        # Cache management
        cache = quality_analysis.get("cache_management", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Cache invalidation" in cache.value:
            score += 10
            feedback.append("✓ Cache invalidation strategy in place")
        elif "Redis" in cache.value or "cache" in cache.value.lower():
            score += 5
            feedback.append("⚠ Caching present but no explicit invalidation")

        return {
            "score": min(100, score),
            "max_score": 100,
            "feedback": feedback,
            "percentage": min(100, score),
        }

    @staticmethod
    def _score_observability(quality_analysis: Dict[str, EvidenceModel], context_enrichment: Dict[str, Any]) -> Dict[str, Any]:
        """Score 0-100: Logging, monitoring, and tracing."""
        score = 0
        feedback = []

        # Observability components
        obs = quality_analysis.get("observability_maturity", EvidenceModel(value="", confidence=0.0, evidence=[]))
        components = sum([
            "Logging" in obs.value,
            "Structured logging" in obs.value,
            "Metrics" in obs.value,
            "Distributed tracing" in obs.value,
        ])

        if components >= 3:
            score += 40
            feedback.append("✓ Comprehensive observability (logging, metrics, tracing)")
        elif components >= 2:
            score += 25
            feedback.append("⚠ Partial observability stack")
        elif components >= 1:
            score += 15
            feedback.append("⚠ Basic logging only")
        else:
            feedback.append("✗ Minimal/no observability")

        # Error logging
        error = quality_analysis.get("error_handling_maturity", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Error logging" in error.value:
            score += 20
            feedback.append("✓ Error logging configured")
        else:
            feedback.append("⚠ Error logging not detected")

        # CI/CD pipeline observability
        ci_cd = context_enrichment.get("ci_cd_maturity", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Automated" in ci_cd.value:
            score += 15
            feedback.append("✓ CI/CD pipeline provides deployment visibility")
        else:
            feedback.append("⚠ No automated CI/CD visibility")

        # Infrastructure monitoring
        infra = context_enrichment.get("infrastructure_maturity", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Enterprise" in infra.value or "Intermediate" in infra.value:
            score += 15
            feedback.append("✓ Infrastructure monitoring likely in place")
        else:
            feedback.append("⚠ Infrastructure monitoring unclear")

        # Health checks
        if "Health checks" in str(quality_analysis.get("resilience_patterns", EvidenceModel(value="", confidence=0.0, evidence=[])).value):
            score += 10
            feedback.append("✓ Health check endpoints")

        return {
            "score": min(100, score),
            "max_score": 100,
            "feedback": feedback,
            "percentage": min(100, score),
        }

    @staticmethod
    def _score_security(quality_analysis: Dict[str, EvidenceModel], detections: Dict[str, Any]) -> Dict[str, Any]:
        """Score 0-100: Security consistency and practices."""
        score = 0
        feedback = []

        # Authentication centralization
        auth = quality_analysis.get("authentication_consistency", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Centralized auth" in auth.value:
            score += 25
            feedback.append("✓ Centralized authentication middleware")
        elif "Token validation" in auth.value:
            score += 15
            feedback.append("⚠ Basic token validation")
        else:
            feedback.append("✗ No centralized auth detected")

        # Authorization
        if "RBAC" in auth.value:
            score += 20
            feedback.append("✓ Role-based access control")
        else:
            feedback.append("⚠ RBAC not detected")
            score += 5

        # Error handling (doesn't leak info)
        error = quality_analysis.get("error_handling_maturity", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Centralized error handling" in error.value:
            score += 15
            feedback.append("✓ Centralized error handling (can prevent info leaks)")
        else:
            feedback.append("⚠ Distributed error handling risk")

        # Session management
        if "Session management" in auth.value:
            score += 15
            feedback.append("✓ Session management configured")
        else:
            feedback.append("⚠ No session management detected")

        # Dependency scanning
        dep = quality_analysis.get("dependency_management", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Dependency scanning" in dep.value:
            score += 15
            feedback.append("✓ Automated dependency scanning")
        else:
            feedback.append("⚠ No dependency vulnerability scanning")

        # Version pinning
        if "Version pinning" in dep.value:
            score += 10
            feedback.append("✓ Dependencies version pinned")
        else:
            feedback.append("⚠ Dependencies may float to risky versions")

        return {
            "score": min(100, score),
            "max_score": 100,
            "feedback": feedback,
            "percentage": min(100, score),
        }

    @staticmethod
    def _score_scalability(quality_analysis: Dict[str, EvidenceModel], context_enrichment: Dict[str, Any]) -> Dict[str, Any]:
        """Score 0-100: Scalability readiness."""
        score = 0
        feedback = []

        # Caching
        cache = quality_analysis.get("cache_management", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Redis" in cache.value or "Memcached" in cache.value:
            score += 30
            feedback.append("✓ External caching layer (Redis/Memcached)")
        elif "Local caching" in cache.value:
            score += 15
            feedback.append("⚠ Only local caching (limited scalability)")
        else:
            feedback.append("✗ No caching - direct DB load")

        # Connection pooling
        resilience = quality_analysis.get("resilience_patterns", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Connection pooling" in resilience.value:
            score += 25
            feedback.append("✓ Connection pooling configured")
        else:
            feedback.append("⚠ No connection pool limits detected")

        # Async processing
        backend = detections.get("backend_framework", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "FastAPI" in backend.value or "Node.js" in backend.value or "Async" in backend.value:
            score += 20
            feedback.append("✓ Async framework enables concurrency")
        else:
            feedback.append("⚠ Synchronous framework limits concurrency")

        # Infrastructure readiness
        infra = context_enrichment.get("infrastructure_maturity", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Enterprise" in infra.value or "Kubernetes" in infra.value:
            score += 15
            feedback.append("✓ Enterprise infrastructure supports scaling")
        elif "Containerized" in infra.value:
            score += 10
            feedback.append("⚠ Containerized but limited orchestration")
        else:
            feedback.append("⚠ Infrastructure may not support scaling")

        # Load balancing indicators
        if "Horizontal scaling" in str(context_enrichment.get("deployment_assumptions", [])):
            score += 10
            feedback.append("✓ Horizontal scaling architecture")

        return {
            "score": min(100, score),
            "max_score": 100,
            "feedback": feedback,
            "percentage": min(100, score),
        }

    @staticmethod
    def _score_implementation_depth(quality_analysis: Dict[str, EvidenceModel]) -> Dict[str, Any]:
        """Score 0-100: Implementation sophistication and depth."""
        score = 0
        feedback = []

        # Error handling sophistication
        error = quality_analysis.get("error_handling_maturity", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Comprehensive try-catch" in error.value and "Custom error types" in error.value:
            score += 25
            feedback.append("✓ Sophisticated error handling")
        elif "Basic exception handling" in error.value:
            score += 10
            feedback.append("⚠ Basic error handling")

        # Resilience pattern sophistication
        resilience = quality_analysis.get("resilience_patterns", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Circuit breaker" in resilience.value and "Retry" in resilience.value:
            score += 25
            feedback.append("✓ Advanced resilience patterns")
        elif "Timeout" in resilience.value:
            score += 10
            feedback.append("⚠ Basic timeout handling")

        # Auth sophistication
        auth = quality_analysis.get("authentication_consistency", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "RBAC" in auth.value and "Session management" in auth.value:
            score += 20
            feedback.append("✓ Sophisticated auth system")
        elif "Centralized auth" in auth.value:
            score += 10
            feedback.append("⚠ Basic auth implementation")

        # Cache sophistication
        cache = quality_analysis.get("cache_management", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Redis" in cache.value and "Cache invalidation" in cache.value:
            score += 15
            feedback.append("✓ Sophisticated cache management")
        elif "Redis" in cache.value:
            score += 8
            feedback.append("⚠ Basic Redis usage")

        # Observability sophistication
        obs = quality_analysis.get("observability_maturity", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Distributed tracing" in obs.value:
            score += 15
            feedback.append("✓ Distributed tracing implemented")
        elif "Structured logging" in obs.value:
            score += 8
            feedback.append("⚠ Basic structured logging")

        return {
            "score": min(100, score),
            "max_score": 100,
            "feedback": feedback,
            "percentage": min(100, score),
        }

    @staticmethod
    def _grade_from_score(score: float) -> str:
        """Convert numerical score to letter grade."""
        if score >= 90:
            return "A (Excellent)"
        elif score >= 80:
            return "B (Good)"
        elif score >= 70:
            return "C (Acceptable)"
        elif score >= 60:
            return "D (Needs Improvement)"
        else:
            return "F (Poor)"

    @staticmethod
    def _generate_quality_summary(scores: Dict[str, Any]) -> str:
        """Generate brief quality summary."""
        top_strength = max(scores.items(), key=lambda x: x[1]["score"])
        bottom_weakness = min(scores.items(), key=lambda x: x[1]["score"])

        return f"Strength: {top_strength[0]} ({top_strength[1]['score']}/100) | " \
               f"Focus Area: {bottom_weakness[0]} ({bottom_weakness[1]['score']}/100)"
