from abc import ABC, abstractmethod
import networkx as nx
from typing import Any
from aaie.graph.models import Finding


class BaseRule(ABC):
    """Abstract base class for all rules."""

    def __init__(self, rule_id: str, description: str) -> None:
        self.rule_id = rule_id
        self.description = description

    @abstractmethod
    def evaluate(self, graph: nx.DiGraph) -> list[Finding]:
        """Evaluate the rule against the graph.
        
        Args:
            graph: The NetworkX DiGraph to evaluate
            
        Returns:
            List of findings
        """
        pass

    @property
    def name(self) -> str:
        return self.__class__.__name__
