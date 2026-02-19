from pathlib import Path
from aaie.graph.models import ScanResult
from aaie.graph.graph_builder import GraphBuilder


class DiagramGenerator:
    """Generates architecture diagrams using Graphviz."""

    COLOR_MAP = {
        "service": "#3498db",
        "database": "#e67e22",
        "queue": "#9b59b6",
        "external_api": "#1abc9c",
        "container": "#e74c3c",
        "infra_resource": "#95a5a6",
        "library": "#2ecc71"
    }

    def __init__(self) -> None:
        pass

    def generate_png(self, result: ScanResult, output_path: Path) -> None:
        builder = GraphBuilder()
        builder.add_nodes_from(result.nodes)
        builder.add_edges_from(result.edges)
        
        try:
            import graphviz
        except ImportError:
            self._generate_dot_file(builder, output_path.with_suffix(".dot"))
            return

        dot = graphviz.Digraph(comment="Architecture")
        dot.attr(rankdir="LR", size="12,8", dpi="150")
        
        for node in result.nodes:
            color = self.COLOR_MAP.get(node.type, "#95a5a6")
            dot.node(
                node.id,
                label=node.name,
                color=color,
                style="filled",
                fillcolor=color,
                fontcolor="white"
            )
        
        for edge in result.edges:
            dot.edge(edge.source, edge.target, label=edge.type)
        
        dot.render(
            filename=output_path.stem,
            directory=output_path.parent,
            format="png",
            cleanup=True
        )

    def generate_dot(self, result: ScanResult, output_path: Path) -> None:
        builder = GraphBuilder()
        builder.add_nodes_from(result.nodes)
        builder.add_edges_from(result.edges)
        self._generate_dot_file(builder, output_path)

    def _generate_dot_file(self, builder: GraphBuilder, output_path: Path) -> None:
        lines = []
        lines.append("digraph architecture {")
        lines.append('    rankdir="LR";')
        lines.append('    size="12,8";')
        lines.append('    dpi="150";')
        lines.append("")
        
        for node_id in builder._graph.nodes():
            node_data = builder._graph.nodes[node_id]
            node_type = node_data.get("type", "service")
            node_name = node_data.get("name", node_id)
            color = self.COLOR_MAP.get(node_type, "#95a5a6")
            
            lines.append(f'    "{node_id}" [label="{node_name}", color="{color}", style=filled, fillcolor="{color}", fontcolor=white];')
        
        lines.append("")
        
        for source, target, data in builder._graph.edges(data=True):
            edge_type = data.get("type", "depends_on")
            lines.append(f'    "{source}" -> "{target}" [label="{edge_type}"];')
        
        lines.append("}")
        
        output_path.write_text("\n".join(lines), encoding="utf-8")

    def generate_svg(self, result: ScanResult, output_path: Path) -> None:
        builder = GraphBuilder()
        builder.add_nodes_from(result.nodes)
        builder.add_edges_from(result.edges)
        
        try:
            import graphviz
        except ImportError:
            return

        dot = graphviz.Digraph(comment="Architecture")
        dot.attr(rankdir="LR", size="12,8", dpi="150")
        
        for node in result.nodes:
            color = self.COLOR_MAP.get(node.type, "#95a5a6")
            dot.node(
                node.id,
                label=node.name,
                color=color,
                style="filled",
                fillcolor=color,
                fontcolor="white"
            )
        
        for edge in result.edges:
            dot.edge(edge.source, edge.target, label=edge.type)
        
        dot.render(
            filename=output_path.stem,
            directory=output_path.parent,
            format="svg",
            cleanup=True
        )
