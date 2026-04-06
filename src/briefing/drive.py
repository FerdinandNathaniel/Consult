"""
Google Drive uploader.

Uploads the generated briefing file to a shared Google Drive folder.
Uses a service account — no OAuth flow needed.

Setup:
1. Create a Google service account (see docs/setup_google_drive.md)
2. Share the target Drive folder with the service account email
3. Save the service account JSON as config/google_service_account.json
4. Set GOOGLE_DRIVE_FOLDER_ID in .env
"""

import logging
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def upload_to_drive(file_path: Path, filename: str) -> str | None:
    """Upload file to Google Drive. Returns the file URL or None on failure."""
    folder_id = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")
    creds_file = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "config/google_service_account.json")

    if not folder_id:
        logger.info("GOOGLE_DRIVE_FOLDER_ID not set — skipping Drive upload")
        return None

    if not Path(creds_file).exists():
        logger.warning(f"Service account file not found at {creds_file} — skipping Drive upload")
        return None

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        creds = service_account.Credentials.from_service_account_file(
            creds_file,
            scopes=["https://www.googleapis.com/auth/drive.file"],
        )
        service = build("drive", "v3", credentials=creds)

        file_metadata = {
            "name": filename,
            "parents": [folder_id],
        }
        media = MediaFileUpload(str(file_path), mimetype="text/markdown")
        uploaded = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, webViewLink",
        ).execute()

        url = uploaded.get("webViewLink", "")
        logger.info(f"Uploaded to Drive: {url}")
        return url

    except ImportError:
        logger.warning("google-api-python-client not installed — skipping Drive upload. Run: pip install google-api-python-client google-auth")
        return None
    except Exception as e:
        logger.error(f"Drive upload failed: {e}")
        return None
