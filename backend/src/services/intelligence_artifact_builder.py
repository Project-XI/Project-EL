"""
Intelligence Artifact Builder — Converts ORACLE StructuredContext to IntelligenceArtifact

Deterministic transformation that packages ORACLE's analysis into a structured,
explainable handoff format for MAIN Agent.
"""

import hashlib
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.models.intelligence_artifact import (
    IntelligenceArtifact,
    VivaTarget,
    ExecutionNode,
    ExecutionPath,
    RuntimeDependency,
    FailureScenario,
    ImplementationSignal,
    WeakPoint,
    IntelligenceCategory,
    AdaptiveThreshold,
    IntelligenceHandoffEvent,
)
from src.models.context import StructuredContext, RuntimeRisk, VivaTarget as OracleVivaTarget


class IntelligenceArtifactBuilder:
    """
    Deterministic builder that transforms ORACLE StructuredContext into
    IntelligenceArtifact for MAIN Agent consumption.
    """

    @staticmethod
    def build(
        session_id: str,
        structured_context: StructuredContext,
        analysis_duration_seconds: float = 0.0,
        repo_path: Optional[str] = None,
    ) -> IntelligenceArtifact:
        """
        Build IntelligenceArtifact from StructuredContext.

        Args:
            session_id: The exam session ID
            structured_context: ORACLE's StructuredContext output
            analysis_duration_seconds: Time taken for analysis
            repo_path: Optional path to cloned repo for evidence collection

        Returns:
            IntelligenceArtifact ready for MAIN Agent
        """

        # Extract backend stack
        backend_stack = {
            "framework": structured_context.backend_framework.value or "Unknown",
            "database": structured_context.database_used.value or "Unknown",
            "authentication": structured_context.authentication_system.value or "Unknown",
        }

        # Extract frontend stack if present
        frontend_stack = None
        if structured_context.frontend_framework:
            frontend_stack = {"framework": structured_context.frontend_framework.value or "Unknown"}

        # Build execution graph nodes
        execution_nodes = IntelligenceArtifactBuilder._build_execution_nodes(structured_context)

        # Build execution paths
        execution_paths = IntelligenceArtifactBuilder._build_execution_paths(
            structured_context, execution_nodes
        )

        # Extract runtime dependencies
        runtime_dependencies = IntelligenceArtifactBuilder._extract_runtime_dependencies(
            structured_context, execution_nodes
        )

        # Extract failure scenarios
        failure_scenarios = IntelligenceArtifactBuilder._extract_failure_scenarios(
            structured_context, execution_paths
        )

        # Extract implementation risks
        implementation_risks = IntelligenceArtifactBuilder._extract_implementation_risks(
            structured_context
        )

        # Extract weak points
        weak_points = IntelligenceArtifactBuilder._extract_weak_points(
            structured_context, implementation_risks
        )

        # Build viva targets
        viva_targets = IntelligenceArtifactBuilder._build_viva_targets(
            structured_context, weak_points, execution_nodes
        )

        # Build adaptive thresholds
        adaptive_thresholds = IntelligenceArtifactBuilder._build_adaptive_thresholds(viva_targets)

        # Extract implementation signals
        implementation_signals = IntelligenceArtifactBuilder._extract_implementation_signals(
            structured_context
        )

        # Build summary and key findings
        summary, key_findings = IntelligenceArtifactBuilder._build_summary(
            structured_context, failure_scenarios, weak_points, viva_targets
        )

        # Create artifact
        artifact = IntelligenceArtifact(
            session_id=session_id,
            oracle_version="v1",
            analysis_duration_seconds=analysis_duration_seconds,
            project_name=structured_context.project_name.value,
            project_type=structured_context.project_type.value,
            backend_stack=backend_stack,
            frontend_stack=frontend_stack,
            architecture_pattern=structured_context.architecture_pattern.value,
            execution_graph_nodes=execution_nodes,
            execution_paths=execution_paths,
            runtime_dependencies=runtime_dependencies,
            failure_scenarios=failure_scenarios,
            implementation_risks=implementation_risks,
            weak_points=weak_points,
            viva_targets=viva_targets,
            adaptive_thresholds=adaptive_thresholds,
            implementation_signals=implementation_signals,
            summary=summary,
            key_findings=key_findings,
            analysis_confidence=structured_context.complexity_mismatch.confidence
            if structured_context.complexity_mismatch
            else 0.8,
        )

        # Compute deterministic hash for replay verification
        artifact.deterministic_hash = IntelligenceArtifactBuilder._compute_hash(artifact)

        return artifact

    @staticmethod
    def _build_execution_nodes(context: StructuredContext) -> List[ExecutionNode]:
        """Extract execution nodes from context."""
        nodes = []

        # Build from execution graph
        if context.execution_graph:
            for i, flow_node in enumerate(context.execution_graph.nodes):
                node = ExecutionNode(
                    node_id=flow_node.id,
                    label=flow_node.label,
                    node_type=flow_node.type.value if hasattr(flow_node.type, "value") else str(flow_node.type),
                    implementation_details=f"Node: {flow_node.label}, Metadata: {flow_node.metadata}",
                    dependencies=[],
                    failure_modes=[],
                )
                nodes.append(node)

        # Build from middleware chain
        for middleware in context.middleware_chain:
            node = ExecutionNode(
                node_id=f"middleware_{len(nodes)}",
                label=middleware.value,
                node_type="MIDDLEWARE",
                implementation_details=f"Middleware: {middleware.value}, Confidence: {middleware.confidence}",
                dependencies=[],
                failure_modes=["Middleware exception", "Request rejection"],
            )
            nodes.append(node)

        return nodes

    @staticmethod
    def _build_execution_paths(context: StructuredContext, nodes: List[ExecutionNode]) -> List[ExecutionPath]:
        """Build execution paths from flows."""
        paths = []

        # Happy path
        if context.execution_graph.nodes:
            happy_path_nodes = [n.id for n in context.execution_graph.nodes[:5]]  # First 5 nodes
            paths.append(
                ExecutionPath(
                    path_id="happy_path",
                    description="Normal request lifecycle",
                    nodes=happy_path_nodes,
                    scenario="HAPPY_PATH",
                    criticality="HIGH",
                )
            )

        # Error path
        if context.execution_graph.failure_paths:
            paths.append(
                ExecutionPath(
                    path_id="error_path",
                    description="Error handling and recovery",
                    nodes=context.execution_graph.failure_paths[:3],
                    scenario="ERROR_PATH",
                    criticality="HIGH",
                )
            )

        return paths

    @staticmethod
    def _extract_runtime_dependencies(context: StructuredContext, nodes: List[ExecutionNode]) -> List[RuntimeDependency]:
        """Extract runtime dependencies from context."""
        deps = []

        # Database dependency
        if context.database_used and context.database_used.value != "Unknown":
            deps.append(
                RuntimeDependency(
                    name=context.database_used.value,
                    type="DATABASE",
                    usage_pattern="Query/Mutation in request lifecycle",
                    criticality="CRITICAL",
                    evidence_snippet=f"Technology detected: {context.database_used.value}",
                )
            )

        # Authentication dependency
        if context.authentication_system and context.authentication_system.value != "Unknown":
            deps.append(
                RuntimeDependency(
                    name=context.authentication_system.value,
                    type="MIDDLEWARE",
                    usage_pattern="Request validation and session management",
                    criticality="CRITICAL",
                )
            )

        # Framework dependency
        if context.backend_framework and context.backend_framework.value != "Unknown":
            deps.append(
                RuntimeDependency(
                    name=context.backend_framework.value,
                    type="LIBRARY",
                    usage_pattern="Request routing and response handling",
                    criticality="CRITICAL",
                )
            )

        return deps

    @staticmethod
    def _extract_failure_scenarios(context: StructuredContext, paths: List[ExecutionPath]) -> List[FailureScenario]:
        """Extract failure scenarios from context."""
        scenarios = []

        # Build from runtime risks
        for i, risk in enumerate(context.runtime_risks):
            scenario = FailureScenario(
                scenario_name=f"Risk: {risk.value}",
                trigger="Runtime condition: " + risk.value,
                propagation_path=["Request Handler", "Service Layer", "Error Handler"],
                impact=risk.value,
                severity=risk.severity,
                detectability="MODERATE",
                evidence_snippet=f"Risk severity: {risk.severity}, Evidence: {risk.evidence}",
            )
            scenarios.append(scenario)

        # Add common failure scenarios
        scenarios.extend(
            [
                FailureScenario(
                    scenario_name="Database Connection Failure",
                    trigger="DB unreachable or timeout",
                    propagation_path=["DB Query", "Service Layer", "Error Handler"],
                    impact="Request failure, user sees error",
                    severity="HIGH",
                    detectability="EASY",
                ),
                FailureScenario(
                    scenario_name="Authentication Bypass",
                    trigger="Invalid token or missing auth header",
                    propagation_path=["Auth Middleware", "Error Handler"],
                    impact="Unauthorized access or request rejection",
                    severity="CRITICAL",
                    detectability="HARD",
                ),
                FailureScenario(
                    scenario_name="Race Condition on Concurrent Writes",
                    trigger="Multiple requests modifying same resource",
                    propagation_path=["DB Query", "Update Logic", "Inconsistency"],
                    impact="Data corruption or lost updates",
                    severity="CRITICAL",
                    detectability="HARD",
                ),
            ]
        )

        return scenarios

    @staticmethod
    def _extract_implementation_risks(context: StructuredContext) -> List[Dict[str, Any]]:
        """Extract implementation risks from context."""
        risks = []

        for runtime_risk in context.runtime_risks:
            risks.append(
                {
                    "area": "Runtime",
                    "risk": runtime_risk.value,
                    "severity": runtime_risk.severity,
                    "evidence": runtime_risk.evidence,
                }
            )

        for inconsistency in context.inconsistencies:
            risks.append(
                {
                    "area": "Consistency",
                    "risk": inconsistency.issue,
                    "severity": inconsistency.severity,
                    "evidence": inconsistency.evidence,
                }
            )

        # Add common implementation risks
        risks.extend(
            [
                {
                    "area": "Caching Strategy",
                    "risk": "Cache invalidation not properly handled",
                    "severity": "HIGH",
                    "evidence": ["Concurrent write scenarios not addressed"],
                },
                {
                    "area": "Error Handling",
                    "risk": "Generic error messages hide specific failures",
                    "severity": "MEDIUM",
                    "evidence": ["Insufficient error logging"],
                },
                {
                    "area": "Async/Concurrency",
                    "risk": "Race conditions in state updates",
                    "severity": "HIGH",
                    "evidence": ["No locking mechanism observed"],
                },
            ]
        )

        return risks

    @staticmethod
    def _extract_weak_points(context: StructuredContext, risks: List[Dict[str, Any]]) -> List[WeakPoint]:
        """Extract weak points for viva probing."""
        weak_points = []

        for risk in risks:
            weak_point = WeakPoint(
                area=risk["area"],
                weakness=risk["risk"],
                why_problematic="Understanding this shows depth of implementation knowledge",
                testing_approach="Ask student to explain how they would handle this scenario",
                evidence_file=None,
            )
            weak_points.append(weak_point)

        return weak_points

    @staticmethod
    def _build_viva_targets(
        context: StructuredContext, weak_points: List[WeakPoint], nodes: List[ExecutionNode]
    ) -> List[VivaTarget]:
        """Build viva targets from context."""
        targets = []

        # Convert ORACLE VivaTargets to IntelligenceArtifact VivaTargets
        for i, oracle_target in enumerate(context.viva_intelligence_targets or []):
            target = VivaTarget(
                target_id=f"target_{i}",
                question=oracle_target.question_target if hasattr(oracle_target, "question_target") else oracle_target.topic,
                category=IntelligenceCategory.ARCHITECTURE,
                difficulty=oracle_target.difficulty,
                depth_score=oracle_target.depth_score if hasattr(oracle_target, "depth_score") else 5.0,
                why_important=f"Question targets {oracle_target.focus}" if hasattr(oracle_target, "focus") else "Core implementation knowledge",
                evidence_references=[],
                follow_up_paths=[],
                expected_coverage=["Implementation details", "Design rationale", "Edge cases"],
                red_flags=["Generic answers", "Vague explanations", "Contradictions"],
            )
            targets.append(target)

        # Add weak-point-based targets
        for i, weak_point in enumerate(weak_points):
            target = VivaTarget(
                target_id=f"weak_point_{i}",
                question=f"How would you handle {weak_point.weakness}?",
                category=IntelligenceCategory.WEAK_POINT,
                difficulty="HARD",
                depth_score=8.0,
                why_important=f"Tests practical handling of: {weak_point.weakness}",
                evidence_references=[],
                follow_up_paths=[
                    "Probe error handling",
                    "Ask about retry logic",
                    "Inquire about monitoring",
                ],
                expected_coverage=[
                    "Specific technical approach",
                    "Trade-offs considered",
                    "Testing strategy",
                ],
                red_flags=[
                    "Hand-waving solution",
                    "Ignoring trade-offs",
                    "No mention of testing",
                ],
            )
            targets.append(target)

        return targets

    @staticmethod
    def _build_adaptive_thresholds(targets: List[VivaTarget]) -> List[AdaptiveThreshold]:
        """Build adaptive thresholds for viva difficulty escalation."""
        thresholds = []

        # Group targets by category for adaptive logic
        categories = set(t.category for t in targets)
        for category in categories:
            category_targets = [t for t in targets if t.category == category]
            weak_trigger = [t.question for t in category_targets if t.difficulty == "HARD"]

            threshold = AdaptiveThreshold(
                topic=category.value,
                weak_point_triggers=weak_trigger[:3],
                strong_point_indicators=[t.question for t in category_targets if t.difficulty == "FOUNDATIONAL"],
                contradiction_escalation=True,
            )
            thresholds.append(threshold)

        return thresholds

    @staticmethod
    def _extract_implementation_signals(context: StructuredContext) -> List[ImplementationSignal]:
        """Extract observable implementation signals from context."""
        signals = []

        # Technology stack signals
        if context.backend_framework and context.backend_framework.value != "Unknown":
            signals.append(
                ImplementationSignal(
                    signal_type="DESIGN_PATTERN",
                    description=f"Backend framework choice: {context.backend_framework.value}",
                    evidence=f"Framework: {context.backend_framework.value}",
                    confidence=context.backend_framework.confidence,
                    risk_level="LOW",
                )
            )

        # Architecture pattern signal
        if context.architecture_pattern and context.architecture_pattern.value:
            signals.append(
                ImplementationSignal(
                    signal_type="DESIGN_PATTERN",
                    description=f"Architecture pattern: {context.architecture_pattern.value}",
                    evidence=f"Inferred pattern: {context.architecture_pattern.value}",
                    confidence=context.architecture_pattern.confidence,
                    risk_level="LOW",
                )
            )

        # Middleware signals
        for middleware in context.middleware_chain:
            signals.append(
                ImplementationSignal(
                    signal_type="ERROR_HANDLING",
                    description=f"Middleware layer: {middleware.value}",
                    evidence=middleware.value,
                    confidence=middleware.confidence,
                    risk_level="MEDIUM",
                )
            )

        return signals

    @staticmethod
    def _build_summary(
        context: StructuredContext,
        failure_scenarios: List[FailureScenario],
        weak_points: List[WeakPoint],
        viva_targets: List[VivaTarget],
    ) -> tuple[str, List[str]]:
        """Build human-readable summary and key findings."""
        
        summary = f"""
ORACLE Analysis Summary for {context.project_name.value}

Project: {context.project_type.value}
Architecture: {context.architecture_pattern.value}
Backend: {context.backend_framework.value}
Database: {context.database_used.value}

Analysis Results:
- Execution paths identified: {len(context.execution_graph.nodes)} nodes
- Failure scenarios detected: {len(failure_scenarios)}
- Implementation weak points: {len(weak_points)}
- Viva targets generated: {len(viva_targets)}

The analysis focused on implementation-aware viva preparation,
identifying areas where student understanding will be probed.
        """.strip()

        key_findings = [
            f"Backend stack: {context.backend_framework.value}, {context.database_used.value}",
            f"Architecture pattern: {context.architecture_pattern.value}",
            f"Identified {len(failure_scenarios)} critical failure scenarios",
            f"Detected {len(weak_points)} areas requiring deep probing",
            f"Generated {len(viva_targets)} implementation-aware viva targets",
        ]

        return summary, key_findings

    @staticmethod
    def _compute_hash(artifact: IntelligenceArtifact) -> str:
        """
        Compute deterministic hash for replay verification.
        Ensures artifact is deterministic and reproducible.
        """
        # Serialize key fields deterministically
        data_to_hash = {
            "session_id": artifact.session_id,
            "project_name": artifact.project_name,
            "backend_stack": artifact.backend_stack,
            "num_viva_targets": len(artifact.viva_targets),
            "num_failure_scenarios": len(artifact.failure_scenarios),
        }

        data_string = json.dumps(data_to_hash, sort_keys=True, default=str)
        return hashlib.sha256(data_string.encode()).hexdigest()[:16]
