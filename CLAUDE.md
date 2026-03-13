# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

This is a documentation-only repository (no build system, no tests). It manages Magic: The Gathering deck lists, strategy guides, upgrade paths, and collection data for both Paper Commander/EDH and MTG Arena. The "code" is Markdown files and one CSV.

## Repository Structure

```
/
├── COMMANDER_DECKBUILDING_RULES.md  ← Source of truth for Brackets 1-5 and Game Changers list
├── COMMANDER_TEMPLATE.md            ← "New Era" card ratios (38 lands, 10 ramp, 12 draw, etc.)
├── DECK_TEMPLATE.md                 ← Structural template for all new deck files
├── GEMINI.md                        ← Full AI context (read this for detailed conventions)
├── history.md                       ← Chronological log of decisions; check before major changes
├── collection.csv                   ← Physical/digital card collection database
├── commander_decks/
│   ├── Owned/       ← Physically built decks (TheHive, Karametra, Sauron, UrDragon, PreCons...)
│   ├── Planning/    ← Decks under development (Omnath, ThaliaGitrog, Yidris, Zangief...)
│   └── External/    ← Decks built for others (John: Rafiq, Christina: Alela, Zimone)
└── arena_decks/     ← MTG Arena decks (DimirMidrange, FirstSliver variants, Omniscience...)
```

## Key Conventions

### Deck File Format (MANDATORY)
- Always use `DECK_TEMPLATE.md` as the structural foundation for new deck files.
- Every deck file must include: strategy overview, categorized card explanations, upgrade roadmap, `## Deck Changelog`, and a **Plain Text Copy/Paste** (Moxfield Import) section.
- Track **Budget vs. Premium** versions of decks to assist with financial/wildcard planning.
- In the "Plain Text Copy/Paste" section, every line must end with **two spaces** for GitHub GFM line breaks.
- Companion `moxfield_import.txt` files use raw text with no trailing spaces — these are for direct paste into Moxfield's Bulk Edit tool.
- **Whenever the main deck file is updated, sync `moxfield_import.txt` to match.**

### Bracket Compliance
- When modifying any Commander deck, verify "Game Changers" card count against `COMMANDER_DECKBUILDING_RULES.md`.
  - Bracket 1-2: Zero Game Changers
  - Bracket 3: Up to three Game Changers
  - Bracket 4-5: No restrictions

### Changelog Format
Every deck change must be logged in `## Deck Changelog` with:
```
- **[YYYY-MM-DD]:** [Summary]
    - **In:** [Card Names]
    - **Out:** [Card Names]
    - **Reason:** [Brief logic]
```

### Order Tracking
Active physical card orders are tracked in `order_tracking.md` within the deck's directory. Use `- [ ]` for pending items and `- [x]` for received items.

### Goldfish Validation
After major deck overhauls, a 5-game "Honest Goldfish" simulation is required using `scripts/goldfish_shuffler.py`. Log results in `GOLDFISH_LOG.md` in the deck's directory. See `COMMANDER_TEMPLATE.md` for the full protocol. When running a simulation, provide **Scryfall links or Markdown card renders for every card drawn or played** so the user can visually track the game state.

### History Log
Summarize significant decisions, deck promotions (Planning → Owned), or overhauls in `history.md` under the appropriate month header.

### GitHub Sync
All changes must be committed and pushed to keep environments synchronized.

## User Preferences

- **Playstyle:** Complex interactions (Cascade, Landfall), Tribal (Slivers), Midrange/Control (Dimir). Dislikes linear aggro.
- **Arena:** Wildcard-rich; has a paid Untapped.gg subscription for meta data and decklists.
- **Paper:** Tracks Budget vs. Premium versions; actively acquires cards via TCGPlayer/similar marketplaces.
