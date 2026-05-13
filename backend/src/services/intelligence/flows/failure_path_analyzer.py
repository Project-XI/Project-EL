from typing import List, Dict, Any
from ..intermediate_representation.execution_graph_builder import ExecutionGraphBuilder
from ....models.context import EvidenceModel

class FailurePathAnalyzer:
    """
    Analyzes how the system handles failures (retries, exceptions, fallbacks).
    """
    
    @staticmethod
    def analyze(repo_path: str, structure: Dict[str, Any], builder: ExecutionGraphBuilder) -> List[EvidenceModel]:
        paths = []
        
        # Look for try-except blocks or global exception handlers
        for file_path in structure.get("file_tree", {}):
            if any(x in file_path.lower() for x in ["exception", "error", "handler"]):
                paths.append(EvidenceModel(
                    value=f"Error handling path detected in {file_path}",
                    confidence=0.8,
                    evidence=[f"Exception handling related file: {file_path}"]
                ))
        
        return paths
