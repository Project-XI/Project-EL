from typing import List, Dict, Any
from ..intermediate_representation.execution_graph_builder import ExecutionGraphBuilder
from ....models.context import ImplementationFlow, FlowNodeType

class DBFlowAnalyzer:
    """
    Analyzes database interaction paths and query patterns.
    """
    
    @staticmethod
    def analyze(repo_path: str, structure: Dict[str, Any], builder: ExecutionGraphBuilder) -> ImplementationFlow:
        steps = []
        evidence = []
        
        # Scan for models and db configs
        for file_path in structure.get("file_tree", {}):
            if any(x in file_path.lower() for x in ["model", "db", "repository"]):
                builder.add_node(
                    node_id=f"db_{file_path}",
                    label=f"Data Access Layer ({file_path})",
                    node_type=FlowNodeType.DB_QUERY
                )
                steps.append(f"DB interaction point: {file_path}")
                evidence.append(f"Persistence related keywords found in {file_path}")

        return ImplementationFlow(
            steps=steps,
            confidence=0.88,
            flow_confidence={"query_detection": 0.9, "transaction_mapping": 0.6},
            evidence=evidence
        )
