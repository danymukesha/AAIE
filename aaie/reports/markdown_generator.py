from collections import Counter
from datetime import datetime
from pathlib import Path
import networkx as nx
from aaie.graph.models import ScanResult, NodeType
from aaie.graph.graph_builder import GraphBuilder


class MarkdownGenerator:
    """Generates Markdown architecture reports."""

    def __init__(self) -> None:
        self.template_dir = Path(__file__).parent / "templates"

    def generate(self, result: ScanResult, output_path: Path) -> None:
        content = self._build_content(result)
        output_path.write_text(content, encoding="utf-8")

    def _build_content(self, result: ScanResult) -> str:
        lines = []
        
        lines.append(f"# Architecture Analysis Report")
        lines.append("")
        lines.append(f"**Generated:** {datetime.utcnow().isoformat()}")
        lines.append(f"**Repository ID:** {result.repo_id}")
        lines.append("")

        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Total Nodes:** {len(result.nodes)}")
        lines.append(f"- **Total Edges:** {len(result.edges)}")
        lines.append(f"- **Findings:** {len(result.findings)}")
        lines.append("")

        lines.append("## Node Statistics")
        lines.append("")
        
        type_counts = Counter(n.type for n in result.nodes)
        for node_type, count in sorted(type_counts.items()):
            lines.append(f"- **{node_type}:** {count}")
        lines.append("")

        lines.append("## Findings")
        lines.append("")
        
        if result.findings:
            for finding in result.findings:
                severity_emoji = self._severity_emoji(finding.severity)
                lines.append(f"### {severity_emoji} {finding.rule_id}")
                lines.append("")
                lines.append(f"**Severity:** {finding.severity}")
                lines.append("")
                lines.append(f"**Message:** {finding.message}")
                lines.append("")
                if finding.node_ids:
                    lines.append(f"**Affected Nodes:** {', '.join(finding.node_ids)}")
                    lines.append("")
        else:
            lines.append("No findings detected.")
            lines.append("")

        lines.append("## Top Central Nodes")
        lines.append("")
        
        builder = GraphBuilder()
        builder.add_nodes_from(result.nodes)
        builder.add_edges_from(result.edges)
        
        if builder.number_of_nodes() > 0:
            centrality = nx.degree_centrality(builder.graph)
            sorted_centrality = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:10]
            
            for node_id, cent in sorted_centrality:
                lines.append(f"- **{node_id}** (centrality: {cent:.3f})")
        else:
            lines.append("No nodes in graph.")
        lines.append("")

        lines.append("## Dependency Matrix")
        lines.append("")
        lines.append("### Edges by Type")
        lines.append("")
        
        edge_counts = Counter(e.type for e in result.edges)
        for edge_type, count in sorted(edge_counts.items()):
            lines.append(f"- **{edge_type}:** {count}")
        lines.append("")

        lines.append("## Suggested Improvements")
        lines.append("")
        lines.extend(self._generate_suggestions(result))
        
        return "\n".join(lines)

    def _severity_emoji(self, severity: str) -> str:
        mapping = {
            "error": ":x:",
            "warning": ":warning:",
            "info": ":information_source:"
        }
        return mapping.get(severity, ":question:")

    def _generate_suggestions(self, result: ScanResult) -> list[str]:
        suggestions = []
        
        finding_types = set(f.rule_id for f in result.findings)
        
        if "circular_dependency" in finding_types:
            suggestions.append("- Review and break circular dependencies to improve maintainability")
        
        if "single_point_failure" in finding_types:
            suggestions.append("- Add redundancy for critical services that have many dependencies")
        
        if "secret_detector" in finding_types:
            suggestions.append("- Move secrets to environment variables or a secrets manager")
        
        if not suggestions:
            suggestions.append("- Architecture looks healthy!")
            suggestions.append("- Consider adding monitoring and alerting for production deployments")
        
        suggestions.append("")
        return suggestions

    def generate_diff_report(self, old_result: ScanResult, new_result: ScanResult, output_path: Path) -> None:
        content = self._build_diff_content(old_result, new_result)
        output_path.write_text(content, encoding="utf-8")

    def _build_diff_content(self, old_result: ScanResult, new_result: ScanResult) -> str:
        lines = []
        
        lines.append(f"# Architecture Diff Report")
        lines.append("")
        lines.append(f"**Generated:** {datetime.utcnow().isoformat()}")
        lines.append("")

        old_nodes = {n.id for n in old_result.nodes}
        new_nodes = {n.id for n in new_result.nodes}
        
        added_nodes = new_nodes - old_nodes
        removed_nodes = old_nodes - new_nodes
        
        lines.append("## Node Changes")
        lines.append("")
        lines.append(f"- **Added:** {len(added_nodes)}")
        lines.append(f"- **Removed:** {len(removed_nodes)}")
        lines.append("")
        
        if added_nodes:
            lines.append("### Added Nodes")
            lines.append("")
            for node_id in sorted(added_nodes):
                lines.append(f"- {node_id}")
            lines.append("")
        
        if removed_nodes:
            lines.append("### Removed Nodes")
            lines.append("")
            for node_id in sorted(removed_nodes):
                lines.append(f"- {node_id}")
            lines.append("")

        old_edges = {(e.source, e.target) for e in old_result.edges}
        new_edges = {(e.source, e.target) for e in new_result.edges}
        
        added_edges = new_edges - old_edges
        removed_edges = old_edges - new_edges
        
        lines.append("## Edge Changes")
        lines.append("")
        lines.append(f"- **Added:** {len(added_edges)}")
        lines.append(f"- **Removed:** {len(removed_edges)}")
        lines.append("")
        
        if added_edges:
            lines.append("### Added Edges")
            lines.append("")
            for source, target in sorted(added_edges):
                lines.append(f"- {source} -> {target}")
            lines.append("")
        
        if removed_edges:
            lines.append("### Removed Edges")
            lines.append("")
            for source, target in sorted(removed_edges):
                lines.append(f"- {source} -> {target}")
            lines.append("")

        old_findings = set((f.rule_id, f.severity, f.message) for f in old_result.findings)
        new_findings = set((f.rule_id, f.severity, f.message) for f in new_result.findings)
        
        added_findings = new_findings - old_findings
        removed_findings = old_findings - new_findings
        
        lines.append("## Findings Changes")
        lines.append("")
        lines.append(f"- **New:** {len(added_findings)}")
        lines.append(f"- **Resolved:** {len(removed_findings)}")
        lines.append("")
        
        if added_findings:
            lines.append("### New Findings")
            lines.append("")
            for rule_id, severity, message in sorted(added_findings):
                lines.append(f"- **[{severity}]** {rule_id}: {message}")
            lines.append("")
        
        if removed_findings:
            lines.append("### Resolved Findings")
            lines.append("")
            for rule_id, severity, message in sorted(removed_findings):
                lines.append(f"- ~~{rule_id}: {message}~~")
            lines.append("")

        return "\n".join(lines)
