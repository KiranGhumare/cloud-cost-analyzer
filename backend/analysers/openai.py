from ..models.schemas import CostFinding
from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        try:
            from openai import AsyncOpenAI  # noqa: F401
        except ImportError:
            raise ImportError("Install the openai package to use this provider: pip install openai")
        self.api_key = api_key
        self.model = model

    async def generate_findings(self, telemetry: dict) -> list[CostFinding]:
        raise NotImplementedError("OpenAI provider is not yet implemented")
