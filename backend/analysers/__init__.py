from .base import LLMProvider
from .claude import ClaudeProvider
from .gemini import GeminiProvider
from .openai import OpenAIProvider

_PROVIDERS: dict[str, type[LLMProvider]] = {
    "anthropic": ClaudeProvider,
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
}


def get_provider(name: str, api_key: str) -> LLMProvider:
    cls = _PROVIDERS.get(name)
    if not cls:
        raise ValueError(
            f"Unknown LLM provider: {name!r}. Available: {list(_PROVIDERS)}"
        )
    return cls(api_key=api_key)
