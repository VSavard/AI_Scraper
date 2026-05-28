from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.models.job import Job
from src.operations.contact_search import ContactSearchOperation
from src.operations.extraction import ExtractionOperation
from src.params import ExtractionParams, ContactSearchParams


def _make_extraction_params(**kwargs) -> ExtractionParams:
    defaults = dict(
        source="adzuna",
        query="data engineer",
        location="Quebec",
        pages=1,
        results_per_page=5,
        enrich=False,
        ai_extract=False,
        score=False,
        criteria="",
        provider="anthropic",
        model=None,
        output=None,
        top=None,
    )
    defaults.update(kwargs)
    return ExtractionParams(**defaults)


def _make_contact_params(**kwargs) -> ContactSearchParams:
    defaults = dict(
        query="data engineer",
        location="Quebec",
        source="adzuna",
        pages=1,
        results_per_page=5,
        provider="anthropic",
        model=None,
        output=None,
    )
    defaults.update(kwargs)
    return ContactSearchParams(**defaults)


class TestExtractionOperation:
    def _adzuna_raw(self) -> dict:
        return {
            "id": "1",
            "title": "Data Engineer",
            "company": {"display_name": "Acme"},
            "location": {"display_name": "Montréal, QC"},
            "redirect_url": "http://example.com",
            "description": "Python, Spark, Databricks.",
            "contract_type": "permanent",
            "contract_time": "full_time",
            "salary_min": 90000,
            "salary_max": 120000,
        }

    def test_run_returns_list_of_dicts(self):
        provider = MagicMock()
        adzuna = MagicMock()
        adzuna.search.return_value = [self._adzuna_raw()]

        op = ExtractionOperation(provider=provider, adzuna=adzuna)
        results = op.run(_make_extraction_params())

        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]["title"] == "Data Engineer"

    def test_run_calls_adzuna_with_query(self):
        provider = MagicMock()
        adzuna = MagicMock()
        adzuna.search.return_value = []

        op = ExtractionOperation(provider=provider, adzuna=adzuna)
        op.run(_make_extraction_params(query="ML engineer", location="Toronto"))

        adzuna.search.assert_called_once()
        call_kwargs = adzuna.search.call_args
        assert "ML engineer" in call_kwargs[0] or call_kwargs[1].get("query") == "ML engineer" or call_kwargs[0][0] == "ML engineer"

    def test_run_guichet_source(self):
        provider = MagicMock()
        guichet = MagicMock()
        guichet.fetch.return_value = []

        op = ExtractionOperation(provider=provider, guichet=guichet)
        op.run(_make_extraction_params(source="guichet-emploi"))

        guichet.fetch.assert_called_once()

    def test_run_all_sources(self):
        provider = MagicMock()
        adzuna = MagicMock()
        guichet = MagicMock()
        adzuna.search.return_value = [self._adzuna_raw()]
        guichet.fetch.return_value = []

        op = ExtractionOperation(provider=provider, adzuna=adzuna, guichet=guichet)
        results = op.run(_make_extraction_params(source="all"))

        adzuna.search.assert_called_once()
        guichet.fetch.assert_called_once()
        assert len(results) == 1

    def test_run_top_limits_results(self):
        provider = MagicMock()
        adzuna = MagicMock()
        adzuna.search.return_value = [self._adzuna_raw(), self._adzuna_raw()]

        op = ExtractionOperation(provider=provider, adzuna=adzuna)
        results = op.run(_make_extraction_params(top=1))
        assert len(results) == 1

    def test_run_ai_extract_called(self):
        provider = MagicMock()
        provider.complete.return_value = (
            '{"title":"Dev","company":"X","location":"MTL","contract_type":"permanent",'
            '"work_schedule":"full-time","technologies":["Python"],'
            '"salary_min":null,"salary_max":null,"salary_currency":"CAD","description":"Good job."}'
        )
        adzuna = MagicMock()
        adzuna.search.return_value = [self._adzuna_raw()]

        op = ExtractionOperation(provider=provider, adzuna=adzuna)
        op.run(_make_extraction_params(ai_extract=True, enrich=False))

        provider.complete.assert_called()


class TestContactSearchOperation:
    def _make_jobs(self, companies: list[str]) -> list[Job]:
        return [
            Job(title="Dev", company=c, location="MTL", url=f"http://{c}.com")
            for c in companies
        ]

    def test_run_deduplicates_companies(self):
        provider = MagicMock()
        provider.complete.return_value = (
            '{"name":"Jane","title":"CTO","linkedin_url":"","email":"","phone":"","confidence":0.8}'
        )
        op = ContactSearchOperation(provider=provider)

        jobs = self._make_jobs(["Acme", "Acme", "BetaCorp"])

        with patch("duckduckgo_search.DDGS") as mock_ddgs:
            mock_ddgs.return_value.__enter__.return_value.text.return_value = [
                {"title": "Jane CTO", "href": "http://linkedin.com", "body": "CTO at Acme"}
            ]
            params = _make_contact_params()
            results = op.run(jobs, params)

        # 2 entreprises uniques → 2 appels search (avec 1 résultat chacun)
        assert len(results) == 2

    def test_run_empty_jobs(self):
        provider = MagicMock()
        op = ContactSearchOperation(provider=provider)
        results = op.run([], _make_contact_params())
        assert results == []

    def test_run_web_search_failure_skipped(self):
        provider = MagicMock()
        op = ContactSearchOperation(provider=provider)

        jobs = self._make_jobs(["Acme"])
        # _web_search catches all exceptions and returns [] — simulate via DDGS raising
        with patch("duckduckgo_search.DDGS", side_effect=Exception("network error")):
            results = op.run(jobs, _make_contact_params())

        assert results == []
