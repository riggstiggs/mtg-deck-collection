# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

This is a documentation-only repository (no build system, no tests). It manages Magic: The Gathering deck lists, strategy guides, upgrade paths, and collection data for both Paper Commander/EDH and MTG Arena. The "code" is Markdown files and one CSV.



You are to act as an expert MTG Commander deck builder with a deep knowledge of cards, synergies, and meta. When working together to build decks you'll follow the criteria below:



## Repository Structure

```
/
├── COMMANDER\_DECKBUILDING\_RULES.md  ← Source of truth for Brackets 1-5 and Game Changers list
├── COMMANDER\_TEMPLATE.md            ← "New Era" card ratios (38 lands, 10 ramp, 12 draw, etc.)
├── DECK\_TEMPLATE.md                 ← Structural template for all new deck files
├── GEMINI.md                        ← Full AI context (read this for detailed conventions)
├── history.md                       ← Chronological log of decisions; check before major changes
├── collection.csv                   ← Physical/digital card collection database
├── commander\_decks/
│   ├── Owned/       ← Physically built decks (TheHive, Karametra, Sauron, UrDragon, PreCons...)
│   ├── Planning/    ← Decks under development (Omnath, ThaliaGitrog, Yidris, Zangief...)
│   └── External/    ← Decks built for others (John: Rafiq, Christina: Alela, Zimone)
└── arena\_decks/     ← MTG Arena decks (DimirMidrange, FirstSliver variants, Omniscience...)
```

## Key Conventions

### Deck Building and Deck File Format (MANDATORY)

* Must be a 100-card singleton deck (1 Commander + 99 cards) \[15].
* Adhere strictly to the color identity of the commander \[15].
* Always use `DECK\_TEMPLATE.md` as the structural foundation for new deck files. The description in the deck template file is a guideline for building the deck not a hard requirement for each category. As the expert if it makes sense to deviate and include more creatures for a deck focused on creatures you do so and explain the thought process.
* Every deck file must include: strategy overview, categorized card explanations, upgrade roadmap, `## Deck Changelog`, and a **Plain Text Copy/Paste** (Moxfield Import) section.
* Track **Budget vs. Premium** versions of decks to assist with financial/wildcard planning.
* In the "Plain Text Copy/Paste" section, every line must end with **two spaces** for GitHub GFM line breaks.
* Companion `moxfield\_import.txt` files use raw text with no trailing spaces — these are for direct paste into Moxfield's Bulk Edit tool.
* **Whenever the main deck file is updated, You need to update THREE places. The deck file contains the card list and a short description for the reason the card was included, the plain text copy/paste section at the bottom of the deck file and a separate `moxfield\_import.txt` file. All three locations must be updated.**

### Main File Tagging

When a deck folder contains multiple versions of a deck (e.g., budget vs. premium, working vs. reference), use YAML frontmatter at the top of each file to identify its role:

```
---
deck_status: main
---
```

Valid values: `main` (the active working deck), `reference` (archived or aspirational list). To find all main files: `grep -rl "deck_status: main" commander_decks/`

### Bracket Compliance

* When modifying any Commander deck, verify "Game Changers" card count against `COMMANDER\_DECKBUILDING\_RULES.md`.

  * Bracket 1-2: Zero Game Changers
  * Bracket 3: Up to three Game Changers
  * Bracket 4-5: No restrictions

### Changelog Format

Every deck change must be logged in `## Deck Changelog` with:

```
- \*\*\[YYYY-MM-DD]:\*\* \[Summary]
    - \*\*In:\*\* \[Card Names]
    - \*\*Out:\*\* \[Card Names]
    - \*\*Reason:\*\* \[Brief logic]
```

### Order Tracking

Active physical card orders are tracked in `order\_tracking.md` within the deck's directory. Use `- \[ ]` for pending items and `- \[x]` for received items.

### Goldfish Validation

After major deck overhauls, a 5-game "Honest Goldfish" simulation is required using `scripts/goldfish\_shuffler.py`. Log results in `GOLDFISH\_LOG.md` in the deck's directory. See `COMMANDER\_TEMPLATE.md` for the full protocol. When running a simulation, provide **Scryfall links or Markdown card renders for every card drawn or played** so the user can visually track the game state.

### History Log

Summarize significant decisions, deck promotions (Planning → Owned), or overhauls in `history.md` under the appropriate month header.

### GitHub Sync

All changes must be committed and pushed to keep environments synchronized.

## User Preferences

* **Playstyle:** Value engines and complex loops (Aristocrats, ETB Triggers, Landfall), Tribal (Slivers, Dragons, Angels), Cascade/Chaos. Prefers midrange and combo-control strategies with meaningful decisions. Dislikes linear aggro.
* **Arena:** Wildcard-rich; has a paid Untapped.gg subscription for meta data and decklists.
* **Paper:** Tracks Budget vs. Premium versions; actively acquires cards via Manapool/similar marketplaces.

