from __future__ import annotations

import json
import tempfile
from unittest.mock import MagicMock

import pytest

from src.operations.fetch import FetchOperation
from src.operations.processing import ProcessOperation
from src.params import (
    FetchParams,
    ProcessParams,
    build_parser,
    parse_fetch_params,
    parse_process_params,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _adzuna_raw(id: str = "1") -> dict:
    return {
        "id": id,
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


def _fetch_params(**kwargs) -> FetchParams:
    defaults = dict(
        source="adzuna", query="data engineer", location="Quebec",
        pages=1, results_per_page=5, output="out.json",
    )
    defaults.update(kwargs)
    return FetchParams(**defaults)


def _process_params(input_file: str, **kwargs) -> ProcessParams:
    defaults = dict(
        input=input_file, enrich=False, ai_extract=False,
        score=False, criteria="", provider="anthropic",
        model=None, output=None, top=None,
    )
    defaults.update(kwargs)
    return ProcessParams(**defaults)


# ── FetchOperation ────────────────────────────────────────────────────────────

class TestFetchOperation:
    def test_run_returns_raw_jobs_v1_envelope(self):
        adzuna = MagicMock()
        adzuna.search.return_value = [_adzuna_raw()]
        op = FetchOperation(adzuna=adzuna)

        result = op.run(_fetch_params())

        assert result["format"] == "raw_jobs_v1"
        assert result["count"] == 1
        assert "fetched_at" in result
        assert result["query"] == "data engineer"

    def test_run_tags_items_with_source(self):
        adzuna = MagicMock()
        adzuna.search.return_value = [_adzuna_raw()]
        op = FetchOperation(adzuna=adzuna)

        result = op.run(_fetch_params(source="adzuna"))
        assert result["items"][0]["_source"] == "adzuna"

    def test_run_guichet_emploi_source(self):
        guichet = MagicMock()
        guichet.fetch.return_value = [{"title": "Dev", "link": "http://x.com"}]
        op = FetchOperation(guichet=guichet)

        result = op.run(_fetch_params(source="guichet-emploi"))

        guichet.fetch.assert_called_once()
        assert result["items"][0]["_source"] == "guichet_emploi"

    def test_run_all_sources_combines_items(self):
        adzuna = MagicMock()
        guichet = MagicMock()
        adzuna.search.return_value = [_adzuna_raw("1")]
        guichet.fetch.return_value = [{"title": "Dev2", "link": "http://y.com"}]
        op = FetchOperation(adzuna=adzuna, guichet=guichet)

        result = op.run(_fetch_params(source="all"))

        assert result["count"] == 2
        sources = {item["_source"] for item in result["items"]}
        assert sources == {"adzuna", "guichet_emploi"}

    def test_run_empty_results(self):
        adzuna = MagicMock()
        adzuna.search.return_value = []
        op = FetchOperation(adzuna=adzuna)

        result = op.run(_fetch_params())
        assert result["count"] == 0
        assert result["items"] == []

    def test_run_multiple_pages(self):
        adzuna = MagicMock()
        adzuna.search.side_effect = [[_adzuna_raw("1")], [_adzuna_raw("2")]]
        op = FetchOperation(adzuna=adzuna)

        result = op.run(_fetch_params(pages=2))
        assert result["count"] == 2
        assert adzuna.search.call_count == 2


# ── ProcessOperation ──────────────────────────────────────────────────────────

class TestProcessOperation:
    def _write_raw(self, items: list[dict]) -> str:
        payload = {
            "format": "raw_jobs_v1",
            "query": "test",
            "location": "",
            "source": "adzuna",
            "fetched_at": "2026-01-01T00:00:00+00:00",
            "count": len(items),
            "items": items,
        }
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(payload, tmp, ensure_ascii=False)
        tmp.close()
        return tmp.name

    def _write_job_dicts(self, jobs: list[dict]) -> str:
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(jobs, tmp, ensure_ascii=False)
        tmp.close()
        return tmp.name

    def test_run_from_raw_jobs_v1(self):
        raw = _adzuna_raw()
        raw["_source"] = "adzuna"
        path = self._write_raw([raw])

        provider = MagicMock()
        op = ProcessOperation(provider=provider)
        results = op.run(_process_params(path))

        assert len(results) == 1
        assert results[0]["title"] == "Data Engineer"

    def test_run_from_job_dicts(self):
        job_dict = {
            "job_id": "x-1", "title": "ML Engineer", "company": "BetaCo",
            "location": "Toronto", "url": "http://x.com",
            "technologies": ["Python"], "salary": {"min": None, "max": None, "currency": "CAD"},
        }
        path = self._write_job_dicts([job_dict])

        provider = MagicMock()
        op = ProcessOperation(provider=provider)
        results = op.run(_process_params(path))

        assert len(results) == 1
        assert results[0]["title"] == "ML Engineer"

    def test_run_ai_extract_called(self):
        raw = _adzuna_raw()
        raw["_source"] = "adzuna"
        path = self._write_raw([raw])

        provider = MagicMock()
        provider.complete.return_value = (
            '{"title":"Dev","company":"X","location":"MTL","contract_type":"permanent",'
            '"work_schedule":"full-time","technologies":["Python","Spark"],'
            '"salary_min":null,"salary_max":null,"salary_currency":"CAD","description":"Good role."}'
        )
        op = ProcessOperation(provider=provider)
        op.run(_process_params(path, ai_extract=True))

        provider.complete.assert_called()

    def test_run_top_limits_results(self):
        items = [dict(_source="adzuna", **_adzuna_raw(str(i))) for i in range(5)]
        path = self._write_raw(items)

        provider = MagicMock()
        op = ProcessOperation(provider=provider)
        results = op.run(_process_params(path, top=2))

        assert len(results) == 2

    def test_run_invalid_format_raises(self):
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump({"format": "unknown_v99", "items": []}, tmp)
        tmp.close()

        provider = MagicMock()
        op = ProcessOperation(provider=provider)
        with pytest.raises(ValueError, match="Format non reconnu"):
            op.run(_process_params(tmp.name))


# ── Params parsing ────────────────────────────────────────────────────────────

def _parse(argv: list[str]):
    return build_parser().parse_args(argv)


class TestFetchParams:
    def test_defaults(self):
        args = _parse(["fetch", "--query", "data engineer", "--output", "raw.json"])
        params = parse_fetch_params(args)
        assert params.query == "data engineer"
        assert params.source == "all"
        assert params.output == "raw.json"
        assert params.pages == 1
        assert params.results_per_page == 10

    def test_output_required(self):
        with pytest.raises(SystemExit):
            _parse(["fetch", "--query", "dev"])  # --output manquant

    def test_source_adzuna(self):
        args = _parse(["fetch", "--query", "dev", "--source", "adzuna", "--output", "f.json"])
        params = parse_fetch_params(args)
        assert params.source == "adzuna"


class TestProcessParams:
    def test_defaults(self):
        args = _parse(["process", "--input", "raw.json"])
        params = parse_process_params(args)
        assert params.input == "raw.json"
        assert params.enrich is True
        assert params.ai_extract is True
        assert params.score is True
        assert params.provider == "anthropic"
        assert params.output is None

    def test_input_required(self):
        with pytest.raises(SystemExit):
            _parse(["process"])  # --input manquant

    def test_flags_disable_steps(self):
        args = _parse(["process", "--input", "f.json", "--no-enrich", "--no-extract", "--no-score"])
        params = parse_process_params(args)
        assert params.enrich is False
        assert params.ai_extract is False
        assert params.score is False

    def test_top_and_output(self):
        args = _parse(["process", "--input", "f.json", "--top", "3", "--output", "out.json"])
        params = parse_process_params(args)
        assert params.top == 3
        assert params.output == "out.json"
