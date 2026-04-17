"""
Formats the scored articles into a clean Markdown briefing document.

Tier 0 items are excluded entirely.
Tier 3 items are hidden by default; set INCLUDE_TIER3=true to show them.
"""

import os
from datetime import datetime, timezone, timedelta

from .models import Article

CET = timezone(timedelta(hours=1))
TIER_LABELS = {
    1: "Perfectly relevant",
    2: "Relevant",
    3: "Low signal",
}


def format_briefing(
    articles: list[Article],
    executive_summary: str,
    profile: dict,
    generated_at: datetime | None = None,
    serendipity_names: list[str] | None = None,
    iterations_used: int = 1,
) -> str:
    if generated_at is None:
        generated_at = datetime.now(CET)

    include_tier3 = os.environ.get("INCLUDE_TIER3", "").lower() in ("true", "1", "yes")

    date_str = generated_at.strftime("%-d %B %Y")
    time_str = generated_at.strftime("%H:%M CET")
    report_title = profile["report"]["title"]

    lines: list[str] = []

    # Header
    lines += [
        f"# Dagelijkse Briefing — {date_str}",
        f"*Gegenereerd om {time_str} | Rapport: {report_title}*",
        "",
    ]

    # Executive summary
    if executive_summary:
        lines += [
            "## Samenvatting",
            "",
            executive_summary,
            "",
        ]

    # Tiers — Tier 0 excluded, Tier 3 conditional
    tiers_to_show = (1, 2, 3) if include_tier3 else (1, 2)
    for tier in tiers_to_show:
        tier_articles = [a for a in articles if a.tier == tier]
        if not tier_articles:
            continue

        label = TIER_LABELS[tier]
        lines += [
            f"## {label} ({len(tier_articles)})",
            "",
        ]

        for a in sorted(tier_articles, key=lambda x: x.published, reverse=True):
            pub_str = a.published.astimezone(CET).strftime("%-d %b, %H:%M")
            lines.append(f"### [{a.title}]({a.url})")
            lines.append(f"*{a.source_name} · {pub_str}*")
            if a.summary:
                lines.append(f"\n{a.summary}")
            if a.tier_reason:
                lines.append(f"\n> {a.tier_reason}")
            lines.append("")

    # Footer
    excluded = [a for a in articles if a.tier == 0]
    tier3 = [a for a in articles if a.tier == 3]
    shown = [a for a in articles if a.tier in tiers_to_show]

    footer_parts = [f"{len(shown)} items · {_count_sources(shown)} bronnen"]
    if excluded:
        footer_parts.append(f"{len(excluded)} uitgesloten (Tier 0 · niet relevant)")
    if tier3 and not include_tier3:
        footer_parts.append(f"{len(tier3)} laag signaal verborgen (stel INCLUDE_TIER3=true in om te tonen)")
    if serendipity_names:
        footer_parts.append(f"Serendipity bronnen vandaag: {', '.join(serendipity_names)}")
    if iterations_used > 1:
        footer_parts.append(f"Kwaliteitscheck: {iterations_used} iteraties uitgevoerd")

    lines += [
        "---",
        f"*{' · '.join(footer_parts)}*",
    ]

    return "\n".join(lines)


def _count_sources(articles: list[Article]) -> int:
    return len({a.source_name for a in articles})
