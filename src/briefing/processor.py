"""
LLM processor: scores articles by relevance to the active report profile,
then generates a short executive summary for Tier 1 items.

All articles are batched into a single prompt to keep API costs minimal.
Estimated cost: ~€0.05–0.10 per daily run with Claude 3.5 Sonnet.
"""

import json
import logging
import os
from textwrap import dedent

from openai import OpenAI

from .models import Article

logger = logging.getLogger(__name__)


def _build_client() -> OpenAI:
    return OpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
    )


def _article_block(idx: int, article: Article) -> str:
    return dedent(f"""\
        [{idx}]
        Title: {article.title}
        Source: {article.source_name} ({article.category})
        Summary: {article.summary or '(no summary available)'}
    """)


def score_articles(articles: list[Article], profile: dict) -> list[Article]:
    if not articles:
        return articles

    model = os.environ.get("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    client = _build_client()

    report = profile["report"]
    tiers = profile["relevance_tiers"]

    system_prompt = dedent(f"""\
        You are a research assistant helping a policy analyst at a central bank.
        The analyst is writing a report titled: "{report['title_en']}"
        Perspective: {report['perspective']}

        Report focus:
        {profile['core_focus']}

        Key themes: {', '.join(profile['themes'])}
        Key actors: {', '.join(profile['key_actors'])}

        Relevance tiers:
        - Tier 1 "{tiers['tier_1']['label']}": {tiers['tier_1']['description']}
        - Tier 2 "{tiers['tier_2']['label']}": {tiers['tier_2']['description']}
        - Tier 3 "{tiers['tier_3']['label']}": {tiers['tier_3']['description']}
    """)

    article_text = "\n".join(_article_block(i, a) for i, a in enumerate(articles))

    user_prompt = dedent(f"""\
        Below are {len(articles)} news items collected in the last 24 hours.
        Assign each a tier (1, 2, or 3) and provide a brief reason (1 sentence).

        Respond ONLY with valid JSON — an array with one object per article, in the same order:
        [
          {{"index": 0, "tier": 1, "reason": "..."}},
          ...
        ]

        Articles:
        {article_text}
    """)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        # The model may wrap the array in a key; handle both formats
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            parsed = next(iter(parsed.values()))

        for item in parsed:
            idx = item["index"]
            if 0 <= idx < len(articles):
                articles[idx].tier = int(item.get("tier", 3))
                articles[idx].tier_reason = item.get("reason", "")
    except Exception as e:
        logger.error(f"LLM scoring failed: {e}")
        # Graceful fallback: mark everything tier 3
        for a in articles:
            if a.tier == 0:
                a.tier = 3
                a.tier_reason = "Scoring unavailable"

    return articles


def generate_executive_summary(articles: list[Article], profile: dict) -> str:
    """Generate a 3–5 sentence executive summary for Tier 1 articles."""
    tier1 = [a for a in articles if a.tier == 1]
    if not tier1:
        return ""

    model = os.environ.get("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    client = _build_client()
    report = profile["report"]

    items_text = "\n".join(
        f"- {a.title} ({a.source_name}): {a.summary}" for a in tier1
    )

    prompt = dedent(f"""\
        You are briefing a senior policy analyst at {report['perspective']}.
        They are writing a report on: "{report['title_en']}"

        These are today's most directly relevant news items:
        {items_text}

        Write a concise executive summary (3–5 sentences, no bullet points) that:
        - Highlights the most important developments
        - Notes any patterns or connections between items
        - Is written in a direct, analytical tone suitable for a central bank analyst
        - Is in English

        Do not start with "Today" or repeat the report title.
    """)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Executive summary generation failed: {e}")
        return ""
