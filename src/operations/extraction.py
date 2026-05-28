from __future__ import annotations

from src.models.job import Job
from src.params import ExtractionParams
from src.processor.extractor import JobExtractor
from src.processor.scorer import JobScorer
from src.providers.base import AIProvider
from src.sources.adzuna import AdzunaSource
from src.sources.guichet_emploi import GuichetEmploiSource
from src.sources.scraper import JobPageScraper
from src.transformations.adzuna import AdzunaTransformation
from src.transformations.guichet_emploi import GuichetEmploiTransformation


class ExtractionOperation:
    """Orchestre la collecte, transformation et enrichissement IA des offres d'emploi.

    Flux :
        Sources (raw dicts)
            → Transformations (Job objects)
            → Scraper HTML (description complète)
            → JobExtractor (champs IA : technologies, salaire, type…)
            → JobScorer (score de pertinence)
            → list[dict] JSON prêts à ingérer
    """

    def __init__(
        self,
        provider: AIProvider,
        adzuna: AdzunaSource | None = None,
        guichet: GuichetEmploiSource | None = None,
        scraper: JobPageScraper | None = None,
    ) -> None:
        self._provider = provider
        self._adzuna = adzuna or AdzunaSource()
        self._guichet = guichet or GuichetEmploiSource()
        self._scraper = scraper or JobPageScraper()
        self._adzuna_transform = AdzunaTransformation()
        self._guichet_transform = GuichetEmploiTransformation()
        self._extractor = JobExtractor(provider)
        self._scorer = JobScorer(provider)

    def run(self, params: ExtractionParams) -> list[dict]:
        jobs = self._collect(params)

        if params.enrich:
            jobs = self._enrich(jobs)

        if params.ai_extract:
            jobs = [self._extractor.extract(j) for j in jobs]

        if params.score and params.criteria:
            jobs = self._scorer.score_many(jobs, params.criteria)

        if params.top:
            jobs = jobs[: params.top]

        return [j.to_dict() for j in jobs]

    # ── Collecte ─────────────────────────────────────────────────────────────

    def _collect(self, params: ExtractionParams) -> list[Job]:
        jobs: list[Job] = []

        if params.source in ("adzuna", "all"):
            for page in range(1, params.pages + 1):
                raw = self._adzuna.search(
                    params.query,
                    location=params.location,
                    page=page,
                    results_per_page=params.results_per_page,
                )
                jobs += self._adzuna_transform.transform_many(raw)

        if params.source in ("guichet-emploi", "all"):
            raw = self._guichet.fetch(
                query=params.query,
                location=params.location,
                max_results=params.pages * params.results_per_page,
            )
            jobs += self._guichet_transform.transform_many(raw)

        return jobs

    # ── Enrichissement HTML ───────────────────────────────────────────────────

    def _enrich(self, jobs: list[Job]) -> list[Job]:
        enriched = []
        for job in jobs:
            try:
                enriched.append(self._scraper.enrich_job(job))
            except Exception:
                enriched.append(job)
        return enriched
