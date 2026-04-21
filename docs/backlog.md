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

## 1. Human-in-the-loop interface (GitHub Pages)

**What:** A lightweight web interface hosted on GitHub Pages where Stefan can read past briefings and give feedback that feeds back into the pipeline.

**Why:** Closes the loop between output quality and configuration. Right now, improving sources or tier calibration requires editing YAML files directly. The interface makes this accessible without touching code.

**Capabilities to include:**

- **Briefing archive** — list and open all past artifacts directly in the browser; no need to download Markdown files from the Actions tab
- **Source feedback** — mark a source as "too noisy" or "very useful" after reading a briefing; feedback is stored and surfaced as suggestions to add/remove from `sources.yaml`
- **Inline source editing** — add a new RSS URL directly from the interface; triggers a PR or commit to `sources.yaml`
- **Article-level feedback** — thumbs up/down on individual articles to help calibrate the tier definitions over time (future: feed this back into the scoring prompt automatically)

**Suggested technical approach:**

- **Frontend:** Static site on GitHub Pages (`gh-pages` branch or `/docs` folder). Vanilla JS or a small framework (Preact, Alpine.js) — no build pipeline needed.
- **Reading artifacts:** GitHub REST API (`/repos/{owner}/{repo}/actions/artifacts`) — public repos don't need auth; private repos need a PAT stored in the page or passed at login.
- **Feedback storage:** Write feedback as a JSON file committed to the repo (e.g. `data/feedback.json`), or open a GitHub Issue with a structured template. A commit-based approach allows the pipeline to read feedback directly.
- **Auth:** GitHub OAuth (free via GitHub Apps) so only Stefan can submit feedback. Or simpler: a shared secret in the URL if the repo is private and access is already restricted.
- **No backend required** — everything goes through the GitHub API from the browser.

**Open questions before building:**
- Is the repo public or private? (Affects artifact API auth approach)
- Should source edits go through a PR for review, or commit directly to `main`?
- How should article-level feedback eventually influence scoring — manual review, or automatically injected into the prompt?

---

## 2. Podcast monitoring

**What:** Include relevant podcast episodes as a content source, either via episode summaries or full transcript analysis.

**Why:** Several high-quality AI policy and economics podcasts (e.g. ECB/DNB institutional podcasts, Exponential View audio, Dwarkesh Patel) surface long-form analysis and expert interviews that never appear in RSS feeds or news articles. A single episode can contain more signal than a week of articles.

**Two approaches (not mutually exclusive):**

- **Summary-only (cheap):** Most podcasts publish episode descriptions and show notes via RSS. Feed these through the existing scoring pipeline like any other article — zero extra cost. Limitation: show notes are often vague marketing copy rather than informative summaries.

- **Transcript analysis (expensive):** Fetch audio, transcribe via Whisper (free, self-hosted) or a transcription API, chunk the transcript, and run a relevance pass to extract the most pertinent segments. Cost: ~€0.10–0.50 per episode; only worth it for confirmed high-signal shows. Better suited to on-demand triggering than automatic daily runs.

**Suggested phased approach:**
1. Start with summary-only — add podcast RSS feeds to `sources.yaml` and see what the scorer makes of show notes
2. If show notes prove too thin, look for feeds that include chapter markers or guest names (many do)
3. Evaluate transcript analysis only if steps 1–2 consistently miss signal that would have been Tier 1

**Candidate podcasts to evaluate:**
- ECB Podcast — directly relevant for DNB perspective
- Exponential View (Azeem Azhar) — AI + economics, directly relevant
- The AI Policy Podcast (CNAS) — US-focused but useful for EU comparison
- Dwarkesh Patel — occasional high-signal researcher/policy guests
- Hard Fork (NYT) — broad tech, lower signal but widely referenced

**Open questions:**
- Which podcasts publish genuinely informative show notes vs. vague descriptions?
- Is Whisper self-hostable within GitHub Actions free minutes, or does transcription need a separate always-on service?
- Should transcript analysis be on-demand (manual trigger per episode) or automatic for a curated shortlist?

---
