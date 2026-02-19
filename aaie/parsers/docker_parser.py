import re
from pathlib import Path
from typing import Any
from aaie.graph.models import Node, Edge, NodeType, EdgeType
from aaie.parsers.base_parser import BaseParser


class DockerParser(BaseParser):
    """Parser for Dockerfiles."""

    def __init__(self) -> None:
        super().__init__()

    @property
    def supported_filenames(self) -> list[str]:
        return ["Dockerfile", "Dockerfile.dev", "Dockerfile.prod", ".dockerignore"]

    def can_parse(self, file_path: Path) -> bool:
        return file_path.name.startswith("Dockerfile") or file_path.name == ".dockerignore"

    def parse(self, file_path: Path) -> tuple[list[Node], list[Edge]]:
        nodes: list[Node] = []
        edges: list[Edge] = []

        if file_path.name == ".dockerignore":
            return nodes, edges

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return nodes, edges

        base_image = self._extract_base_image(content)
        exposed_ports = self._extract_ports(content)
        build_args = self._extract_build_args(content)

        container_id = f"container:{file_path.parent.name}"
        container_node = Node(
            id=container_id,
            name=file_path.parent.name,
            type=NodeType.CONTAINER,
            metadata={
                "base_image": base_image,
                "exposed_ports": exposed_ports,
                "build_args": build_args,
                "dockerfile": str(file_path)
            }
        )
        nodes.append(container_node)

        if base_image:
            base_image_id = f"lib:{base_image}"
            base_image_node = Node(
                id=base_image_id,
                name=base_image,
                type=NodeType.LIBRARY,
                metadata={"type": "docker_image"}
            )
            nodes.append(base_image_node)
            edges.append(Edge(
                source=container_id,
                target=base_image_id,
                type=EdgeType.DEPENDS_ON,
                metadata={"relationship": "base_image"}
            ))

        return nodes, edges

    def _extract_base_image(self, content: str) -> str | None:
        match = re.search(r'^FROM\s+(?:--platform=[^\s]+\s+)?([^\s]+)', content, re.MULTILINE)
        if match:
            return match.group(1)
        return None

    def _extract_ports(self, content: str) -> list[str]:
        ports = []
        matches = re.findall(r'^EXPOSE\s+(\d+)', content, re.MULTILINE)
        for match in matches:
            ports.append(match)
        return ports

    def _extract_build_args(self, content: str) -> list[str]:
        args = []
        matches = re.findall(r'^ARG\s+([^\s=]+)', content, re.MULTILINE)
        for match in matches:
            args.append(match)
        return args
