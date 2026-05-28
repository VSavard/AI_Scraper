from __future__ import annotations

from src.models.job import Job
from src.transformations.base import BaseTransformation


class AdzunaTransformation(BaseTransformation[dict, Job]):
    """Transforme une réponse brute de l'API Adzuna en objet Job."""

    def transform(self, raw: dict) -> Job:
        location = raw.get("location", {}).get("display_name", "")
        company = raw.get("company", {}).get("display_name", "")
        salary_min = raw.get("salary_min")
        salary_max = raw.get("salary_max")

        return Job(
            job_id=f"adzuna-{raw.get('id', '')}",
            title=raw.get("title", ""),
            company=company,
            location=location,
            url=raw.get("redirect_url", ""),
            description=raw.get("description", ""),
            contract_type=self._map_contract(raw.get("contract_type", "")),
            work_schedule=self._map_schedule(raw.get("contract_time", "")),
            salary_min=float(salary_min) if salary_min else None,
            salary_max=float(salary_max) if salary_max else None,
            source="adzuna",
            language=raw.get("language", "en"),
        )

    def to_output(self, item: Job) -> dict:
        return item.to_dict()

    @staticmethod
    def _map_contract(value: str) -> str:
        mapping = {
            "permanent": "permanent",
            "contract": "contract",
            "internship": "internship",
            "temporary": "temporary",
        }
        return mapping.get(value.lower(), value)

    @staticmethod
    def _map_schedule(value: str) -> str:
        mapping = {
            "full_time": "full-time",
            "part_time": "part-time",
        }
        return mapping.get(value.lower(), value)
