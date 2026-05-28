from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class BaseTransformation(ABC, Generic[InputT, OutputT]):
    """Contrat commun pour toutes les transformations de données.

    Chaque implémentation reçoit de la donnée brute (dict depuis une source)
    et produit un objet du domaine, ainsi qu'un dict JSON prêt à ingérer.
    """

    @abstractmethod
    def transform(self, raw: InputT) -> OutputT:
        """Transforme un enregistrement brut en objet du domaine."""
        ...

    @abstractmethod
    def to_output(self, item: OutputT) -> dict:
        """Sérialise un objet du domaine en dict JSON pour ingestion."""
        ...

    def transform_many(self, items: list[InputT]) -> list[OutputT]:
        """Transforme une liste en ignorant silencieusement les erreurs."""
        results: list[OutputT] = []
        for raw in items:
            try:
                results.append(self.transform(raw))
            except Exception:
                pass
        return results

    def to_output_many(self, items: list[OutputT]) -> list[dict]:
        return [self.to_output(item) for item in items]

    def pipeline(self, items: list[InputT]) -> list[dict]:
        """Raccourci : transform_many → to_output_many en une seule passe."""
        return self.to_output_many(self.transform_many(items))
