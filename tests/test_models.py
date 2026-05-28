from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.models.contact import Contact
from src.models.job import Job


class TestJob:
    def test_salary_range_min_max(self):
        job = Job(title="Dev", company="Acme", location="MTL", url="http://x.com")
        job.salary_min = 80_000
        job.salary_max = 110_000
        result = job.salary_range()
        assert "80,000" in result
        assert "110,000" in result
        assert "CAD" in result

    def test_salary_range_min_only(self):
        job = Job(title="Dev", company="Acme", location="MTL", url="http://x.com")
        job.salary_min = 75_000
        result = job.salary_range()
        assert "75,000" in result
        assert "+" in result

    def test_salary_range_none(self):
        job = Job(title="Dev", company="Acme", location="MTL", url="http://x.com")
        assert job.salary_range() == "Non précisé"

    def test_to_dict_structure(self):
        job = Job(
            title="Data Engineer",
            company="Acme",
            location="Montréal, QC",
            url="http://example.com",
            technologies=["Python", "Spark"],
            contract_type="permanent",
            work_schedule="full-time",
        )
        d = job.to_dict()
        assert d["title"] == "Data Engineer"
        assert d["technologies"] == ["Python", "Spark"]
        assert d["contract_type"] == "permanent"
        assert d["work_schedule"] == "full-time"
        assert "salary" in d
        assert "extracted_at" in d

    def test_to_dict_salary_nested(self):
        job = Job(title="Dev", company="X", location="QC", url="u")
        job.salary_min = 90_000
        job.salary_max = 120_000
        d = job.to_dict()
        assert d["salary"]["min"] == 90_000
        assert d["salary"]["max"] == 120_000
        assert d["salary"]["currency"] == "CAD"

    def test_extracted_at_auto(self):
        before = datetime.now(UTC)
        job = Job(title="Dev", company="X", location="QC", url="u")
        after = datetime.now(UTC)
        assert before <= job.extracted_at <= after


class TestContact:
    def test_to_dict_structure(self):
        contact = Contact(
            company="Acme",
            name="Jane Doe",
            title="CTO",
            linkedin_url="https://linkedin.com/in/janedoe",
            confidence=0.9,
        )
        d = contact.to_dict()
        assert d["company"] == "Acme"
        assert d["name"] == "Jane Doe"
        assert d["title"] == "CTO"
        assert d["confidence"] == 0.9
        assert "extracted_at" in d

    def test_defaults(self):
        contact = Contact(company="Corp", name="John", title="VP IT")
        assert contact.email == ""
        assert contact.phone == ""
        assert contact.linkedin_url == ""
        assert contact.source == "web_search"
