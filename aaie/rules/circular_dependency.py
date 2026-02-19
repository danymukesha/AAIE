import networkx as nx
from aaie.graph.models import Finding
from aaie.rules.base_rule import BaseRule


class CircularDependencyRule(BaseRule):
    """Detects circular dependencies in the architecture graph."""

    def __init__(self) -> None:
        super().__init__(
            rule_id="circular_dependency",
            description="Detects circular dependencies between services"
        )

    def evaluate(self, graph: nx.DiGraph) -> list[Finding]:
        findings = []

        try:
            cycles = list(nx.simple_cycles(graph))
        except Exception:
            return findings

        for cycle in cycles:
            if len(cycle) < 2:
                continue

            cycle_str = " -> ".join(cycle)
            finding = Finding(
                rule_id=self.rule_id,
                severity="warning",
                message=f"Circular dependency detected: {cycle_str}",
                node_ids=cycle,
                metadata={"cycle": cycle}
            )
            findings.append(finding)

        return findings
