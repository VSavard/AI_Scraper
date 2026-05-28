from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Settings:
    anthropic_api_key: str | None
    openai_api_key: str | None
    gemini_api_key: str | None
    adzuna_app_id: str | None
    adzuna_app_key: str | None
    http_proxy: str | None


def load_settings(env_file: Path | None = None) -> Settings:
    """Load secrets from .env file and environment variables.

    Priority: environment variables > .env file.
    """
    candidates = [
        env_file,
        Path(".env"),
        Path(__file__).parent.parent / ".env",
    ]
    for path in candidates:
        if path and path.exists():
            load_dotenv(path, override=False)
            break

    return Settings(
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
        openai_api_key=os.environ.get("OPENAI_API_KEY"),
        gemini_api_key=os.environ.get("GEMINI_API_KEY"),
        adzuna_app_id=os.environ.get("ADZUNA_APP_ID"),
        adzuna_app_key=os.environ.get("ADZUNA_APP_KEY"),
        http_proxy=os.environ.get("HTTP_PROXY"),
    )


def validate(settings: Settings, provider: str) -> None:
    """Raise a clear error if required secrets are missing."""
    errors: list[str] = []

    if provider == "anthropic" and not settings.anthropic_api_key:
        errors.append("ANTHROPIC_API_KEY  — https://console.anthropic.com/settings/keys")

    if provider == "openai" and not settings.openai_api_key:
        errors.append("OPENAI_API_KEY     — https://platform.openai.com/api-keys")

    if provider == "gemini" and not settings.gemini_api_key:
        errors.append("GEMINI_API_KEY     — https://aistudio.google.com/apikey")

    if not settings.adzuna_app_id or not settings.adzuna_app_key:
        errors.append("ADZUNA_APP_ID / ADZUNA_APP_KEY  — https://developer.adzuna.com/")

    if errors:
        lines = "\n  ".join(errors)
        print(
            f"\nMissing secrets — add them to your .env file or environment:\n\n  {lines}\n\n"
            "Copy .env.example to .env and fill in the values.\n",
            file=sys.stderr,
        )
        sys.exit(1)
