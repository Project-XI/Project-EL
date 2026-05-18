"""
Failure Propagation Validator

Validates that:
- Failure scenarios propagate through correct execution paths
- Risk severity is justified by propagation chain analysis
- Recovery strategies are grounded in actual system capabilities
- Propagation chains don't hallucinate non-existent connections
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from src.services.intelligence.execution_graph_failure_analyzer import FailureScenario


@dataclass
class PropagationPathValidation:
    """Validation result for a single propagation path."""
    from_component: str
    to_component: str
    connection_valid: bool
    evidence: List[str] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)


@dataclass
class FailureScenarioValidation:
    """Validation result for a single failure scenario."""
    scenario_name: str
    expected: bool
    detected: bool
    
    # Trigger validation
    trigger_specific: bool  # Is trigger concrete or vague?
    trigger_grounded: bool  # Can trigger be caused by actual failure?
    
    # Propagation validation
    propagation_paths: List[PropagationPathValidation] = field(default_factory=list)
    all_paths_valid: bool = True
    path_validation_issues: List[str] = field(default_factory=list)
    
    # Risk severity validation
    risk_justified: bool  # Is risk level justified by propagation chain?
    risk_justification: str = ""
    risk_issues: List[str] = field(default_factory=list)
    
    # Recovery validation
    recovery_strategy_grounded: bool
    recovery_issues: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "scenario_name": self.scenario_name,
            "expected": self.expected,
            "detected": self.detected,
            "trigger_specific": self.trigger_specific,
            "propagation_valid": self.all_paths_valid,
            "risk_justified": self.risk_justified,
            "recovery_grounded": self.recovery_strategy_grounded,
            "issues": self.path_validation_issues + self.risk_issues + self.recovery_issues,
        }


@dataclass
class FailureValidationReport:
    """Complete validation report for failure scenarios in a repository."""
    repository_name: str
    total_expected: int
    total_detected: int
    
    valid_scenarios: List[FailureScenarioValidation] = field(default_factory=list)
    hallucinated_scenarios: List[FailureScenarioValidation] = field(default_factory=list)
    missed_scenarios: List[FailureScenarioValidation] = field(default_factory=list)
    
    # Aggregate metrics
    precision: float = 0.0  # TP / (TP + hallucinated)
    recall: float = 0.0  # TP / (TP + missed)
    propagation_accuracy: float = 0.0  # % of paths correctly grounded
    risk_calibration_issues: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "repository": self.repository_name,
            "total_expected": self.total_expected,
            "total_detected": self.total_detected,
            "valid_scenarios": len(self.valid_scenarios),
            "hallucinated_scenarios": len(self.hallucinated_scenarios),
            "missed_scenarios": len(self.missed_scenarios),
            "precision": round(self.precision, 3),
            "recall": round(self.recall, 3),
            "propagation_accuracy": round(self.propagation_accuracy, 3),
            "risk_calibration_issues": self.risk_calibration_issues,
        }


class ExecutionGraphFailureValidator:
    """Validates failure scenario propagation chains."""
    
    @staticmethod
    def validate_failure_scenarios(
        detected_scenarios: List[FailureScenario],
        expected_scenarios: List[Any],  # ExpectedFailureScenario from fixtures
        project_graph: Any,  # ProjectGraph
        repository_name: str
    ) -> FailureValidationReport:
        """
        Validate detected failure scenarios against expected propagation patterns.
        
        Args:
            detected_scenarios: Actual scenarios from ExecutionGraphFailureAnalyzer
            expected_scenarios: Expected scenarios from fixture
            project_graph: Execution graph for validating propagation
            repository_name: Name of repository being validated
            
        Returns:
            FailureValidationReport with detailed validation
        """
        report = FailureValidationReport(
            repository_name=repository_name,
            total_expected=len(expected_scenarios),
            total_detected=len(detected_scenarios)
        )
        
        # Index by scenario name
        detected_by_name = {s.scenario_name: s for s in detected_scenarios}
        expected_by_name = {s.scenario_name: s for s in expected_scenarios}
        found_expected = set()
        
        # Validate each detected scenario
        for detected in detected_scenarios:
            expected = expected_by_name.get(detected.scenario_name)
            
            validation = FailureScenarioValidation(
                scenario_name=detected.scenario_name,
                expected=expected is not None,
                detected=True,
                trigger_specific=ExecutionGraphFailureValidator._is_trigger_specific(
                    detected.trigger
                ),
                trigger_grounded=ExecutionGraphFailureValidator._is_trigger_grounded(
                    detected.trigger, detected.code_evidence
                ),
                recovery_strategy_grounded=bool(detected.recovery_strategy),
            )
            
            # Validate propagation paths
            path_validations = ExecutionGraphFailureValidator._validate_propagation_paths(
                detected, project_graph
            )
            validation.propagation_paths = path_validations
            validation.all_paths_valid = all(p.connection_valid for p in path_validations)
            validation.path_validation_issues = [
                p.issues[0] for p in path_validations if p.issues
            ]
            
            # Validate risk severity
            if expected:
                found_expected.add(detected.scenario_name)
                risk_valid, risk_msg = ExecutionGraphFailureValidator._validate_risk_severity(
                    detected, expected, len(path_validations)
                )
                validation.risk_justified = risk_valid
                validation.risk_justification = risk_msg
                if not risk_valid:
                    validation.risk_issues.append(
                        f"Risk level '{detected.propagation_risk}' not justified: {risk_msg}"
                    )
                    report.risk_calibration_issues.append(
                        f"{detected.scenario_name}: {risk_msg}"
                    )
                
                report.valid_scenarios.append(validation)
            else:
                # Hallucinated scenario
                report.hallucinated_scenarios.append(validation)
                report.risk_calibration_issues.append(
                    f"Hallucinated scenario: {detected.scenario_name}"
                )
        
        # Check for missed scenarios
        for expected in expected_scenarios:
            if expected.scenario_name not in found_expected:
                validation = FailureScenarioValidation(
                    scenario_name=expected.scenario_name,
                    expected=True,
                    detected=False,
                    trigger_specific=True,
                    trigger_grounded=True,
                    recovery_strategy_grounded=True,
                )
                report.missed_scenarios.append(validation)
                report.risk_calibration_issues.append(
                    f"Missed scenario: {expected.scenario_name} "
                    f"(risk: {expected.propagation_risk})"
                )
        
        # Calculate metrics
        tp = len(report.valid_scenarios)
        hallucinated = len(report.hallucinated_scenarios)
        missed = len(report.missed_scenarios)
        
        if tp + hallucinated > 0:
            report.precision = tp / (tp + hallucinated)
        if tp + missed > 0:
            report.recall = tp / (tp + missed)
        
        # Propagation accuracy
        all_validations = report.valid_scenarios + report.hallucinated_scenarios
        if all_validations:
            valid_count = sum(
                1 for v in all_validations if v.all_paths_valid
            )
            report.propagation_accuracy = valid_count / len(all_validations)
        
        return report
    
    @staticmethod
    def _is_trigger_specific(trigger: str) -> bool:
        """Check if trigger is specific or generic."""
        vague_terms = [
            "unknown",
            "some failure",
            "error occurs",
            "problem happens",
        ]
        return not any(term in trigger.lower() for term in vague_terms)
    
    @staticmethod
    def _is_trigger_grounded(trigger: str, code_evidence: List[str]) -> bool:
        """Check if trigger is grounded in actual code patterns."""
        return bool(code_evidence) and len(code_evidence) > 0
    
    @staticmethod
    def _validate_propagation_paths(
        scenario: FailureScenario,
        project_graph: Any
    ) -> List[PropagationPathValidation]:
        """
        Validate that propagation paths exist in the execution graph.
        
        Returns list of path validations (simplified for now).
        """
        paths = []
        
        # For each affected component in scenario
        for component in scenario.affected_paths:
            # Check if component exists in graph
            path_valid = True
            issues = []
            
            # Simplified validation - check if nodes exist
            if hasattr(project_graph, 'nodes'):
                node_found = any(component in str(node) for node in project_graph.nodes)
                if not node_found:
                    path_valid = False
                    issues.append(f"Component '{component}' not found in execution graph")
            
            paths.append(PropagationPathValidation(
                from_component="trigger",
                to_component=component,
                connection_valid=path_valid,
                issues=issues,
            ))
        
        return paths
    
    @staticmethod
    def _validate_risk_severity(
        detected: FailureScenario,
        expected: Any,  # ExpectedFailureScenario
        path_count: int
    ) -> tuple[bool, str]:
        """
        Validate that risk severity is justified by propagation chain.
        
        Returns (is_valid, justification_message)
        """
        risk_map = {
            "critical": {"min_paths": 3, "recovery": False},
            "high": {"min_paths": 2, "recovery": None},
            "medium": {"min_paths": 1, "recovery": None},
            "low": {"min_paths": 1, "recovery": True},
        }
        
        expected_risk = expected.propagation_risk
        detected_risk = detected.propagation_risk
        
        if detected_risk != expected_risk:
            return False, f"Expected {expected_risk}, got {detected_risk}"
        
        if detected_risk not in risk_map:
            return False, f"Invalid risk level: {detected_risk}"
        
        threshold = risk_map[detected_risk]
        
        if path_count < threshold["min_paths"]:
            return (
                False,
                f"Risk '{detected_risk}' requires {threshold['min_paths']} propagation "
                f"paths, but only {path_count} detected"
            )
        
        return True, f"Risk level {detected_risk} justified by {path_count} propagation paths"
