#!/usr/bin/env python3
"""Validate a deck config JSON before building the CSV.

Usage:
    python3 ./scripts/validate_deck_config.py <config.json> [--import-csv <scryfall_export.csv>]

Checks:
    1. Active card count == 100
    2. Category minimums met (lands 38, ramp 10, card_advantage 12, interaction 10, wrath 2)
    3. No duplicate entries in category lists
    4. All cut_reasons cards exist in decklist
    5. All category list cards exist in decklist (and are not cut)
    6. If --import-csv provided: warns about original deck cards missing from have_physical
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

CATEGORY_MINIMUMS = {
    "ramp": 10,
    "card_advantage": 12,
    "interaction": 10,
    "wrath": 2,
}

LAND_MINIMUM = 38


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a deck config JSON.")
    parser.add_argument("config", help="Path to deck config JSON")
    parser.add_argument("--import-csv", help="Original Scryfall export CSV to check have_physical")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}")
        sys.exit(1)

    config = json.loads(config_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    warnings: list[str] = []

    decklist = config.get("decklist", [])
    cut_reasons = config.get("cut_reasons", {})
    have_physical = set(config.get("have_physical", []))
    cuts = set(cut_reasons.keys())

    # Build active card set and counts
    all_names = {e["name"] for e in decklist}
    active_cards = {e["name"]: e["count"] for e in decklist if e["name"] not in cuts}
    active_total = sum(active_cards.values())

    # 1. Card count
    if active_total != 100:
        errors.append(f"Active card count is {active_total}, expected 100")

    # 2. cut_reasons cards exist in decklist
    for name in cuts:
        if name not in all_names:
            errors.append(f"cut_reasons references '{name}' which is not in decklist")

    # 3. Duplicate entries in category lists
    for cat in ["ramp", "card_advantage", "interaction", "wrath", "lands"]:
        entries = config.get(cat, [])
        dupes = [name for name, count in Counter(entries).items() if count > 1]
        if dupes:
            errors.append(f"Duplicate entries in '{cat}': {dupes}")

    # 4. Category list cards exist in decklist and are not cut
    for cat in ["ramp", "card_advantage", "interaction", "wrath"]:
        for name in config.get(cat, []):
            if name not in all_names:
                errors.append(f"'{cat}' references '{name}' which is not in decklist")
            elif name in cuts:
                warnings.append(f"'{cat}' references '{name}' which is marked as cut — remove from category list")

    # 5. Category minimums
    for cat, minimum in CATEGORY_MINIMUMS.items():
        count = sum(1 for name in config.get(cat, []) if name in active_cards)
        if count < minimum:
            errors.append(f"'{cat}' has {count} active cards, minimum is {minimum}")

    # 6. Land count
    land_names = set(config.get("lands", []))
    land_total = sum(count for name, count in active_cards.items() if name in land_names)
    if land_total < LAND_MINIMUM:
        errors.append(f"Land count is {land_total}, minimum is {LAND_MINIMUM}")

    # 7. have_physical check against import CSV
    if args.import_csv:
        import_path = Path(args.import_csv)
        if not import_path.exists():
            warnings.append(f"Import CSV not found: {import_path}")
        else:
            with open(import_path, newline="", encoding="utf-8") as f:
                orig_names = {row["name"] for row in csv.DictReader(f)}
            missing_physical = orig_names - have_physical
            if missing_physical:
                errors.append(
                    f"{len(missing_physical)} original deck cards not in have_physical: "
                    + ", ".join(sorted(missing_physical)[:5])
                    + (" ..." if len(missing_physical) > 5 else "")
                )

    # Report
    print(f"Config: {config_path}")
    print(f"Active cards: {active_total}/100")
    print(f"Cut cards: {len(cuts)}")
    print()

    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"  ⚠  {w}")
        print()

    if errors:
        print("ERRORS:")
        for e in errors:
            print(f"  ✗  {e}")
        print()
        print(f"Validation FAILED — {len(errors)} error(s), {len(warnings)} warning(s)")
        sys.exit(1)
    else:
        print(f"Validation PASSED — {len(warnings)} warning(s)")


if __name__ == "__main__":
    main()
