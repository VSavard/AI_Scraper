from __future__ import annotations

import json
import re

from src.models.job import Job
from src.providers.base import AIProvider


_SYSTEM = """You are a job data extraction assistant.
Given raw text from a job posting page, extract structured information and return ONLY valid JSON.
No explanation, no markdown, just the JSON object."""

_PROMPT_TEMPLATE = """Extract the following fields from this job posting text.
Return a JSON object with these exact keys:
- title (string)
- company (string)
- location (string)
- contract_type (string: "full-time", "part-time", "contract", "internship", or "")
- salary_min (number or null)
- salary_max (number or null)
- salary_currency (string, default "CAD")
- skills (array of strings, max 15)
- description (string, 2-3 sentence summary)

Job posting text:
{text}"""


class JobExtractor:
    """Use an AI provider to extract structured job data from raw page text."""

    def __init__(self, provider: AIProvider) -> None:
        self._provider = provider

    def extract(self, job: Job) -> Job:
        if not job.description:
            return job

        text = job.description[:6000]
        prompt = _PROMPT_TEMPLATE.format(text=text)

        try:
            raw = self._provider.complete(system=_SYSTEM, user=prompt, max_token=1024)
            data = self._parse_json(raw)
        except Exception:
            return job

        job.title = data.get("title") or job.title
        job.company = data.get("company") or job.company
        job.location = data.get("location") or job.location
        job.contract_type = data.get("contract_type") or job.contract_type
        job.salary_min = data.get("salary_min") or job.salary_min
        job.salary_max = data.get("salary_max") or job.salary_max
        job.salary_currency = data.get("salary_currency") or job.salary_currency
        job.skills = data.get("skills") or job.skills
        job.description = data.get("description") or job.description
        return job

    @staticmethod
    def _parse_json(text: str) -> dict:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(text)
