"""
Observable Engineering Signals: Evidence-grounded observations of implementation patterns.
No speculation, no arbitrary scores - only explicitly grounded signals with evidence references.
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from ...models.context import EvidenceModel


@dataclass
class EngineeringSignal:
    """
    An observable engineering signal with explicit evidence.
    
    Signals are NOT scores or grades. They are concrete observations
    of implementation patterns, each traceable to specific code evidence.
    """
    signal_name: str
    category: str  # e.g., "error_handling", "resilience", "observability"
    confidence: float  # 0.0-1.0 based on evidence strength
    evidence_files: List[str]  # Specific files containing evidence
    description: str  # What was observed
    risk_level: str  # "low", "medium", "high", "critical" or "N/A"
    recommendation: str  # Only if risk is detected


class ObservableSignalsEngine:
    """
    Generates explicit, evidence-grounded engineering signals.
    
    Philosophy:
    - Observable signals are facts about the codebase, not judgments
    - Each signal must reference specific files/patterns
    - No arbitrary scores or grades
    - Risk levels only where actual risks are detected
    - Recommendations only when actionable
    """

    @staticmethod
    def extract_signals(
        repo_path: str,
        structure: Dict[str, Any],
        detections: Dict[str, Any],
        execution_graph: Any = None
    ) -> Dict[str, List[EngineeringSignal]]:
        """
        Extract observable signals across 6 implementation categories.
        Returns signals grouped by category with full evidence tracing.
        """
        signals = {
            "error_handling": ObservableSignalsEngine._extract_error_handling_signals(repo_path),
            "resilience_patterns": ObservableSignalsEngine._extract_resilience_signals(repo_path),
            "observability": ObservableSignalsEngine._extract_observability_signals(repo_path),
            "architecture": ObservableSignalsEngine._extract_architecture_signals(repo_path, structure),
            "auth_consistency": ObservableSignalsEngine._extract_auth_signals(repo_path),
            "operational_dependencies": ObservableSignalsEngine._extract_operational_signals(repo_path),
        }
        return signals

    @staticmethod
    def _extract_error_handling_signals(repo_path: str) -> List[EngineeringSignal]:
        """Observable patterns in error handling implementation."""
        import os
        import re
        
        signals = []
        
        # Check for centralized error handler
        error_handlers_found = []
        try_catch_count = 0
        
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', 'venv']]
            
            for file in files[:10]:
                if file.endswith(('.py', '.ts', '.tsx', '.js', '.jsx')):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                            if re.search(r'(error_handler|ErrorHandler|exception_handler|ExceptionHandler)', content):
                                error_handlers_found.append(filepath.replace(repo_path, ''))
                            
                            try_catch_count += len(re.findall(r'(try:|except:|catch)', content))
                    except:
                        pass
        
        if error_handlers_found:
            signals.append(EngineeringSignal(
                signal_name="Centralized Error Handler Detected",
                category="error_handling",
                confidence=0.85,
                evidence_files=error_handlers_found,
                description=f"Centralized error handling middleware found in {len(error_handlers_found)} file(s)",
                risk_level="N/A",
                recommendation=""
            ))
        else:
            signals.append(EngineeringSignal(
                signal_name="No Centralized Error Handler",
                category="error_handling",
                confidence=0.7,
                evidence_files=[],
                description="No centralized error handler detected. Error handling may be distributed.",
                risk_level="medium",
                recommendation="Consider implementing centralized error middleware for consistent error responses."
            ))
        
        if try_catch_count < 5:
            signals.append(EngineeringSignal(
                signal_name="Limited Exception Coverage",
                category="error_handling",
                confidence=0.6,
                evidence_files=[],
                description=f"Limited exception handling detected (~{try_catch_count} try/catch blocks found)",
                risk_level="medium",
                recommendation="Increase try-catch coverage for critical code paths."
            ))
        
        return signals

    @staticmethod
    def _extract_resilience_signals(repo_path: str) -> List[EngineeringSignal]:
        """Observable patterns in resilience implementation."""
        import os
        import re
        
        signals = []
        resilience_patterns = {
            "retry_logic": r"(retry|Retry|RETRY|exponential.*backoff)",
            "circuit_breaker": r"(circuit.*breaker|CircuitBreaker)",
            "timeout_handling": r"(timeout|Timeout|TIMEOUT)",
            "connection_pooling": r"(pool|Pool|POOL|connection)",
        }
        
        found_patterns = {}
        
        for pattern_name, pattern_regex in resilience_patterns.items():
            found_files = []
            for root, dirs, files in os.walk(repo_path):
                dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__']]
                for file in files[:5]:
                    if file.endswith(('.py', '.ts', '.js')):
                        filepath = os.path.join(root, file)
                        try:
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                if re.search(pattern_regex, f.read(), re.IGNORECASE):
                                    found_files.append(filepath.replace(repo_path, ''))
                        except:
                            pass
            found_patterns[pattern_name] = found_files
        
        if found_patterns["retry_logic"]:
            signals.append(EngineeringSignal(
                signal_name="Retry Logic Implementation",
                category="resilience_patterns",
                confidence=0.8,
                evidence_files=found_patterns["retry_logic"],
                description=f"Retry logic detected in {len(found_patterns['retry_logic'])} file(s)",
                risk_level="N/A",
                recommendation=""
            ))
        
        if found_patterns["circuit_breaker"]:
            signals.append(EngineeringSignal(
                signal_name="Circuit Breaker Pattern",
                category="resilience_patterns",
                confidence=0.85,
                evidence_files=found_patterns["circuit_breaker"],
                description="Circuit breaker pattern implemented for fault tolerance",
                risk_level="N/A",
                recommendation=""
            ))
        elif found_patterns["timeout_handling"]:
            signals.append(EngineeringSignal(
                signal_name="Timeout Handling Without Circuit Breaker",
                category="resilience_patterns",
                confidence=0.7,
                evidence_files=found_patterns["timeout_handling"],
                description="Timeout handling present but no circuit breaker for cascading failure prevention",
                risk_level="medium",
                recommendation="Consider adding circuit breaker pattern to prevent cascading failures to dependent services."
            ))
        else:
            signals.append(EngineeringSignal(
                signal_name="Limited Resilience Patterns",
                category="resilience_patterns",
                confidence=0.6,
                evidence_files=[],
                description="No retry, circuit breaker, or timeout handling detected",
                risk_level="high",
                recommendation="Implement resilience patterns for external API/database dependencies."
            ))
        
        return signals

    @staticmethod
    def _extract_observability_signals(repo_path: str) -> List[EngineeringSignal]:
        """Observable logging, monitoring, tracing setup."""
        import os
        
        signals = []
        
        observability_indicators = {
            "structured_logging": ["winston", "pino", "bunyan", "log4js"],
            "metrics": ["prometheus", "statsd", "graphite"],
            "tracing": ["jaeger", "opentelemetry", "zipkin"],
            "health_checks": ["health", "readiness", "liveness"],
        }
        
        found_indicators = {}
        
        for category, keywords in observability_indicators.items():
            for root, dirs, files in os.walk(repo_path):
                dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules']]
                for file in files:
                    if file.endswith(('.py', '.ts', '.js', '.json')):
                        filepath = os.path.join(root, file)
                        try:
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                for keyword in keywords:
                                    if keyword.lower() in content.lower():
                                        if category not in found_indicators:
                                            found_indicators[category] = []
                                        found_indicators[category].append(filepath.replace(repo_path, ''))
                                        break
                        except:
                            pass
        
        if found_indicators.get("structured_logging"):
            signals.append(EngineeringSignal(
                signal_name="Structured Logging Present",
                category="observability",
                confidence=0.85,
                evidence_files=found_indicators["structured_logging"][:3],
                description="Structured logging framework detected",
                risk_level="N/A",
                recommendation=""
            ))
        
        if found_indicators.get("metrics"):
            signals.append(EngineeringSignal(
                signal_name="Metrics Collection",
                category="observability",
                confidence=0.8,
                evidence_files=found_indicators["metrics"][:2],
                description="Metrics collection framework detected",
                risk_level="N/A",
                recommendation=""
            ))
        
        if found_indicators.get("tracing"):
            signals.append(EngineeringSignal(
                signal_name="Distributed Tracing",
                category="observability",
                confidence=0.85,
                evidence_files=found_indicators["tracing"][:2],
                description="Distributed tracing framework detected",
                risk_level="N/A",
                recommendation=""
            ))
        
        if not found_indicators:
            signals.append(EngineeringSignal(
                signal_name="Minimal Observability Infrastructure",
                category="observability",
                confidence=0.7,
                evidence_files=[],
                description="No structured logging, metrics, or tracing frameworks detected",
                risk_level="medium",
                recommendation="Add observability infrastructure for production debugging and monitoring."
            ))
        
        return signals

    @staticmethod
    def _extract_architecture_signals(repo_path: str, structure: Dict[str, Any]) -> List[EngineeringSignal]:
        """Observable architecture patterns and separation."""
        import os
        
        signals = []
        
        # Check for layer directories
        common_layers = ["models", "controllers", "services", "routes", "middleware", "utils"]
        found_layers = []
        
        try:
            for item in os.listdir(repo_path):
                if item in common_layers and os.path.isdir(os.path.join(repo_path, item)):
                    found_layers.append(item)
        except:
            pass
        
        if len(found_layers) >= 4:
            signals.append(EngineeringSignal(
                signal_name="Multi-Layer Architecture",
                category="architecture",
                confidence=0.8,
                evidence_files=found_layers,
                description=f"Clear architectural layers detected: {', '.join(found_layers)}",
                risk_level="N/A",
                recommendation=""
            ))
        elif len(found_layers) >= 2:
            signals.append(EngineeringSignal(
                signal_name="Partial Layer Separation",
                category="architecture",
                confidence=0.6,
                evidence_files=found_layers,
                description=f"Some layer separation: {', '.join(found_layers)}. Others may be missing.",
                risk_level="low",
                recommendation="Consider adding missing architectural layers for better separation of concerns."
            ))
        else:
            signals.append(EngineeringSignal(
                signal_name="Unclear Architecture Separation",
                category="architecture",
                confidence=0.5,
                evidence_files=[],
                description="No clear architectural layers detected",
                risk_level="medium",
                recommendation="Implement clear separation between models, business logic, and routing."
            ))
        
        return signals

    @staticmethod
    def _extract_auth_signals(repo_path: str) -> List[EngineeringSignal]:
        """Observable authentication and authorization patterns."""
        import os
        import re
        
        signals = []
        
        auth_patterns = {
            "centralized_auth": r"(auth.*middleware|middleware.*auth|AuthMiddleware)",
            "token_validation": r"(verify.*token|validate.*jwt|check.*token)",
            "rbac": r"(role.*based|rbac|permission|authorize)",
        }
        
        found_patterns = {}
        
        for pattern_name, pattern_regex in auth_patterns.items():
            found_files = []
            for root, dirs, files in os.walk(repo_path):
                dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules']]
                for file in files[:5]:
                    if file.endswith(('.py', '.ts', '.js')):
                        filepath = os.path.join(root, file)
                        try:
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                if re.search(pattern_regex, f.read(), re.IGNORECASE):
                                    found_files.append(filepath.replace(repo_path, ''))
                        except:
                            pass
            found_patterns[pattern_name] = found_files
        
        if found_patterns["centralized_auth"]:
            signals.append(EngineeringSignal(
                signal_name="Centralized Auth Middleware",
                category="auth_consistency",
                confidence=0.85,
                evidence_files=found_patterns["centralized_auth"],
                description="Centralized authentication middleware detected",
                risk_level="N/A",
                recommendation=""
            ))
        
        if found_patterns["token_validation"]:
            signals.append(EngineeringSignal(
                signal_name="Token Validation Logic",
                category="auth_consistency",
                confidence=0.8,
                evidence_files=found_patterns["token_validation"],
                description="Token verification/validation logic found",
                risk_level="N/A",
                recommendation=""
            ))
        
        if not found_patterns["centralized_auth"]:
            signals.append(EngineeringSignal(
                signal_name="No Centralized Auth",
                category="auth_consistency",
                confidence=0.7,
                evidence_files=[],
                description="No centralized auth middleware detected. Auth may be distributed across routes.",
                risk_level="high",
                recommendation="Implement centralized authentication middleware to ensure consistent auth policies."
            ))
        
        if found_patterns["rbac"]:
            signals.append(EngineeringSignal(
                signal_name="Role-Based Access Control",
                category="auth_consistency",
                confidence=0.8,
                evidence_files=found_patterns["rbac"],
                description="RBAC patterns detected for permission management",
                risk_level="N/A",
                recommendation=""
            ))
        
        return signals

    @staticmethod
    def _extract_operational_signals(repo_path: str) -> List[EngineeringSignal]:
        """Observable operational dependencies and deployment patterns."""
        import os
        
        signals = []
        
        deployment_configs = {
            "docker": ["Dockerfile", "docker-compose.yml"],
            "kubernetes": ["k8s/", "helm/"],
            "ci_cd": [".github/workflows", ".gitlab-ci.yml", ".circleci"],
            "env_config": [".env.example", "config/"],
        }
        
        found_configs = {}
        
        for config_type, files_to_check in deployment_configs.items():
            for filename in files_to_check:
                if os.path.exists(os.path.join(repo_path, filename)):
                    if config_type not in found_configs:
                        found_configs[config_type] = []
                    found_configs[config_type].append(filename)
        
        if found_configs.get("docker"):
            signals.append(EngineeringSignal(
                signal_name="Containerized Deployment",
                category="operational_dependencies",
                confidence=0.9,
                evidence_files=found_configs["docker"],
                description=f"Docker configuration found: {', '.join(found_configs['docker'])}",
                risk_level="N/A",
                recommendation=""
            ))
        
        if found_configs.get("kubernetes"):
            signals.append(EngineeringSignal(
                signal_name="Kubernetes Orchestration",
                category="operational_dependencies",
                confidence=0.9,
                evidence_files=found_configs["kubernetes"],
                description="Kubernetes manifests or Helm charts detected",
                risk_level="N/A",
                recommendation=""
            ))
        
        if found_configs.get("ci_cd"):
            signals.append(EngineeringSignal(
                signal_name="Automated CI/CD Pipeline",
                category="operational_dependencies",
                confidence=0.9,
                evidence_files=found_configs["ci_cd"],
                description="Automated CI/CD pipeline configuration detected",
                risk_level="N/A",
                recommendation=""
            ))
        
        if found_configs.get("env_config"):
            signals.append(EngineeringSignal(
                signal_name="Environment Configuration",
                category="operational_dependencies",
                confidence=0.85,
                evidence_files=found_configs["env_config"],
                description="Environment configuration templates found",
                risk_level="N/A",
                recommendation=""
            ))
        
        if not found_configs:
            signals.append(EngineeringSignal(
                signal_name="No Deployment Automation Detected",
                category="operational_dependencies",
                confidence=0.6,
                evidence_files=[],
                description="No Docker, Kubernetes, or CI/CD configuration found",
                risk_level="medium",
                recommendation="Add containerization and/or deployment automation configuration."
            ))
        
        return signals

    @staticmethod
    def format_signals_report(signals_by_category: Dict[str, List[EngineeringSignal]]) -> str:
        """Format signals into a readable report."""
        report = []
        report.append("=" * 80)
        report.append("OBSERVABLE ENGINEERING SIGNALS REPORT")
        report.append("=" * 80)
        report.append("")
        
        for category, signals_list in signals_by_category.items():
            report.append(f"\n{category.upper()}")
            report.append("-" * 40)
            
            for signal in signals_list:
                confidence_pct = int(signal.confidence * 100)
                report.append(f"\n  ✓ {signal.signal_name}")
                report.append(f"    Confidence: {confidence_pct}%")
                
                if signal.risk_level != "N/A":
                    report.append(f"    Risk Level: {signal.risk_level.upper()}")
                
                report.append(f"    Observation: {signal.description}")
                
                if signal.evidence_files:
                    report.append(f"    Evidence Files: {', '.join(signal.evidence_files[:3])}")
                
                if signal.recommendation:
                    report.append(f"    → Recommendation: {signal.recommendation}")
        
        report.append("\n" + "=" * 80)
        return "\n".join(report)
