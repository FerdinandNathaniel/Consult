"""
Daily briefing — main entry point.

Usage:
    python -m src.briefing.run              # normal run
    python -m src.briefing.run --dry-run    # fetch and format, skip LLM scoring and Drive upload
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import yaml
from dotenv import load_dotenv

from .fetchers.rss import fetch_rss_articles
from .fetchers.social import fetch_social_articles
from .formatter import format_briefing
from .processor import generate_executive_summary, score_articles

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("briefing.run")

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "outputs"))


def load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def main(dry_run: bool = False) -> None:
    logger.info("Starting daily briefing run")

    sources = load_yaml(CONFIG_DIR / "sources.yaml")
    profile = load_yaml(CONFIG_DIR / "report_profile.yaml")

    # --- Fetch ---
    articles = []
    articles += fetch_rss_articles(sources.get("rss_feeds", []))
    articles += fetch_social_articles(sources.get("social", {}))

    # Handle web_sources: items tagged type=rss are passed through the RSS fetcher
    web_as_rss = [
        s for s in sources.get("web_sources", []) if s.get("type") == "rss"
    ]
    if web_as_rss:
        articles += fetch_rss_articles(web_as_rss)

    logger.info(f"Total articles fetched: {len(articles)}")

    if not articles:
        logger.warning("No articles fetched — briefing will be empty")

    # --- Score ---
    if not dry_run:
        articles = score_articles(articles, profile)
        executive_summary = generate_executive_summary(articles, profile)
    else:
        logger.info("Dry run: skipping LLM scoring")
        for a in articles:
            a.tier = 2
            a.tier_reason = "(dry run)"
        executive_summary = "(dry run — no executive summary generated)"

    # --- Format ---
    briefing_md = format_briefing(articles, executive_summary, profile)

    # --- Write output ---
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(timezone(timedelta(hours=1))).strftime("%Y-%m-%d")
    filename = f"briefing_{date_str}.md"
    output_path = OUTPUT_DIR / filename

    output_path.write_text(briefing_md, encoding="utf-8")
    logger.info(f"Briefing written to {output_path}")

    # --- Upload to Drive ---
    # Disabled: service accounts lack personal Drive quota.
    # Output is stored locally and uploaded as a GitHub Actions artifact.
    # Re-enable once a Shared Drive is available (requires supportsAllDrives=True in drive.py).
    # if not dry_run:
    #     from .drive import upload_to_drive
    #     url = upload_to_drive(output_path, filename)
    #     if url:
    #         logger.info(f"Available in Drive: {url}")

    # Print path for CI visibility
    print(str(output_path))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Skip LLM calls and Drive upload")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
