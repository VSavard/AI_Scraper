from __future__ import annotations

import os

import anthropic


class AnthropicProvider:
    """Claude provider via the Anthropic SDK."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-6",
    ) -> None:
        self._client = anthropic.Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])
        self.model = model

    def complete(self, system: str, user: str, max_token: int = 1024) -> str:
        message = self._client.messages.create(
            model=self.model,
            max_tokens=max_token,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return message.content[0].text
