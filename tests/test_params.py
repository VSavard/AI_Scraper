from __future__ import annotations

import pytest

from src.params import (
    build_parser,
    parse_contact_params,
    parse_extraction_params,
    parse_pipeline_params,
)


def _parse(argv: list[str]):
    return build_parser().parse_args(argv)


class TestExtractParams:
    def test_defaults(self):
        args = _parse(["extract", "--query", "data engineer"])
        params = parse_extraction_params(args)
        assert params.query == "data engineer"
        assert params.source == "all"
        assert params.location == ""
        assert params.pages == 1
        assert params.results_per_page == 10
        assert params.enrich is True
        assert params.ai_extract is True
        assert params.score is True
        assert params.provider == "anthropic"
        assert params.output is None

    def test_flags_no_enrich_no_extract(self):
        args = _parse(["extract", "--query", "dev", "--no-enrich", "--no-extract", "--no-score"])
        params = parse_extraction_params(args)
        assert params.enrich is False
        assert params.ai_extract is False
        assert params.score is False

    def test_source_guichet(self):
        args = _parse(["extract", "--query", "dev", "--source", "guichet-emploi"])
        params = parse_extraction_params(args)
        assert params.source == "guichet-emploi"

    def test_output_and_top(self):
        args = _parse(["extract", "--query", "dev", "--output", "out.json", "--top", "5"])
        params = parse_extraction_params(args)
        assert params.output == "out.json"
        assert params.top == 5

    def test_provider_gemini(self):
        args = _parse(["extract", "--query", "dev", "--provider", "gemini"])
        params = parse_extraction_params(args)
        assert params.provider == "gemini"

    def test_invalid_source_raises(self):
        with pytest.raises(SystemExit):
            _parse(["extract", "--query", "dev", "--source", "invalid"])


class TestContactParams:
    def test_defaults(self):
        args = _parse(["search-contacts", "--query", "ingénieur"])
        params = parse_contact_params(args)
        assert params.query == "ingénieur"
        assert params.provider == "anthropic"
        assert params.output is None

    def test_with_output(self):
        args = _parse(["search-contacts", "--query", "dev", "--output", "contacts.json"])
        params = parse_contact_params(args)
        assert params.output == "contacts.json"


class TestPipelineParams:
    def test_defaults(self):
        args = _parse(["pipeline", "--query", "ML engineer"])
        params = parse_pipeline_params(args)
        assert params.query == "ML engineer"
        assert params.jobs_output is None
        assert params.contacts_output is None

    def test_outputs(self):
        args = _parse([
            "pipeline", "--query", "dev",
            "--jobs-output", "jobs.json",
            "--contacts-output", "contacts.json",
        ])
        params = parse_pipeline_params(args)
        assert params.jobs_output == "jobs.json"
        assert params.contacts_output == "contacts.json"


class TestParserRequirements:
    def test_missing_query_raises(self):
        with pytest.raises(SystemExit):
            _parse(["extract"])

    def test_missing_command_raises(self):
        with pytest.raises(SystemExit):
            _parse(["--query", "dev"])
