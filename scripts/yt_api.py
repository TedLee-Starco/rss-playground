"""Shared YouTube Data API v3 helpers."""

import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path


def load_api_key() -> str:
    env_file = Path(".env")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("YOUTUBE_API_KEY="):
                return line.split("=", 1)[1].strip()
    key = os.environ.get("YOUTUBE_API_KEY", "")
    if not key:
        sys.exit(
            "YOUTUBE_API_KEY not set.\n"
            "Add it to your .env file: YOUTUBE_API_KEY=AIza..."
        )
    return key


def fetch_channel(api_key: str, **params: str) -> dict:
    """Call the channels endpoint and return the first item, or {}."""
    query = urllib.parse.urlencode({"part": "snippet", "key": api_key, **params})
    url = f"https://www.googleapis.com/youtube/v3/channels?{query}"
    with urllib.request.urlopen(url) as resp:
        data = json.load(resp)
    items = data.get("items", [])
    return items[0] if items else {}


def resolve_channel(url: str, api_key: str) -> tuple[str, str]:
    """Return (channel_id, channel_title) for a YouTube channel URL."""
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.rstrip("/")

    # youtube.com/channel/UCxxxxxxx — no API call needed
    m = re.match(r"^/channel/(UC[\w-]+)$", path)
    if m:
        channel_id = m.group(1)
        item = fetch_channel(api_key, id=channel_id)
        title = item.get("snippet", {}).get("title", channel_id) if item else channel_id
        return channel_id, title

    # youtube.com/@handle
    m = re.match(r"^/@([\w.-]+)$", path)
    if m:
        item = fetch_channel(api_key, forHandle=m.group(1))
        if not item:
            sys.exit(f"Channel not found for handle: @{m.group(1)}")
        return item["id"], item["snippet"]["title"]

    # youtube.com/c/name or youtube.com/user/name
    m = re.match(r"^/(?:c|user)/([\w.-]+)$", path)
    if m:
        item = fetch_channel(api_key, forUsername=m.group(1))
        if not item:
            sys.exit(f"Channel not found for username: {m.group(1)}")
        return item["id"], item["snippet"]["title"]

    sys.exit(f"Unrecognized YouTube URL format: {url}")
