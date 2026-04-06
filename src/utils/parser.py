import argparse
from dataclasses import dataclass

@dataclass
class ScraperArgs:
    """Typed representation of resolved CLI arguments."""

    url: str | None
    prompt: str | None
    output: str | None
    stream: bool
    proxy: str | None
    delay_min: float
    delay_max: float
    verbose: bool

    @property
    def delay_range(self) -> tuple[float, float]:
        """Return delay bounds as a tuple for use in ScraperSession."""
        return (self.delay_min, self.delay_max)


def build_parser() -> argparse.ArgumentParser:
    """
    Build and return the configured argument parser.

    Keeping this separate from parse_args() allows callers to print help
    independently (e.g. on validation errors in main).
    """
    parser = argparse.ArgumentParser(
        description="🕷️ AI Web Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ai-scraper --url "https://quotes.toscrape.com" --prompt "Extract all quotes"
  ai-scraper --url "https://news.ycombinator.com" --prompt "List top 10 titles" --output results.json
  ai-scraper --url "https://example.com" --prompt "Summarize the page" --stream
  ai-scraper  # Interactive mode
        """,

    )

    target = parser.add_argument_group("Targets")
    target.add_argument("--url", metavar="URL", help="URL to scrape")
    target.add_argument(
        "--prompt",
        metavar="TEXT",
        help="Instruction for the AI (e.g. 'Extract all prices')",
    )

    output = parser.add_argument_group("Output")
    output.add_argument(
        "--output",
        metavar="FILE",
        help="Path to the JSON output file (optional)",
    )
    output.add_argument(
        "--stream",
        action="store_true",
        default=False,
        help="Stream the response instead of returning structured JSON",
    )

    network = parser.add_argument_group("Network")
    network.add_argument(
        "--proxy",
        metavar="URL",
        help="HTTP/HTTPS proxy (e.g. http://user.pass@host:port)",
    )

    network.add_argument(
        "--delay-min",
        type=float,
        default=1.5,
        metavar="SEC",
        help="Minimum delay between requests in seconds (default: 1.5)",
    )

    network.add_argument(
        "--delay-max",
        type=float,
        default=3.5,
        metavar="SEC",
        help="Maximum delay between requests in seconds (default: 3.5)",
    )

    debug = parser.add_argument_group("Debug")
    debug.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Enable DEBUG-level logging",
    )

    return parser

def parse_args(argv: list[str] | None = None) -> ScraperArgs:
    """
    Parse CLI arguments and return them as a typed dataclass.

    Args:
        argv: Argument list to parse. Defaults to sys.argv when None.

    Returns:
        ScraperArgs with all fields resolved and typed.

    Raises:
        SystemExit: If arguments are invalid (handled by argparse).
    """
    namespace = build_parser().parse_args(argv)

    return ScraperArgs(
        url=namespace.url,
        prompt=namespace.prompt,
        output=namespace.output,
        stream=namespace.stream,
        proxy=namespace.proxy,
        delay_min=namespace.delay_min,
        delay_max=namespace.delay_max,
        verbose=namespace.verbose,
    )
