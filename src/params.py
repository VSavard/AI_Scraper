from __future__ import annotations

import argparse
from dataclasses import dataclass


# ── Dataclasses de paramètres ────────────────────────────────────────────────

@dataclass
class ExtractionParams:
    source: str           # adzuna | guichet-emploi | all
    query: str
    location: str
    pages: int
    results_per_page: int
    enrich: bool          # enrichissement via scraping HTML
    ai_extract: bool      # extraction structurée IA
    score: bool
    criteria: str
    provider: str
    model: str | None
    output: str | None
    top: int | None


@dataclass
class ContactSearchParams:
    query: str
    location: str
    source: str           # adzuna | guichet-emploi | all (pour trouver les entreprises)
    pages: int
    results_per_page: int
    provider: str
    model: str | None
    output: str | None


@dataclass
class FetchParams:
    source: str           # adzuna | guichet-emploi | all
    query: str
    location: str
    pages: int
    results_per_page: int
    output: str           # fichier JSON de sortie (obligatoire)


@dataclass
class ProcessParams:
    input: str            # fichier JSON brut (raw_jobs_v1) ou déjà transformé
    enrich: bool          # enrichissement via scraping HTML
    ai_extract: bool      # extraction structurée IA
    score: bool
    criteria: str
    provider: str
    model: str | None
    output: str | None
    top: int | None


@dataclass
class PipelineParams:
    query: str
    location: str
    source: str
    pages: int
    results_per_page: int
    criteria: str
    provider: str
    model: str | None
    jobs_output: str | None
    contacts_output: str | None


# ── Construction du parser ────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-scraper",
        description="Extracteur d'offres d'emploi assisté par IA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commandes :
  fetch            Télécharger les données brutes (sans IA) et sauvegarder en JSON
  process          Traiter un fichier brut existant avec l'IA (extraction + scoring)
  extract          fetch + process en une seule passe
  search-contacts  Rechercher les contacts TI des entreprises trouvées
  pipeline         extract + search-contacts en séquence

Exemples :
  ai-scraper fetch --source all --query "data engineer" --output raw.json
  ai-scraper process --input raw.json --criteria "Python, remote" --output jobs.json
  ai-scraper extract --source all --query "data engineer" --location Quebec
  ai-scraper search-contacts --query "ingénieur données" --location "Montréal"
  ai-scraper pipeline --query "développeur Python" --criteria "remote, senior"
        """,
    )

    sub = parser.add_subparsers(dest="command", required=True)
    _add_fetch(sub)
    _add_process(sub)
    _add_extract(sub)
    _add_search_contacts(sub)
    _add_pipeline(sub)
    return parser


def _common_source_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--query", required=True, help="Mots-clés de recherche")
    p.add_argument("--location", default="", help="Localisation (ex: Quebec)")
    p.add_argument(
        "--source",
        default="all",
        choices=["adzuna", "guichet-emploi", "all"],
        help="Source de données (défaut: all)",
    )
    p.add_argument("--pages", type=int, default=1, help="Pages Adzuna à récupérer")
    p.add_argument("--results", type=int, default=10, help="Résultats par page")


def _common_ai_args(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--provider",
        default="anthropic",
        choices=["anthropic", "openai", "gemini"],
        help="Provider IA (défaut: anthropic)",
    )
    p.add_argument("--model", default=None, help="Modèle IA à utiliser")


def _add_fetch(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "fetch",
        help="Télécharger les données brutes sans IA et sauvegarder en JSON",
    )
    _common_source_args(p)
    p.add_argument("--output", metavar="FILE", required=True, help="Fichier JSON de sortie (obligatoire)")


def _add_process(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "process",
        help="Traiter un fichier JSON brut avec l'IA (extraction + scoring)",
    )
    p.add_argument("--input", metavar="FILE", required=True, help="Fichier JSON brut produit par fetch")
    _common_ai_args(p)
    p.add_argument("--no-enrich", action="store_true", help="Ne pas scraper les pages individuelles")
    p.add_argument("--no-extract", action="store_true", help="Désactiver l'extraction IA")
    p.add_argument("--no-score", action="store_true", help="Désactiver le scoring IA")
    p.add_argument("--criteria", default="", help="Critères de scoring (ex: 'Python, remote, senior')")
    p.add_argument("--output", metavar="FILE", help="Fichier JSON de sortie")
    p.add_argument("--top", type=int, default=None, help="Afficher uniquement les N meilleurs résultats")


def _add_extract(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("extract", help="Extraire et analyser les offres d'emploi")
    _common_source_args(p)
    _common_ai_args(p)
    p.add_argument("--no-enrich", action="store_true", help="Ne pas scraper les pages individuelles")
    p.add_argument("--no-extract", action="store_true", help="Désactiver l'extraction IA")
    p.add_argument("--no-score", action="store_true", help="Désactiver le scoring IA")
    p.add_argument("--criteria", default="", help="Critères de scoring (ex: 'Python, remote, senior')")
    p.add_argument("--output", metavar="FILE", help="Fichier JSON de sortie")
    p.add_argument("--top", type=int, default=None, help="Afficher uniquement les N meilleurs résultats")


def _add_search_contacts(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("search-contacts", help="Rechercher les contacts TI des entreprises")
    _common_source_args(p)
    _common_ai_args(p)
    p.add_argument("--output", metavar="FILE", help="Fichier JSON de sortie")


def _add_pipeline(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("pipeline", help="Exécuter l'extraction et la recherche de contacts en séquence")
    _common_source_args(p)
    _common_ai_args(p)
    p.add_argument("--criteria", default="", help="Critères de scoring des offres")
    p.add_argument("--jobs-output", metavar="FILE", help="Fichier JSON pour les offres")
    p.add_argument("--contacts-output", metavar="FILE", help="Fichier JSON pour les contacts")


# ── Résolution des namespaces vers dataclasses ────────────────────────────────

def parse_extraction_params(args: argparse.Namespace) -> ExtractionParams:
    return ExtractionParams(
        source=args.source,
        query=args.query,
        location=args.location,
        pages=args.pages,
        results_per_page=args.results,
        enrich=not args.no_enrich,
        ai_extract=not args.no_extract,
        score=not args.no_score,
        criteria=args.criteria,
        provider=args.provider,
        model=args.model,
        output=args.output,
        top=args.top,
    )


def parse_contact_params(args: argparse.Namespace) -> ContactSearchParams:
    return ContactSearchParams(
        query=args.query,
        location=args.location,
        source=args.source,
        pages=args.pages,
        results_per_page=args.results,
        provider=args.provider,
        model=args.model,
        output=args.output,
    )


def parse_fetch_params(args: argparse.Namespace) -> FetchParams:
    return FetchParams(
        source=args.source,
        query=args.query,
        location=args.location,
        pages=args.pages,
        results_per_page=args.results,
        output=args.output,
    )


def parse_process_params(args: argparse.Namespace) -> ProcessParams:
    return ProcessParams(
        input=args.input,
        enrich=not args.no_enrich,
        ai_extract=not args.no_extract,
        score=not args.no_score,
        criteria=args.criteria,
        provider=args.provider,
        model=args.model,
        output=args.output,
        top=args.top,
    )


def parse_pipeline_params(args: argparse.Namespace) -> PipelineParams:
    return PipelineParams(
        query=args.query,
        location=args.location,
        source=args.source,
        pages=args.pages,
        results_per_page=args.results,
        criteria=args.criteria,
        provider=args.provider,
        model=args.model,
        jobs_output=args.jobs_output,
        contacts_output=args.contacts_output,
    )
