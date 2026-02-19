import json
from pathlib import Path
from typing import Any
import networkx as nx
from aaie.graph.graph_builder import GraphBuilder
from aaie.graph.models import Node, Edge


class GraphSerializer:
    """Handles serialization and deserialization of the architecture graph."""

    @staticmethod
    def to_json(builder: GraphBuilder, path: Path) -> None:
        """Export graph to JSON file."""
        data = {
            "nodes": [
                {
                    "id": node_id,
                    "name": builder._graph.nodes[node_id].get("name", node_id),
                    "type": builder._graph.nodes[node_id].get("type", "service"),
                    "metadata": builder._graph.nodes[node_id].get("metadata", {})
                }
                for node_id in builder._graph.nodes()
            ],
            "edges": [
                {
                    "source": source,
                    "target": target,
                    "type": builder._graph.edges[source, target].get("type", "depends_on"),
                    "metadata": builder._graph.edges[source, target].get("metadata", {})
                }
                for source, target in builder._graph.edges()
            ]
        }
        path.write_text(json.dumps(data, indent=2))

    @staticmethod
    def from_json(path: Path) -> GraphBuilder:
        """Import graph from JSON file."""
        data = json.loads(path.read_text())
        builder = GraphBuilder()

        for node_data in data.get("nodes", []):
            builder.add_node(Node(
                id=node_data["id"],
                name=node_data.get("name", node_data["id"]),
                type=node_data.get("type", "service"),
                metadata=node_data.get("metadata", {})
            ))

        for edge_data in data.get("edges", []):
            builder.add_edge(Edge(
                source=edge_data["source"],
                target=edge_data["target"],
                type=edge_data.get("type", "depends_on"),
                metadata=edge_data.get("metadata", {})
            ))

        return builder

    @staticmethod
    def to_gexf(builder: GraphBuilder, path: Path) -> None:
        """Export graph to GEXF format."""
        nx.write_gexf(builder.graph, path)

    @staticmethod
    def to_dot(builder: GraphBuilder, path: Path) -> None:
        """Export graph to DOT format."""
        nx.drawing.nx_pydot.write_dot(builder.graph, path)

    @staticmethod
    def to_dict(builder: GraphBuilder) -> dict[str, Any]:
        """Export graph to dictionary."""
        nodes = []
        for node_id in builder._graph.nodes():
            nodes.append({
                "id": node_id,
                "name": builder._graph.nodes[node_id].get("name", node_id),
                "type": builder._graph.nodes[node_id].get("type", "service"),
                "metadata": builder._graph.nodes[node_id].get("metadata", {})
            })

        edges = []
        for source, target in builder._graph.edges():
            edges.append({
                "source": source,
                "target": target,
                "type": builder._graph.edges[source, target].get("type", "depends_on"),
                "metadata": builder._graph.edges[source, target].get("metadata", {})
            })

        return {"nodes": nodes, "edges": edges}
