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
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# https://docs.google.com/spreadsheets/d/1Y7XRF8CeMX3kpcdX0Qf7Jm7qoa2HIxwyiy1PycHlq2w/edit?usp=sharing

DEFAULT_SHEET_ID = "1Y7XRF8CeMX3kpcdX0Qf7Jm7qoa2HIxwyiy1PycHlq2w"
OUTPUT_PATH = Path("data/owned_cards.csv")
GDRIVE_FILE_ID_RE = re.compile(r"/(?:file|spreadsheets)/d/([A-Za-z0-9_-]+)")


def gdrive_export_url(file_id: str) -> str:
    return f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv"


def extract_gdrive_file_id(url: str) -> str:
    match = GDRIVE_FILE_ID_RE.search(url)
    if not match:
        raise SystemExit(f"Could not extract file ID from Google Drive URL: {url}")
    return match.group(1)


def fetch_csv(file_id: str) -> str:
    url = gdrive_export_url(file_id)
    request = Request(url, headers={"User-Agent": "MagicDeckBuilder/1.0"})
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
    parser.add_argument("--url", metavar="GDRIVE_URL", help="Google Drive share link to fetch instead of the default sheet")
    args = parser.parse_args()

    file_id = extract_gdrive_file_id(args.url) if args.url else DEFAULT_SHEET_ID

    if not args.no_sync:
        print("Fetching owned cards from Google Sheets...", flush=True)
        csv_text = fetch_csv(file_id)
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
