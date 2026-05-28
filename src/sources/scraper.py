from __future__ import annotations

import time
import random

import requests
from bs4 import BeautifulSoup

from src.models.job import Job


_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
]


class JobPageScraper:
    """Fetch and parse the raw HTML of an individual job posting page."""

    def __init__(
        self,
        delay_min: float = 1.5,
        delay_max: float = 3.5,
        proxy: str | None = None,
    ) -> None:
        self.delay_min = delay_min
        self.delay_max = delay_max
        self._session = requests.Session()
        if proxy:
            self._session.proxies = {"http": proxy, "https": proxy}

    def fetch_html(self, url: str) -> str:
        self._session.headers.update({"User-Agent": random.choice(_USER_AGENTS)})
        time.sleep(random.uniform(self.delay_min, self.delay_max))
        response = self._session.get(url, timeout=15)
        response.raise_for_status()
        return response.text

    def extract_text(self, html: str) -> str:
        """Return cleaned visible text suitable for AI processing."""
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return " ".join(soup.get_text(separator=" ").split())

    def enrich_job(self, job: Job) -> Job:
        """Fetch the job page and attach raw description text for AI extraction."""
        try:
            html = self.fetch_html(job.url)
            job.description = self.extract_text(html)
        except Exception:
            pass
        return job
