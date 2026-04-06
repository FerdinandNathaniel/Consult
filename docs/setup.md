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

## 5. Updating sources and report profile

- **Add/remove news sources**: edit `config/sources.yaml`
- **Change relevance criteria for a new report**: edit `config/report_profile.yaml`
- Both files are plain YAML — no code changes needed.
