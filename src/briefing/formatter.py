"""
Formats the scored articles into a clean Markdown briefing document.
"""

from datetime import datetime, timezone, timedelta

from .models import Article

CET = timezone(timedelta(hours=1))
TIER_LABELS = {
    1: "Perfectly relevant",
    2: "Relevant",
    3: "Potentially relevant",
}


def format_briefing(
    articles: list[Article],
    executive_summary: str,
    profile: dict,
    generated_at: datetime | None = None,
) -> str:
    if generated_at is None:
        generated_at = datetime.now(CET)

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

    # Tiers
    for tier in (1, 2, 3):
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
    total = len(articles)
    lines += [
        "---",
        f"*{total} items verwerkt uit {_count_sources(articles)} bronnen.*",
    ]

    return "\n".join(lines)


def _count_sources(articles: list[Article]) -> int:
    return len({a.source_name for a in articles})
