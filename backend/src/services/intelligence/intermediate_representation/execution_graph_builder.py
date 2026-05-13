from typing import List, Dict, Any, Optional
from ....models.context import ExecutionGraph, FlowNode, FlowEdge, FlowNodeType

class ExecutionGraphBuilder:
    """
    Utility class for building and manipulating the ExecutionGraph.
    """
    def __init__(self):
        self.graph = ExecutionGraph()

    def add_node(self, node_id: str, label: str, node_type: FlowNodeType, metadata: Dict[str, Any] = {}):
        if not any(n.id == node_id for n in self.graph.nodes):
            self.graph.nodes.append(FlowNode(id=node_id, label=label, type=node_type, metadata=metadata))

    def add_edge(self, source: str, target: str, relationship: str, confidence: float = 1.0, evidence: List[str] = []):
        self.graph.edges.append(FlowEdge(
            source=source,
            target=target,
            relationship=relationship,
            confidence=confidence,
            evidence=evidence
        ))

    def add_risk(self, risk: str):
        if risk not in self.graph.risk_flags:
            self.graph.risk_flags.append(risk)

    def add_auth_point(self, point: str):
        if point not in self.graph.auth_points:
            self.graph.auth_points.append(point)

    def get_graph(self) -> ExecutionGraph:
        return self.graph
