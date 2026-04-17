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

## 3. Model choice: Claude Sonnet via OpenRouter

**Decision:** Use `anthropic/claude-sonnet-4.6` as the default model, accessed through OpenRouter rather than directly through the Anthropic API.

**Why Claude Sonnet:** Strong instruction-following for structured JSON output, analytical prose quality suitable for central bank briefings, cost-effective at ~$3/M tokens.

**Why OpenRouter:** Single API key, easy model switching via the `OPENROUTER_MODEL` env var without code changes, no direct Anthropic contract required.

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

**Decision:** Twitter/X accounts are monitored via RSSHub. LinkedIn is not supported.

**Why RSSHub:** Free, no API keys, integrates with the existing RSS fetcher. Note: the public instance (`rsshub.app`) no longer serves Twitter feeds as of 2026 — self-hosting RSSHub is required to re-enable social fetching.

**Why no LinkedIn:** No viable free or low-cost API exists.

---

## 7. GitHub Actions for scheduling

**Decision:** The briefing runs on a GitHub Actions workflow triggered by a daily cron at 04:00 UTC (05:00 CET / 06:00 CEST).

**Why:** No always-on server is needed. GitHub Actions is free at this usage volume, the workflow is version-controlled alongside the code, and it can be triggered manually from the Actions tab for testing. The 04:00 UTC trigger ensures the briefing is ready before 06:00 CET when Stefan starts his day. Artifacts are retained for 90 days (the maximum on the free plan — see §11).

---

## 8. Google Drive delivery — temporarily disabled

**Decision:** Drive upload is currently disabled. Output is delivered via GitHub Actions artifacts. The service account auth approach (no OAuth) is still the right call for automation.

**Why disabled:** Service accounts have no personal Drive storage quota — uploading to a regular "My Drive" folder returns `storageQuotaExceeded`. Reading from Drive with the service account works without issue.

**To re-enable:** Create a Shared Drive (requires Google Workspace), add the service account as a member, and add `supportsAllDrives=True` to the `files().create()` call in `drive.py`.

---

## 9. Graceful degradation at every stage

**Decision:** Failures at any stage do not abort the run; the pipeline continues and delivers whatever it can.

**Specifics:**
- Failed RSS/social feeds → logged and skipped; other sources continue
- Failed LLM scoring → all articles fall back to Tier 3 (unranked but still delivered)
- Failed Drive upload → briefing is still saved locally to `outputs/`

**Why:** A partial or unranked briefing is more useful than no briefing. Stefan should always get something in the morning, even if a dependency is temporarily unavailable.

---

## 11. GitHub Actions artifact retention limit

**Decision:** Artifact retention is set to 90 days, the maximum allowed on the GitHub Free plan.

**Why:** Artifacts cannot be stored indefinitely — GitHub enforces a hard ceiling of 90 days (Free/Pro/Team) or 400 days (Enterprise). Briefing files older than 90 days are automatically deleted. If long-term archiving is needed, the alternatives are: attaching files to a GitHub Release (permanent), committing them to a dedicated archive repository, or restoring Drive delivery via a Shared Drive (see §8).

---

## 10. 25-hour lookback window

**Decision:** Article fetching uses a 25-hour lookback window rather than exactly 24 hours.

**Why:** The daily run does not execute at a perfectly consistent time (clock drift, GitHub Actions queue delays). A 25-hour window ensures articles published near the previous run boundary are not silently dropped. The extra hour has negligible impact on noise.
