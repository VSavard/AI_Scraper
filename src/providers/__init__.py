from __future__ import annotations

from src.providers.base import AIProvider


def get_provider(name: str, **kwargs) -> AIProvider:
    """Return an AIProvider instance by name ("anthropic" or "openai")."""
    name = name.lower()
    if name == "anthropic":
        from src.providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider(**kwargs)
    if name == "openai":
        from src.providers.openai_provider import OpenAIProvider
        return OpenAIProvider(**kwargs)
    raise ValueError(f"Unknown provider: {name!r}. Choose 'anthropic' or 'openai'.")
