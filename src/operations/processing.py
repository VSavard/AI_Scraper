from __future__ import annotations

import json

from src.models.job import Job
from src.params import ProcessParams
from src.processor.extractor import JobExtractor
from src.processor.scorer import JobScorer
from src.providers.base import AIProvider
from src.sources.scraper import JobPageScraper
from src.transformations.adzuna import AdzunaTransformation
from src.transformations.guichet_emploi import GuichetEmploiTransformation


class ProcessOperation:
    """Applique transformation + enrichissement IA sur un fichier de données brutes.

    Accepte deux formats d'entrée :
    - ``raw_jobs_v1``  : JSON produit par FetchOperation (dicts bruts + champ ``_source``)
    - Liste de Job dicts : JSON déjà transformé (``job_id``, ``title``, ``company``…)

    Flux :
        Fichier JSON
            → Détection du format
            → Transformation vers Job objects (si format brut)
            → Scraper HTML (optionnel)
            → JobExtractor via IA
            → JobScorer via IA
            → list[dict] prêts à ingérer
    """

    def __init__(
        self,
        provider: AIProvider,
        scraper: JobPageScraper | None = None,
    ) -> None:
        self._provider = provider
        self._scraper = scraper or JobPageScraper()
        self._extractor = JobExtractor(provider)
        self._scorer = JobScorer(provider)
        self._adzuna_transform = AdzunaTransformation()
        self._guichet_transform = GuichetEmploiTransformation()

    def run(self, params: ProcessParams) -> list[dict]:
        with open(params.input, encoding="utf-8") as f:
            data = json.load(f)

        jobs = self._load(data)

        if params.enrich:
            jobs = self._enrich(jobs)

        if params.ai_extract:
            jobs = [self._extractor.extract(j) for j in jobs]

        if params.score and params.criteria:
            jobs = self._scorer.score_many(jobs, params.criteria)

        if params.top:
            jobs = jobs[: params.top]

        return [j.to_dict() for j in jobs]

    # ── Chargement ────────────────────────────────────────────────────────────

    def _load(self, data: dict | list) -> list[Job]:
        """Détecte le format et retourne une liste de Job objects."""
        if isinstance(data, dict) and data.get("format") == "raw_jobs_v1":
            return self._from_raw(data["items"])
        if isinstance(data, list):
            return self._from_job_dicts(data)
        raise ValueError(
            "Format non reconnu. Attendu : liste de job dicts ou enveloppe raw_jobs_v1."
        )

    def _from_raw(self, items: list[dict]) -> list[Job]:
        """Transforme des dicts bruts (avec champ ``_source``) en Job objects."""
        jobs: list[Job] = []
        for item in items:
            source = item.pop("_source", "adzuna")
            try:
                if source == "adzuna":
                    jobs.append(self._adzuna_transform.transform(item))
                elif source == "guichet_emploi":
                    jobs.append(self._guichet_transform.transform(item))
            except Exception:
                pass
        return jobs

    def _from_job_dicts(self, items: list[dict]) -> list[Job]:
        """Reconstruit des Job objects à partir d'un JSON déjà transformé."""
        from datetime import datetime

        jobs: list[Job] = []
        for d in items:
            try:
                salary = d.get("salary", {})
                jobs.append(
                    Job(
                        job_id=d.get("job_id", ""),
                        title=d.get("title", ""),
                        company=d.get("company", ""),
                        location=d.get("location", ""),
                        url=d.get("url", ""),
                        description=d.get("description", ""),
                        contract_type=d.get("contract_type", ""),
                        work_schedule=d.get("work_schedule", ""),
                        technologies=d.get("technologies", []),
                        salary_min=salary.get("min"),
                        salary_max=salary.get("max"),
                        salary_currency=salary.get("currency", "CAD"),
                        source=d.get("source", ""),
                        language=d.get("language", ""),
                    )
                )
            except Exception:
                pass
        return jobs

    def _enrich(self, jobs: list[Job]) -> list[Job]:
        enriched = []
        for job in jobs:
            try:
                enriched.append(self._scraper.enrich_job(job))
            except Exception:
                enriched.append(job)
        return enriched
