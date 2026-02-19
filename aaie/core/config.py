from pathlib import Path
from typing import Any
from pydantic import BaseModel


class Config(BaseModel):
    """Configuration for the AAIE engine."""
    
    db_path: Path | None = None
    output_dir: Path | None = None
    include_patterns: list[str] = ["*.py", "*.tf", "*.yaml", "*.yml", "Dockerfile", "package.json", "requirements.txt"]
    exclude_patterns: list[str] = ["__pycache__", ".git", "node_modules", ".venv", "venv", ".pytest_cache"]
    max_file_size: int = 1024 * 1024
    enable_rules: list[str] = ["circular_dependency", "single_point_failure", "secret_detector"]
    spf_threshold: int = 3
    
    class Config:
        arbitrary_types_allowed = True


DEFAULT_CONFIG = Config()
