from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Job:
    """Structured representation of a job posting."""

    title: str
    company: str
    location: str
    url: str

    description: str = ""
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str = "CAD"
    contract_type: str = ""
    skills: list[str] = field(default_factory=list)
    posted_at: datetime | None = None
    source: str = ""

    score: float | None = None
    score_rationale: str = ""

    def salary_range(self) -> str:
        if self.salary_min and self.salary_max:
            return f"{self.salary_min:,.0f}–{self.salary_max:,.0f} {self.salary_currency}"
        if self.salary_min:
            return f"{self.salary_min:,.0f}+ {self.salary_currency}"
        return "Non précisé"

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "url": self.url,
            "description": self.description,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "salary_currency": self.salary_currency,
            "contract_type": self.contract_type,
            "skills": self.skills,
            "posted_at": self.posted_at.isoformat() if self.posted_at else None,
            "source": self.source,
            "score": self.score,
            "score_rationale": self.score_rationale,
        }
