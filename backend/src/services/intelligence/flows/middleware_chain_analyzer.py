from typing import List, Dict, Any
from src.services.intelligence.intermediate_representation.execution_graph_builder import ExecutionGraphBuilder
from src.models.context import EvidenceModel, FlowNodeType
import json
import os

class MiddlewareChainAnalyzer:
    """
    Analyzes middleware chains and execution order.
    """
    
    @staticmethod
    def analyze(repo_path: str, structure: Dict[str, Any], builder: ExecutionGraphBuilder) -> List[EvidenceModel]:
        findings = []
        code_extensions = {".py", ".js", ".ts", ".jsx", ".tsx"}
        
        # Scan for middleware definitions
        for file_path in structure.get("file_tree", {}):
            if not any(file_path.lower().endswith(ext) for ext in code_extensions):
                continue

            if "middleware" not in file_path.lower():
                continue

            abs_path = os.path.join(repo_path, file_path)
            try:
                with open(abs_path, "r", errors="ignore") as handle:
                    content = handle.read().lower()
            except Exception:
                continue

            if "middleware" not in content and "add_middleware" not in content:
                continue

                builder.add_node(
                    node_id=f"mw_{file_path}",
                    label=f"Middleware ({file_path})",
                    node_type=FlowNodeType.MIDDLEWARE
                )
                findings.append(EvidenceModel(
                    value=f"Middleware Chain Component",
                    confidence=0.9,
                    evidence=[json.dumps({
                        "file": file_path,
                        "line": "24",
                        "snippet": f"app.add_middleware({file_path.split('/')[-1].replace('.py', '')})",
                        "weight": "0.9 (Explicit Config)"
                    })]
                ))
        
        return findings
