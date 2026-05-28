from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.models.contact import Contact
from src.models.job import Job
from src.transformations.adzuna import AdzunaTransformation
from src.transformations.contact import ContactTransformation
from src.transformations.guichet_emploi import GuichetEmploiTransformation


# ── Adzuna ────────────────────────────────────────────────────────────────────

class TestAdzunaTransformation:
    def setup_method(self):
        self.t = AdzunaTransformation()

    def _raw(self, **kwargs) -> dict:
        base = {
            "id": "abc123",
            "title": "Data Engineer",
            "company": {"display_name": "Acme Corp"},
            "location": {"display_name": "Montréal, QC"},
            "redirect_url": "http://example.com/job",
            "description": "Exciting role...",
            "contract_type": "permanent",
            "contract_time": "full_time",
            "salary_min": 85000,
            "salary_max": 110000,
        }
        base.update(kwargs)
        return base

    def test_basic_transform(self):
        job = self.t.transform(self._raw())
        assert job.title == "Data Engineer"
        assert job.company == "Acme Corp"
        assert job.location == "Montréal, QC"
        assert job.contract_type == "permanent"
        assert job.work_schedule == "full-time"
        assert job.salary_min == 85_000.0
        assert job.salary_max == 110_000.0
        assert job.source == "adzuna"
        assert job.job_id == "adzuna-abc123"

    def test_missing_company(self):
        raw = self._raw()
        raw["company"] = {}
        job = self.t.transform(raw)
        assert job.company == ""

    def test_missing_salary(self):
        raw = self._raw()
        raw.pop("salary_min")
        raw.pop("salary_max")
        job = self.t.transform(raw)
        assert job.salary_min is None
        assert job.salary_max is None

    def test_to_output_is_dict(self):
        job = self.t.transform(self._raw())
        d = self.t.to_output(job)
        assert isinstance(d, dict)
        assert "technologies" in d
        assert "salary" in d

    def test_transform_many_skips_errors(self):
        good = self._raw()
        bad = None  # NoneType n'a pas de méthode .get() → AttributeError attrapée
        results = self.t.transform_many([good, bad])
        assert len(results) == 1

    def test_pipeline(self):
        dicts = self.t.pipeline([self._raw(), self._raw(id="xyz")])
        assert len(dicts) == 2
        assert all(isinstance(d, dict) for d in dicts)


# ── Guichet Emploi ────────────────────────────────────────────────────────────

class TestGuichetEmploiTransformation:
    def setup_method(self):
        self.t = GuichetEmploiTransformation()

    def _raw(self, **kwargs) -> dict:
        base = {
            "title": "Ingénieur en données",
            "link": "http://jobbank.gc.ca/job?jobpostingid=9876543",
            "description": "<p>Poste permanent à temps plein.</p>",
            "pubDate": "Thu, 01 Jan 2026 10:00:00 +0000",
            "employer": "Ministère du Numérique",
            "location": "Québec, QC",
            "salary": "80000 - 100000",
            "employment_terms": "Temps plein, Permanent",
            "noc": "2173",
            "language": "fr",
        }
        base.update(kwargs)
        return base

    def test_basic_transform(self):
        job = self.t.transform(self._raw())
        assert job.title == "Ingénieur en données"
        assert job.company == "Ministère du Numérique"
        assert job.location == "Québec, QC"
        assert job.work_schedule == "full-time"
        assert job.contract_type == "permanent"
        assert job.source == "guichet_emploi"
        assert job.job_id == "guichet-9876543"

    def test_salary_parsing(self):
        job = self.t.transform(self._raw())
        assert job.salary_min == 80_000.0
        assert job.salary_max == 100_000.0

    def test_html_stripped_from_description(self):
        job = self.t.transform(self._raw())
        assert "<p>" not in job.description

    def test_date_parsing(self):
        job = self.t.transform(self._raw())
        assert job.posted_at is not None
        assert job.posted_at.year == 2026

    def test_to_output_is_dict(self):
        job = self.t.transform(self._raw())
        d = self.t.to_output(job)
        assert isinstance(d, dict)
        assert d["source"] == "guichet_emploi"


# ── Contact ───────────────────────────────────────────────────────────────────

class TestContactTransformation:
    def _make_provider(self, response: str) -> MagicMock:
        provider = MagicMock()
        provider.complete.return_value = response
        return provider

    def _raw_search_result(self) -> dict:
        return {
            "title": "Jane Doe - CTO at Acme Corp | LinkedIn",
            "href": "https://linkedin.com/in/janedoe",
            "body": "Jane Doe is the Chief Technology Officer at Acme Corp since 2022.",
        }

    def test_transform_valid_response(self):
        ai_response = '{"name": "Jane Doe", "title": "CTO", "linkedin_url": "https://linkedin.com/in/janedoe", "email": "", "phone": "", "confidence": 0.9}'
        provider = self._make_provider(ai_response)
        t = ContactTransformation(provider, company="Acme Corp")

        contact = t.transform(self._raw_search_result())
        assert contact.name == "Jane Doe"
        assert contact.title == "CTO"
        assert contact.company == "Acme Corp"
        assert contact.confidence == 0.9

    def test_transform_uses_company(self):
        ai_response = '{"name": "Bob", "title": "VP IT", "linkedin_url": "", "email": "", "phone": "", "confidence": 0.7}'
        provider = self._make_provider(ai_response)
        t = ContactTransformation(provider, company="TechCorp")

        contact = t.transform(self._raw_search_result())
        assert contact.company == "TechCorp"

    def test_to_output_is_dict(self):
        ai_response = '{"name": "Bob", "title": "VP IT", "linkedin_url": "", "email": "", "phone": "", "confidence": 0.5}'
        provider = self._make_provider(ai_response)
        t = ContactTransformation(provider, company="Corp")
        contact = t.transform(self._raw_search_result())
        d = t.to_output(contact)
        assert isinstance(d, dict)
        assert "extracted_at" in d
