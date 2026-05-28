#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
from __future__ import annotations

import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


USER_AGENT = "MagicDeckBuilder/1.0 (https://github.com/; contact: local)"
BULK_URL = "https://api.scryfall.com/bulk-data"
DATA_DIR = Path("data/scryfall")
META_PATH = DATA_DIR / "default-cards.meta.json"


def fetch_json(url: str) -> dict:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8") if exc.fp else ""
        message = body.strip() or f"HTTP {exc.code}"
        raise SystemExit(f"Failed to fetch {url} ({message}).") from exc
    except URLError as exc:
        raise SystemExit(f"Network error contacting {url}.") from exc


def load_meta() -> dict | None:
    if not META_PATH.exists():
        return None
    return json.loads(META_PATH.read_text(encoding="utf-8"))


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Download Scryfall bulk default cards.")
    parser.add_argument(
        "--local",
        help="Use a local bulk JSON file instead of downloading",
    )
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if args.local:
        local_path = Path(args.local)
        if not local_path.exists():
            raise SystemExit(f"Local bulk file not found: {local_path}")
        output_path = DATA_DIR / local_path.name
        if output_path != local_path:
            output_path.write_bytes(local_path.read_bytes())
        meta = {
            "updated_at": "local",
            "download_uri": "local",
            "path": str(output_path),
        }
        META_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print(f"Registered local bulk file: {output_path}")
        return

    bulk = fetch_json(BULK_URL)
    items = bulk.get("data", []) if isinstance(bulk, dict) else []
    entry = next((item for item in items if item.get("type") == "default_cards"), None)
    if not entry:
        raise SystemExit("default_cards bulk entry not found.")

    updated_at = entry.get("updated_at")
    download_uri = entry.get("download_uri")
    if not updated_at or not download_uri:
        raise SystemExit("Bulk data entry missing updated_at or download_uri.")

    meta = load_meta()
    if meta and meta.get("updated_at") == updated_at:
        print("Bulk data already up to date.")
        return

    output_path = DATA_DIR / f"default-cards-{updated_at.replace(':', '').replace('-', '')}.json"
    print(f"Downloading bulk data to {output_path}")
    request = Request(download_uri, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urlopen(request, timeout=60) as response:
            output_path.write_bytes(response.read())
    except HTTPError as exc:
        body = exc.read().decode("utf-8") if exc.fp else ""
        message = body.strip() or f"HTTP {exc.code}"
        raise SystemExit(f"Failed to download bulk data ({message}).") from exc
    except URLError as exc:
        raise SystemExit("Network error downloading bulk data.") from exc

    meta = {
        "updated_at": updated_at,
        "download_uri": download_uri,
        "path": str(output_path),
    }
    META_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Updated metadata at {META_PATH}")


if __name__ == "__main__":
    main()
