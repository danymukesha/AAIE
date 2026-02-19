import hashlib
from pathlib import Path
from typing import Any
from aaie.graph.models import ScanResult
from aaie.storage.database import Database


class RepositoryStore:
    """High-level repository storage operations."""

    def __init__(self, db: Database | None = None) -> None:
        self.db = db or Database()

    def _generate_repo_id(self, path: Path) -> str:
        return hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:16]

    def register_repository(self, path: Path) -> str:
        repo_id = self._generate_repo_id(path)
        self.db.save_repository(
            repo_id=repo_id,
            name=path.name,
            path=str(path.resolve())
        )
        return repo_id

    def get_repository(self, repo_id: str) -> dict[str, Any] | None:
        return self.db.get_repository(repo_id)

    def list_repositories(self) -> list[dict[str, Any]]:
        return self.db.list_repositories()

    def save_scan_result(self, path: Path, result: ScanResult) -> int:
        repo_id = self._generate_repo_id(path)
        self.db.save_repository(
            repo_id=repo_id,
            name=path.name,
            path=str(path.resolve())
        )
        return self.db.save_scan(repo_id, result)

    def get_scan_result(self, scan_id: int) -> ScanResult | None:
        return self.db.get_scan(scan_id)

    def get_latest_scan(self, path: Path) -> ScanResult | None:
        repo_id = self._generate_repo_id(path)
        return self.db.get_latest_scan(repo_id)

    def list_scans(self, path: Path) -> list[dict[str, Any]]:
        repo_id = self._generate_repo_id(path)
        return self.db.list_scans(repo_id)
