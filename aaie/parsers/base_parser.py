from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from aaie.graph.models import Node, Edge


class BaseParser(ABC):
    """Abstract base class for all parsers."""

    def __init__(self) -> None:
        self._nodes: list[Node] = []
        self._edges: list[Edge] = []

    @abstractmethod
    def parse(self, file_path: Path) -> tuple[list[Node], list[Edge]]:
        """Parse a file and return nodes and edges.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            Tuple of (nodes, edges)
        """
        pass

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if this parser can handle the file, False otherwise
        """
        pass

    @property
    def supported_extensions(self) -> list[str]:
        """Return list of supported file extensions."""
        return []

    @property
    def supported_filenames(self) -> list[str]:
        """Return list of supported filenames."""
        return []
