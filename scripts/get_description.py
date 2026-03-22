"""Print the description of a public YouTube video.

Usage:
    YOUTUBE_API_KEY=AIza... uv run python scripts/get_description.py <video_id>

Or store your key in a .env file:
    echo "YOUTUBE_API_KEY=AIza..." > .env
    uv run python scripts/get_description.py <video_id>
"""

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path


def load_api_key() -> str:
    # Load from .env file if present
    env_file = Path(".env")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("YOUTUBE_API_KEY="):
                return line.split("=", 1)[1].strip()

    key = os.environ.get("YOUTUBE_API_KEY", "")
    if not key:
        sys.exit(
            "YOUTUBE_API_KEY not set.\n"
            "Create an API key at https://console.cloud.google.com/apis/credentials\n"
            "then either export it or add it to a .env file."
        )
    return key


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(f"Usage: {sys.argv[0]} <video_id>")

    video_id = sys.argv[1]
    api_key = load_api_key()

    params = urllib.parse.urlencode({"part": "snippet", "id": video_id, "key": api_key})
    url = f"https://www.googleapis.com/youtube/v3/videos?{params}"

    try:
        with urllib.request.urlopen(url) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        sys.exit(f"YouTube API error {e.code}: {e.read().decode()}")

    items = data.get("items", [])
    if not items:
        sys.exit(f"Video not found: {video_id}")

    print(items[0]["snippet"].get("description", ""))


if __name__ == "__main__":
    main()
