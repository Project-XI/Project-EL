"""
Implementation Quality Analyzer: Evaluates code quality dimensions beyond simple tech detection.
Analyzes error handling, resilience patterns, architecture separation, observability, and more.
"""

import os
import re
from typing import Dict, Any, List, Tuple
from ...models.context import EvidenceModel


class ImplementationQualityAnalyzer:
    """
    Analyzes implementation quality across multiple dimensions:
    - Error handling maturity
    - Cache invalidation patterns
    - Authentication consistency
    - Layered architecture separation
    - API design quality
    - Resilience patterns
    - Observability/logging
    - Code duplication indicators
    - Fallback handling
    """

    @staticmethod
    def analyze_implementation_quality(repo_path: str, structure: Dict[str, Any]) -> Dict[str, EvidenceModel]:
        """
        Comprehensive quality analysis across key dimensions.
        Returns a dict mapping quality dimensions to EvidenceModel scores.
        """
        return {
            "error_handling_maturity": ImplementationQualityAnalyzer._analyze_error_handling(repo_path),
            "cache_management": ImplementationQualityAnalyzer._analyze_cache_patterns(repo_path),
            "authentication_consistency": ImplementationQualityAnalyzer._analyze_auth_consistency(repo_path),
            "architecture_separation": ImplementationQualityAnalyzer._analyze_architecture_separation(repo_path, structure),
            "api_design_quality": ImplementationQualityAnalyzer._analyze_api_design(repo_path),
            "resilience_patterns": ImplementationQualityAnalyzer._analyze_resilience(repo_path),
            "observability_maturity": ImplementationQualityAnalyzer._analyze_observability(repo_path),
            "code_duplication": ImplementationQualityAnalyzer._analyze_code_duplication(repo_path),
            "fallback_handling": ImplementationQualityAnalyzer._analyze_fallback_handling(repo_path),
            "dependency_management": ImplementationQualityAnalyzer._analyze_dependency_management(repo_path),
        }

    @staticmethod
    def _analyze_error_handling(repo_path: str) -> EvidenceModel:
        """Analyze error handling maturity and coverage."""
        quality_indicators = []
        evidence = []

        # Check for centralized error handling
        has_error_handler = ImplementationQualityAnalyzer._search_files(
            repo_path, 
            r"(error_handler|ErrorHandler|exception_handler|ExceptionHandler|error_middleware|ErrorMiddleware)"
        )
        
        # Check for try-catch coverage
        try_catch_count = ImplementationQualityAnalyzer._search_files(
            repo_path,
            r"(try:|try\s*{|except:|except\s|catch\s*\{|catch\s*\()"
        )

        # Check for custom error classes
        has_custom_errors = ImplementationQualityAnalyzer._search_files(
            repo_path,
            r"(class\s+\w+Error|class\s+\w+Exception)"
        )

        # Check for error logging
        has_error_logging = ImplementationQualityAnalyzer._search_files(
            repo_path,
            r"(logger\.error|log\.error|console\.error|exception_logger)"
        )

        if has_error_handler:
            quality_indicators.append("Centralized error handling")
            evidence.append("Centralized error handler/middleware detected")

        if try_catch_count > 10:
            quality_indicators.append("Comprehensive try-catch coverage")
            evidence.append(f"~{try_catch_count} exception handlers found")
        elif try_catch_count > 3:
            quality_indicators.append("Basic exception handling")
            evidence.append(f"~{try_catch_count} exception handlers found")

        if has_custom_errors:
            quality_indicators.append("Custom error types")
            evidence.append("Custom error/exception classes defined")

        if has_error_logging:
            quality_indicators.append("Error logging")
            evidence.append("Error logging infrastructure detected")

        confidence = min(0.9, 0.3 + len(quality_indicators) * 0.15)
        value = " + ".join(quality_indicators) if quality_indicators else "Minimal error handling"

        return EvidenceModel(
            value=value,
            confidence=confidence,
            evidence=evidence if evidence else ["Limited error handling evidence"]
        )

    @staticmethod
    def _analyze_cache_patterns(repo_path: str) -> EvidenceModel:
        """Analyze cache invalidation and management patterns."""
        indicators = []
        evidence = []

        # Check for cache libraries
        has_redis = ImplementationQualityAnalyzer._search_files(repo_path, r"(redis|Redis|REDIS)")
        has_memcached = ImplementationQualityAnalyzer._search_files(repo_path, r"(memcached|Memcached)")
        has_local_cache = ImplementationQualityAnalyzer._search_files(repo_path, r"(@cache|@lru_cache|memoize)")

        # Check for cache invalidation patterns
        has_invalidation = ImplementationQualityAnalyzer._search_files(
            repo_path,
            r"(cache.*invalidat|invalidat.*cache|cache.*clear|clear.*cache|cache.*delete|delete.*cache|cache.*flush)"
        )

        # Check for cache key strategy
        has_key_strategy = ImplementationQualityAnalyzer._search_files(
            repo_path,
            r"(cache_key|CACHE_KEY|cache.*key|cache.*prefix)"
        )

        if has_redis:
            indicators.append("Redis caching")
            evidence.append("Redis detected")
        if has_memcached:
            indicators.append("Memcached")
            evidence.append("Memcached detected")
        if has_local_cache:
            indicators.append("Local caching")
            evidence.append("Local cache decorators detected")

        if has_invalidation:
            indicators.append("Cache invalidation patterns")
            evidence.append("Cache invalidation logic found")
        else:
            evidence.append("Warning: No explicit cache invalidation detected")

        if has_key_strategy:
            indicators.append("Structured cache keys")
            evidence.append("Cache key strategy found")

        confidence = 0.6 if indicators else 0.2
        value = " + ".join(indicators) if indicators else "No caching infrastructure"

        return EvidenceModel(value=value, confidence=confidence, evidence=evidence)

    @staticmethod
    def _analyze_auth_consistency(repo_path: str) -> EvidenceModel:
        """Analyze authentication implementation consistency."""
        indicators = []
        evidence = []

        # Check for auth middleware
        has_auth_middleware = ImplementationQualityAnalyzer._search_files(
            repo_path,
            r"(auth.*middleware|middleware.*auth|AuthMiddleware|authentication_middleware)"
        )

        # Check for token validation
        has_token_validation = ImplementationQualityAnalyzer._search_files(
            repo_path,
            r"(verify.*token|token.*verify|validate.*jwt|jwt.*validate|check.*auth)"
        )

        # Check for role-based access
        has_rbac = ImplementationQualityAnalyzer._search_files(
            repo_path,
            r"(role.*based|rbac|permission|require.*role|check.*role|authorize)"
        )

        # Check for session management
        has_session = ImplementationQualityAnalyzer._search_files(
            repo_path,
            r"(session|Session|SESSION|logout|Logout)"
        )

        if has_auth_middleware:
            indicators.append("Centralized auth")
            evidence.append("Auth middleware detected")

        if has_token_validation:
            indicators.append("Token validation")
            evidence.append("Token verification logic found")

        if has_rbac:
            indicators.append("RBAC")
            evidence.append("Role-based access control implemented")

        if has_session:
            indicators.append("Session management")
            evidence.append("Session handling detected")

        confidence = 0.5 + len(indicators) * 0.1
        value = " + ".join(indicators) if indicators else "Basic/Minimal auth"

        return EvidenceModel(value=value, confidence=confidence, evidence=evidence)

    @staticmethod
    def _analyze_architecture_separation(repo_path: str, structure: Dict[str, Any]) -> EvidenceModel:
        """Analyze layered architecture separation quality."""
        indicators = []
        evidence = []

        # Check for clear layer directories
        common_layers = ["models", "controllers", "services", "routes", "middleware", "utils", "config"]
        found_layers = []
        
        for item in os.listdir(repo_path):
            if os.path.isdir(os.path.join(repo_path, item)) and item in common_layers:
                found_layers.append(item)

        if len(found_layers) >= 4:
            indicators.append("Clear layered structure")
            evidence.append(f"Found {len(found_layers)} architectural layers")
        elif len(found_layers) >= 2:
            indicators.append("Partial layering")
            evidence.append(f"Found {len(found_layers)} architectural layers")

        # Check for separation of concerns
        has_model_separation = ImplementationQualityAnalyzer._search_files(repo_path, r"(models|entities|schema)")
        has_business_logic = ImplementationQualityAnalyzer._search_files(repo_path, r"(services|business|logic)")
        has_routes = ImplementationQualityAnalyzer._search_files(repo_path, r"(routes|handlers|endpoints)")

        if has_model_separation and has_business_logic and has_routes:
            indicators.append("Good separation of concerns")
            evidence.append("Models, business logic, and routes separated")

        confidence = 0.4 + len(indicators) * 0.15
        value = " + ".join(indicators) if indicators else "Unclear/Monolithic"

        return EvidenceModel(value=value, confidence=confidence, evidence=evidence)

    @staticmethod
    def _analyze_api_design(repo_path: str) -> EvidenceModel:
        """Analyze API design quality and consistency."""
        indicators = []
        evidence = []

        # Check for API documentation
        has_swagger = ImplementationQualityAnalyzer._search_files(repo_path, r"(swagger|openapi|OpenAPI)")
        has_api_docs = os.path.exists(os.path.join(repo_path, "docs")) or \
                      os.path.exists(os.path.join(repo_path, "api.md"))

        # Check for consistent error responses
        has_error_responses = ImplementationQualityAnalyzer._search_files(
            repo_path,
            r"(error.*response|response.*error|status.*code|http.*status)"
        )

        # Check for versioning
        has_versioning = ImplementationQualityAnalyzer._search_files(
            repo_path,
            r"(/v[0-9]|/api/v[0-9]|version|API_VERSION)"
        )

        # Check for pagination
        has_pagination = ImplementationQualityAnalyzer._search_files(
            repo_path,
            r"(pagination|paginate|limit|offset|page)"
        )

        if has_swagger:
            indicators.append("Swagger/OpenAPI docs")
            evidence.append("API documentation framework detected")
        elif has_api_docs:
            indicators.append("API documentation")
            evidence.append("API docs directory found")

        if has_error_responses:
            indicators.append("Consistent error responses")
            evidence.append("Standardized error handling found")

        if has_versioning:
            indicators.append("API versioning")
            evidence.append("API version management detected")

        if has_pagination:
            indicators.append("Pagination")
            evidence.append("Pagination logic found")

        confidence = 0.5 + len(indicators) * 0.1
        value = " + ".join(indicators) if indicators else "Basic API design"

        return EvidenceModel(value=value, confidence=confidence, evidence=evidence)

    @staticmethod
    def _analyze_resilience(repo_path: str) -> EvidenceModel:
        """Analyze resilience patterns: retries, circuit breakers, timeouts, fallbacks."""
        indicators = []
        evidence = []

        # Check for retry logic
        has_retry = ImplementationQualityAnalyzer._search_files(
            repo_path,
            r"(retry|Retry|RETRY|exponential.*backoff|backoff)"
        )

        # Check for circuit breakers
        has_circuit_breaker = ImplementationQualityAnalyzer._search_files(
            repo_path,
            r"(circuit.*breaker|CircuitBreaker|breaker)"
        )

        # Check for timeouts
        has_timeout = ImplementationQualityAnalyzer._search_files(
            repo_path,
            r"(timeout|Timeout|TIMEOUT|connection.*timeout)"
        )

        # Check for bulkheads/connection limits
        has_bulkhead = ImplementationQualityAnalyzer._search_files(
            repo_path,
            r"(max.*connection|connection.*pool|pool|bulkhead|thread.*pool)"
        )

        if has_retry:
            indicators.append("Retry logic")
            evidence.append("Retry mechanisms detected")

        if has_circuit_breaker:
            indicators.append("Circuit breakers")
            evidence.append("Circuit breaker pattern detected")

        if has_timeout:
            indicators.append("Timeout handling")
            evidence.append("Timeout configuration found")

        if has_bulkhead:
            indicators.append("Connection pooling")
            evidence.append("Connection management detected")

        confidence = 0.3 + len(indicators) * 0.15
        value = " + ".join(indicators) if indicators else "Basic/No resilience patterns"

        return EvidenceModel(value=value, confidence=confidence, evidence=evidence)

    @staticmethod
    def _analyze_observability(repo_path: str) -> EvidenceModel:
        """Analyze observability: logging, metrics, tracing."""
        indicators = []
        evidence = []

        # Logging
        has_logging = ImplementationQualityAnalyzer._search_files(
            repo_path,
            r"(logger|logging|log\.|console\.log|console\.error|winston|pino)"
        )

        # Structured logging
        has_structured = ImplementationQualityAnalyzer._search_files(
            repo_path,
            r"(json.*log|structured.*log|log.*json|logrus|bunyan)"
        )

        # Metrics
        has_metrics = ImplementationQualityAnalyzer._search_files(
            repo_path,
            r"(prometheus|metrics|statsd|graphite|influxdb)"
        )

        # Tracing
        has_tracing = ImplementationQualityAnalyzer._search_files(
            repo_path,
            r"(tracing|trace|jaeger|opentelemetry|otel|zipkin)"
        )

        if has_logging:
            indicators.append("Logging")
            evidence.append("Logging infrastructure found")

        if has_structured:
            indicators.append("Structured logging")
            evidence.append("Structured logging detected")

        if has_metrics:
            indicators.append("Metrics")
            evidence.append("Metrics collection found")

        if has_tracing:
            indicators.append("Distributed tracing")
            evidence.append("Tracing infrastructure detected")

        confidence = 0.4 + len(indicators) * 0.15
        value = " + ".join(indicators) if indicators else "Minimal observability"

        return EvidenceModel(value=value, confidence=confidence, evidence=evidence)

    @staticmethod
    def _analyze_code_duplication(repo_path: str) -> EvidenceModel:
        """Detect code duplication and utility extraction patterns."""
        indicators = []
        evidence = []

        # Check for utilities/helpers
        has_utils = os.path.exists(os.path.join(repo_path, "utils")) or \
                   os.path.exists(os.path.join(repo_path, "helpers")) or \
                   os.path.exists(os.path.join(repo_path, "lib"))

        # Check for shared/common modules
        has_shared = os.path.exists(os.path.join(repo_path, "shared")) or \
                    os.path.exists(os.path.join(repo_path, "common"))

        # Check for constants/config
        has_constants = ImplementationQualityAnalyzer._search_files(
            repo_path,
            r"(constants|CONSTANTS|config|CONFIG)"
        )

        if has_utils:
            indicators.append("Utility extraction")
            evidence.append("Utils/helpers directory found")

        if has_shared:
            indicators.append("Shared modules")
            evidence.append("Shared/common directory found")

        if has_constants:
            indicators.append("Centralized constants")
            evidence.append("Constants/config management found")

        confidence = 0.5 if indicators else 0.3
        value = "Good code reuse" if len(indicators) >= 2 else \
                ("Partial reuse" if indicators else "Potential duplication")

        return EvidenceModel(value=value, confidence=confidence, evidence=evidence)

    @staticmethod
    def _analyze_fallback_handling(repo_path: str) -> EvidenceModel:
        """Analyze graceful degradation and fallback strategies."""
        indicators = []
        evidence = []

        # Check for fallback logic
        has_fallback = ImplementationQualityAnalyzer._search_files(
            repo_path,
            r"(fallback|default.*value|fallback.*response|graceful.*degrad)"
        )

        # Check for default values
        has_defaults = ImplementationQualityAnalyzer._search_files(
            repo_path,
            r"(default|DEFAULT|default_to|or\s+\w+)"
        )

        # Check for feature flags
        has_feature_flags = ImplementationQualityAnalyzer._search_files(
            repo_path,
            r"(feature.*flag|feature.*toggle|toggle|flag)"
        )

        if has_fallback:
            indicators.append("Fallback strategies")
            evidence.append("Fallback logic detected")

        if has_defaults:
            indicators.append("Default values")
            evidence.append("Default handling found")

        if has_feature_flags:
            indicators.append("Feature flags")
            evidence.append("Feature flag management detected")

        confidence = 0.5 if indicators else 0.2
        value = " + ".join(indicators) if indicators else "Limited fallback handling"

        return EvidenceModel(value=value, confidence=confidence, evidence=evidence)

    @staticmethod
    def _analyze_dependency_management(repo_path: str) -> EvidenceModel:
        """Analyze dependency management quality."""
        indicators = []
        evidence = []

        # Check for lock files
        has_lock = any(os.path.exists(os.path.join(repo_path, f)) 
                      for f in ["package-lock.json", "yarn.lock", "Pipfile.lock", "poetry.lock"])

        # Check for version pinning
        has_version_pins = ImplementationQualityAnalyzer._search_files(
            repo_path,
            r"([0-9]+\.[0-9]+\.[0-9]+)"
        )

        # Check for dependency scanning
        has_scanning = any(os.path.exists(os.path.join(repo_path, f))
                          for f in ["dependabot.yml", ".snyk", "renovate.json"])

        if has_lock:
            indicators.append("Lock files")
            evidence.append("Dependency lock files detected")

        if has_version_pins:
            indicators.append("Version pinning")
            evidence.append("Specific version constraints found")

        if has_scanning:
            indicators.append("Dependency scanning")
            evidence.append("Automated dependency checks configured")

        confidence = 0.6 + len(indicators) * 0.1
        value = " + ".join(indicators) if indicators else "Basic dependency mgmt"

        return EvidenceModel(value=value, confidence=confidence, evidence=evidence)

    @staticmethod
    def _search_files(repo_path: str, pattern: str, max_files: int = 100) -> int:
        """Search for a pattern in Python/TypeScript/JavaScript files."""
        count = 0
        file_count = 0
        
        for root, dirs, files in os.walk(repo_path):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', 'venv', '.env', 'dist', 'build']]
            
            for file in files[:5]:  # Limit files per directory
                if file.endswith(('.py', '.ts', '.tsx', '.js', '.jsx', '.java', '.go', '.rs')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if re.search(pattern, content, re.IGNORECASE):
                                count += 1
                        file_count += 1
                    except Exception:
                        pass
            
            if file_count >= max_files:
                break
        
        return count
