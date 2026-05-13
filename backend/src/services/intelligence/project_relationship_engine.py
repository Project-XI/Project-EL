import os
import re
from typing import List, Dict, Any
from ...models.context import ProjectGraph, ProjectNode, ProjectEdge

class ProjectRelationshipEngine:
    """
    Infers relationships between project components using code-level evidence.
    """
    
    @staticmethod
    def infer_relationships(repo_path: str, detections: Dict[str, Any], structure: Dict[str, Any]) -> ProjectGraph:
        nodes = []
        edges = []
        
        # 1. Map existing detections to nodes
        node_map = {}
        for key, model in detections.items():
            if model.value != "Unknown":
                node_id = key.split("_")[0] # e.g. "frontend", "backend"
                node = ProjectNode(
                    id=node_id,
                    label=model.value,
                    type=node_id,
                    metadata={"source": model.evidence}
                )
                nodes.append(node)
                node_map[node_id] = node

        # 2. Infer Edge: Frontend -> Backend
        if "frontend" in node_map and "backend" in node_map:
            evidence = []
            # Look for API calls in frontend files
            for rel_path in structure.get("file_tree", {}):
                if any(x in rel_path.lower() for x in ["src", "app"]) and any(x in rel_path.lower() for x in [".js", ".ts", ".jsx", ".tsx"]):
                    path = os.path.join(repo_path, rel_path)
                    try:
                        with open(path, 'r') as f:
                            content = f.read()
                            if "fetch(" in content or "axios" in content or "/api/" in content:
                                evidence.append(f"API interaction detected in {rel_path}")
                    except:
                        pass
            
            if evidence:
                edges.append(ProjectEdge(
                    source="frontend",
                    target="backend",
                    relationship="API Communication",
                    confidence=0.9,
                    evidence=list(set(evidence))[:3]
                ))

        # 3. Infer Edge: Backend -> Database
        if "backend" in node_map and "database" in node_map:
            evidence = []
            # Look for DB connection strings or imports in backend files
            db_type = node_map["database"].label.lower()
            for rel_path in structure.get("file_tree", {}):
                if any(x in rel_path.lower() for x in ["backend", "server", "api"]):
                    path = os.path.join(repo_path, rel_path)
                    try:
                        with open(path, 'r') as f:
                            content = f.read().lower()
                            if "mongodb://" in content or "postgresql://" in content or "mongoose.connect" in content:
                                evidence.append(f"DB connection string/logic found in {rel_path}")
                    except:
                        pass
            
            if evidence:
                edges.append(ProjectEdge(
                    source="backend",
                    target="database",
                    relationship="Data Persistence",
                    confidence=0.95,
                    evidence=list(set(evidence))[:3]
                ))

        # 4. Infer Edge: Auth -> Backend
        if "authentication" in detections and detections["authentication"].value != "Unknown":
            nodes.append(ProjectNode(id="auth", label=detections["authentication"].value, type="middleware"))
            edges.append(ProjectEdge(
                source="auth",
                target="backend",
                relationship="Secures",
                confidence=0.85,
                evidence=["Authentication middleware/patterns detected in backend config"]
            ))

        return ProjectGraph(nodes=nodes, edges=edges)
