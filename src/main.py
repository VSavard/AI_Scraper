from __future__ import annotations

import json
import sys

from src.config import load_settings, validate
from src.operations.contact_search import ContactSearchOperation
from src.operations.extraction import ExtractionOperation
from src.params import (
    build_parser,
    parse_contact_params,
    parse_extraction_params,
    parse_pipeline_params,
)
from src.providers import get_provider


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    settings = load_settings()
    validate(settings, provider=args.provider)

    provider_kwargs = {"model": args.model} if args.model else {}
    provider = get_provider(args.provider, **provider_kwargs)

    try:
        if args.command == "extract":
            _cmd_extract(args, provider)

        elif args.command == "search-contacts":
            _cmd_search_contacts(args, provider)

        elif args.command == "pipeline":
            _cmd_pipeline(args, provider)

    except KeyboardInterrupt:
        print("\nInterrompu.", file=sys.stderr)
        sys.exit(0)


# ── Commandes ─────────────────────────────────────────────────────────────────

def _cmd_extract(args, provider) -> None:
    from src.sources.adzuna import AdzunaSource
    from src.config import load_settings

    settings = load_settings()
    params = parse_extraction_params(args)

    op = ExtractionOperation(
        provider=provider,
        adzuna=AdzunaSource(app_id=settings.adzuna_app_id, app_key=settings.adzuna_app_key),
    )

    print(f"Extraction : '{params.query}' | source={params.source} | lieu={params.location or 'tous'}")
    results = op.run(params)
    _display_jobs(results, params.top)
    _save(results, params.output, label="offres")


def _cmd_search_contacts(args, provider) -> None:
    from src.sources.adzuna import AdzunaSource
    from src.config import load_settings

    settings = load_settings()
    # On extrait d'abord les offres pour récupérer la liste des entreprises
    extract_params = parse_extraction_params(args)
    extract_params.enrich = False
    extract_params.ai_extract = False
    extract_params.score = False

    extract_op = ExtractionOperation(
        provider=provider,
        adzuna=AdzunaSource(app_id=settings.adzuna_app_id, app_key=settings.adzuna_app_key),
    )
    jobs_dicts = extract_op.run(extract_params)

    # Reconstitue les Job objects depuis les dicts pour les passer à ContactSearch
    from src.models.job import Job
    from datetime import datetime
    jobs = [
        Job(
            title=d["title"],
            company=d["company"],
            location=d["location"],
            url=d["url"],
            source=d.get("source", ""),
        )
        for d in jobs_dicts
    ]

    contact_params = parse_contact_params(args)
    contact_op = ContactSearchOperation(provider=provider)

    print(f"Recherche de contacts TI pour {len(set(j.company for j in jobs))} entreprises...")
    results = contact_op.run(jobs, contact_params)
    _display_contacts(results)
    _save(results, contact_params.output, label="contacts")


def _cmd_pipeline(args, provider) -> None:
    from src.sources.adzuna import AdzunaSource
    from src.config import load_settings
    from src.models.job import Job

    settings = load_settings()
    pipeline_params = parse_pipeline_params(args)

    # ── Étape 1 : extraction ──────────────────────────────────────────────
    from src.params import ExtractionParams
    extract_params = ExtractionParams(
        source=pipeline_params.source,
        query=pipeline_params.query,
        location=pipeline_params.location,
        pages=pipeline_params.pages,
        results_per_page=pipeline_params.results_per_page,
        enrich=True,
        ai_extract=True,
        score=bool(pipeline_params.criteria),
        criteria=pipeline_params.criteria,
        provider=pipeline_params.provider,
        model=pipeline_params.model,
        output=pipeline_params.jobs_output,
        top=None,
    )
    extract_op = ExtractionOperation(
        provider=provider,
        adzuna=AdzunaSource(app_id=settings.adzuna_app_id, app_key=settings.adzuna_app_key),
    )
    print(f"[Pipeline] Extraction : '{pipeline_params.query}'")
    jobs_dicts = extract_op.run(extract_params)
    _display_jobs(jobs_dicts)
    _save(jobs_dicts, pipeline_params.jobs_output, label="offres")

    # ── Étape 2 : contacts ────────────────────────────────────────────────
    jobs = [
        Job(title=d["title"], company=d["company"], location=d["location"], url=d["url"])
        for d in jobs_dicts
    ]
    from src.params import ContactSearchParams
    contact_params = ContactSearchParams(
        query=pipeline_params.query,
        location=pipeline_params.location,
        source=pipeline_params.source,
        pages=pipeline_params.pages,
        results_per_page=pipeline_params.results_per_page,
        provider=pipeline_params.provider,
        model=pipeline_params.model,
        output=pipeline_params.contacts_output,
    )
    contact_op = ContactSearchOperation(provider=provider)
    print(f"\n[Pipeline] Recherche contacts pour {len(set(j.company for j in jobs))} entreprises...")
    contacts_dicts = contact_op.run(jobs, contact_params)
    _display_contacts(contacts_dicts)
    _save(contacts_dicts, pipeline_params.contacts_output, label="contacts")


# ── Affichage ──────────────────────────────────────────────────────────────────

def _display_jobs(jobs: list[dict], top: int | None = None) -> None:
    items = jobs[:top] if top else jobs
    print(f"\n{'='*60}\nOFFRES D'EMPLOI — {len(items)} résultat(s)\n{'='*60}")
    for i, j in enumerate(items, 1):
        salary = j.get("salary", {})
        sal_str = ""
        if salary.get("min"):
            sal_str = f"  Salaire  : {salary['min']:,.0f}"
            if salary.get("max"):
                sal_str += f"–{salary['max']:,.0f} {salary.get('currency','CAD')}"
        score = j.get("score")
        tech = ", ".join(j.get("technologies", [])[:6])
        print(f"\n{i}. {j['title']} @ {j['company']}")
        print(f"   Lieu     : {j['location']}")
        print(f"   Contrat  : {j.get('contract_type') or 'N/A'} | {j.get('work_schedule') or 'N/A'}")
        if tech:
            print(f"   Stack    : {tech}")
        if sal_str:
            print(sal_str)
        if score is not None:
            print(f"   Score    : {score:.1f}/10")
        print(f"   URL      : {j['url']}")


def _display_contacts(contacts: list[dict]) -> None:
    print(f"\n{'='*60}\nCONTACTS TI — {len(contacts)} résultat(s)\n{'='*60}")
    for i, c in enumerate(contacts, 1):
        print(f"\n{i}. {c['name']} — {c['title']}")
        print(f"   Entreprise : {c['company']}")
        if c.get("linkedin_url"):
            print(f"   LinkedIn   : {c['linkedin_url']}")
        if c.get("email"):
            print(f"   Courriel   : {c['email']}")
        if c.get("phone"):
            print(f"   Téléphone  : {c['phone']}")
        print(f"   Confiance  : {c.get('confidence', 0):.0%}")


def _save(data: list[dict], path: str | None, label: str = "résultats") -> None:
    if not path:
        return
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n{len(data)} {label} sauvegardé(s) dans {path}")


if __name__ == "__main__":
    main()
