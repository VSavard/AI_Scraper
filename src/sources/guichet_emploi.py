from __future__ import annotations

import xml.etree.ElementTree as ET

import requests


_FEED_URL = "https://www.jobbank.gc.ca/xmlfeed/rss-emploi.xml"

_NS = {
    "media":   "http://search.yahoo.com/mrss/",
    "georss":  "http://www.georss.org/georss",
    "jb":      "http://www.jobbank.gc.ca/",
}


class GuichetEmploiSource:
    """Récupère les offres du Guichet Emploi Canada via le flux RSS XML.

    Retourne des dicts bruts — la transformation vers Job est déléguée
    à GuichetEmploiTransformation.

    Documentation du flux :
        https://www.jobbank.gc.ca/developers/data_feed
    """

    def __init__(self, language: str = "fr") -> None:
        self.language = language  # "fr" ou "en"

    def fetch(
        self,
        query: str = "",
        location: str = "",
        max_results: int = 50,
    ) -> list[dict]:
        params: dict[str, str] = {"lang": self.language}
        if query:
            params["searchstring"] = query
        if location:
            params["locationstring"] = location

        response = requests.get(_FEED_URL, params=params, timeout=15)
        response.raise_for_status()
        return self._parse(response.text, max_results)

    def _parse(self, xml_text: str, max_results: int) -> list[dict]:
        root = ET.fromstring(xml_text)
        channel = root.find("channel")
        if channel is None:
            return []

        items = []
        for item in channel.findall("item")[:max_results]:
            items.append(self._item_to_dict(item))
        return items

    def _item_to_dict(self, item: ET.Element) -> dict:
        def text(tag: str) -> str:
            el = item.find(tag)
            return (el.text or "").strip() if el is not None else ""

        def ns_text(ns: str, tag: str) -> str:
            el = item.find(f"{{{_NS[ns]}}}{tag}")
            return (el.text or "").strip() if el is not None else ""

        return {
            "title":            text("title"),
            "link":             text("link"),
            "description":      text("description"),
            "pubDate":          text("pubDate"),
            "employer":         ns_text("jb", "employer"),
            "location":         ns_text("jb", "location"),
            "salary":           ns_text("jb", "salary"),
            "employment_terms": ns_text("jb", "employmentTerms"),
            "noc":              ns_text("jb", "noc"),
            "language":         self.language,
        }
