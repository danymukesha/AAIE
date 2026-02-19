import re
from pathlib import Path
from typing import Any
import networkx as nx
from aaie.graph.models import Finding
from aaie.rules.base_rule import BaseRule


class SecretDetectorRule(BaseRule):
    """Detects hardcoded secrets in code and configuration files."""

    SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
        ("aws_access_key", re.compile(r'(?:aws_access_key_id|aws_access_key)\s*[=:]\s*["\']?([A-Z0-9]{20})["\']?', re.IGNORECASE)),
        ("aws_secret_key", re.compile(r'(?:aws_secret_access_key|aws_secret_key)\s*[=:]\s*["\']?([A-Za-z0-9/+=]{40})["\']?', re.IGNORECASE)),
        ("github_token", re.compile(r'(?:gh_token|github_token|GITHUB_TOKEN)\s*[=:]\s*["\']?([a-zA-Z0-9_]{36,})["\']?', re.IGNORECASE)),
        ("api_key", re.compile(r'(?:api_key|apikey|API_KEY)\s*[=:]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?', re.IGNORECASE)),
        ("password", re.compile(r'(?:password|passwd|pwd)\s*[=:]\s*["\']?([^\s"\']{8,})["\']?', re.IGNORECASE)),
        ("private_key", re.compile(r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----')),
        ("jwt_token", re.compile(r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*')),
        ("database_url", re.compile(r'(?:database_url|DB_URL|db_url)\s*[=:]\s*["\']?(mysql|postgres|mongodb|redis)://[^\s"\']+["\']?', re.IGNORECASE)),
        ("slack_token", re.compile(r'xox[baprs]-[0-9]{10,13}-[0-9]{10,13}[a-zA-Z0-9-]*')),
        ("stripe_key", re.compile(r'(?:sk|pk)_(?:test|live)_[a-zA-Z0-9]{24,}')),
    ]

    def __init__(self) -> None:
        super().__init__(
            rule_id="secret_detector",
            description="Detects hardcoded secrets in code and configuration files"
        )

    def evaluate(self, graph: nx.DiGraph) -> list[Finding]:
        findings = []

        for node_id, node_data in graph.nodes(data=True):
            metadata = node_data.get("metadata", {})
            
            if "source" in metadata:
                findings.extend(self._scan_file(metadata["source"], node_id))

            if "dockerfile" in metadata:
                findings.extend(self._scan_file(metadata["dockerfile"], node_id))

            for key, value in metadata.items():
                if isinstance(value, str):
                    findings.extend(self._scan_string(value, node_id, key))

        return findings

    def _scan_file(self, file_path: str, node_id: str) -> list[Finding]:
        findings = []
        
        try:
            path = Path(file_path)
            if not path.exists():
                return findings
            
            content = path.read_text(encoding="utf-8")
            
            for secret_type, pattern in self.SECRET_PATTERNS:
                matches = pattern.finditer(content)
                for match in matches:
                    if secret_type == "private_key":
                        line_num = content[:match.start()].count('\n') + 1
                        finding = Finding(
                            rule_id=self.rule_id,
                            severity="error",
                            message=f"Private key detected in {file_path} (line {line_num})",
                            node_ids=[node_id],
                            metadata={"file": file_path, "line": line_num, "type": secret_type}
                        )
                    else:
                        line_num = content[:match.start()].count('\n') + 1
                        finding = Finding(
                            rule_id=self.rule_id,
                            severity="error",
                            message=f"Potential {secret_type} detected in {file_path} (line {line_num})",
                            node_ids=[node_id],
                            metadata={"file": file_path, "line": line_num, "type": secret_type}
                        )
                    findings.append(finding)
                    
        except Exception:
            pass
            
        return findings

    def _scan_string(self, text: str, node_id: str, context: str) -> list[Finding]:
        findings = []
        
        for secret_type, pattern in self.SECRET_PATTERNS:
            if pattern.search(text):
                finding = Finding(
                    rule_id=self.rule_id,
                    severity="error",
                    message=f"Potential {secret_type} detected in node metadata ({context})",
                    node_ids=[node_id],
                    metadata={"type": secret_type, "context": context}
                )
                findings.append(finding)
                
        return findings
