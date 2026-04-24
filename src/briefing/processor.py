"""
LLM processor: scores articles by relevance to the active report profile,
then generates a short executive summary for Tier 1 items.

All articles are batched into a single prompt to keep API costs minimal.
Estimated cost: ~€0.05–0.10 per daily run with Claude Sonnet 4.6.
"""

import json
import logging
import os
from textwrap import dedent

from openai import OpenAI

from .models import Article

logger = logging.getLogger(__name__)


def _build_client() -> OpenAI:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENROUTER_API_KEY is not set — LLM calls will be skipped")
    return OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )


def _article_block(idx: int, article: Article) -> str:
    return dedent(f"""\
        [{idx}]
        Title: {article.title}
        Source: {article.source_name} ({article.category})
        Summary: {article.summary or '(no summary available)'}
    """)


def score_articles(articles: list[Article], profile: dict) -> tuple[list[Article], bool]:
    """Return (articles, scoring_ok). scoring_ok is False when the LLM call failed."""
    if not articles:
        return articles, True

    model = os.environ.get("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-6")
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

        Relevance tiers — assign EXACTLY one tier to each article:
        - Tier 0 "{tiers['tier_0']['label']}": {tiers['tier_0']['description']}
        - Tier 1 "{tiers['tier_1']['label']}": {tiers['tier_1']['description']}
        - Tier 2 "{tiers['tier_2']['label']}": {tiers['tier_2']['description']}
        - Tier 3 "{tiers['tier_3']['label']}": {tiers['tier_3']['description']}

        When in doubt between Tier 0 and Tier 3, assign Tier 0.
        Reserve Tier 3 for credible institutional sources only.
    """)

    article_text = "\n".join(_article_block(i, a) for i, a in enumerate(articles))

    user_prompt = dedent(f"""\
        Below are {len(articles)} news items collected in the last 24 hours.
        Assign each a tier (0, 1, 2, or 3) and provide a brief reason (1 sentence).

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
        return articles, True
    except EnvironmentError as e:
        logger.warning(f"LLM scoring skipped: {e}")
        for a in articles:
            if a.tier == 0:
                a.tier = 3
                a.tier_reason = "Scoring unavailable (API key not set)"
        return articles, False
    except Exception as e:
        error_type = type(e).__name__
        logger.error(f"LLM scoring failed [{error_type}]: {e}")
        for a in articles:
            if a.tier == 0:
                a.tier = 3
                a.tier_reason = f"Scoring unavailable ({error_type})"
        return articles, False


def generate_executive_summary(articles: list[Article], profile: dict) -> str:
    """Generate a 3–5 sentence executive summary for Tier 1 articles."""
    tier1 = [a for a in articles if a.tier == 1]
    if not tier1:
        return ""

    model = os.environ.get("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-6")
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
