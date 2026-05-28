from __future__ import annotations

import json
import re

from src.models.job import Job
from src.providers.base import AIProvider


_SYSTEM = """You are a job relevance scoring assistant.
Evaluate a job posting against a candidate's criteria and return ONLY valid JSON.
No explanation, no markdown, just the JSON object."""

_PROMPT_TEMPLATE = """Score this job posting on a scale from 0.0 to 10.0 based on:
- Relevance to the search criteria: {criteria}
- Salary competitiveness
- Career growth potential
- Technology stack (if applicable)

Return a JSON object with:
- score (float between 0 and 10)
- rationale (string, 1-2 sentences explaining the score)
- strengths (array of strings, max 3)
- weaknesses (array of strings, max 3)

Job details:
Title: {title}
Company: {company}
Location: {location}
Contract: {contract_type}
Salary: {salary}
Skills: {skills}
Description: {description}"""


class JobScorer:
    """Use an AI provider to score and analyse job postings."""

    def __init__(self, provider: AIProvider) -> None:
        self._provider = provider

    def score(self, job: Job, criteria: str) -> Job:
        prompt = _PROMPT_TEMPLATE.format(
            criteria=criteria,
            title=job.title,
            company=job.company,
            location=job.location,
            contract_type=job.contract_type or "unknown",
            salary=job.salary_range(),
            skills=", ".join(job.skills) if job.skills else "not specified",
            description=job.description[:2000],
        )

        try:
            raw = self._provider.complete(system=_SYSTEM, user=prompt, max_token=512)
            data = self._parse_json(raw)
        except Exception:
            return job

        job.score = float(data.get("score", 0))
        strengths = data.get("strengths", [])
        weaknesses = data.get("weaknesses", [])
        rationale = data.get("rationale", "")
        parts = [rationale]
        if strengths:
            parts.append("Strengths: " + ", ".join(strengths))
        if weaknesses:
            parts.append("Weaknesses: " + ", ".join(weaknesses))
        job.score_rationale = " | ".join(p for p in parts if p)
        return job

    def score_many(self, jobs: list[Job], criteria: str) -> list[Job]:
        scored = [self.score(job, criteria) for job in jobs]
        return sorted(scored, key=lambda j: j.score or 0, reverse=True)

    @staticmethod
    def _parse_json(text: str) -> dict:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(text)
