from typing import Dict, Any, List
from ...models.context import ProjectGraph, ProjectNode, ProjectEdge

class ProjectGraphBuilder:
    """
    Builds a conceptual graph of the project architecture based on detected components.
    """
    
    @staticmethod
    def build(detections: Dict[str, Any], structure: Dict[str, Any]) -> ProjectGraph:
        nodes = []
        edges = []
        
        # 1. Add Frontend Node
        if "frontend_framework" in detections:
            nodes.append(ProjectNode(
                id="frontend",
                label=detections["frontend_framework"].value,
                type="frontend"
            ))

        # 2. Add Backend Node
        if "backend_framework" in detections:
            nodes.append(ProjectNode(
                id="backend",
                label=detections["backend_framework"].value,
                type="backend"
            ))
            if "frontend_framework" in detections:
                edges.append(ProjectEdge(source="frontend", target="backend", label="API Calls"))

        # 3. Add Database Node
        if "database_used" in detections:
            nodes.append(ProjectNode(
                id="database",
                label=detections["database_used"].value,
                type="database"
            ))
            if "backend_framework" in detections:
                edges.append(ProjectEdge(source="backend", target="database", label="Data Persistence"))

        # 4. Add Auth Node
        if "authentication_system" in detections:
            nodes.append(ProjectNode(
                id="auth",
                label=detections["authentication_system"].value,
                type="middleware"
            ))
            if "backend_framework" in detections:
                edges.append(ProjectEdge(source="auth", target="backend", label="Secures"))

        return ProjectGraph(nodes=nodes, edges=edges)
