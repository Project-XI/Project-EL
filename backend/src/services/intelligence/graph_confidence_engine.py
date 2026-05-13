from typing import List
from ...models.context import ProjectGraph, ProjectEdge

class GraphConfidenceEngine:
    """
    Refines and aggregates confidence scores for the project graph.
    """
    
    @staticmethod
    def refine_scores(graph: ProjectGraph) -> ProjectGraph:
        for edge in graph.edges:
            # Heuristic: More evidence = higher confidence
            evidence_count = len(edge.evidence)
            if evidence_count > 2:
                edge.confidence = min(0.99, edge.confidence + 0.05)
            elif evidence_count == 1:
                edge.confidence = min(0.9, edge.confidence)
                
        return graph
