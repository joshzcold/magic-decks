# Magic The Gathering Deck Building

Here is my guide for building a good magic the gathering commander deck.

When building or improving a deck we should use the local Scryfall bulk cache to look up card data and the Scryfall search tools for additions.

## Import

When given a url like this `https://scryfall.com/@joshzcold/decks/0f887feb-e05f-4d87-8ebc-45fd0e3d799b`

export as a full csv so we can gather as much information needed when creating our csv as an export.

```bash
python3 ./scripts/fetch_deck_csv.py "https://scryfall.com/@joshzcold/decks/<deck-id>" /tmp/<deckname>.csv
```

Assume that cards from the list are cards we have physical ownership of.

## Validation

Always validate the config before building the CSV:

```bash
python3 ./scripts/validate_deck_config.py <config.json> --import-csv /tmp/<deckname>.csv
```

This checks:
- Active card count == 100
- Category minimums met (lands 38, ramp 10, card_advantage 12, interaction 10, wrath 2)
- No duplicate entries in category lists
- All cut_reasons and category list cards exist in decklist
- All original deck cards are in `have_physical`

Fix all errors before proceeding to build.

## CSV Builder Script

Use `python3 ./scripts/build_deck_csv.py` to generate a deck CSV with Scryfall data.

Before building a deck CSV, ensure the bulk data cache and index are up to date:

```bash
python3 ./scripts/update_bulk_cache.py
python3 ./scripts/build_bulk_index.py
```

If you already downloaded a bulk JSON, register it locally:

```bash
python3 ./scripts/update_bulk_cache.py --local /path/to/default-cards.json
```

This script assumes the decklist comes from Scryfall exports (no manual name normalization).

Example usage:

```bash
python3 ./scripts/build_deck_csv.py ./jasmine_boreal_rebuild_05_25_2026.csv ./jasmine_boreal_rebuild_config.json
```

Deck exports default to `decks/` when you use relative paths.

Config JSON fields:

- `decklist`: list of objects with `name` and `count` fields
- `adds`: list of cards to add
- `cut_reasons`: mapping of card name to cut reason
- `lands`, `ramp`, `card_advantage`, `interaction`, `wrath`: card lists for deck rules
- `have_physical`: list of cards already owned

## Price

We generally want to keep below 1$ however for cards that change the game we can extend price.


| Price | Rule |
| --- | --- |
|<=1$ | General cards that build up the majority of the deck|
|>=1$ | Should provide interesting value over normal card draw, ramp or interaction|
|>5$| Should be super valuable to a game. Can win the game in the right scenario|


When it comes to expensive cards in a list  you can ask if I already own this in person.
If not you can try to recommend away from an expensive cards, otherwise assume I already have it and might want to use it as a powerful card.

## Deck Categories

### On Theme Cards

These are cards that fit the overall theme of the commander deck.
Can be creatures, enchantments, artifacts that fit the overall goal of the deck.

#### Mana Values for Cards

Use this reference when choosing to keep or cut on-theme cards.


| Mana Value | Requirement |
| --- | --- |
| >=6 | Must dramatically change the game or provide an insurmountable advantage within one turn |
| 5 | Must provide a dramatic advantage the turn it comes down or will run away in game within 2 turns if not countered. |
| 4 | Must be powerful pieces that push your deck into overdrive or set you up to have an incredibly impactful next few turns |
| 1-3 | Need to be useful engine pieces that provide values turn after turn as the game progresses |


### Card Advantage

- Cards that get the user more cards.

- Needs to be a net positive and should not give positive outcomes to opponents

- Minimum x12 cards

- Should have synergy with the rest of the deck. Be on theme.

### Ramp

- Minimum x10 pieces of normal ramp

- Find x2 pieces of "explosive" ramp. These are cards that be gather up a ton of mana in a short burst for some cost.

### Lands

- Minimum x38 pieces of Land

- Ratio of Basic to Non-Basic Lands depends on the commander.

If the commander has more color variety (greater than 2 colors not counting colorless) then we might want more non-basic.

For a 2 color commander I like to go 13 basic + 13 basic + 13 non-basic

### Interaction

- These are cards that fit:
    - Removal: removes opponent's cards
    - Interruption: stops an opponent's move/task
    - Protection: protects my creatures from opponents.
    - Wrath: wipes the board

- Have x10 pieces of interaction (non wrath)

- Have x2 pieces of wrath

## Making Suggestions/Cuts

When finding replaces for cards that are in-effective always provide a table of cards that are being cut and for what reason. Display the replacement cards next to the cut card and include a reason for why we need the new card.

## Config Bootstrap Script

If you only have a Scryfall CSV export, generate a starter config JSON:

```bash
python3 ./scripts/build_config_from_csv.py /tmp/<deckname>.csv ./<deckname>_config.json
```

## Export

We prefer a Table/CSV that matches these headers. We use google sheets for import.

Required headers:

```csv
Quantity,Card Title,Have Physical Copy,Cut,Cut Reason,Deck Rule,Rarity,MTG Edition,Mana Value,Image,Price,Rule Text
```

Example:

```csv
Quantity,Card Title,Have Physical Copy,Cut,Cut Reason,Deck Rule,Rarity,MTG Edition,Mana Value,Image,Price,Rule Text
1,Ankle Biter,true,false,,On Theme,Common,OTJ,3,=IMAGE("https://api.scryfall.com/cards/named?exact=Ankle%20Biter&format=image&version=normal"),0.58$,<oracle text>
1,Old Cut Card,,true,"Trimmed low-impact equipment for draw engines.",Interaction,Uncommon,DMU,4,=IMAGE("https://api.scryfall.com/cards/named?exact=Old%20Cut%20Card&format=image&version=normal"),0.36$,<oracle text>
...

```

For Google Sheets generate an XLSX using `uv run --script ./scripts/export_to_sheets.py` (run it directly so the `uv run --script` shebang installs dependencies). This also writes a `.txt` file for Scryfall import in the format `<quantity> <name>`.

**Important:** The script automatically prepends `decks/` to the xlsx and txt output paths. Pass only the filename (not the full path) for those arguments:

```bash
uv run --script ./scripts/export_to_sheets.py decks/<deckname>.csv <deckname>.xlsx <deckname>.txt
```
