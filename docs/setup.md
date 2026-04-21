# Setup Guide

## 1. Local development environment

```bash
# Create the Python environment
pyenv install 3.12
pyenv local consult  # already set in .python-version

# Install dependencies
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
```

## 2. Test the briefing locally

```bash
# Dry run — fetches articles, skips LLM and Drive upload (free, no API key needed)
python -m src.briefing.run --dry-run

# Full run — requires OPENROUTER_API_KEY in .env
python -m src.briefing.run
```

The output file lands in `outputs/briefing_YYYY-MM-DD.md`.

---

## 3. GitHub Actions setup

### Add secrets to the repository

Go to **Settings → Secrets and variables → Actions** and add:

| Secret name | Value |
|---|---|
| `OPENROUTER_API_KEY` | Your OpenRouter API key |
| `GOOGLE_DRIVE_FOLDER_ID` | The folder ID from the Drive URL |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Full contents of the service account JSON file |

### Schedule
The workflow runs every day at **04:00 UTC (05:00 CET / 06:00 CEST)**. To change the time, edit the `cron` line in `.github/workflows/daily_briefing.yml`.

You can also trigger it manually from the **Actions** tab → **Daily Briefing** → **Run workflow**.

---

## 4. Google Drive setup

To have the briefing automatically land in a shared Drive folder:

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (e.g. "consult-briefing")
3. Enable the **Google Drive API**
4. Create a **Service Account** → download the JSON key file
5. Save the JSON as `config/google_service_account.json` locally (**never commit this file**)
6. In Google Drive, right-click the target folder → **Share** → paste the service account email (ends in `@...gserviceaccount.com`) → give it **Editor** access
7. Copy the folder ID from the Drive URL and set `GOOGLE_DRIVE_FOLDER_ID` in `.env`

For GitHub Actions, paste the entire JSON content as the `GOOGLE_SERVICE_ACCOUNT_JSON` secret.

---

## 5. Twitter/X social monitoring via self-hosted RSSHub

The public `rsshub.app` instance no longer serves Twitter/X feeds. Self-hosting RSSHub restores the six (and growing) Twitter accounts configured in `sources.yaml`.

### Fastest option: Railway (one-click, ~€3–5/month)

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click **New Project → Deploy from GitHub repo** and search for `DIYgod/RSSHub`
   - Or use the official template: **New Project → Template → search "RSSHub"**
3. Railway will auto-deploy — copy the generated URL (e.g. `https://rsshub-production-xxxx.up.railway.app`)
4. Test it: open `https://your-rsshub-url/twitter/user/sama` — you should see a feed
5. In **GitHub Actions secrets**, add:
   - Secret name: `RSSHUB_INSTANCE`
   - Value: your Railway URL (no trailing slash)

Then update `config/sources.yaml` to read from the secret. For now, set it directly:

```yaml
social:
  rsshub_instance: "https://your-rsshub-url.up.railway.app"
```

Or keep it as an environment variable and pass it from GitHub Actions by adding to the workflow `env` block:
```yaml
RSSHUB_INSTANCE: ${{ secrets.RSSHUB_INSTANCE }}
```
(The social fetcher reads `sources.yaml` directly today — a small code change would be needed to override it from env. Until then, update the URL in `sources.yaml` directly.)

### Alternative: Fly.io (free tier available)

```bash
# Install flyctl, then:
fly launch --image diygod/rsshub --name rsshub-stefan
fly scale memory 256  # RSSHub needs ~200MB
```

### Notes
- RSSHub does not require a Twitter API key for basic timeline scraping
- The `rsshub.app` public instance may come back online periodically — check before committing to self-hosting
- Twitter rate limits apply; the 11 accounts currently configured are well within safe limits

---

## 6. Updating sources and report profile

- **Add/remove news sources**: edit `config/sources.yaml`
- **Change relevance criteria for a new report**: edit `config/report_profile.yaml`
- Both files are plain YAML — no code changes needed.
