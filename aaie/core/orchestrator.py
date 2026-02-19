import os
from pathlib import Path
from typing import Any
from aaie.core.config import Config, DEFAULT_CONFIG
from aaie.graph.models import ScanResult, Node, Edge, Finding
from aaie.graph.graph_builder import GraphBuilder
from aaie.parsers import (
    PythonParser,
    TerraformParser,
    DockerParser,
    K8sParser,
    PackageParser,
    BaseParser
)
from aaie.rules import (
    BaseRule,
    CircularDependencyRule,
    SinglePointFailureRule,
    SecretDetectorRule
)
from aaie.storage import RepositoryStore
from aaie.reports import MarkdownGenerator, DiagramGenerator


class Orchestrator:
    """Main orchestrator for the AAIE engine."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or DEFAULT_CONFIG
        self.parsers: list[BaseParser] = [
            PythonParser(),
            TerraformParser(),
            DockerParser(),
            K8sParser(),
            PackageParser()
        ]
        self.rules: list[BaseRule] = [
            CircularDependencyRule(),
            SinglePointFailureRule(threshold=self.config.spf_threshold),
            SecretDetectorRule()
        ]
        self.store = RepositoryStore()

    def scan(self, repo_path: Path) -> ScanResult:
        repo_path = repo_path.resolve()
        
        nodes, edges = self._collect_entities(repo_path)
        
        graph = GraphBuilder()
        graph.add_nodes_from(nodes)
        
        seen_edges: set[tuple[str, str]] = set()
        for edge in edges:
            if (edge.source, edge.target) not in seen_edges:
                try:
                    graph.add_edge(edge)
                    seen_edges.add((edge.source, edge.target))
                except ValueError:
                    pass
        
        findings = self._evaluate_rules(graph.graph)
        
        result = ScanResult(
            repo_id=self.store._generate_repo_id(repo_path),
            nodes=graph.get_nodes_by_type("service") + 
                  graph.get_nodes_by_type("database") + 
                  graph.get_nodes_by_type("queue") +
                  graph.get_nodes_by_type("external_api") +
                  graph.get_nodes_by_type("container") +
                  graph.get_nodes_by_type("infra_resource") +
                  graph.get_nodes_by_type("library"),
            edges=graph.get_edges(),
            findings=findings,
            metadata={"repo_path": str(repo_path)}
        )
        
        return result

    def _collect_entities(self, repo_path: Path) -> tuple[list[Node], list[Edge]]:
        all_nodes: list[Node] = []
        all_edges: list[Edge] = []
        
        seen_node_ids: set[str] = set()
        
        for file_path in self._walk_repository(repo_path):
            parser = self._select_parser(file_path)
            if parser is None:
                continue
            
            try:
                if file_path.stat().st_size > self.config.max_file_size:
                    continue
            except OSError:
                continue
            
            nodes, edges = parser.parse(file_path)
            
            for node in nodes:
                if node.id not in seen_node_ids:
                    all_nodes.append(node)
                    seen_node_ids.add(node.id)
            
            all_edges.extend(edges)
        
        return all_nodes, all_edges

    def _walk_repository(self, repo_path: Path) -> list[Path]:
        files = []
        
        for root, dirs, filenames in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in self.config.exclude_patterns]
            
            root_path = Path(root)
            
            for filename in filenames:
                file_path = root_path / filename
                
                if any(file_path.match(pattern) for pattern in self.config.include_patterns):
                    files.append(file_path)
        
        return files

    def _select_parser(self, file_path: Path) -> BaseParser | None:
        for parser in self.parsers:
            if parser.can_parse(file_path):
                return parser
        return None

    def _evaluate_rules(self, graph) -> list[Finding]:
        from aaie.graph.models import Finding
        
        findings = []
        
        for rule in self.rules:
            if rule.rule_id in self.config.enable_rules:
                findings.extend(rule.evaluate(graph))
        
        return findings

    def generate_report(self, result: ScanResult, output_path: Path) -> None:
        md_gen = MarkdownGenerator()
        md_gen.generate(result, output_path.with_suffix(".md"))
        
        diag_gen = DiagramGenerator()
        diag_gen.generate_dot(result, output_path.with_suffix(".dot"))

    def save_result(self, repo_path: Path, result: ScanResult) -> int:
        return self.store.save_scan_result(repo_path, result)

    def get_result(self, scan_id: int) -> ScanResult | None:
        return self.store.get_scan_result(scan_id)

    def list_repositories(self) -> list[dict[str, Any]]:
        return self.store.list_repositories()
