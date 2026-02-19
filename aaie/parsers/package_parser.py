import json
import re
from pathlib import Path
from typing import Any
from aaie.graph.models import Node, Edge, NodeType, EdgeType
from aaie.parsers.base_parser import BaseParser


class PackageParser(BaseParser):
    """Parser for package.json and requirements.txt files."""

    def __init__(self) -> None:
        super().__init__()

    @property
    def supported_filenames(self) -> list[str]:
        return ["package.json", "requirements.txt", "Pipfile", "pyproject.toml", "poetry.lock", "package-lock.json"]

    def can_parse(self, file_path: Path) -> bool:
        return file_path.name in (
            "package.json", 
            "requirements.txt", 
            "Pipfile", 
            "pyproject.toml",
            "package-lock.json"
        )

    def parse(self, file_path: Path) -> tuple[list[Node], list[Edge]]:
        if file_path.name == "package.json":
            return self._parse_package_json(file_path)
        elif file_path.name == "requirements.txt":
            return self._parse_requirements_txt(file_path)
        elif file_path.name == "pyproject.toml":
            return self._parse_pyproject_toml(file_path)
        return [], []

    def _parse_package_json(self, file_path: Path) -> tuple[list[Node], list[Edge]]:
        nodes: list[Node] = []
        edges: list[Edge] = []

        try:
            content = file_path.read_text(encoding="utf-8")
            data = json.loads(content)
        except Exception:
            return nodes, edges

        project_name = data.get("name", file_path.parent.name)
        project_version = data.get("version", "unknown")

        project_node = Node(
            id=f"npm:{project_name}",
            name=project_name,
            type=NodeType.SERVICE,
            metadata={
                "version": project_version,
                "language": "javascript/typescript"
            }
        )
        nodes.append(project_node)

        deps = {}
        deps.update(data.get("dependencies", {}))
        deps.update(data.get("devDependencies", {}))

        for lib_name, lib_version in deps.items():
            lib_node = Node(
                id=f"lib:{lib_name}",
                name=lib_name,
                type=NodeType.LIBRARY,
                metadata={
                    "version": lib_version,
                    "package_manager": "npm",
                    "source": str(file_path)
                }
            )
            nodes.append(lib_node)
            edges.append(Edge(
                source=project_node.id,
                target=lib_node.id,
                type=EdgeType.DEPENDS_ON,
                metadata={"version": lib_version}
            ))

        return nodes, edges

    def _parse_requirements_txt(self, file_path: Path) -> tuple[list[Node], list[Edge]]:
        nodes: list[Node] = []
        edges: list[Edge] = []

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return nodes, edges

        project_node = Node(
            id=f"python:{file_path.parent.name}",
            name=file_path.parent.name,
            type=NodeType.SERVICE,
            metadata={"language": "python"}
        )
        nodes.append(project_node)

        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue

            match = re.match(r'^([a-zA-Z0-9_-]+)([=<>!~]+.*)?$', line)
            if match:
                lib_name = match.group(1)
                lib_version = match.group(2) or "any"

                lib_node = Node(
                    id=f"lib:{lib_name}",
                    name=lib_name,
                    type=NodeType.LIBRARY,
                    metadata={
                        "version": lib_version,
                        "package_manager": "pip",
                        "source": str(file_path)
                    }
                )
                nodes.append(lib_node)
                edges.append(Edge(
                    source=project_node.id,
                    target=lib_node.id,
                    type=EdgeType.DEPENDS_ON,
                    metadata={"version": lib_version}
                ))

        return nodes, edges

    def _parse_pyproject_toml(self, file_path: Path) -> tuple[list[Node], list[Edge]]:
        nodes: list[Node] = []
        edges: list[Edge] = []

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return nodes, edges

        project_node = Node(
            id=f"python:{file_path.parent.name}",
            name=file_path.parent.name,
            type=NodeType.SERVICE,
            metadata={"language": "python", "build_system": "poetry"}
        )
        nodes.append(project_node)

        deps_pattern = re.compile(r'(?:dependencies|dev-dependencies)\s*=\s*\[(.*?)\]', re.DOTALL)
        for match in deps_pattern.finditer(content):
            deps_block = match.group(1)
            lib_matches = re.findall(r'"([^"]+)"', deps_block)
            for lib_name in lib_matches:
                lib_node = Node(
                    id=f"lib:{lib_name}",
                    name=lib_name,
                    type=NodeType.LIBRARY,
                    metadata={
                        "package_manager": "poetry",
                        "source": str(file_path)
                    }
                )
                nodes.append(lib_node)
                edges.append(Edge(
                    source=project_node.id,
                    target=lib_node.id,
                    type=EdgeType.DEPENDS_ON,
                    metadata={}
                ))

        return nodes, edges
