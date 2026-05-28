from __future__ import annotations

import os

from google import genai
from google.genai import types


class GeminiProvider:
    """Gemini provider via the Google Gen AI SDK."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.0-flash",
    ) -> None:
        self._client = genai.Client(api_key=api_key or os.environ["GEMINI_API_KEY"])
        self.model = model

    def complete(self, system: str, user: str, max_token: int = 1024) -> str:
        response = self._client.models.generate_content(
            model=self.model,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=max_token,
            ),
        )
        return response.text or ""
