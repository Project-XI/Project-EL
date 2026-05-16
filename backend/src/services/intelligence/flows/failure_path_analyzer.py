from typing import List, Dict, Any
from ..intermediate_representation.execution_graph_builder import ExecutionGraphBuilder
from ....models.context import EvidenceModel
import os

class FailurePathAnalyzer:
    """
    Analyzes how the system handles failures (retries, exceptions, fallbacks).
    """
    
    @staticmethod
    def analyze(repo_path: str, structure: Dict[str, Any], builder: ExecutionGraphBuilder) -> List[EvidenceModel]:
        paths = []
        code_extensions = {".py", ".js", ".ts", ".jsx", ".tsx"}
        
        # Look for try-except blocks or global exception handlers
        for file_path in structure.get("file_tree", {}):
            if not any(file_path.lower().endswith(ext) for ext in code_extensions):
                continue

            if not any(x in file_path.lower() for x in ["exception", "error", "handler", "middleware", "route"]):
                continue

            abs_path = os.path.join(repo_path, file_path)
            try:
                with open(abs_path, "r", errors="ignore") as handle:
                    content = handle.read().lower()
            except Exception:
                continue

            if not any(marker in content for marker in ["try:", "except", "catch", "raise", "abort", "exception", "error"]):
                continue

                paths.append(EvidenceModel(
                    value=f"Error handling path detected in {file_path}",
                    confidence=0.8,
                    evidence=[f"Exception handling related file: {file_path}"]
                ))
        
        return paths
