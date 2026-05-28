from __future__ import annotations

import re
from datetime import datetime

from src.models.job import Job
from src.transformations.base import BaseTransformation


class GuichetEmploiTransformation(BaseTransformation[dict, Job]):
    """Transforme un item RSS du Guichet Emploi Canada en objet Job."""

    def transform(self, raw: dict) -> Job:
        return Job(
            job_id=f"guichet-{self._extract_id(raw.get('link', ''))}",
            title=self._clean(raw.get("title", "")),
            company=self._clean(raw.get("employer", "")),
            location=self._clean(raw.get("location", "")),
            url=raw.get("link", ""),
            description=self._strip_html(raw.get("description", "")),
            contract_type=self._map_noc(raw.get("noc", ""), raw.get("employment_terms", "")),
            work_schedule=self._map_schedule(raw.get("employment_terms", "")),
            salary_min=self._parse_salary_min(raw.get("salary", "")),
            salary_max=self._parse_salary_max(raw.get("salary", "")),
            posted_at=self._parse_date(raw.get("pubDate", "")),
            source="guichet_emploi",
            language=raw.get("language", "fr"),
        )

    def to_output(self, item: Job) -> dict:
        return item.to_dict()

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _clean(text: str) -> str:
        return text.strip()

    @staticmethod
    def _strip_html(html: str) -> str:
        return re.sub(r"<[^>]+>", " ", html).strip()

    @staticmethod
    def _extract_id(url: str) -> str:
        match = re.search(r"jobpostingid=(\d+)", url, re.IGNORECASE)
        return match.group(1) if match else url[-12:]

    @staticmethod
    def _map_noc(noc: str, terms: str) -> str:
        terms_lower = terms.lower()
        if "permanent" in terms_lower:
            return "permanent"
        if "temporaire" in terms_lower or "temporary" in terms_lower:
            return "temporary"
        if "contrat" in terms_lower or "contract" in terms_lower:
            return "contract"
        return ""

    @staticmethod
    def _map_schedule(terms: str) -> str:
        terms_lower = terms.lower()
        if "temps plein" in terms_lower or "full" in terms_lower:
            return "full-time"
        if "temps partiel" in terms_lower or "part" in terms_lower:
            return "part-time"
        return ""

    @staticmethod
    def _parse_salary_min(salary_str: str) -> float | None:
        numbers = re.findall(r"[\d,]+(?:\.\d+)?", salary_str.replace(",", ""))
        return float(numbers[0]) if numbers else None

    @staticmethod
    def _parse_salary_max(salary_str: str) -> float | None:
        numbers = re.findall(r"[\d,]+(?:\.\d+)?", salary_str.replace(",", ""))
        return float(numbers[1]) if len(numbers) > 1 else None

    @staticmethod
    def _parse_date(date_str: str) -> datetime | None:
        for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z"):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
