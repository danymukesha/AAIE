import re
from pathlib import Path
from typing import Any
from aaie.graph.models import Node, Edge, NodeType, EdgeType
from aaie.parsers.base_parser import BaseParser


class TerraformParser(BaseParser):
    """Parser for Terraform configuration files."""

    def __init__(self) -> None:
        super().__init__()
        self._resources: list[Node] = []
        self._dependencies: list[Edge] = []

    @property
    def supported_extensions(self) -> list[str]:
        return [".tf"]

    @property
    def supported_filenames(self) -> list[str]:
        return ["terraform.tfvars", "variables.tf", "outputs.tf", "main.tf", "providers.tf"]

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix == ".tf"

    def parse(self, file_path: Path) -> tuple[list[Node], list[Edge]]:
        self._resources = []
        self._dependencies = []

        try:
            content = file_path.read_text(encoding="utf-8")
            self._parse_terraform(content)
        except Exception:
            pass

        return self._resources, self._dependencies

    def _parse_terraform(self, content: str) -> None:
        resource_pattern = re.compile(
            r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{(.*?)\n\}',
            re.DOTALL | re.MULTILINE
        )

        for match in resource_pattern.finditer(content):
            resource_type = match.group(1)
            resource_name = match.group(2)
            resource_block = match.group(3)

            node = self._create_resource_node(resource_type, resource_name, resource_block)
            if node:
                self._resources.append(node)

            deps = self._extract_dependencies(resource_block)
            for dep in deps:
                source_id = f"{resource_type}.{resource_name}"
                self._dependencies.append(Edge(
                    source=source_id,
                    target=dep,
                    type=EdgeType.DEPENDS_ON,
                    metadata={"file": "terraform"}
                ))

    def _create_resource_node(self, resource_type: str, resource_name: str, block: str) -> Node | None:
        type_mapping = {
            "aws_instance": NodeType.INFRA_RESOURCE,
            "aws_ec2_instance": NodeType.INFRA_RESOURCE,
            "aws_lambda_function": NodeType.INFRA_RESOURCE,
            "aws_ecs_service": NodeType.SERVICE,
            "aws_ecs_task_definition": NodeType.CONTAINER,
            "aws_db_instance": NodeType.DATABASE,
            "aws_rds_cluster": NodeType.DATABASE,
            "aws_s3_bucket": NodeType.INFRA_RESOURCE,
            "aws_sqs_queue": NodeType.QUEUE,
            "aws_sns_topic": NodeType.QUEUE,
            "aws_vpc": NodeType.INFRA_RESOURCE,
            "aws_subnet": NodeType.INFRA_RESOURCE,
            "aws_security_group": NodeType.INFRA_RESOURCE,
            "aws_iam_role": NodeType.INFRA_RESOURCE,
            "aws_iam_policy": NodeType.INFRA_RESOURCE,
            "aws_elb": NodeType.INFRA_RESOURCE,
            "aws_lb": NodeType.INFRA_RESOURCE,
            "aws_cloudwatch_log_group": NodeType.INFRA_RESOURCE,
            "aws_dynamodb_table": NodeType.DATABASE,
            "aws_elasticsearch_domain": NodeType.DATABASE,
            "aws_redis_cluster": NodeType.DATABASE,
            "aws_mq_broker": NodeType.QUEUE,
            "aws_kinesis_stream": NodeType.QUEUE,
            "aws_kinesis_firehose_delivery_stream": NodeType.QUEUE,
            "google_compute_instance": NodeType.INFRA_RESOURCE,
            "google_cloud_sql_database_instance": NodeType.DATABASE,
            "google_storage_bucket": NodeType.INFRA_RESOURCE,
            "azurerm_virtual_machine": NodeType.INFRA_RESOURCE,
            "azurerm_sql_database": NodeType.DATABASE,
            "azurerm_storage_account": NodeType.INFRA_RESOURCE,
            "null_resource": NodeType.INFRA_RESOURCE,
            "local_file": NodeType.INFRA_RESOURCE,
            "kubernetes_pod": NodeType.CONTAINER,
            "kubernetes_service": NodeType.SERVICE,
            "kubernetes_deployment": NodeType.SERVICE,
        }

        node_type = type_mapping.get(resource_type, NodeType.INFRA_RESOURCE)

        metadata: dict[str, Any] = {
            "resource_type": resource_type,
            "resource_name": resource_name
        }

        if "ami" in block:
            ami_match = re.search(r'ami\s*=\s*"([^"]+)"', block)
            if ami_match:
                metadata["ami"] = ami_match.group(1)

        if "instance_type" in block:
            it_match = re.search(r'instance_type\s*=\s*"([^"]+)"', block)
            if it_match:
                metadata["instance_type"] = it_match.group(1)

        if "engine" in block:
            eng_match = re.search(r'engine\s*=\s*"([^"]+)"', block)
            if eng_match:
                metadata["engine"] = eng_match.group(1)

        if "bucket" in block:
            bkt_match = re.search(r'bucket\s*=\s*"([^"]+)"', block)
            if bkt_match:
                metadata["bucket"] = bkt_match.group(1)

        if "vpc_id" in block:
            vpc_match = re.search(r'vpc_id\s*=\s*"([^"]+)"', block)
            if vpc_match:
                metadata["vpc_id"] = vpc_match.group(1)

        if "subnet_ids" in block:
            subnet_match = re.search(r'subnet_ids\s*=\s*\[(.*?)\]', block)
            if subnet_match:
                metadata["subnet_ids"] = subnet_match.group(1)

        return Node(
            id=f"{resource_type}.{resource_name}",
            name=resource_name,
            type=node_type,
            metadata=metadata
        )

    def _extract_dependencies(self, block: str) -> list[str]:
        deps = []

        ref_pattern = re.compile(r'\$\{([^}]+)\}')
        for match in ref_pattern.finditer(block):
            ref = match.group(1)

            resource_ref = re.search(r'(aws_|google_|azurerm_|null_)?([a-z_]+)\.([a-z_]+)', ref)
            if resource_ref:
                resource_type = resource_ref.group(2)
                resource_name = resource_ref.group(3)
                if resource_type and resource_name:
                    deps.append(f"{resource_type}.{resource_name}")

        module_pattern = re.compile(r'module\.([a-z0-9_-]+)')
        for match in module_pattern.finditer(block):
            deps.append(f"module.{match.group(1)}")

        return deps
