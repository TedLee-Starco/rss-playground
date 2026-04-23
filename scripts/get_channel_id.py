"""Print the channel ID for a YouTube channel URL.

Usage:
    uv run python scripts/get_channel_id.py <youtube_url>

Examples:
    uv run python scripts/get_channel_id.py https://www.youtube.com/@MrBeast
    uv run python scripts/get_channel_id.py https://www.youtube.com/channel/UCX6OQ3DkcsbYNE6H8uQQuVA
    uv run python scripts/get_channel_id.py https://www.youtube.com/c/MrBeast6000
"""

import sys

from yt_api import load_api_key, resolve_channel


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(f"Usage: {sys.argv[0]} <youtube_url>")
    channel_id, _ = resolve_channel(sys.argv[1], load_api_key())
    print(channel_id)


if __name__ == "__main__":
    main()
