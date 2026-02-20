import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any
from aaie.graph.models import Node, Edge, Finding, ScanResult


class Database:
    """SQLite database for storing scan results."""

    def __init__(self, db_path: Path | None = None) -> None:
        if db_path is None:
            db_path = Path.home() / ".aaie" / "aaie.db"
        
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS repositories (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_scanned TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repo_id TEXT NOT NULL,
                    scanned_at TEXT NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (repo_id) REFERENCES repositories(id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT NOT NULL,
                    scan_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    metadata TEXT,
                    PRIMARY KEY (scan_id, id),
                    FOREIGN KEY (scan_id) REFERENCES scans(id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    target TEXT NOT NULL,
                    type TEXT NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (scan_id) REFERENCES scans(id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS findings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id INTEGER NOT NULL,
                    rule_id TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    node_ids TEXT,
                    metadata TEXT,
                    FOREIGN KEY (scan_id) REFERENCES scans(id)
                )
            """)

    def save_repository(self, repo_id: str, name: str, path: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO repositories (id, name, path, created_at)
                VALUES (?, ?, ?, ?)
            """, (repo_id, name, path, datetime.utcnow().isoformat()))

    def get_repository(self, repo_id: str) -> dict[str, Any] | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM repositories WHERE id = ?
            """, (repo_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def list_repositories(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM repositories ORDER BY last_scanned DESC")
            return [dict(row) for row in cursor.fetchall()]

    def save_scan(self, repo_id: str, result: ScanResult) -> int:
        with sqlite3.connect(self.db_path) as conn:
            scanned_at = datetime.utcnow().isoformat()
            cursor = conn.execute("""
                INSERT INTO scans (repo_id, scanned_at, metadata)
                VALUES (?, ?, ?)
            """, (repo_id, scanned_at, json.dumps(result.metadata)))
            scan_id = cursor.lastrowid
            if scan_id is None:
                raise RuntimeError("Failed to save scan")

            conn.execute("""
                UPDATE repositories SET last_scanned = ? WHERE id = ?
            """, (scanned_at, repo_id))

            for node in result.nodes:
                conn.execute("""
                    INSERT INTO nodes (id, scan_id, name, type, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (node.id, scan_id, node.name, node.type, json.dumps(node.metadata)))

            for edge in result.edges:
                conn.execute("""
                    INSERT INTO edges (scan_id, source, target, type, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (scan_id, edge.source, edge.target, edge.type, json.dumps(edge.metadata)))

            for finding in result.findings:
                conn.execute("""
                    INSERT INTO findings (scan_id, rule_id, severity, message, node_ids, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    scan_id, 
                    finding.rule_id, 
                    finding.severity, 
                    finding.message, 
                    json.dumps(finding.node_ids),
                    json.dumps(finding.metadata)
                ))

            return scan_id

    def get_scan(self, scan_id: int) -> ScanResult | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            scan_row = conn.execute("SELECT * FROM scans WHERE id = ?", (scan_id,)).fetchone()
            if not scan_row:
                return None

            repo_id = scan_row["repo_id"]

            nodes = []
            for node_row in conn.execute("SELECT * FROM nodes WHERE scan_id = ?", (scan_id,)):
                nodes.append(Node(
                    id=node_row["id"],
                    name=node_row["name"],
                    type=node_row["type"],
                    metadata=json.loads(node_row["metadata"] or "{}")
                ))

            edges = []
            for edge_row in conn.execute("SELECT * FROM edges WHERE scan_id = ?", (scan_id,)):
                edges.append(Edge(
                    source=edge_row["source"],
                    target=edge_row["target"],
                    type=edge_row["type"],
                    metadata=json.loads(edge_row["metadata"] or "{}")
                ))

            findings = []
            for finding_row in conn.execute("SELECT * FROM findings WHERE scan_id = ?", (scan_id,)):
                findings.append(Finding(
                    rule_id=finding_row["rule_id"],
                    severity=finding_row["severity"],
                    message=finding_row["message"],
                    node_ids=json.loads(finding_row["node_ids"] or "[]"),
                    metadata=json.loads(finding_row["metadata"] or "{}")
                ))

            return ScanResult(
                repo_id=repo_id,
                nodes=nodes,
                edges=edges,
                findings=findings,
                metadata=json.loads(scan_row["metadata"] or "{}")
            )

    def get_latest_scan(self, repo_id: str) -> ScanResult | None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id FROM scans WHERE repo_id = ? ORDER BY scanned_at DESC LIMIT 1
            """, (repo_id,))
            row = cursor.fetchone()
            if row:
                return self.get_scan(row[0])
            return None

    def list_scans(self, repo_id: str) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT id, repo_id, scanned_at, metadata FROM scans 
                WHERE repo_id = ? ORDER BY scanned_at DESC
            """, (repo_id,))
            return [dict(row) for row in cursor.fetchall()]
