from __future__ import annotations

import json
import re

from src.models.job import Job
from src.providers.base import AIProvider


_SYSTEM = """Tu es un assistant d'extraction de données d'emploi.
À partir du texte brut d'une offre d'emploi, extrais les informations structurées et retourne UNIQUEMENT un JSON valide.
Aucune explication, aucun markdown — seulement l'objet JSON."""

_PROMPT_TEMPLATE = """Extrais les champs suivants de cette offre d'emploi.
Retourne un objet JSON avec ces clés exactes :
- title (string) : intitulé du poste
- company (string) : nom de l'entreprise
- location (string) : ville et province (ex: "Montréal, QC")
- contract_type (string) : "permanent" | "temporary" | "contract" | "internship" | ""
- work_schedule (string) : "full-time" | "part-time" | ""
- technologies (array de strings, max 15) : langages, frameworks, outils, plateformes
- salary_min (number ou null)
- salary_max (number ou null)
- salary_currency (string, défaut "CAD")
- description (string) : résumé 2-3 phrases

Texte de l'offre :
{text}"""


class JobExtractor:
    """Utilise un provider IA pour extraire les données structurées d'une offre."""

    def __init__(self, provider: AIProvider) -> None:
        self._provider = provider

    def extract(self, job: Job) -> Job:
        if not job.description:
            return job

        prompt = _PROMPT_TEMPLATE.format(text=job.description[:6000])

        try:
            raw = self._provider.complete(system=_SYSTEM, user=prompt, max_token=1024)
            data = self._parse_json(raw)
        except Exception:
            return job

        job.title = data.get("title") or job.title
        job.company = data.get("company") or job.company
        job.location = data.get("location") or job.location
        job.contract_type = data.get("contract_type") or job.contract_type
        job.work_schedule = data.get("work_schedule") or job.work_schedule
        job.technologies = data.get("technologies") or job.technologies
        job.salary_min = data.get("salary_min") or job.salary_min
        job.salary_max = data.get("salary_max") or job.salary_max
        job.salary_currency = data.get("salary_currency") or job.salary_currency
        job.description = data.get("description") or job.description
        return job

    @staticmethod
    def _parse_json(text: str) -> dict:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(text)
