from __future__ import annotations

import argparse
import json
import sys

from src.models.job import Job
from src.processor.extractor import JobExtractor
from src.processor.scorer import JobScorer
from src.providers import get_provider
from src.sources.adzuna import AdzunaSource
from src.sources.scraper import JobPageScraper


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AI Job Scraper — extract and score job postings with AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main --query "data engineer" --location "Quebec" --criteria "Python, Spark, remote"
  python -m src.main --query "developer" --provider openai --pages 2 --output jobs.json
  python -m src.main --query "ML engineer" --no-scrape --no-score
        """,
    )

    parser.add_argument("--query", required=True, help="Job search query (e.g. 'data engineer')")
    parser.add_argument("--location", default="", help="Location filter (e.g. 'Quebec')")
    parser.add_argument("--criteria", default="", help="Scoring criteria (e.g. 'Python, remote, senior')")
    parser.add_argument("--provider", default="anthropic", choices=["anthropic", "openai"], help="AI provider")
    parser.add_argument("--model", default=None, help="Override model name for the selected provider")
    parser.add_argument("--pages", type=int, default=1, help="Number of Adzuna pages to fetch (default: 1)")
    parser.add_argument("--results", type=int, default=10, help="Results per page (default: 10)")
    parser.add_argument("--no-scrape", action="store_true", help="Skip fetching individual job pages")
    parser.add_argument("--no-extract", action="store_true", help="Skip AI structured extraction")
    parser.add_argument("--no-score", action="store_true", help="Skip AI scoring")
    parser.add_argument("--output", metavar="FILE", help="Save results to JSON file")
    parser.add_argument("--top", type=int, default=None, help="Show only top N scored results")
    return parser


def run(args: argparse.Namespace) -> list[Job]:
    provider_kwargs = {}
    if args.model:
        provider_kwargs["model"] = args.model

    provider = get_provider(args.provider, **provider_kwargs)
    extractor = JobExtractor(provider)
    scorer = JobScorer(provider)
    scraper = JobPageScraper()
    source = AdzunaSource()

    print(f"Searching Adzuna: '{args.query}' in '{args.location or 'all locations'}'...")
    jobs: list[Job] = []
    for page in range(1, args.pages + 1):
        batch = source.search(args.query, location=args.location, page=page, results_per_page=args.results)
        jobs.extend(batch)
        print(f"  Page {page}: {len(batch)} jobs fetched (total: {len(jobs)})")

    if not args.no_scrape:
        print(f"Scraping {len(jobs)} job pages for full descriptions...")
        for i, job in enumerate(jobs, 1):
            scraper.enrich_job(job)
            print(f"  [{i}/{len(jobs)}] {job.title} @ {job.company}")

    if not args.no_extract:
        print("Extracting structured data with AI...")
        for i, job in enumerate(jobs, 1):
            extractor.extract(job)
            print(f"  [{i}/{len(jobs)}] Extracted: {job.title}")

    if not args.no_score and args.criteria:
        print(f"Scoring jobs against: '{args.criteria}'...")
        jobs = scorer.score_many(jobs, args.criteria)

    return jobs


def display(jobs: list[Job], top: int | None = None) -> None:
    items = jobs[:top] if top else jobs
    print(f"\n{'='*60}")
    print(f"RESULTS: {len(items)} job(s)")
    print(f"{'='*60}")
    for i, job in enumerate(items, 1):
        score_str = f"  Score: {job.score:.1f}/10" if job.score is not None else ""
        print(f"\n{i}. {job.title} @ {job.company}")
        print(f"   Location : {job.location}")
        print(f"   Salary   : {job.salary_range()}")
        print(f"   Contract : {job.contract_type or 'N/A'}")
        print(f"   Skills   : {', '.join(job.skills[:8]) if job.skills else 'N/A'}")
        if score_str:
            print(score_str)
        if job.score_rationale:
            print(f"   Rationale: {job.score_rationale[:200]}")
        print(f"   URL      : {job.url}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        jobs = run(args)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(0)

    display(jobs, top=args.top)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump([j.to_dict() for j in jobs], f, ensure_ascii=False, indent=2)
        print(f"\nSaved {len(jobs)} jobs to {args.output}")


if __name__ == "__main__":
    main()
