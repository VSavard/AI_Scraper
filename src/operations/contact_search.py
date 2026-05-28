from __future__ import annotations

from src.models.contact import Contact
from src.models.job import Job
from src.params import ContactSearchParams
from src.providers.base import AIProvider
from src.transformations.contact import ContactTransformation


class ContactSearchOperation:
    """Recherche les personnes en autorité TI pour chaque entreprise trouvée.

    Flux :
        ExtractionOperation (Job objects)
            → Déduplique les entreprises
            → Recherche web DuckDuckGo par entreprise
            → ContactTransformation / IA (Contact objects)
            → list[dict] JSON prêts à ingérer
    """

    _IT_TITLES = (
        'CTO OR "Chief Technology Officer" OR "VP Technology" OR "VP IT" '
        'OR "Director IT" OR "Directeur TI" OR "VP Technologie"'
    )

    def __init__(self, provider: AIProvider) -> None:
        self._provider = provider

    def run(self, jobs: list[Job], params: ContactSearchParams) -> list[dict]:
        companies = self._unique_companies(jobs)
        contacts: list[Contact] = []

        for company in companies:
            results = self._web_search(company)
            if not results:
                continue
            transformer = ContactTransformation(self._provider, company)
            contacts += transformer.transform_many(results)

        # Déduplique par (company, name)
        seen: set[tuple[str, str]] = set()
        unique: list[Contact] = []
        for c in contacts:
            key = (c.company.lower(), c.name.lower())
            if key not in seen and c.name:
                seen.add(key)
                unique.append(c)

        return [c.to_dict() for c in unique]

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _unique_companies(jobs: list[Job]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for job in jobs:
            name = job.company.strip()
            if name and name.lower() not in seen:
                seen.add(name.lower())
                result.append(name)
        return result

    def _web_search(self, company: str) -> list[dict]:
        try:
            from duckduckgo_search import DDGS

            query = f'"{company}" ({self._IT_TITLES})'
            with DDGS() as ddgs:
                return list(ddgs.text(query, max_results=5))
        except Exception:
            return []
