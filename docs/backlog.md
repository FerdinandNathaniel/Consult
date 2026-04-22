# Backlog

---

## Active

### A. Fix signal quality: approach TBD

**Problem:** The pipeline alternates between two failure modes — (1) too restrictive: relevant content gets filtered out, and (2) too noisy: Tier 2/3 fills up with low-value articles.

Specific fix approach not yet agreed. Revisit after source expansion (B) is live and we can see whether coverage improvement alone changes the pattern.

---

### B. Expand credible source coverage

**Problem:** The pipeline currently has ~25 core RSS feeds and ~15 serendipity sources. That's insufficient to reliably catch EU/NL institutional output, central bank research, and the AI policy think-tank ecosystem. Gaps mean relevant content simply never enters the pipeline, no matter how good the scoring is.

**Sources to add** (add to `config/sources.yaml`; tier each as `core` or `serendipity`):

*EU & central bank institutional (core — high reliability, low noise):*
- ECB Working Papers RSS — `https://www.ecb.europa.eu/pub/research/working-papers/rss.html`
- DNB Working Papers — `https://www.dnb.nl/en/publications/dnb-working-papers/` (check for RSS; else add as web_source)
- European Parliament Think Tank (EPRS) — `https://www.europarl.europa.eu/thinktank/en/recent.rss`
- OECD iLibrary AI — `https://www.oecd-ilibrary.org/rss/content/area/sti?format=rss` (or search for OECD AI policy RSS)
- European Investment Bank (EIB) research — check for RSS

*Dutch ecosystem (core):*
- RVO (Rijksdienst voor Ondernemend Nederland) — AI/digitalisering publications; find RSS or add as web_source
- Techleap.nl blog/news — `https://techleap.nl/news` (check for RSS)
- NWO (Dutch Research Council) — AI-related funding news
- Holland FinTech — fintech + AI in Netherlands financial sector

*AI policy think tanks (serendipity — good signal, infrequent):*
- Centre for the Governance of AI (GovAI) — `https://www.governance.ai/feed`
- AI Now Institute — `https://ainowinstitute.org/feed`
- Future of Life Institute — `https://futureoflife.org/feed/`
- Zhi-heng Wang / CSET (Center for Security and Emerging Technology) — `https://cset.georgetown.edu/feed/`
- Bertelsmann Stiftung (German think tank, EU AI policy) — find RSS

*Startup & investment data (serendipity):*
- Dealroom blog — `https://dealroom.co/blog/feed` (EU startup/VC data, directly relevant)
- Atomico State of European Tech blog — check for RSS
- First Minute Capital / Forward Partners — lower priority

**Steps:**
1. Validate each URL returns a working feed (run locally with `--dry-run` to see fetch counts)
2. Add confirmed feeds to `sources.yaml` under the appropriate section (`rss_feeds` for core, `serendipity_pool` for lower-frequency)
3. Set `language` and `category` fields per entry (follow existing conventions)
4. Run one live briefing, check that new sources contribute articles and score correctly

**Open questions:**
- DNB's own website: does it have an RSS feed for working papers / press releases? Worth checking — it's the most directly relevant institutional source.
- Should Dealroom and Sifted overlap? (Sifted is already in core — Dealroom adds data-driven investment angles.)
- How large should the serendipity pool grow before we change `SERENDIPITY_N` from 3 to 5?

---

## Future

Future features and improvements, in rough priority order. Not scheduled — pick up when the time is right.

---

## Active

_Nothing currently queued._

---

## On hold

Deprioritized — revisit once active items are properly finished.

- **Google Drive delivery** — code exists in `src/briefing/drive.py` but is disabled; artifacts via GitHub Actions serve as delivery for now; requires a Google Workspace Shared Drive to re-enable
- **Email newsletter ingestion** — planned v2 feature (dedicated inbox + IMAP access); not started
- **Web scraping** — CBS Statline, Rijksoverheid, and AIAct.eu are configured in `config/sources.yaml` under `web_sources` but the fetcher is not implemented

---

## Future (things to look at)

Longer-horizon ideas, not yet scheduled.

### Human-in-the-loop interface (GitHub Pages)

