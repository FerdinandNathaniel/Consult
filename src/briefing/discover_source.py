"""Discover and add an RSS feed for a given website URL.

Usage: python src/briefing/discover_source.py <website_url>

Exit 0 on success (feed found and appended to config/sources.yaml).
Exit 1 if no valid feed could be discovered.
"""

import os
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

import feedparser
import requests
import yaml
from bs4 import BeautifulSoup
from openai import OpenAI

SOURCES_PATH = Path("config/sources.yaml")
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; RSS-Discovery/1.0)"}
REQUEST_TIMEOUT = 12


def is_valid_feed(url: str) -> bool:
    try:
        feed = feedparser.parse(url)
        return bool(feed.entries) or bool(feed.feed.get("title"))
    except Exception:
        return False


def discover_via_html(url: str) -> str | None:
    try:
        r = requests.get(url, timeout=REQUEST_TIMEOUT, headers=REQUEST_HEADERS)
        soup = BeautifulSoup(r.text, "html.parser")
        for link in soup.find_all("link", rel="alternate"):
            link_type = link.get("type", "")
            if "rss" in link_type or "atom" in link_type:
                href = link.get("href", "").strip()
                if href:
                    return urljoin(url, href)
    except Exception:
        pass
    return None


def discover_via_common_paths(url: str) -> str | None:
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    candidates = [
        "/feed",
        "/rss",
        "/feed.xml",
        "/rss.xml",
        "/atom.xml",
        "/feeds/posts/default",
        "/blog/feed",
        "/news/feed",
        "/en/rss.xml",
    ]
    for path in candidates:
        candidate = base + path
        if is_valid_feed(candidate):
            return candidate
    return None


def discover_via_llm(url: str) -> tuple[str, str] | None:
    client = OpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
    )
    model = os.environ.get("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-6")

    response = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": (
                f"You are an RSS feed discovery assistant.\n\n"
                f"Website URL: {url}\n\n"
                "Reply with ONLY a JSON object (no markdown, no explanation):\n"
                '{"feed_url": "<most likely RSS/Atom feed URL>", "name": "<short descriptive source name>"}\n\n'
                'If you cannot reasonably guess a feed URL, set "feed_url" to null.'
            ),
        }],
        temperature=0,
        max_tokens=200,
    )

    import json
    text = response.choices[0].message.content.strip()
    # Strip markdown code fences if present
    text = re.sub(r"^```[a-z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    try:
        data = json.loads(text)
        feed_url = data.get("feed_url")
        name = data.get("name", "")
        if feed_url:
            return feed_url, name
    except Exception:
        pass
    return None


def get_feed_title(feed_url: str, fallback: str) -> str:
    try:
        feed = feedparser.parse(feed_url)
        return feed.feed.get("title", "").strip() or fallback
    except Exception:
        return fallback


def append_to_sources(source_name: str, feed_url: str) -> None:
    content = SOURCES_PATH.read_text()

    # Format the new entry lines using PyYAML scalar quoting
    name_scalar = yaml.dump(source_name, allow_unicode=True, default_flow_style=True).strip()
    url_scalar = yaml.dump(feed_url, allow_unicode=True, default_flow_style=True).strip()
    new_block = f"  - name: {name_scalar}\n    url: {url_scalar}\n"

    # Insert just before the next top-level section to stay inside rss_feeds
    inserted = False
    for marker in ["social:", "web_sources:", "serendipity_sources:"]:
        pattern = f"\n{marker}"
        if pattern in content:
            content = content.replace(pattern, f"\n{new_block}{pattern[1:]}", 1)
            inserted = True
            break

    if not inserted:
        content = content.rstrip("\n") + "\n" + new_block

    SOURCES_PATH.write_text(content)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: discover_source.py <website_url>", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1].strip()
    print(f"Discovering RSS feed for: {url}")

    feed_url: str | None = None
    source_name: str = ""

    # 1. Check if URL is already a valid feed
    print("Checking if URL is already an RSS feed…")
    if is_valid_feed(url):
        feed_url = url
        print("URL is already a valid feed.")

    # 2. HTML autodiscovery
    if not feed_url:
        print("Trying HTML autodiscovery…")
        feed_url = discover_via_html(url)
        if feed_url:
            print(f"Found via HTML autodiscovery: {feed_url}")

    # 3. Common paths
    if not feed_url:
        print("Trying common feed paths…")
        feed_url = discover_via_common_paths(url)
        if feed_url:
            print(f"Found via common path: {feed_url}")

    # 4. LLM suggestion
    if not feed_url:
        print("Asking LLM for a feed URL suggestion…")
        result = discover_via_llm(url)
        if result:
            candidate, llm_name = result
            print(f"LLM suggested: {candidate}")
            if is_valid_feed(candidate):
                feed_url = candidate
                source_name = llm_name
                print("LLM suggestion validated.")
            else:
                print(f"LLM suggestion could not be validated: {candidate}")

    if not feed_url:
        print(f"ERROR: Could not find a valid RSS feed for {url}", file=sys.stderr)
        sys.exit(1)

    # Resolve source name from the feed if not already set by LLM
    if not source_name:
        source_name = get_feed_title(feed_url, fallback=urlparse(url).netloc)

    # Check for duplicates
    existing = yaml.safe_load(SOURCES_PATH.read_text())
    existing_urls = [s.get("url", "") for s in (existing.get("rss_feeds") or [])]
    if feed_url in existing_urls:
        print(f"Feed already in sources.yaml: {feed_url}")
        sys.exit(0)

    append_to_sources(source_name, feed_url)
    print(f'SUCCESS: Added "{source_name}" ({feed_url})')


if __name__ == "__main__":
    main()
