from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class Job:
    """Offre d'emploi structurée, prête à ingérer en JSON."""

    # ── Champs obligatoires ──────────────────────────────────────────────────
    title: str
    company: str
    location: str
    url: str

    # ── Classification ───────────────────────────────────────────────────────
    contract_type: str = ""     # permanent | temporary | contract | internship
    work_schedule: str = ""     # full-time | part-time

    # ── Technologies ─────────────────────────────────────────────────────────
    technologies: list[str] = field(default_factory=list)

    # ── Salaire ──────────────────────────────────────────────────────────────
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str = "CAD"

    # ── Contenu ──────────────────────────────────────────────────────────────
    description: str = ""

    # ── Métadonnées ──────────────────────────────────────────────────────────
    job_id: str = ""
    source: str = ""
    language: str = ""
    posted_at: datetime | None = None
    extracted_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # ── Scoring IA ───────────────────────────────────────────────────────────
    score: float | None = None
    score_rationale: str = ""

    # ── Helpers ──────────────────────────────────────────────────────────────
    def salary_range(self) -> str:
        if self.salary_min and self.salary_max:
            return f"{self.salary_min:,.0f}–{self.salary_max:,.0f} {self.salary_currency}"
        if self.salary_min:
            return f"{self.salary_min:,.0f}+ {self.salary_currency}"
        return "Non précisé"

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "contract_type": self.contract_type,
            "work_schedule": self.work_schedule,
            "technologies": self.technologies,
            "salary": {
                "min": self.salary_min,
                "max": self.salary_max,
                "currency": self.salary_currency,
            },
            "description": self.description,
            "url": self.url,
            "source": self.source,
            "language": self.language,
            "posted_at": self.posted_at.isoformat() if self.posted_at else None,
            "extracted_at": self.extracted_at.isoformat(),
            "score": self.score,
            "score_rationale": self.score_rationale,
        }
