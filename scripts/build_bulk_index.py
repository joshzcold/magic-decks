#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DATA_DIR = Path("data/scryfall")
META_PATH = DATA_DIR / "default-cards.meta.json"
INDEX_PATH = DATA_DIR / "default-cards-index.json"


def load_bulk_path() -> Path:
    if not META_PATH.exists():
        raise SystemExit("Bulk metadata not found. Run update_bulk_cache.py first.")
    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    path = meta.get("path") if isinstance(meta, dict) else None
    if not path:
        raise SystemExit("Bulk metadata missing path.")
    bulk_path = Path(path)
    if not bulk_path.exists():
        raise SystemExit(f"Bulk file not found: {bulk_path}")
    return bulk_path


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    bulk_path = load_bulk_path()
    print(f"Loading bulk data: {bulk_path}")

    data = json.loads(bulk_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("Bulk file should be a JSON array.")

    index: dict[str, dict[str, Any]] = {}
    for card in data:
        if not isinstance(card, dict):
            continue
        name = card.get("name")
        if not name:
            continue
        if card.get("lang") != "en":
            continue
        if card.get("set_type") == "token":
            continue
        if card.get("digital") is True:
            continue
        if card.get("game") and card.get("game") not in {"paper", "mtgo", "arena"}:
            continue

        prices = card.get("prices") if isinstance(card.get("prices"), dict) else {}
        image_uris = card.get("image_uris") if isinstance(card.get("image_uris"), dict) else {}

        released_at = card.get("released_at") or ""
        current = index.get(name)
        if current and current.get("released_at", "") >= released_at:
            continue

        index[name] = {
            "name": name,
            "set": card.get("set", ""),
            "rarity": card.get("rarity", ""),
            "cmc": card.get("cmc", ""),
            "oracle_text": card.get("oracle_text", ""),
            "price_usd": prices.get("usd", ""),
            "image_normal": image_uris.get("normal", ""),
            "released_at": released_at,
        }

    INDEX_PATH.write_text(json.dumps(index, indent=2), encoding="utf-8")
    print(f"Wrote index: {INDEX_PATH}")


if __name__ == "__main__":
    main()
