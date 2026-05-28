from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class Contact:
    """Personne en autorité TI trouvée via recherche web, prête à ingérer en JSON."""

    # ── Champs obligatoires ──────────────────────────────────────────────────
    company: str
    name: str
    title: str

    # ── Coordonnées ──────────────────────────────────────────────────────────
    linkedin_url: str = ""
    email: str = ""
    phone: str = ""

    # ── Métadonnées ──────────────────────────────────────────────────────────
    source: str = "web_search"
    confidence: float = 0.0
    extracted_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict:
        return {
            "company": self.company,
            "name": self.name,
            "title": self.title,
            "linkedin_url": self.linkedin_url,
            "email": self.email,
            "phone": self.phone,
            "source": self.source,
            "confidence": self.confidence,
            "extracted_at": self.extracted_at.isoformat(),
        }
