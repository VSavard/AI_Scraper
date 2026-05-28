from __future__ import annotations

import json
import re

from src.models.contact import Contact
from src.providers.base import AIProvider
from src.transformations.base import BaseTransformation


_SYSTEM = """Tu es un assistant d'extraction de contacts professionnels.
Analyse les résultats de recherche web et retourne UNIQUEMENT un JSON valide.
Aucune explication, aucun markdown — seulement l'objet JSON."""

_PROMPT_TEMPLATE = """Extrais les informations de contact du résultat de recherche suivant.
Retourne un objet JSON avec les clés :
- name (string) : prénom et nom complet
- title (string) : titre du poste
- linkedin_url (string ou "") : URL LinkedIn si présente
- email (string ou "") : adresse courriel si présente
- phone (string ou "") : numéro de téléphone si présent
- confidence (float 0.0–1.0) : confiance dans l'exactitude des données

Entreprise cible : {company}

Résultat de recherche :
Titre : {result_title}
URL   : {result_url}
Extrait : {result_body}"""


class ContactTransformation(BaseTransformation[dict, Contact]):
    """Transforme un résultat de recherche web en objet Contact via IA."""

    def __init__(self, provider: AIProvider, company: str) -> None:
        self._provider = provider
        self._company = company

    def transform(self, raw: dict) -> Contact:
        prompt = _PROMPT_TEMPLATE.format(
            company=self._company,
            result_title=raw.get("title", ""),
            result_url=raw.get("href", raw.get("url", "")),
            result_body=raw.get("body", raw.get("snippet", ""))[:1500],
        )
        response = self._provider.complete(system=_SYSTEM, user=prompt, max_token=512)
        data = self._parse_json(response)

        return Contact(
            company=self._company,
            name=data.get("name", ""),
            title=data.get("title", ""),
            linkedin_url=data.get("linkedin_url", ""),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            confidence=float(data.get("confidence", 0.0)),
        )

    def to_output(self, item: Contact) -> dict:
        return item.to_dict()

    @staticmethod
    def _parse_json(text: str) -> dict:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(text)
