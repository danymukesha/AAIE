import networkx as nx
from aaie.graph.models import Finding
from aaie.rules.base_rule import BaseRule


class SinglePointFailureRule(BaseRule):
    """Detects single points of failure in the architecture."""

    def __init__(self, threshold: int = 3) -> None:
        super().__init__(
            rule_id="single_point_failure",
            description="Detects nodes that are single points of failure"
        )
        self.threshold = threshold

    def evaluate(self, graph: nx.DiGraph) -> list[Finding]:
        findings = []

        for node_id in graph.nodes():
            in_degree = graph.in_degree(node_id)
            node_data = graph.nodes[node_id]
            node_name = node_data.get("name", node_id)
            node_type = node_data.get("type", "unknown")
            
            if in_degree >= self.threshold:
                finding = Finding(
                    rule_id=self.rule_id,
                    severity="warning",
                    message=f"Potential single point of failure: {node_name} (type: {node_type}) has {in_degree} incoming dependencies",
                    node_ids=[node_id],
                    metadata={
                        "in_degree": in_degree,
                        "node_type": node_type,
                        "predecessors": list(graph.predecessors(node_id))
                    }
                )
                findings.append(finding)

            if node_type_has_reliability_concern(node_type):
                successors = list(graph.successors(node_id))
                if len(successors) == 0:
                    finding = Finding(
                        rule_id=self.rule_id,
                        severity="info",
                        message=f"Node {node_id} has no outgoing connections - may be orphaned",
                        node_ids=[node_id],
                        metadata={"type": "orphaned"}
                    )
                    findings.append(finding)

        return findings


def node_type_has_reliability_concern(node_type: str) -> bool:
    """Check if a node type is a reliability concern when isolated."""
    return node_type in ("service", "database", "queue", "container")
