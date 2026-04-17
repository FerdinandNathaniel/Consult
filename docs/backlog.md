# Backlog

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
