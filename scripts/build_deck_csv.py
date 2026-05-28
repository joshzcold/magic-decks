#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote


@dataclass(frozen=True)
class DeckConfig:
    decklist: list[dict[str, Any]]
    adds: list[str]
    cut_reasons: dict[str, str]
    lands: list[str]
    ramp: list[str]
    card_advantage: list[str]
    interaction: list[str]
    wrath: list[str]
    have_physical: list[str]


def load_config(path: Path) -> DeckConfig:
    print(f"Loading config: {path}", flush=True)
    data = json.loads(path.read_text(encoding="utf-8"))
    return DeckConfig(
        decklist=list(data.get("decklist", [])),
        adds=list(data.get("adds", [])),
        cut_reasons=dict(data.get("cut_reasons", {})),
        lands=list(data.get("lands", [])),
        ramp=list(data.get("ramp", [])),
        card_advantage=list(data.get("card_advantage", [])),
        interaction=list(data.get("interaction", [])),
        wrath=list(data.get("wrath", [])),
        have_physical=list(data.get("have_physical", [])),
    )


def parse_decklist_config(decklist: list[dict[str, Any]]) -> dict[str, int]:
    print(f"Parsing decklist entries: {len(decklist)}", flush=True)
    cards: dict[str, int] = {}
    for entry in decklist:
        name = entry.get("name")
        count = entry.get("count", 1)
        if not name:
            raise SystemExit("Decklist entries must include a name.")
        cards[name] = cards.get(name, 0) + int(count)
    return cards


def image_formula(name: str) -> str:
    return f'=IMAGE("https://api.scryfall.com/cards/named?exact={quote(name)}&format=image&version=normal")'


def deck_rule_for(
    name: str,
    lands: set[str],
    ramp: set[str],
    card_advantage: set[str],
    interaction: set[str],
    wrath: set[str],
) -> str:
    if name in lands:
        return "Lands"
    if name in wrath:
        return "Wrath"
    if name in interaction:
        return "Interaction"
    if name in card_advantage:
        return "Card Advantage"
    if name in ramp:
        return "Ramp"
    return "On Theme"


def iter_rows(
    cards: dict[str, int],
    cut_reasons: dict[str, str],
    lands: set[str],
    ramp: set[str],
    card_advantage: set[str],
    interaction: set[str],
    wrath: set[str],
    have_physical: set[str],
    index: dict[str, dict[str, Any]],
) -> Iterable[list[Any]]:
    names = sorted(cards.keys())
    total = len(names)

    for idx, name in enumerate(names, start=1):
        qty = cards[name]
        print(f"Processing {idx}/{total}: {name}", flush=True)
        card = index.get(name)
        if not card:
            raise SystemExit(f"Card not found in index: {name}")

        rarity = card.get("rarity", "")
        set_code = card.get("set", "")
        cmc = card.get("cmc", "")
        oracle_text = card.get("oracle_text", "")
        price = card.get("price_usd")
        price_str = f"${price}" if price else ""

        yield [
            qty,
            name,
            "true" if name in have_physical else "false",
            "true" if name in cut_reasons else "false",
            cut_reasons.get(name, ""),
            deck_rule_for(name, lands, ramp, card_advantage, interaction, wrath),
            rarity.title() if rarity else "",
            set_code.upper() if set_code else "",
            int(cmc) if isinstance(cmc, (int, float)) and cmc == int(cmc) else cmc,
            image_formula(name),
            price_str,
            oracle_text.replace("\n", " "),
        ]


def load_index(path: Path) -> dict[str, dict[str, Any]]:
    print(f"Loading index: {path}", flush=True)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("Index file must be a JSON object.")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Build deck CSV using Scryfall data.")
    parser.add_argument("csv_path", help="Output CSV path")
    parser.add_argument("config_path", help="JSON config file")
    parser.add_argument(
        "--index",
        default="data/scryfall/default-cards-index.json",
        help="Path to the local Scryfall card index JSON",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv_path)
    config_path = Path(args.config_path)
    index_path = Path(args.index)

    if not csv_path.is_absolute():
        csv_path = Path("decks") / csv_path
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    config = load_config(config_path)
    if not config.decklist:
        raise SystemExit("Config must include 'decklist'.")
    cards = parse_decklist_config(config.decklist)

    print(f"Decklist unique cards: {len(cards)}", flush=True)

    index = load_index(index_path)

    normalized_adds = list(config.adds)
    normalized_cut_reasons = dict(config.cut_reasons)
    normalized_lands = set(config.lands)
    normalized_ramp = set(config.ramp)
    normalized_card_advantage = set(config.card_advantage)
    normalized_interaction = set(config.interaction)
    normalized_wrath = set(config.wrath)
    normalized_have_physical = set(config.have_physical)

    normalized_cards = dict(cards)
    for name in normalized_adds:
        print(f"Adding card: {name}", flush=True)
        normalized_cards[name] = normalized_cards.get(name, 0) + 1

    header = [
        "Quantity",
        "Card Title",
        "Have Physical Copy",
        "Cut",
        "Cut Reason",
        "Deck Rule",
        "Rarity",
        "MTG Edition",
        "Mana Value",
        "Image",
        "Price",
        "Rule Text",
    ]

    print(f"Writing CSV: {csv_path}", flush=True)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        for row in iter_rows(
            normalized_cards,
            normalized_cut_reasons,
            normalized_lands,
            normalized_ramp,
            normalized_card_advantage,
            normalized_interaction,
            normalized_wrath,
            normalized_have_physical,
            index,
        ):
            writer.writerow(row)

    print(f"Wrote CSV to {csv_path}")


if __name__ == "__main__":
    main()
