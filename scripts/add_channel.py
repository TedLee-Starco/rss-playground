"""Add a YouTube channel entry to channels.json interactively.

Usage:
    uv run python scripts/add_channel.py <youtube_url>

Examples:
    uv run python scripts/add_channel.py https://www.youtube.com/@MrBeast
    uv run python scripts/add_channel.py https://www.youtube.com/channel/UCX6OQ3DkcsbYNE6H8uQQuVA
"""

import json
import sys
from pathlib import Path

from yt_api import load_api_key, resolve_channel

CHANNELS_FILE = Path("channels.json")

WEBHOOK_KEYS = [
    "STRATEGY_WEBHOOK",
    "BASE_WEBHOOK",
    "CHANNEL_WEBHOOK",
]

BASE_WEBHOOK_EXTRAS = {
    "message": "快去複製這個陣容！",
    "showDescriptionUrls": True,
    "descriptionUrlFilter": "https://link.clashofclans.com/en",
}


def pick_webhook() -> str:
    print("\nAvailable webhook keys:")
    for i, key in enumerate(WEBHOOK_KEYS, 1):
        print(f"  {i}. {key}")
    while True:
        choice = input("Select webhook [1-3]: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(WEBHOOK_KEYS):
            return WEBHOOK_KEYS[int(choice) - 1]
        print("Invalid choice, try again.")


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(f"Usage: {sys.argv[0]} <youtube_url>")

    channel_id, channel_title = resolve_channel(sys.argv[1], load_api_key())

    print(f"\nChannel found: {channel_title}")
    print(f"Channel ID:    {channel_id}")

    name = input(f"Display name [{channel_title}]: ").strip() or channel_title
    webhook_key = pick_webhook()

    channels: list[dict] = json.loads(CHANNELS_FILE.read_text())
    next_id = max(c["id"] for c in channels) + 1

    entry: dict = {
        "id": next_id,
        "channelId": channel_id,
        "name": name,
        "webhookKey": webhook_key,
    }

    if webhook_key == "BASE_WEBHOOK":
        entry.update(BASE_WEBHOOK_EXTRAS)

    channels.append(entry)
    CHANNELS_FILE.write_text(json.dumps(channels, ensure_ascii=False, indent=2) + "\n")

    print(f"\nAdded entry #{next_id} to channels.json:")
    print(json.dumps(entry, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
