#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DECK_ID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)
USER_AGENT = "MagicDeckBuilder/1.0 (https://github.com/; contact: local)"


def extract_deck_id(value: str) -> str:
    match = DECK_ID_RE.search(value)
    if not match:
        raise SystemExit("Deck URL must include a deck UUID.")
    return match.group(0)


def fetch_csv(deck_id: str) -> str:
    url = f"https://api.scryfall.com/decks/{deck_id}/export/csv"
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/csv"})
    try:
        with urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8")
    except HTTPError as exc:
        body = exc.read().decode("utf-8") if exc.fp else ""
        message = body.strip() or f"HTTP {exc.code}"
        raise SystemExit(f"Failed to fetch deck CSV ({message}).") from exc
    except URLError as exc:
        raise SystemExit("Network error contacting Scryfall.") from exc


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download a Scryfall deck CSV export by URL or ID."
    )
    parser.add_argument("deck", help="Deck URL or deck UUID")
    parser.add_argument(
        "output",
        nargs="?",
        help="Output CSV path (default: /tmp/scryfall-deck-<id>.csv)",
    )
    args = parser.parse_args()

    deck_id = extract_deck_id(args.deck)
    output_path = Path(args.output) if args.output else Path(f"/tmp/scryfall-deck-{deck_id}.csv")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    csv_text = fetch_csv(deck_id)
    output_path.write_text(csv_text, encoding="utf-8")

    print(f"Wrote deck CSV: {output_path}")


if __name__ == "__main__":
    main()
