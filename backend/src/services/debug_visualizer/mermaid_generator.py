from typing import List, Dict, Any
from src.models.context import ExecutionGraph, FlowNodeType

class MermaidGenerator:
    """
    Generates Mermaid.js diagrams from the ExecutionGraph for debug visualization.
    """
    
    @staticmethod
    def generate(graph: ExecutionGraph) -> str:
        lines = ["graph TD"]
        
        # 1. Define Nodes with styling based on type
        for node in graph.nodes:
            label = node.label.replace('"', "'")
            style = ""
            if node.type == FlowNodeType.AUTH_HANDLER:
                style = ":::auth"
            elif node.type == FlowNodeType.DB_QUERY:
                style = ":::db"
            elif node.type == FlowNodeType.MIDDLEWARE:
                style = ":::middleware"
            
            lines.append(f"    {node.id}[\"{label}\"]{style}")

        # 2. Define Edges
        for edge in graph.edges:
            lines.append(f"    {edge.source} -->|{edge.relationship}| {edge.target}")

        # 3. Add Styling
        lines.append("")
        lines.append("    classDef auth fill:#f96,stroke:#333,stroke-width:2px;")
        lines.append("    classDef db fill:#69f,stroke:#333,stroke-width:2px;")
        lines.append("    classDef middleware fill:#9f6,stroke:#333,stroke-width:2px;")
        
        return "\n".join(lines)

    @staticmethod
    def save_to_file(mermaid_str: str, output_path: str):
        with open(output_path, 'w') as f:
            f.write(mermaid_str)