A lightweight web interface hosted on GitHub Pages where Stefan can read past briefings and give feedback that feeds back into the pipeline.

**Why:** Closes the loop between output quality and configuration. Right now, improving sources or tier calibration requires editing YAML files directly.

**Capabilities to include:**

- **Briefing archive** — list and open all past artifacts in the browser; no need to download Markdown files from the Actions tab
- **Source feedback** — mark a source as "too noisy" or "very useful"; feedback stored and surfaced as suggestions to update `sources.yaml`
- **Inline source editing** — add a new RSS URL directly from the interface; triggers a PR or commit to `sources.yaml`
- **Article-level feedback** — thumbs up/down on individual articles to help calibrate tier definitions over time (future: feed back into scoring prompt automatically)

**Suggested technical approach:**

- **Frontend:** Static site on GitHub Pages. Vanilla JS or small framework (Preact, Alpine.js) — no build pipeline needed.
- **Reading artifacts:** GitHub REST API (`/repos/{owner}/{repo}/actions/artifacts`) — public repos need no auth; private repos need a PAT.
- **Feedback storage:** JSON file committed to the repo (`data/feedback.json`), or GitHub Issues with a structured template.
- **Auth:** GitHub OAuth (free via GitHub Apps), or a shared secret in the URL for a private repo.
- **No backend required** — everything goes through the GitHub API from the browser.

**Open questions before building:**
- Is the repo public or private? (Affects artifact API auth)
- Should source edits go through a PR for review, or commit directly to `main`?
- How should article-level feedback influence scoring — manual review or auto-inject into the prompt?

---

### Podcast monitoring

Include relevant podcast episodes as a content source, either via episode summaries or full transcript analysis.

**Why:** Several high-quality AI policy and economics podcasts (ECB/DNB institutional, Exponential View, Dwarkesh Patel) surface long-form analysis that never appears in RSS feeds. A single episode can contain more signal than a week of articles.

**Two approaches (not mutually exclusive):**

- **Summary-only (cheap):** Most podcasts publish episode descriptions via RSS — feed these through the existing scoring pipeline like any other article. Limitation: show notes are often vague marketing copy rather than informative summaries.
- **Transcript analysis (expensive):** Fetch audio, transcribe via Whisper, chunk, and run a relevance pass. Cost: ~€0.10–0.50/episode; only worth it for confirmed high-signal shows. Better suited to on-demand triggering than automatic daily runs.

**Suggested phased approach:**
1. Add podcast RSS feeds to `sources.yaml` and see what the scorer makes of show notes
2. If show notes prove too thin, look for feeds that include chapter markers or guest names
3. Evaluate transcript analysis only if steps 1–2 consistently miss Tier 1 signal

**Candidate podcasts:**
- ECB Podcast — directly relevant for DNB perspective
- Exponential View (Azeem Azhar) — AI + economics
- The AI Policy Podcast (CNAS) — US-focused but useful for EU comparison
- Dwarkesh Patel — occasional high-signal researcher/policy guests
- Hard Fork (NYT) — broad tech, lower signal but widely referenced

**Open questions:**
- Which podcasts publish genuinely informative show notes vs. vague descriptions?
- Is Whisper self-hostable within GitHub Actions free minutes, or does transcription need a separate always-on service?
- Should transcript analysis be on-demand (manual trigger per episode) or automatic for a curated shortlist?

---

## Done

- **Twitter/X fetching** — self-hosted RSSHub on Railway; configured via `social.rsshub_instance` in `sources.yaml`
- **GitHub Actions scheduling** — daily at 04:00 UTC (05:00 CET / 06:00 CEST); artifact retention 90 days
- **RSS feeds** — 11 active sources configured; 3 disabled with notes
- **LLM scoring & summary** — batched single call; cost ~€0.05–0.10/day
- **Graceful degradation** — failed sources or LLM calls never abort the run; Stefan always gets something
- **25-hour lookback** — prevents articles near run boundaries from being silently dropped
- **README** — full project description, quick-start, architecture diagram, and operational notes (Twitter cookie refresh, Tier 3 flag)
- **CET timezone correction** — replaced hardcoded `+1` with `ZoneInfo("Europe/Amsterdam")` in `run.py`; now correctly shifts to CEST in summer
