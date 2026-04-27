from datetime import datetime

from src.briefing.weekly import build_roundup_filename


def test_build_roundup_filename_uses_date_and_time():
    now = datetime(2026, 4, 27, 20, 30)

    assert build_roundup_filename(now) == "roundup_2026-04-27_2030.md"