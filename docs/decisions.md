# Design Decisions

A record of key architectural and tooling choices made during development, and the reasoning behind them.

---

## 1. Single-pass stateless pipeline

**Decision:** The pipeline runs as a single pass — fetch → score → format → deliver — with no database and no persistent state between runs.

**Why:** Simplicity and cost. Each run is self-contained, which makes it easy to test locally, debug, and run on GitHub Actions without any infrastructure beyond the repo itself. Articles are ephemeral by design; the briefing document is the only output that matters.

---

## 2. Single batched LLM call for article scoring

**Decision:** All fetched articles are sent to the LLM in one prompt, rather than one API call per article.

**Why:** Cost. Per-article calls would cost €1–2/day at typical article volumes; a single batched call costs €0.05–0.10/day. Claude 3.5 Sonnet handles large contexts reliably, so there is no quality trade-off at the volumes this system produces (~50–100 articles/day).

---

## 3. Model choice: Claude 3.5 Sonnet via OpenRouter

**Decision:** Use Claude 3.5 Sonnet as the default model, accessed through OpenRouter rather than directly through the Anthropic API.

**Why Claude 3.5 Sonnet:**
- Strong instruction-following for structured JSON output (critical for reliable scoring)
- Analytical prose quality suitable for executive summaries addressed to a central bank analyst
- Cost-effective at ~$3/M tokens, keeping daily costs well within budget

**Why OpenRouter:**
- Single API key covers many model providers
- Easy to swap models (e.g. to a cheaper model for testing, or a more capable one for future tasks) via the `OPENROUTER_MODEL` environment variable — no code changes needed
- No direct contract or billing relationship with Anthropic required

---

## 4. Two separate LLM calls: scoring and summary

**Decision:** Article scoring and executive summary generation are two separate API calls with different parameters.

**Why:** The two tasks have different output requirements:
- **Scoring** needs structured, deterministic output → `response_format: json_object`, temperature 0.2
- **Summary** needs natural prose → no JSON constraint, temperature 0.3

Merging them into one call would require either compromising the JSON format or adding significant prompt complexity. Keeping them separate makes each prompt simpler and more reliable.

---

## 5. YAML-driven configuration with no hardcoded report logic

**Decision:** All report-specific behavior (sources, themes, actors, tier definitions) lives in `config/sources.yaml` and `config/report_profile.yaml`. The Python code contains no report-specific knowledge.

**Why:** The same pipeline should work for future reports without any code changes. Stefan or a collaborator can update which sources to monitor or change the relevance criteria by editing plain YAML files. This also makes it easier to run the briefing against a test profile without touching the production config.

---

## 6. RSSHub for Twitter/X social monitoring

**Decision:** Twitter/X accounts are monitored by converting them to RSS feeds via a public RSSHub instance. LinkedIn is not supported.

**Why RSSHub:** It is free, requires no API keys, and integrates cleanly with the existing RSS fetcher. The public instance (`rsshub.app`) is sufficient for this volume; self-hosting is documented as an option if rate limits become an issue.

**Why no LinkedIn:** No viable free or low-cost API exists for LinkedIn feed access. The decision was made to skip it rather than introduce a paid dependency or brittle scraping.

---

## 7. GitHub Actions for scheduling

**Decision:** The briefing runs on a GitHub Actions workflow triggered by a daily cron at 04:00 UTC (05:00 CET / 06:00 CEST).

**Why:** No always-on server is needed. GitHub Actions is free at this usage volume, the workflow is version-controlled alongside the code, and it can be triggered manually from the Actions tab for testing. The 04:00 UTC trigger ensures the briefing is ready before 06:00 CET when Stefan starts his day. Artifacts are retained for 30 days as a backup.

---

## 8. Google Drive delivery via service account

**Decision:** The briefing is uploaded to Google Drive using a service account (JSON key file), not OAuth.

**Why:** OAuth requires a user to authorize the app and manage token refresh. A service account is fully automated — once the service account email is given Editor access to the target folder, uploads work indefinitely without any user interaction. This is appropriate for an unattended nightly job.

---

## 9. Graceful degradation at every stage

**Decision:** Failures at any stage do not abort the run; the pipeline continues and delivers whatever it can.

**Specifics:**
- Failed RSS/social feeds → logged and skipped; other sources continue
- Failed LLM scoring → all articles fall back to Tier 3 (unranked but still delivered)
- Failed Drive upload → briefing is still saved locally to `outputs/`

**Why:** A partial or unranked briefing is more useful than no briefing. Stefan should always get something in the morning, even if a dependency is temporarily unavailable.

---

## 10. 25-hour lookback window

**Decision:** Article fetching uses a 25-hour lookback window rather than exactly 24 hours.

**Why:** The daily run does not execute at a perfectly consistent time (clock drift, GitHub Actions queue delays). A 25-hour window ensures articles published near the previous run boundary are not silently dropped. The extra hour has negligible impact on noise.
