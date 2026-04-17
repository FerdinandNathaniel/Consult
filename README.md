# Consult — Daily AI Briefing Agent

An automated daily briefing that fetches, scores, and summarises AI policy and startup ecosystem news for a senior analyst at De Nederlandsche Bank (DNB).

Runs every morning at 05:00 CET via GitHub Actions. Output is a Markdown file delivered as a workflow artifact.

---

## What it does

1. **Fetches** articles from institutional RSS feeds, EU policy outlets, newsletters, and (optionally) Twitter/X accounts
2. **Scores** each article with an LLM against the active report profile (Tier 1 = perfectly relevant → Tier 0 = exclude)
3. **Filters** — only Tier 1 and Tier 2 articles appear by default; noise is suppressed
4. **Summarises** Tier 1 items into a 3–5 sentence executive summary
5. **Delivers** the briefing as a GitHub Actions artifact (retained 90 days)

A serendipity mechanism randomly samples additional sources each run to surface less obvious signals. If Tier 1 coverage is sparse, the pipeline iterates up to 3 times fetching from the extended source pool.

---

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env   # add your OPENROUTER_API_KEY
python -m src.briefing.run --dry-run   # fetch only, no LLM
python -m src.briefing.run             # full run
```

Output: `outputs/briefing_YYYY-MM-DD.md`

See [docs/setup.md](docs/setup.md) for GitHub Actions setup, Google Drive integration, and RSSHub deployment.

---

## Configuration

| File | Purpose |
|---|---|
| `config/sources.yaml` | RSS feeds, Twitter accounts, serendipity pool |
| `config/report_profile.yaml` | Report focus, key themes, relevance tier definitions |

No code changes needed to add sources or adjust relevance criteria — edit the YAML files directly.

---

## Key operational notes

### Twitter/X feeds require manual cookie refresh (~monthly)

Social monitoring runs via a self-hosted [RSSHub](https://github.com/DIYgod/RSSHub) instance. RSSHub authenticates with X using session cookies, which expire periodically.

**Symptom:** Twitter accounts silently stop appearing in the briefing (no error — the feed just returns empty).

**Fix (2 minutes):**
1. Open [x.com](https://x.com) in your browser while logged in
2. DevTools → Application → Cookies → `https://x.com`
3. Copy `auth_token` and `ct0`
4. In your Railway dashboard → RSSHub service → Variables → update `TWITTER_AUTH_TOKEN` and `TWITTER_CT0`

Railway redeploys automatically. The briefing will pick up Twitter again on the next run.

**Why not automate this?** Automated login to extract cookies is blocked by X and risks account suspension. The official API costs $100+/month for the required access tier. See [docs/decisions.md](docs/decisions.md) §12 for full reasoning.

### Scoring requires an OpenRouter API key

Set `OPENROUTER_API_KEY` as a GitHub Actions secret. Without it, all articles fall back to Tier 3 and no executive summary is generated. The briefing still delivers — it just won't be scored.

### Tier 3 is hidden by default

Set `INCLUDE_TIER3=true` in the workflow env to include low-signal articles in the output.

---

## Architecture

```
sources.yaml ─┐
               ├─▶ fetch (RSS + Twitter/RSSHub)
report_profile ┘         │
                          ▼
                   deduplicate + serendipity sampling
                          │
                          ▼
                   LLM scoring (Tier 0–3, batched)
                          │
                   ┌──────┴──────┐
                   │  quality    │ Tier 1 < threshold?
                   │  pass loop  │ fetch more → re-score
                   └──────┬──────┘ (max 3 iterations)
                          │
                          ▼
                   executive summary (Tier 1 only)
                          │
                          ▼
                   format → outputs/briefing_YYYY-MM-DD.md
                          │
                          ▼
                   GitHub Actions artifact (90 days)
```

See [docs/decisions.md](docs/decisions.md) for the reasoning behind each architectural choice.
