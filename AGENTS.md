# Magic The Gathering Deck Building

Here is my guide for building a good magic the gathering commander deck.

When building or improving a deck we should use the scryfall mcp server to search and get details on cards

## Price

We generally want to keep below 1$ however for cards that change the game we can extend price.


| Price | Rule |
| --- | --- |
|<=1$ | General cards that build up the majority of the deck|
|>=1$ | Should provide intresting value over normal card draw, ramp or interaction|
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
| 5 | Must provide a dramatic afvantage the turn it comes down or will run away in game withint 2 turns if not countered. |
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
    - Innteruption: stops an opponent's move/task
    - Protection: protects my creatures from opponents.
    - Wrath: wipes the board

- Have x10 pieces of interaction (non wrath)

- Have x2 pieces of wrath

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

For Google Sheets generate an XLSX using `./scripts/export_to_sheets.py` (run it directly so the `uv run --script` shebang installs dependencies).

## CSV Builder Script

Use `./scripts/build_deck_csv.py` to generate a deck CSV with Scryfall data.

Example usage:

```bash
python ./scripts/build_deck_csv.py ./jasmine_boreal_rebuild_05_25_2026.csv ./jasmine_boreal_rebuild_config.json
```

Config JSON fields:

- `decklist`: list of objects with `name` and `count` fields
- `adds`: list of cards to add
- `cut_reasons`: mapping of card name to cut reason
- `lands`, `ramp`, `card_advantage`, `interaction`, `wrath`: card lists for deck rules
- `have_physical`: list of cards already owned
