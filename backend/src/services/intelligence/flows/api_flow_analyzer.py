import os
from typing import List, Dict, Any
from ..intermediate_representation.execution_graph_builder import ExecutionGraphBuilder
from ....models.context import ImplementationFlow, FlowNodeType

class APIFlowAnalyzer:
    """
    Analyzes API request lifecycles: routes, handlers, and service layers.
    """
    
    @staticmethod
    def analyze(repo_path: str, structure: Dict[str, Any], builder: ExecutionGraphBuilder) -> ImplementationFlow:
        steps = []
        evidence = []
        code_extensions = {".py", ".js", ".ts", ".jsx", ".tsx"}
        
        # Identify route entry points
        for file_path in structure.get("file_tree", {}):
            if not any(file_path.lower().endswith(ext) for ext in code_extensions):
                continue

            if not any(x in file_path.lower() for x in ["route", "controller", "api"]):
                continue

            abs_path = os.path.join(repo_path, file_path)
            try:
                with open(abs_path, "r", errors="ignore") as handle:
                    content = handle.read().lower()
            except Exception:
                continue

            if not any(marker in content for marker in ["@app.", "@router.", "include_router", "fetch(", "axios", "/api/"]):
                continue

                builder.add_node(
                    node_id=f"api_{file_path}",
                    label=f"API Entry ({file_path})",
                    node_type=FlowNodeType.ROUTE,
                    metadata={"file": file_path}
                )
                steps.append(f"API Route detected in {file_path}")
                evidence.append(f"Static route pattern found in {file_path}")

        return ImplementationFlow(
            steps=steps,
            confidence=0.8,
            flow_confidence={"route_mapping": 0.85, "service_tracing": 0.7},
            evidence=evidence
        )
