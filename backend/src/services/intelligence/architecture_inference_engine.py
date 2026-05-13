from typing import Dict, Any, List
from ...models.context import ProjectGraph, EvidenceModel

class ArchitectureInferenceEngine:
    """
    Infers high-level architecture patterns from the project graph and tech detections.
    """
    
    @staticmethod
    def infer_architecture(graph: ProjectGraph, detections: Dict[str, Any]) -> EvidenceModel:
        evidence = []
        pattern = "Unknown Architecture"
        confidence = 0.0
        
        nodes_labels = [n.label.lower() for n in graph.nodes]
        has_frontend = "frontend" in [n.type for n in graph.nodes]
        has_backend = "backend" in [n.type for n in graph.nodes]
        has_db = "database" in [n.type for n in graph.nodes]

        # 1. MERN Pattern
        if all(x in nodes_labels for x in ["react", "express", "mongodb"]):
            pattern = "MERN Stack Architecture"
            confidence = 0.98
            evidence = ["React frontend, Express backend, and MongoDB database detected in sync."]
        
        # 2. REST Client-Server
        elif has_frontend and has_backend:
            edge_labels = [e.relationship for e in graph.edges]
            if "API Communication" in edge_labels:
                pattern = "REST Client-Server Architecture"
                confidence = 0.92
                evidence = [
                    "Separated frontend and backend components detected.",
                    "Active API communication flow inferred from frontend service calls."
                ]
        
        # 3. Layered Monolith (Simple Backend + DB)
        elif has_backend and has_db and not has_frontend:
            pattern = "Layered Backend Architecture"
            confidence = 0.85
            evidence = ["Backend service with direct database persistence detected without a decoupled frontend."]

        # 4. Fallback or Specific Frameworks
        if pattern == "Unknown Architecture" and has_backend:
            backend_val = detections.get("backend_framework").value if detections.get("backend_framework") else "Unknown"
            pattern = f"{backend_val}-based Architecture"
            confidence = 0.7
            evidence = [f"Architecture centered around {backend_val} framework."]

        return EvidenceModel(
            value=pattern,
            confidence=confidence,
            evidence=evidence
        )
