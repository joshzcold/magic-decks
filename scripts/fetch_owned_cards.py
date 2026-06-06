#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
from __future__ import annotations

import argparse
import csv
import io
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SHEET_ID = "1Y7XRF8CeMX3kpcdX0Qf7Jm7qoa2HIxwyiy1PycHlq2w"
SHEET_GID = "1008471280"
EXPORT_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={SHEET_GID}"
OUTPUT_PATH = Path("data/owned_cards.csv")


def fetch_csv() -> str:
    request = Request(EXPORT_URL, headers={"User-Agent": "MagicDeckBuilder/1.0"})
    try:
        with urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8")
    except HTTPError as exc:
        body = exc.read().decode("utf-8") if exc.fp else ""
        raise SystemExit(f"Failed to fetch sheet ({body.strip() or exc.code}).") from exc
    except URLError as exc:
        raise SystemExit(f"Network error: {exc}") from exc


def load_owned(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def lookup(rows: list[dict], name: str) -> list[dict]:
    name_lower = name.lower()
    return [r for r in rows if r.get("Name", "").lower() == name_lower]


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync owned cards from Google Sheets.")
    parser.add_argument("--lookup", metavar="NAME", help="Check if a card is owned")
    parser.add_argument("--no-sync", action="store_true", help="Skip download, use cached CSV")
    args = parser.parse_args()

    if not args.no_sync:
        print("Fetching owned cards from Google Sheets...", flush=True)
        csv_text = fetch_csv()
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text(csv_text, encoding="utf-8")
        rows = list(csv.DictReader(io.StringIO(csv_text)))
        print(f"Saved {len(rows)} cards to {OUTPUT_PATH}")
    else:
        if not OUTPUT_PATH.exists():
            raise SystemExit(f"No cached file at {OUTPUT_PATH}. Run without --no-sync first.")
        rows = load_owned(OUTPUT_PATH)
        print(f"Loaded {len(rows)} cards from {OUTPUT_PATH}")

    if args.lookup:
        matches = lookup(rows, args.lookup)
        if matches:
            print(f"\nOwned: {args.lookup}")
            for m in matches:
                binder = m.get("Binder Name", "?")
                qty = m.get("Quantity", "?")
                foil = " (foil)" if m.get("Foil", "normal") != "normal" else ""
                condition = m.get("Condition", "")
                print(f"  {qty}x  binder={binder}  condition={condition}{foil}")
        else:
            print(f"\nNot owned: {args.lookup}")


if __name__ == "__main__":
    main()
