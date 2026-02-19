from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class NodeType(Enum):
    SERVICE = "service"
    DATABASE = "database"
    QUEUE = "queue"
    EXTERNAL_API = "external_api"
    CONTAINER = "container"
    INFRA_RESOURCE = "infra_resource"
    LIBRARY = "library"


class EdgeType(Enum):
    CALLS = "calls"
    DEPENDS_ON = "depends_on"
    CONNECTS_TO = "connects_to"
    BUILDS = "builds"
    DEPLOYS = "deploys"


class Node(BaseModel):
    id: str = Field(description="Unique identifier for the node")
    name: str = Field(description="Human-readable name")
    type: NodeType = Field(description="Type of the node")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        use_enum_values = True


class Edge(BaseModel):
    source: str = Field(description="Source node ID")
    target: str = Field(description="Target node ID")
    type: EdgeType = Field(description="Type of relationship")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        use_enum_values = True


class Finding(BaseModel):
    rule_id: str = Field(description="Identifier of the rule that generated this finding")
    severity: str = Field(description="Severity level: info, warning, error")
    message: str = Field(description="Human-readable description")
    node_ids: list[str] = Field(default_factory=list, description="Related node IDs")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ScanResult(BaseModel):
    repo_id: str = Field(description="Repository identifier")
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
