"""
Failure-Path Intelligence Engine: Reasons about runtime failure scenarios and resilience.
Analyzes what breaks when dependencies fail, middleware breaks, or edge cases occur.
"""

from typing import Dict, Any, List
from ...models.context import EvidenceModel, VivaTarget


class FailurePathIntelligenceEngine:
    """
    Analyzes failure scenarios and their propagation:
    - Database connection failures
    - Cache/Redis failures
    - Authentication failures
    - External API failures
    - Timeout scenarios
    - Middleware failures
    - Background job failures
    - Recovery mechanisms
    """

    @staticmethod
    def analyze_failure_paths(
        repo_path: str,
        detections: Dict[str, Any],
        quality_analysis: Dict[str, EvidenceModel],
        context_enrichment: Dict[str, Any]
    ) -> Dict[str, EvidenceModel]:
        """
        Comprehensive failure path analysis.
        Returns a dict mapping failure scenarios to risk assessments.
        """
        return {
            "database_failure_risk": FailurePathIntelligenceEngine._analyze_db_failure_risk(detections, quality_analysis),
            "cache_failure_impact": FailurePathIntelligenceEngine._analyze_cache_failure_impact(detections, quality_analysis),
            "auth_failure_propagation": FailurePathIntelligenceEngine._analyze_auth_failure(detections, quality_analysis),
            "external_api_resilience": FailurePathIntelligenceEngine._analyze_external_api_resilience(quality_analysis),
            "middleware_failure_impact": FailurePathIntelligenceEngine._analyze_middleware_failure(quality_analysis),
            "timeout_handling": FailurePathIntelligenceEngine._analyze_timeout_handling(quality_analysis),
            "graceful_degradation": FailurePathIntelligenceEngine._analyze_graceful_degradation(quality_analysis),
            "recovery_mechanisms": FailurePathIntelligenceEngine._analyze_recovery_mechanisms(quality_analysis),
        }

    @staticmethod
    def _analyze_db_failure_risk(detections: Dict[str, Any], quality_analysis: Dict[str, EvidenceModel]) -> EvidenceModel:
        """Assess risk when database becomes unavailable."""
        risk_factors = []
        evidence = []

        # Check if caching is in place
        cache_quality = quality_analysis.get("cache_management", EvidenceModel(value="None", confidence=0.0, evidence=[]))
        if "No caching" in cache_quality.value or cache_quality.confidence < 0.3:
            risk_factors.append("No caching layer")
            evidence.append("Database queries directly hit DB without caching")

        # Check for connection pooling
        resilience_quality = quality_analysis.get("resilience_patterns", EvidenceModel(value="None", confidence=0.0, evidence=[]))
        if "Connection pooling" not in resilience_quality.value:
            risk_factors.append("No connection pooling")
            evidence.append("Connection pool limits not configured")

        # Database-specific risks
        db_type = detections.get("database_used", EvidenceModel(value="Unknown", confidence=0.0, evidence=[]))
        if "NoSQL" in str(db_type.value) or "MongoDB" in str(db_type.value):
            risk_factors.append("NoSQL without transactions")
            evidence.append("NoSQL databases may lack ACID guarantees")

        # Determine risk level
        risk_level = "HIGH" if len(risk_factors) >= 2 else "MEDIUM" if risk_factors else "LOW"
        confidence = 0.7 + len(risk_factors) * 0.1
        
        return EvidenceModel(
            value=f"{risk_level}: {' + '.join(risk_factors) if risk_factors else 'Moderate risk'}",
            confidence=min(0.95, confidence),
            evidence=evidence if evidence else ["Standard database failure risk"]
        )

    @staticmethod
    def _analyze_cache_failure_impact(detections: Dict[str, Any], quality_analysis: Dict[str, EvidenceModel]) -> EvidenceModel:
        """Assess impact when cache becomes unavailable."""
        impact = []
        evidence = []

        cache_quality = quality_analysis.get("cache_management", EvidenceModel(value="None", confidence=0.0, evidence=[]))
        
        if "Redis" in cache_quality.value or "Memcached" in cache_quality.value:
            # Cache is being used
            error_handling = quality_analysis.get("error_handling_maturity", EvidenceModel(value="None", confidence=0.0, evidence=[]))
            
            if "Centralized error handling" in error_handling.value:
                impact.append("Fallback to DB configured")
                evidence.append("Error middleware likely handles cache misses")
            else:
                impact.append("Potential cascading failures")
                evidence.append("No centralized error handling detected")
            
            # Check for timeout handling
            resilience = quality_analysis.get("resilience_patterns", EvidenceModel(value="None", confidence=0.0, evidence=[]))
            if "Timeout" in resilience.value:
                impact.append("Timeout protection active")
                evidence.append("Timeout handling configured")

        if not impact:
            impact = ["No explicit cache impact handling"]
            evidence = ["Cache failures may cause direct DB overload"]

        confidence = 0.65 + len(impact) * 0.1
        return EvidenceModel(
            value=" + ".join(impact),
            confidence=min(0.9, confidence),
            evidence=evidence
        )

    @staticmethod
    def _analyze_auth_failure(detections: Dict[str, Any], quality_analysis: Dict[str, EvidenceModel]) -> EvidenceModel:
        """Assess authentication failure propagation."""
        failure_modes = []
        evidence = []

        auth_quality = quality_analysis.get("authentication_consistency", EvidenceModel(value="None", confidence=0.0, evidence=[]))
        
        if "Centralized auth" not in auth_quality.value:
            failure_modes.append("No centralized auth middleware")
            evidence.append("Auth checks may be inconsistent across endpoints")
        
        if "Token validation" not in auth_quality.value:
            failure_modes.append("Unclear token validation strategy")
            evidence.append("Token validation logic not clearly detected")
        
        if "RBAC" not in auth_quality.value:
            failure_modes.append("No explicit permission checks")
            evidence.append("Role-based access control not detected")

        error_handling = quality_analysis.get("error_handling_maturity", EvidenceModel(value="None", confidence=0.0, evidence=[]))
        if "Error logging" not in error_handling.value:
            failure_modes.append("Auth failures may not be logged")
            evidence.append("Error logging not detected")

        risk_level = "CRITICAL" if len(failure_modes) >= 3 else "HIGH" if len(failure_modes) >= 1 else "MEDIUM"
        confidence = 0.7 + len(failure_modes) * 0.08

        return EvidenceModel(
            value=f"{risk_level}: {' → '.join(failure_modes) if failure_modes else 'Resilient auth'}",
            confidence=min(0.9, confidence),
            evidence=evidence if evidence else ["Standard auth failure handling"]
        )

    @staticmethod
    def _analyze_external_api_resilience(quality_analysis: Dict[str, EvidenceModel]) -> EvidenceModel:
        """Assess resilience when external APIs fail."""
        resilience_features = []
        evidence = []

        resilience_quality = quality_analysis.get("resilience_patterns", EvidenceModel(value="None", confidence=0.0, evidence=[]))
        
        if "Retry logic" in resilience_quality.value:
            resilience_features.append("Retries configured")
            evidence.append("Automatic retry mechanism present")
        else:
            evidence.append("No retry logic detected")

        if "Circuit breakers" in resilience_quality.value:
            resilience_features.append("Circuit breaker protection")
            evidence.append("Circuit breaker pattern implemented")
        else:
            evidence.append("No circuit breaker detected")

        if "Timeout handling" in resilience_quality.value:
            resilience_features.append("Timeouts configured")
            evidence.append("Request timeouts detected")
        else:
            evidence.append("No timeout protection detected")

        fallback_quality = quality_analysis.get("fallback_handling", EvidenceModel(value="None", confidence=0.0, evidence=[]))
        if "Fallback" in fallback_quality.value or "default" in fallback_quality.value.lower():
            resilience_features.append("Fallback responses")
            evidence.append("Graceful degradation implemented")

        resilience_level = "HIGH" if len(resilience_features) >= 3 else "MEDIUM" if resilience_features else "LOW"
        confidence = 0.6 + len(resilience_features) * 0.12

        return EvidenceModel(
            value=f"{resilience_level}: {' + '.join(resilience_features) if resilience_features else 'Minimal resilience'}",
            confidence=min(0.85, confidence),
            evidence=evidence if evidence else ["Standard API resilience"]
        )

    @staticmethod
    def _analyze_middleware_failure(quality_analysis: Dict[str, EvidenceModel]) -> EvidenceModel:
        """Assess impact when middleware chain breaks."""
        impacts = []
        evidence = []

        auth_quality = quality_analysis.get("authentication_consistency", EvidenceModel(value="None", confidence=0.0, evidence=[]))
        if "Centralized auth" in auth_quality.value:
            impacts.append("Auth middleware single point of failure")
            evidence.append("Centralized auth middleware detected")

        error_handling = quality_analysis.get("error_handling_maturity", EvidenceModel(value="None", confidence=0.0, evidence=[]))
        if "Centralized error handling" in error_handling.value:
            impacts.append("Error handler single point of failure")
            evidence.append("Centralized error middleware detected")

        if not impacts:
            impacts = ["Multiple middleware failure points"]
            evidence = ["Distributed middleware increases failure complexity"]

        confidence = 0.65
        return EvidenceModel(
            value="MODERATE: " + " + ".join(impacts),
            confidence=confidence,
            evidence=evidence
        )

    @staticmethod
    def _analyze_timeout_handling(quality_analysis: Dict[str, EvidenceModel]) -> EvidenceModel:
        """Assess timeout handling configuration."""
        timeout_coverage = []
        evidence = []

        resilience = quality_analysis.get("resilience_patterns", EvidenceModel(value="None", confidence=0.0, evidence=[]))
        if "Timeout" in resilience.value:
            timeout_coverage.append("Request timeouts configured")
            evidence.append("Timeout logic detected")
        else:
            evidence.append("No explicit timeout configuration found")

        if "Retry" in resilience.value:
            timeout_coverage.append("Retry-after logic")
            evidence.append("Retry mechanism can handle timeouts")

        if not timeout_coverage:
            timeout_coverage = ["No timeout protection"]
            evidence = ["System may hang on slow/unresponsive services"]

        confidence = 0.7 if timeout_coverage else 0.3
        return EvidenceModel(
            value=" + ".join(timeout_coverage),
            confidence=confidence,
            evidence=evidence
        )

    @staticmethod
    def _analyze_graceful_degradation(quality_analysis: Dict[str, EvidenceModel]) -> EvidenceModel:
        """Assess graceful degradation capabilities."""
        degradation_features = []
        evidence = []

        fallback = quality_analysis.get("fallback_handling", EvidenceModel(value="None", confidence=0.0, evidence=[]))
        if "Fallback" in fallback.value:
            degradation_features.append("Fallback logic")
            evidence.append("Explicit fallback strategies detected")

        if "Feature flags" in fallback.value:
            degradation_features.append("Feature flags")
            evidence.append("Feature flag-based degradation available")

        cache = quality_analysis.get("cache_management", EvidenceModel(value="None", confidence=0.0, evidence=[]))
        if "Redis" in cache.value or "cache" in cache.value.lower():
            degradation_features.append("Stale data caching")
            evidence.append("Cache-based degradation possible")

        if not degradation_features:
            degradation_features = ["Limited graceful degradation"]
            evidence = ["System likely fails hard rather than degrading"]

        confidence = 0.6 + len(degradation_features) * 0.12
        return EvidenceModel(
            value=" + ".join(degradation_features),
            confidence=min(0.85, confidence),
            evidence=evidence
        )

    @staticmethod
    def _analyze_recovery_mechanisms(quality_analysis: Dict[str, EvidenceModel]) -> EvidenceModel:
        """Assess recovery mechanisms and self-healing capabilities."""
        recovery_features = []
        evidence = []

        resilience = quality_analysis.get("resilience_patterns", EvidenceModel(value="None", confidence=0.0, evidence=[]))
        if "Retry" in resilience.value:
            recovery_features.append("Automatic retries")
            evidence.append("Retry mechanism can recover from transient failures")

        if "Circuit breaker" in resilience.value:
            recovery_features.append("Circuit breaker recovery")
            evidence.append("Circuit breaker can trip and recover")

        error_handling = quality_analysis.get("error_handling_maturity", EvidenceModel(value="None", confidence=0.0, evidence=[]))
        if "Error logging" in error_handling.value:
            recovery_features.append("Error monitoring")
            evidence.append("Errors logged for recovery analysis")

        observability = quality_analysis.get("observability_maturity", EvidenceModel(value="None", confidence=0.0, evidence=[]))
        if "Distributed tracing" in observability.value or "Metrics" in observability.value:
            recovery_features.append("Observability for diagnosis")
            evidence.append("Monitoring infrastructure aids recovery")

        if not recovery_features:
            recovery_features = ["Limited recovery automation"]
            evidence = ["Recovery likely requires manual intervention"]

        confidence = 0.55 + len(recovery_features) * 0.1
        return EvidenceModel(
            value=" + ".join(recovery_features),
            confidence=min(0.85, confidence),
            evidence=evidence
        )

    @staticmethod
    def generate_failure_focused_viva_targets(
        failure_analysis: Dict[str, EvidenceModel],
        quality_analysis: Dict[str, EvidenceModel]
    ) -> List[VivaTarget]:
        """
        Generate Viva questions focused on failure scenarios and operational knowledge.
        """
        targets = []

        # Database failure scenarios
        db_risk = failure_analysis.get("database_failure_risk", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "HIGH" in str(db_risk.value) or "CRITICAL" in str(db_risk.value):
            targets.append(VivaTarget(
                topic="Database Resilience",
                question_target="DB Failure Handling",
                difficulty="hard",
                importance_score=0.95,
                focus="What happens if the database becomes unavailable? How does the system behave?"
            ))

        # Cache failure scenarios
        cache_impact = failure_analysis.get("cache_failure_impact", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "Redis" in str(quality_analysis.get("cache_management", EvidenceModel(value="", confidence=0.0, evidence=[])).value):
            targets.append(VivaTarget(
                topic="Cache Management",
                question_target="Cache Failure Recovery",
                difficulty="hard",
                importance_score=0.85,
                focus="Describe what happens if Redis crashes during high-load scenarios. What's your recovery strategy?"
            ))

        # Auth middleware failure
        auth_risk = failure_analysis.get("auth_failure_propagation", EvidenceModel(value="", confidence=0.0, evidence=[]))
        if "CRITICAL" in str(auth_risk.value) or "HIGH" in str(auth_risk.value):
            targets.append(VivaTarget(
                topic="Authentication Security",
                question_target="Auth Middleware Failure",
                difficulty="hard",
                importance_score=0.95,
                focus="What happens if JWT verification middleware fails? Which requests succeed and which fail?"
            ))

        # External API resilience
        targets.append(VivaTarget(
            topic="External Dependencies",
            question_target="API Resilience",
            difficulty="hard",
            importance_score=0.8,
            focus="How does your system handle timeouts from external APIs? What's the user experience?"
        ))

        # Graceful degradation
        degradation = failure_analysis.get("graceful_degradation", EvidenceModel(value="", confidence=0.0, evidence=[]))
        targets.append(VivaTarget(
            topic="System Reliability",
            question_target="Graceful Degradation",
            difficulty="medium",
            importance_score=0.75,
            focus="Describe how the system gracefully degrades when dependencies fail."
        ))

        return targets
