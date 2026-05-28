from __future__ import annotations

import os
from typing import Any

import requests


_BASE_URL = "https://api.adzuna.com/v1/api/jobs"


class AdzunaSource:
    """Récupère les offres d'emploi brutes depuis l'API Adzuna.

    Retourne des dicts bruts — la transformation vers Job est déléguée
    à AdzunaTransformation.
    """

    def __init__(
        self,
        app_id: str | None = None,
        app_key: str | None = None,
        country: str = "ca",
    ) -> None:
        self.app_id = app_id or os.environ.get("ADZUNA_APP_ID", "")
        self.app_key = app_key or os.environ.get("ADZUNA_APP_KEY", "")
        self.country = country

    def search(
        self,
        query: str,
        location: str = "",
        page: int = 1,
        results_per_page: int = 20,
    ) -> list[dict]:
        params: dict[str, Any] = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": results_per_page,
            "what_or": query,
            "content-type": "application/json",
        }
        if location:
            params["where"] = location

        url = f"{_BASE_URL}/{self.country}/search/{page}"
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json().get("results", [])
