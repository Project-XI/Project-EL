from typing import List, Dict, Any
from src.services.intelligence.intermediate_representation.execution_graph_builder import ExecutionGraphBuilder
from src.models.context import EvidenceModel, FlowNodeType

class MiddlewareChainAnalyzer:
    """
    Analyzes middleware chains and execution order.
    """
    
    @staticmethod
    def analyze(repo_path: str, structure: Dict[str, Any], builder: ExecutionGraphBuilder) -> List[EvidenceModel]:
        findings = []
        
        # Scan for middleware definitions
        for file_path in structure.get("file_tree", {}):
            if "middleware" in file_path.lower():
                builder.add_node(
                    node_id=f"mw_{file_path}",
                    label=f"Middleware ({file_path})",
                    node_type=FlowNodeType.MIDDLEWARE
                )
                findings.append(EvidenceModel(
                    value=f"Middleware chain component: {file_path}",
                    confidence=0.9,
                    evidence=[f"File found in middleware-specific path: {file_path}"]
                ))
        
        return findings
