from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.sources.adzuna import AdzunaSource
from src.sources.guichet_emploi import GuichetEmploiSource


# ── Adzuna ────────────────────────────────────────────────────────────────────

class TestAdzunaSource:
    def _mock_response(self, results: list[dict]) -> MagicMock:
        resp = MagicMock()
        resp.json.return_value = {"results": results}
        resp.raise_for_status.return_value = None
        return resp

    @patch("src.sources.adzuna.requests.get")
    def test_search_returns_raw_dicts(self, mock_get):
        mock_get.return_value = self._mock_response([
            {"id": "1", "title": "Dev", "company": {"display_name": "X"},
             "location": {"display_name": "MTL"}, "redirect_url": "http://x.com"},
        ])
        source = AdzunaSource(app_id="id", app_key="key")
        results = source.search("developer")
        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]["title"] == "Dev"

    @patch("src.sources.adzuna.requests.get")
    def test_search_empty_results(self, mock_get):
        mock_get.return_value = self._mock_response([])
        source = AdzunaSource(app_id="id", app_key="key")
        results = source.search("xyz")
        assert results == []

    @patch("src.sources.adzuna.requests.get")
    def test_search_passes_location(self, mock_get):
        mock_get.return_value = self._mock_response([])
        source = AdzunaSource(app_id="id", app_key="key")
        source.search("dev", location="Quebec")
        call_kwargs = mock_get.call_args[1]["params"]
        assert call_kwargs["where"] == "Quebec"

    @patch("src.sources.adzuna.requests.get")
    def test_search_raises_on_http_error(self, mock_get):
        from requests.exceptions import HTTPError
        resp = MagicMock()
        resp.raise_for_status.side_effect = HTTPError("404")
        mock_get.return_value = resp
        source = AdzunaSource(app_id="id", app_key="key")
        with pytest.raises(HTTPError):
            source.search("dev")


# ── Guichet Emploi ────────────────────────────────────────────────────────────

_SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:jb="http://www.jobbank.gc.ca/">
  <channel>
    <title>Guichet-Emplois</title>
    <item>
      <title>Ingénieur logiciel</title>
      <link>http://jobbank.gc.ca/job?jobpostingid=111</link>
      <description>Poste permanent.</description>
      <pubDate>Mon, 27 May 2026 09:00:00 +0000</pubDate>
      <jb:employer>Acme Québec</jb:employer>
      <jb:location>Montréal, QC</jb:location>
      <jb:salary>90000 - 120000</jb:salary>
      <jb:employmentTerms>Temps plein, Permanent</jb:employmentTerms>
    </item>
  </channel>
</rss>"""


class TestGuichetEmploiSource:
    @patch("src.sources.guichet_emploi.requests.get")
    def test_fetch_returns_list(self, mock_get):
        resp = MagicMock()
        resp.text = _SAMPLE_RSS
        resp.raise_for_status.return_value = None
        mock_get.return_value = resp

        source = GuichetEmploiSource()
        results = source.fetch(query="ingénieur")
        assert isinstance(results, list)
        assert len(results) == 1

    @patch("src.sources.guichet_emploi.requests.get")
    def test_fetch_parses_fields(self, mock_get):
        resp = MagicMock()
        resp.text = _SAMPLE_RSS
        resp.raise_for_status.return_value = None
        mock_get.return_value = resp

        source = GuichetEmploiSource()
        item = source.fetch()[0]
        assert item["title"] == "Ingénieur logiciel"
        assert item["employer"] == "Acme Québec"
        assert item["location"] == "Montréal, QC"
        assert item["salary"] == "90000 - 120000"
        assert item["language"] == "fr"

    @patch("src.sources.guichet_emploi.requests.get")
    def test_fetch_max_results(self, mock_get):
        # RSS avec 3 items, max_results=1
        rss = _SAMPLE_RSS.replace(
            "</channel>",
            "<item><title>Job2</title><link>http://x.com/2</link></item>"
            "<item><title>Job3</title><link>http://x.com/3</link></item>"
            "</channel>",
        )
        resp = MagicMock()
        resp.text = rss
        resp.raise_for_status.return_value = None
        mock_get.return_value = resp

        source = GuichetEmploiSource()
        results = source.fetch(max_results=1)
        assert len(results) == 1
