"""Print the channel ID for a YouTube channel URL.

Usage:
    uv run python scripts/get_channel_id.py <youtube_url>

Examples:
    uv run python scripts/get_channel_id.py https://www.youtube.com/@MrBeast
    uv run python scripts/get_channel_id.py https://www.youtube.com/channel/UCX6OQ3DkcsbYNE6H8uQQuVA
    uv run python scripts/get_channel_id.py https://www.youtube.com/c/MrBeast6000
"""

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


def lookup_by_handle(handle: str, api_key: str) -> str:
    params = urllib.parse.urlencode({"part": "id", "forHandle": handle, "key": api_key})
    url = f"https://www.googleapis.com/youtube/v3/channels?{params}"
    with urllib.request.urlopen(url) as resp:
        data = json.load(resp)
    items = data.get("items", [])
    if not items:
        sys.exit(f"Channel not found for handle: @{handle}")
    return items[0]["id"]


def lookup_by_username(username: str, api_key: str) -> str:
    params = urllib.parse.urlencode(
        {"part": "id", "forUsername": username, "key": api_key}
    )
    url = f"https://www.googleapis.com/youtube/v3/channels?{params}"
    with urllib.request.urlopen(url) as resp:
        data = json.load(resp)
    items = data.get("items", [])
    if not items:
        sys.exit(f"Channel not found for username: {username}")
    return items[0]["id"]


def resolve(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.rstrip("/")

    # youtube.com/channel/UCxxxxxxx
    m = re.match(r"^/channel/(UC[\w-]+)$", path)
    if m:
        return m.group(1)

    # youtube.com/@handle
    m = re.match(r"^/@([\w.-]+)$", path)
    if m:
        return lookup_by_handle(m.group(1), load_api_key())

    # youtube.com/c/name or youtube.com/user/name
    m = re.match(r"^/(?:c|user)/([\w.-]+)$", path)
    if m:
        return lookup_by_username(m.group(1), load_api_key())

    sys.exit(f"Unrecognized YouTube URL format: {url}")


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(f"Usage: {sys.argv[0]} <youtube_url>")
    print(resolve(sys.argv[1]))


if __name__ == "__main__":
    main()
