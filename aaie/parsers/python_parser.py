import ast
import re
from pathlib import Path
from typing import Any
from aaie.graph.models import Node, Edge, NodeType, EdgeType
from aaie.parsers.base_parser import BaseParser


class PythonParser(BaseParser):
    """Parser for Python source files using the ast module."""

    def __init__(self) -> None:
        super().__init__()
        self._current_module: str = ""
        self._imports: dict[str, list[str]] = {}
        self._services: list[Node] = []
        self._databases: list[Node] = []
        self._function_calls: list[tuple[str, str]] = []

    @property
    def supported_extensions(self) -> list[str]:
        return [".py"]

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix == ".py"

    def parse(self, file_path: Path) -> tuple[list[Node], list[Edge]]:
        self._imports = {}
        self._services = []
        self._databases = []
        self._function_calls = []

        self._current_module = self._module_name_from_path(file_path)

        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(file_path))
            self._visit_tree(tree)
        except SyntaxError:
            pass

        nodes = []
        edges = []

        nodes.extend(self._services)
        nodes.extend(self._databases)

        for lib, deps in self._imports.items():
            if not lib:
                continue
            lib_node = Node(
                id=f"lib:{lib}",
                name=lib,
                type=NodeType.LIBRARY,
                metadata={"source": self._current_module}
            )
            nodes.append(lib_node)

        for service in self._services:
            for lib, _ in self._imports.items():
                if lib:
                    edges.append(Edge(
                        source=service.id,
                        target=f"lib:{lib}",
                        type=EdgeType.DEPENDS_ON,
                        metadata={"import": lib}
                    ))

        for source_func, target_func in self._function_calls:
            if self._node_exists(source_func, self._services) and self._node_exists(target_func, self._services):
                edges.append(Edge(
                    source=source_func,
                    target=target_func,
                    type=EdgeType.CALLS,
                    metadata={}
                ))

        return nodes, edges

    def _module_name_from_path(self, path: Path) -> str:
        parts = list(path.parts)
        if "src" in parts:
            idx = parts.index("src")
            parts = parts[idx + 1:]
        elif "aaie" in parts:
            idx = parts.index("aaie")
            parts = parts[idx + 1:]
        stem = path.stem
        all_parts = list(parts[:-1]) + [stem]
        return ".".join(all_parts)

    def _node_exists(self, name: str, nodes: list[Node]) -> bool:
        return any(n.id == name or n.name == name for n in nodes)

    def _visit_tree(self, tree: ast.AST) -> None:
        visitor = PythonASTVisitor(
            current_module=self._current_module,
            imports=self._imports,
            services=self._services,
            databases=self._databases,
            function_calls=self._function_calls
        )
        visitor.visit(tree)


class PythonASTVisitor(ast.NodeVisitor):
    def __init__(
        self,
        current_module: str,
        imports: dict[str, list[str]],
        services: list[Node],
        databases: list[Node],
        function_calls: list[tuple[str, str]]
    ) -> None:
        self.current_module = current_module
        self.imports = imports
        self.services = services
        self.databases = databases
        self.function_calls = function_calls

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            lib_name = alias.name.split(".")[0]
            if lib_name not in self.imports:
                self.imports[lib_name] = []
            self.imports[lib_name].append(alias.name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            lib_name = node.module.split(".")[0]
            if lib_name not in self.imports:
                self.imports[lib_name] = []
            for alias in node.names:
                self.imports[lib_name].append(f"{node.module}.{alias.name}")

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        node_id = f"{self.current_module}.{node.name}"

        if self._is_fastapi_app(node) or self._is_flask_app(node):
            self.services.append(Node(
                id=node_id,
                name=node.name,
                type=NodeType.SERVICE,
                metadata={"module": self.current_module, "framework": self._detect_framework(node)}
            ))

        if self._is_database_model(node):
            self.databases.append(Node(
                id=node_id,
                name=node.name,
                type=NodeType.DATABASE,
                metadata={"module": self.current_module}
            ))

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        func_id = f"{self.current_module}.{node.name}"

        if self._is_route_handler(node):
            if not any(s.id == func_id for s in self.services):
                self.services.append(Node(
                    id=func_id,
                    name=node.name,
                    type=NodeType.SERVICE,
                    metadata={"module": self.current_module, "handler": True}
                ))

        for call in ast.walk(node):
            if isinstance(call, ast.Call):
                if isinstance(call.func, ast.Name):
                    target_id = f"{self.current_module}.{call.func.id}"
                    self.function_calls.append((func_id, target_id))

        self.generic_visit(node)

    def _is_fastapi_app(self, node: ast.ClassDef) -> bool:
        for base in node.bases:
            if isinstance(base, ast.Name):
                if base.id in ("FastAPI", "APIRouter"):
                    return True
        return False

    def _is_flask_app(self, node: ast.ClassDef) -> bool:
        for base in node.bases:
            if isinstance(base, ast.Name):
                if base.id in ("Flask", "Blueprint"):
                    return True
        return False

    def _is_database_model(self, node: ast.ClassDef) -> bool:
        for base in node.bases:
            if isinstance(base, ast.Name):
                if base.id in ("Model", "Document"):
                    return True
        return False

    def _is_route_handler(self, node: ast.FunctionDef) -> bool:
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                if decorator.id in ("get", "post", "put", "delete", "patch", "route"):
                    return True
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    if decorator.func.id in ("get", "post", "put", "delete", "patch", "route"):
                        return True
                elif isinstance(decorator.func, ast.Attribute):
                    if decorator.func.attr in ("get", "post", "put", "delete", "patch", "route", "app", "router"):
                        return True
        return False

    def _detect_framework(self, node: ast.ClassDef) -> str:
        if self._is_fastapi_app(node):
            return "fastapi"
        elif self._is_flask_app(node):
            return "flask"
        return "unknown"
