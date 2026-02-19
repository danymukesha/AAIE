import networkx as nx
from typing import Any
from aaie.graph.models import Node, Edge, Finding


class GraphBuilder:
    """Builds and manages the architecture dependency graph using NetworkX DiGraph."""

    def __init__(self) -> None:
        self._graph: nx.DiGraph = nx.DiGraph()

    @property
    def graph(self) -> nx.DiGraph:
        return self._graph

    def add_node(self, node: Node) -> None:
        """Add a node to the graph, updating if it already exists."""
        self._graph.add_node(
            node.id,
            name=node.name,
            type=node.type,
            metadata=node.metadata
        )

    def add_edge(self, edge: Edge) -> None:
        """Add an edge to the graph."""
        if edge.source not in self._graph:
            raise ValueError(f"Source node {edge.source} not in graph")
        if edge.target not in self._graph:
            raise ValueError(f"Target node {edge.target} not in graph")
        self._graph.add_edge(
            edge.source,
            edge.target,
            type=edge.type,
            metadata=edge.metadata
        )

    def add_nodes_from(self, nodes: list[Node]) -> None:
        """Add multiple nodes to the graph."""
        for node in nodes:
            self.add_node(node)

    def add_edges_from(self, edges: list[Edge]) -> None:
        """Add multiple edges to the graph."""
        for edge in edges:
            self.add_edge(edge)

    def get_node(self, node_id: str) -> Node | None:
        """Retrieve a node by ID."""
        if node_id not in self._graph:
            return None
        data = self._graph.nodes[node_id]
        return Node(
            id=node_id,
            name=data.get("name", node_id),
            type=data.get("type", "service"),
            metadata=data.get("metadata", {})
        )

    def get_nodes_by_type(self, node_type: str) -> list[Node]:
        """Get all nodes of a specific type."""
        nodes = []
        for node_id, data in self._graph.nodes(data=True):
            if data.get("type") == node_type:
                nodes.append(Node(
                    id=node_id,
                    name=data.get("name", node_id),
                    type=node_type,
                    metadata=data.get("metadata", {})
                ))
        return nodes

    def get_edges(self) -> list[Edge]:
        """Get all edges in the graph."""
        edges = []
        for source, target, data in self._graph.edges(data=True):
            edges.append(Edge(
                source=source,
                target=target,
                type=data.get("type", "depends_on"),
                metadata=data.get("metadata", {})
            ))
        return edges

    def get_in_degree(self, node_id: str) -> int:
        """Get the in-degree of a node."""
        return self._graph.in_degree(node_id)

    def get_out_degree(self, node_id: str) -> int:
        """Get the out-degree of a node."""
        return self._graph.out_degree(node_id)

    def get_predecessors(self, node_id: str) -> list[str]:
        """Get all predecessors of a node."""
        return list(self._graph.predecessors(node_id))

    def get_successors(self, node_id: str) -> list[str]:
        """Get all successors of a node."""
        return list(self._graph.successors(node_id))

    def nodes(self) -> list[str]:
        """Get all node IDs."""
        return list(self._graph.nodes())

    def edges(self) -> list[tuple[str, str]]:
        """Get all edges as tuples."""
        return list(self._graph.edges())

    def number_of_nodes(self) -> int:
        """Get the number of nodes."""
        return self._graph.number_of_nodes()

    def number_of_edges(self) -> int:
        """Get the number of edges."""
        return self._graph.number_of_edges()

    def to_dict(self) -> dict[str, Any]:
        """Export graph to dictionary format."""
        return nx.node_link_data(self._graph)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GraphBuilder":
        """Import graph from dictionary format."""
        builder = cls()
        graph = nx.node_link_graph(data)
        builder._graph = graph
        return builder

    def clear(self) -> None:
        """Clear all nodes and edges from the graph."""
        self._graph.clear()
