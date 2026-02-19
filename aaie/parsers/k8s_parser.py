import re
import yaml
from pathlib import Path
from typing import Any
from aaie.graph.models import Node, Edge, NodeType, EdgeType
from aaie.parsers.base_parser import BaseParser


class K8sParser(BaseParser):
    """Parser for Kubernetes YAML manifests."""

    def __init__(self) -> None:
        super().__init__()

    @property
    def supported_extensions(self) -> list[str]:
        return [".yaml", ".yml"]

    def can_parse(self, file_path: Path) -> bool:
        if file_path.suffix not in (".yaml", ".yml"):
            return False
        try:
            content = file_path.read_text(encoding="utf-8")
            docs = list(yaml.safe_load_all(content))
            for doc in docs:
                if doc and isinstance(doc, dict):
                    kind = doc.get("kind", "")
                    if kind in ("Deployment", "Service", "ConfigMap", "Secret", "Pod", 
                               "StatefulSet", "DaemonSet", "Job", "CronJob", "Ingress",
                               "Namespace", "PersistentVolume", "PersistentVolumeClaim",
                               "ServiceAccount", "Role", "RoleBinding", "ClusterRole",
                               "ClusterRoleBinding", "NetworkPolicy"):
                        return True
        except Exception:
            pass
        return False

    def parse(self, file_path: Path) -> tuple[list[Node], list[Edge]]:
        nodes: list[Node] = []
        edges: list[Edge] = []

        try:
            content = file_path.read_text(encoding="utf-8")
            docs = list(yaml.safe_load_all(content))
        except Exception:
            return nodes, edges

        for doc in docs:
            if not doc or not isinstance(doc, dict):
                continue

            kind = doc.get("kind", "")
            metadata = doc.get("metadata", {})
            name = metadata.get("name", "unknown")
            namespace = metadata.get("namespace", "default")

            node_id = f"k8s:{kind.lower()}:{name}"
            
            node = self._create_node(kind, name, namespace, doc)
            if node:
                nodes.append(node)

            if kind == "Deployment":
                pod_spec = doc.get("spec", {}).get("template", {}).get("spec", {})
                containers = pod_spec.get("containers", [])
                for container in containers:
                    container_name = container.get("name", "unknown")
                    container_id = f"k8s:container:{namespace}/{name}/{container_name}"
                    container_node = Node(
                        id=container_id,
                        name=container_name,
                        type=NodeType.CONTAINER,
                        metadata={
                            "image": container.get("image", ""),
                            "ports": [p.get("containerPort") for p in container.get("ports", []) if p.get("containerPort")],
                            "env": [e.get("name") for e in container.get("env", [])],
                            "namespace": namespace,
                            "parent": name
                        }
                    )
                    nodes.append(container_node)
                    edges.append(Edge(
                        source=node_id,
                        target=container_id,
                        type=EdgeType.BUILDS,
                        metadata={}
                    ))

            if kind == "Service":
                selector = doc.get("spec", {}).get("selector", {})
                if selector:
                    edges.append(Edge(
                        source=node_id,
                        target=f"k8s:deployment:{namespace}/",
                        type=EdgeType.CONNECTS_TO,
                        metadata={"selector": selector}
                    ))

        return nodes, edges

    def _create_node(self, kind: str, name: str, namespace: str, doc: dict[str, Any]) -> Node | None:
        type_mapping = {
            "Deployment": NodeType.SERVICE,
            "Service": NodeType.SERVICE,
            "Pod": NodeType.CONTAINER,
            "StatefulSet": NodeType.SERVICE,
            "DaemonSet": NodeType.SERVICE,
            "Job": NodeType.SERVICE,
            "CronJob": NodeType.SERVICE,
            "ConfigMap": NodeType.INFRA_RESOURCE,
            "Secret": NodeType.INFRA_RESOURCE,
            "Ingress": NodeType.INFRA_RESOURCE,
            "PersistentVolume": NodeType.INFRA_RESOURCE,
            "PersistentVolumeClaim": NodeType.DATABASE,
            "Namespace": NodeType.INFRA_RESOURCE,
            "ServiceAccount": NodeType.INFRA_RESOURCE,
            "Role": NodeType.INFRA_RESOURCE,
            "ClusterRole": NodeType.INFRA_RESOURCE,
        }

        node_type = type_mapping.get(kind, NodeType.INFRA_RESOURCE)

        metadata: dict[str, Any] = {
            "namespace": namespace,
            "kind": kind
        }

        spec = doc.get("spec", {})
        
        if kind == "Service":
            svc_type = spec.get("type", "ClusterIP")
            metadata["service_type"] = svc_type
            metadata["ports"] = [p.get("port") for p in spec.get("ports", []) if p.get("port")]
        
        if kind == "Deployment":
            replicas = spec.get("replicas")
            if replicas is not None:
                metadata["replicas"] = replicas
        
        if kind == "ConfigMap":
            metadata["data_keys"] = list(spec.get("data", {}).keys())
        
        if kind == "Secret":
            metadata["type"] = spec.get("type", "Opaque")
            metadata["data_keys"] = list(spec.get("data", {}).keys())

        return Node(
            id=f"k8s:{kind.lower()}:{name}",
            name=name,
            type=node_type,
            metadata=metadata
        )
