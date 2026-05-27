from __future__ import annotations

import os
from typing import Any

import requests

from src.models.job import Job


_BASE_URL = "https://api.adzuna.com/v1/api/jobs"


class AdzunaSource:
    """Fetch job listings from the Adzuna API."""

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
    ) -> list[Job]:
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

        return [self._to_job(item) for item in response.json().get("results", [])]

    def _to_job(self, data: dict) -> Job:
        salary = data.get("salary_min"), data.get("salary_max")
        location = data.get("location", {}).get("display_name", "")
        company = data.get("company", {}).get("display_name", "")

        return Job(
            title=data.get("title", ""),
            company=company,
            location=location,
            url=data.get("redirect_url", ""),
            description=data.get("description", ""),
            salary_min=float(salary[0]) if salary[0] else None,
            salary_max=float(salary[1]) if salary[1] else None,
            contract_type=data.get("contract_type", ""),
            source="adzuna",
        )
