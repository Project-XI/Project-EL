from typing import List
from ...models.context import ProjectGraph, ProjectEdge

class GraphConfidenceEngine:
    """
    Refines and aggregates confidence scores for the project graph.
    """
    
    @staticmethod
    def refine_scores(graph: ProjectGraph) -> ProjectGraph:
        for edge in graph.edges:
            # Weighted Evidence Aggregation
            # Signals: 
            # - Explicit import (Weight: 0.6)
            # - Config file entry (Weight: 0.3)
            # - Indirect call (Weight: 0.1)
            
            score = 0.0
            for ev in edge.evidence:
                if any(x in ev.lower() for x in ["import", "from"]):
                    score += 0.6
                elif any(x in ev.lower() for x in ["config", "json", "env", "yml"]):
                    score += 0.3
                else:
                    score += 0.1
            
            edge.confidence = min(0.99, score)
                
        return graph
