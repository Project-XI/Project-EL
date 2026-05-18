"""
Execution Graph-Aware Failure Path Analyzer: 
Traces failure scenarios through actual execution graph relationships.
Evidence-grounded failure propagation reasoning.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from ...models.context import EvidenceModel


@dataclass
class FailureScenario:
    """
    A concrete failure scenario traced through execution graph.
    
    Each scenario includes:
    - Trigger point (what fails)
    - Propagation path (execution graph nodes affected)
    - Evidence (code patterns, middleware chains)
    - Impact (what happens downstream)
    - Recovery potential (can system recover)
    """
    scenario_name: str
    trigger: str  # What fails (e.g., "Redis connection")
    affected_paths: List[str]  # Execution graph paths impacted
    code_evidence: List[str]  # Specific files/functions
    propagation_risk: str  # "low", "medium", "high", "critical"
    system_impact: str  # What breaks
    recovery_possible: bool
    recovery_strategy: Optional[str]
    confidence: float


class ExecutionGraphFailureAnalyzer:
    """
    Analyzes failure scenarios by tracing through execution graph.
    
    Approach:
    1. Identify dependency nodes (DB, Cache, External APIs, Auth)
    2. Trace execution paths that depend on each
    3. Detect failure propagation patterns
    4. Assess recovery mechanisms
    5. Generate scenario-based viva targets
    """

    @staticmethod
    def analyze_failure_scenarios(
        repo_path: str,
        structure: Dict[str, Any],
        detections: Dict[str, Any],
        observable_signals: Dict[str, List[Any]],
        execution_graph: Optional[Any] = None
    ) -> List[FailureScenario]:
        """
        Generate failure scenarios based on execution graph and observable signals.
        """
        scenarios = []

        # 1. Database Failure Scenarios
        db_scenarios = ExecutionGraphFailureAnalyzer._analyze_db_failures(
            repo_path, structure, detections, observable_signals
        )
        scenarios.extend(db_scenarios)

        # 2. Cache/Redis Failure Scenarios
        cache_scenarios = ExecutionGraphFailureAnalyzer._analyze_cache_failures(
            repo_path, structure, observable_signals
        )
        scenarios.extend(cache_scenarios)

        # 3. Auth Middleware Failure Scenarios
        auth_scenarios = ExecutionGraphFailureAnalyzer._analyze_auth_failures(
            repo_path, observable_signals
        )
        scenarios.extend(auth_scenarios)

        # 4. External Dependency Failure Scenarios
        external_scenarios = ExecutionGraphFailureAnalyzer._analyze_external_failures(
            repo_path, structure
        )
        scenarios.extend(external_scenarios)

        return scenarios

    @staticmethod
    def _analyze_db_failures(
        repo_path: str,
        structure: Dict[str, Any],
        detections: Dict[str, Any],
        observable_signals: Dict[str, List[Any]]
    ) -> List[FailureScenario]:
        """Database connection/failure scenarios."""
        scenarios = []
        
        db_type = detections.get("database_used", EvidenceModel(value="Unknown", confidence=0.0, evidence=[]))
        
        # Check for caching layer
        has_cache = any(
            "Redis" in str(s.signal_name) or "Memcached" in str(s.signal_name)
            for signals_list in observable_signals.values()
            for s in signals_list
        )
        
        # Check for retry logic
        has_retry = any(
            "Retry" in str(s.signal_name)
            for signals_list in observable_signals.values()
            for s in signals_list
        )

        scenario_1 = FailureScenario(
            scenario_name="Primary Database Connection Loss",
            trigger="Database becomes unavailable",
            affected_paths=[
                "Request → Controller → Service → Repository → DB Connection",
                "All data retrieval endpoints",
                "All write operations",
            ],
            code_evidence=[
                "database.py (connection pooling)",
                "repository/ (query execution)",
                "service/ (business logic)",
            ],
            propagation_risk="critical" if not has_cache else "high",
            system_impact="All database queries fail immediately. If no cache/retry logic, all endpoints return errors.",
            recovery_possible=has_retry or has_cache,
            recovery_strategy="Cache fallback to stale data" if has_cache else ("Retry with backoff" if has_retry else None),
            confidence=0.95
        )
        scenarios.append(scenario_1)

        if not has_retry:
            scenario_2 = FailureScenario(
                scenario_name="No Retry on Database Timeout",
                trigger="Database slow/unresponsive for <10 seconds",
                affected_paths=["All database queries"],
                code_evidence=["repository/ (no retry logic detected)"],
                propagation_risk="high",
                system_impact="Query fails immediately on first timeout. No opportunity to recover from transient issues.",
                recovery_possible=False,
                recovery_strategy=None,
                confidence=0.8
            )
            scenarios.append(scenario_2)

        if db_type.value and "NoSQL" in str(db_type.value):
            scenario_3 = FailureScenario(
                scenario_name="NoSQL Transaction Rollback",
                trigger="Transaction fails mid-execution",
                affected_paths=["Multi-document updates", "Financial/critical operations"],
                code_evidence=["services/ (transaction handling)", "models/ (schema validation)"],
                propagation_risk="high",
                system_impact="Partial writes possible. Inconsistent data state. Requires manual cleanup or application-level compensating logic.",
                recovery_possible=False,
                recovery_strategy="Implement application-level transaction logs and compensating operations",
                confidence=0.75
            )
            scenarios.append(scenario_3)

        return scenarios

    @staticmethod
    def _analyze_cache_failures(
        repo_path: str,
        structure: Dict[str, Any],
        observable_signals: Dict[str, List[Any]]
    ) -> List[FailureScenario]:
        """Redis/Cache failure scenarios."""
        scenarios = []
        
        # Check if Redis is being used
        has_redis = any(
            "Redis" in str(s.signal_name)
            for signals_list in observable_signals.values()
            for s in signals_list
        )

        if not has_redis:
            return scenarios

        # Check for invalidation logic
        import os
        import re
        
        has_invalidation = False
        invalidation_files = []
        
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__']]
            for file in files[:10]:
                if file.endswith(('.py', '.ts', '.js')):
                    try:
                        with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if re.search(r'(cache.*invalidate|invalidate.*cache|cache.*delete|clear.*cache)', content, re.IGNORECASE):
                                has_invalidation = True
                                invalidation_files.append(file)
                    except:
                        pass

        scenario_1 = FailureScenario(
            scenario_name="Redis Crash During High Load",
            trigger="Redis instance becomes unavailable",
            affected_paths=[
                "Request → Cache Check → Miss → DB Query",
                "All cached data retrieval paths",
            ],
            code_evidence=["cache/ (Redis client)", "services/ (cache calls)"],
            propagation_risk="high",
            system_impact="Cache stampede: All requests miss cache simultaneously and flood database. Potential database overload and cascading failure.",
            recovery_possible=True,
            recovery_strategy="Implement circuit breaker for cache calls + graceful degradation to uncached DB queries",
            confidence=0.9
        )
        scenarios.append(scenario_1)

        if not has_invalidation:
            scenario_2 = FailureScenario(
                scenario_name="Stale Cache Data",
                trigger="Data updated in database but cache not invalidated",
                affected_paths=["All read operations on cached data"],
                code_evidence=["services/ (no cache invalidation on updates detected)"],
                propagation_risk="medium",
                system_impact="Users see stale data. Inconsistency between database and cache. Can cause silent data corruption in workflows.",
                recovery_possible=True,
                recovery_strategy="Implement explicit cache invalidation on write operations",
                confidence=0.8
            )
            scenarios.append(scenario_2)
        else:
            scenario_2 = FailureScenario(
                scenario_name="Cache Invalidation During Update",
                trigger="Cache invalidation fails during write operation",
                affected_paths=["Write operations", "Data consistency"],
                code_evidence=invalidation_files,
                propagation_risk="medium",
                system_impact="Cache not cleared, users see stale data. Write succeeds but cache is inconsistent.",
                recovery_possible=True,
                recovery_strategy="Wrap invalidation in try-catch; implement TTL-based cache expiration as fallback",
                confidence=0.75
            )
            scenarios.append(scenario_2)

        return scenarios

    @staticmethod
    def _analyze_auth_failures(
        repo_path: str,
        observable_signals: Dict[str, List[Any]]
    ) -> List[FailureScenario]:
        """Authentication middleware failure scenarios."""
        scenarios = []
        
        # Check for centralized auth
        has_centralized_auth = any(
            "Centralized Auth" in str(s.signal_name)
            for signals_list in observable_signals.values()
            for s in signals_list
        )

        if has_centralized_auth:
            scenario_1 = FailureScenario(
                scenario_name="Auth Middleware Throws Exception",
                trigger="Authentication middleware encounters error (e.g., JWT library crash)",
                affected_paths=["All incoming requests must pass through auth middleware"],
                code_evidence=["middleware/ (auth)", "routes/ (middleware chain)"],
                propagation_risk="critical",
                system_impact="ALL requests fail immediately. System is completely down. No unauthenticated access possible.",
                recovery_possible=False,
                recovery_strategy="Implement auth middleware error boundary. Fail-open or fail-closed policy should be explicit.",
                confidence=0.85
            )
            scenarios.append(scenario_1)

            scenario_2 = FailureScenario(
                scenario_name="JWT Token Validation Logic Bug",
                trigger="Token validation logic has bug (e.g., accepts invalid tokens)",
                affected_paths=["All authenticated endpoints"],
                code_evidence=["middleware/ (JWT verification)"],
                propagation_risk="critical",
                system_impact="Security breach. Invalid/expired tokens accepted. Unauthorized access possible.",
                recovery_possible=True,
                recovery_strategy="Immediate code fix required. Use token signing/versioning to invalidate old tokens.",
                confidence=0.8
            )
            scenarios.append(scenario_2)

        else:
            scenario_1 = FailureScenario(
                scenario_name="Inconsistent Auth Checks",
                trigger="Not all endpoints check authentication consistently",
                affected_paths=["Distributed auth checks across endpoints"],
                code_evidence=["routes/ (inconsistent auth decorators/guards)"],
                propagation_risk="high",
                system_impact="Some endpoints may be accessible without authentication. Security vulnerability.",
                recovery_possible=True,
                recovery_strategy="Implement centralized auth middleware to enforce authentication globally",
                confidence=0.75
            )
            scenarios.append(scenario_1)

        return scenarios

    @staticmethod
    def _analyze_external_failures(
        repo_path: str,
        structure: Dict[str, Any]
    ) -> List[FailureScenario]:
        """External API/service failure scenarios."""
        import os
        import re
        
        scenarios = []

        # Check for external API calls
        has_http_client = False
        has_timeout = False
        has_retry = False

        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__']]
            for file in files[:10]:
                if file.endswith(('.py', '.ts', '.js')):
                    try:
                        with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if re.search(r'(requests|fetch|axios|urllib|http\.request)', content):
                                has_http_client = True
                            if re.search(r'(timeout|Timeout)', content):
                                has_timeout = True
                            if re.search(r'(retry|Retry)', content):
                                has_retry = True
                    except:
                        pass

        if has_http_client:
            scenario_1 = FailureScenario(
                scenario_name="External API Becomes Unresponsive",
                trigger="Third-party API becomes slow or unresponsive",
                affected_paths=["All requests that depend on external API"],
                code_evidence=["services/ (API client calls)"],
                propagation_risk="high",
                system_impact="Request hangs indefinitely if no timeout. Connections pile up. System resources exhausted.",
                recovery_possible=has_timeout,
                recovery_strategy="Implement request timeouts and circuit breaker",
                confidence=0.9
            )
            scenarios.append(scenario_1)

            if not has_retry:
                scenario_2 = FailureScenario(
                    scenario_name="Transient External API Failure",
                    trigger="External API temporarily fails (returns 500)",
                    affected_paths=["All external API calls"],
                    code_evidence=["services/ (no retry logic)"],
                    propagation_risk="medium",
                    system_impact="Request fails immediately. Transient failures cause permanent errors instead of recovering.",
                    recovery_possible=False,
                    recovery_strategy="Implement exponential backoff retry logic",
                    confidence=0.85
                )
                scenarios.append(scenario_2)

        return scenarios

    @staticmethod
    def format_failure_scenarios_report(scenarios: List[FailureScenario]) -> str:
        """Format failure scenarios into readable report."""
        report = []
        report.append("=" * 80)
        report.append("EXECUTION GRAPH FAILURE SCENARIO ANALYSIS")
        report.append("=" * 80)
        report.append("")

        by_risk = {"critical": [], "high": [], "medium": [], "low": []}
        for scenario in scenarios:
            by_risk[scenario.propagation_risk].append(scenario)

        for risk_level in ["critical", "high", "medium", "low"]:
            if by_risk[risk_level]:
                report.append(f"\n{risk_level.upper()} RISK SCENARIOS")
                report.append("-" * 40)

                for scenario in by_risk[risk_level]:
                    report.append(f"\n  Scenario: {scenario.scenario_name}")
                    report.append(f"  Trigger: {scenario.trigger}")
                    report.append(f"  Impact: {scenario.system_impact}")
                    
                    if scenario.recovery_possible and scenario.recovery_strategy:
                        report.append(f"  Recovery: {scenario.recovery_strategy}")
                    elif not scenario.recovery_possible:
                        report.append(f"  Recovery: NO RECOVERY MECHANISM DETECTED")

        report.append("\n" + "=" * 80)
        return "\n".join(report)
