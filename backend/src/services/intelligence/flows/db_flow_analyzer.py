import os
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
        code_extensions = {".py", ".js", ".ts", ".jsx", ".tsx"}
        db_markers = ["sqlalchemy", "sqlite", "postgres", "psycopg", "mongodb", "mongoose", "mysql", "orm", "database", "query"]
        
        # Scan for models and db configs
        for file_path in structure.get("file_tree", {}):
            if not any(file_path.lower().endswith(ext) for ext in code_extensions):
                continue

            if not any(x in file_path.lower() for x in ["model", "db", "repository", "schema", "data"]):
                continue

            abs_path = os.path.join(repo_path, file_path)
            try:
                with open(abs_path, "r", errors="ignore") as handle:
                    content = handle.read().lower()
            except Exception:
                continue

            if not any(marker in content for marker in db_markers):
                continue

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
