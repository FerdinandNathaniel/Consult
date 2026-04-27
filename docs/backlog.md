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

### A. Fix signal quality

Calibrate scoring so the briefing surfaces the right articles — less noise, no important items missed.

**Why:** Over-filtering or mis-tiering means Stefan either misses signal or has to wade through irrelevant items.

**Status:** Approach not yet settled — the previously proposed fix (flip tie-break default from Tier 0 to Tier 3) was rejected as the right path forward. Root cause needs more investigation before a fix is prescribed.

**Files:** `config/report_profile.yaml`, `src/briefing/processor.py`

---

### B. Expand and maintain sources

Keep `config/sources.yaml` up to date with high-quality, relevant feeds as the landscape evolves.

**Why:** The AI policy and investment space moves fast; new institutional sources appear and existing ones shift in relevance. A one-off expansion is not enough — this needs a repeatable process.

**Status:** Some sources added (ECB WP, DNB WP, others), but coverage is still incomplete. Will remain a recurring gap until a proper discovery-and-validation workflow is in place.

**Recurring need:** This item should stay active until two things exist:
1. A defined process for discovering and vetting new sources (part of item C skills)
2. The human-in-the-loop dashboard (Future) — which lets Stefan flag and add sources without touching YAML

**Candidate sources still to evaluate:** EPRS, GovAI, AI Now, Dealroom, RVO, Techleap, NWO (and others surfaced during use)

---

### C. Set up project skills (CLAUDE.md)

Define reusable Claude Code skills and CLAUDE.md instructions so every session starts with full context and consistent behavior — no manual re-explanation needed.

**Why:** Without explicit skills, Claude re-derives conventions each session (or gets them wrong). Good skills also reduce prompt tokens and make the agent faster.

**Inspired by:** [Analysis of 12k+ repos with CLAUDE.md files](https://www.reddit.com/r/ClaudeCode/comments/1srm2vv/we_analyzed_12356_repos_with_claudemd_files/)

**Skills / instructions to define:**

- **Coding style** — preferred Python patterns for this repo (naming, structure, error handling, no unnecessary abstractions)
- **Documentation (README)** — when and how to update the README; what sections to keep current (sources, architecture, ops notes)
- **Explicit memory protocol** — where repo-level memory lives, how to add/update/remove entries, what belongs in memory vs. backlog vs. code comments
- **Adding new sources** — step-by-step: find the RSS URL, check it exists, add to `config/sources.yaml` with the right fields, verify with a dry-run
- **Dry-run procedure** — exact command(s) to run a local dry-run without hitting the LLM or producing artifacts; what to check in the output
- **Backlog protocol** — how to read `docs/backlog.md`, mark items done, move items between sections, add a new item (format, required fields)

**Suggested approach:**

1. Start with a `CLAUDE.md` at repo root covering the most-used workflows (dry-run, adding sources, backlog)
2. Add a `.claude/skills/` directory for longer multi-step skills (e.g. "add a new source end-to-end")
3. Validate each skill in a real session before marking done

**Open questions:**
- Should skills live in `.claude/` or inline in `CLAUDE.md`?
- Are any skills general enough to go in the user-level `~/.claude/` instead?

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

A lightweight dashboard on GitHub Pages for reading briefings, managing sources, and triggering runs.

**Status:** v1 built and merged. Files: `web/index.html`, `.github/workflows/deploy_pages.yml`.

**What's live in v1:**
- Briefing archive — read past briefings in the browser (pipeline now commits to `briefings/` on each run)
- Source feedback — 👍/👎 per source, stored in `data/source_feedback.json`
- Add source — form commits directly to `config/sources.yaml` on main
- Manual run trigger — calls `workflow_dispatch` via GitHub API
- PAT auth — stored in localStorage; no backend needed

**One-time setup (Fabian):**
1. Make repo public in Settings → General (required for GitHub Pages on free plan)
2. Enable Pages in Settings → Pages → Source: GitHub Actions
3. Create a fine-grained PAT scoped to this repo with `Contents: read/write`, `Actions: write`, and `Variables: read/write` permissions, then share it with Stefan once (e.g. Signal). `Variables` is needed for the "Save as default" button; without it the PATCH to `actions/variables/OPENROUTER_MODEL` returns 403.

**Stefan's one-time setup:**
- Paste the token Fabian sent into the dashboard — stored in the browser, never needed again

**What's not in v1 (future):**
- Article-level feedback (thumbs up/down on individual items)
- Source feedback feeding back into scoring automatically
- Briefings archive beyond 90-day artifact retention (now stored in `briefings/` in the repo indefinitely)

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

- **Weekly round-up** — `src/briefing/weekly.py` reads the 7 most recent daily briefings, de-duplicates stories, and produces timestamped files like `roundups/roundup_YYYY-MM-DD_HHMM.md`; scheduled via `.github/workflows/weekly_roundup.yml` (Monday 05:00 UTC)
- **Social "what are people talking about" section** — daily briefing now includes a `## Wat bespreken gevolgde accounts?` section (LLM-generated thematic summary of social posts); social posts are handled separately from news scoring; weekly round-up synthesises these into a weekly social view
- **Twitter/X fetching** — self-hosted RSSHub on Railway; configured via `social.rsshub_instance` in `sources.yaml`
- **GitHub Actions scheduling** — daily at 04:00 UTC (05:00 CET / 06:00 CEST); artifact retention 90 days
- **RSS feeds** — 11 active sources configured; 3 disabled with notes
- **LLM scoring & summary** — batched single call; cost ~€0.05–0.10/day
- **Graceful degradation** — failed sources or LLM calls never abort the run; Stefan always gets something
- **25-hour lookback** — prevents articles near run boundaries from being silently dropped
- **README** — full project description, quick-start, architecture diagram, and operational notes (Twitter cookie refresh, Tier 3 flag)
- **CET timezone correction** — replaced hardcoded `+1` with `ZoneInfo("Europe/Amsterdam")` in `run.py`; now correctly shifts to CEST in summer
