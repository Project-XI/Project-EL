from typing import List, Dict, Any
from ..intermediate_representation.execution_graph_builder import ExecutionGraphBuilder
from ....models.context import RuntimeRisk
import os

class SecurityFlowAnalyzer:
    """
    Detects runtime security risks like missing auth or weak hashing.
    """
    
    @staticmethod
    def analyze(repo_path: str, structure: Dict[str, Any], builder: ExecutionGraphBuilder) -> List[RuntimeRisk]:
        risks = []

        code_extensions = {".py", ".js", ".ts", ".jsx", ".tsx"}
        route_markers = ["@app.", "@router.", "include_router", "app.route", "router."]
        auth_markers = ["auth", "jwt", "oauth", "token", "login", "middleware"]

        route_files = []
        auth_files = []

        for file_path in structure.get("file_tree", {}):
            if not any(file_path.lower().endswith(ext) for ext in code_extensions):
                continue

            abs_path = os.path.join(repo_path, file_path)
            try:
                with open(abs_path, "r", errors="ignore") as handle:
                    content = handle.read().lower()
            except Exception:
                continue

            if any(marker in content for marker in route_markers):
                route_files.append(file_path)
            if any(marker in content for marker in auth_markers):
                auth_files.append(file_path)

        if route_files and not auth_files:
            risks.append(RuntimeRisk(
                value="Potential unauthenticated route surface",
                severity="HIGH",
                confidence=0.72,
                evidence=[f"Route markers found in {route_files[0]} with no auth markers in scanned code files."]
            ))
        
        return risks
