from __future__ import annotations

from datetime import UTC, datetime

from src.params import FetchParams
from src.sources.adzuna import AdzunaSource
from src.sources.guichet_emploi import GuichetEmploiSource


class FetchOperation:
    """Télécharge les données brutes depuis les sources sans aucun traitement IA.

    Flux :
        AdzunaSource / GuichetEmploiSource
            → list[dict] bruts enrichis d'un champ ``_source``
            → enveloppe ``raw_jobs_v1`` prête à être sauvegardée et relue
              par ProcessOperation

    Aucune clé AI requise.
    """

    def __init__(
        self,
        adzuna: AdzunaSource | None = None,
        guichet: GuichetEmploiSource | None = None,
    ) -> None:
        self._adzuna = adzuna or AdzunaSource()
        self._guichet = guichet or GuichetEmploiSource()

    def run(self, params: FetchParams) -> dict:
        items: list[dict] = []

        if params.source in ("adzuna", "all"):
            for page in range(1, params.pages + 1):
                batch = self._adzuna.search(
                    params.query,
                    location=params.location,
                    page=page,
                    results_per_page=params.results_per_page,
                )
                for item in batch:
                    item["_source"] = "adzuna"
                items.extend(batch)

        if params.source in ("guichet-emploi", "all"):
            batch = self._guichet.fetch(
                query=params.query,
                location=params.location,
                max_results=params.pages * params.results_per_page,
            )
            for item in batch:
                item["_source"] = "guichet_emploi"
            items.extend(batch)

        return {
            "format": "raw_jobs_v1",
            "query": params.query,
            "location": params.location,
            "source": params.source,
            "fetched_at": datetime.now(UTC).isoformat(),
            "count": len(items),
            "items": items,
        }
