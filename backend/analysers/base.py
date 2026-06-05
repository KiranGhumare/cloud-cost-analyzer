from abc import ABC, abstractmethod

from ..models.schemas import CostFinding


class LLMProvider(ABC):
    @abstractmethod
    async def generate_findings(self, telemetry: dict) -> list[CostFinding]:
        """Analyse collected AWS telemetry and return prioritised cost findings."""
        ...
