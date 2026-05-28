#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def load_decklist(csv_path: Path) -> list[dict[str, int]]:
    decklist: list[dict[str, int]] = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise SystemExit("CSV header missing.")
        for row in reader:
            name = (row.get("name") or "").strip()
            if not name:
                continue
            count_str = (row.get("count") or "1").strip()
            try:
                count = int(count_str)
            except ValueError:
                raise SystemExit(f"Invalid count '{count_str}' for {name}.")
            decklist.append({"name": name, "count": count})
    if not decklist:
        raise SystemExit("No cards found in CSV.")
    return decklist


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a deck config JSON from a Scryfall CSV export."
    )
    parser.add_argument("csv_path", help="Scryfall deck CSV path")
    parser.add_argument("output_path", help="Output JSON config path")
    args = parser.parse_args()

    csv_path = Path(args.csv_path)
    output_path = Path(args.output_path)

    decklist = load_decklist(csv_path)
    config = {
        "decklist": decklist,
        "adds": [],
        "cut_reasons": {},
        "lands": [],
        "ramp": [],
        "card_advantage": [],
        "interaction": [],
        "wrath": [],
        "have_physical": [],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"Wrote config JSON: {output_path}")


if __name__ == "__main__":
    main()
