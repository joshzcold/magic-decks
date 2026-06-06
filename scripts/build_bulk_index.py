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
        # Skip premium/specialty sets — prices are inflated and unrepresentative
        if card.get("set_type") in {"secret_lair", "memorabilia", "treasure_chest", "box"}:
            continue

        prices = card.get("prices") if isinstance(card.get("prices"), dict) else {}
        image_uris = card.get("image_uris") if isinstance(card.get("image_uris"), dict) else {}

        # Prefer regular printings over premium variants (showcase/borderless/extendedart
        # cost significantly more and don't represent market price for gameplay copies)
        PREMIUM_FRAMES = {"showcase", "extendedart", "inverted"}
        frame_effects = set(card.get("frame_effects") or [])
        is_premium = bool(frame_effects & PREMIUM_FRAMES) or card.get("border_color") == "borderless"

        released_at = card.get("released_at") or ""
        new_price = prices.get("usd")
        current = index.get(name)
        if current:
            current_price = current.get("price_usd")
            current_premium = current.get("is_premium", False)
            # Never replace a regular printing with a premium one
            if not current_premium and is_premium:
                continue
            # Always prefer a regular printing over a premium one
            if current_premium and not is_premium:
                pass  # fall through to replace
            # Don't replace a priced entry with an unpriced one
            elif current_price and not new_price:
                continue
            # Always prefer a priced entry over an unpriced one, regardless of date
            elif not current_price and new_price:
                pass  # fall through to replace
            elif current.get("released_at", "") >= released_at:
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
            "is_premium": is_premium,
        }

    INDEX_PATH.write_text(json.dumps(index, indent=2), encoding="utf-8")
    print(f"Wrote index: {INDEX_PATH}")


if __name__ == "__main__":
    main()
