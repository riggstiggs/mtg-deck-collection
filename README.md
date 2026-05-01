# Magic: The Gathering Deck Project

This repository manages deck lists, analysis, and upgrade plans for both Paper Magic (Commander/EDH) and MTG Arena. It tracks deck evolution, power level compliance, and collection data.

## 🛠️ Key Project Features

*   **Commander Bracket System:** All Commander decks are categorized into 5 Brackets (Exhibition to cEDH) to ensure balanced gameplay.
*   **Game Changers Tracking:** Monitoring high-impact staples as defined in `COMMANDER_DECKBUILDING_RULES.md`.
*   **Deck Changelogs:** Every deck maintains a chronological history of card changes and the reasoning behind them.
*   **Arena Optimization:** Leveraging Untapped.gg data and Wildcard management to maintain Tier 1 performance.

---

## 📂 Project Structure

### 📜 Root Files
*   **`COMMANDER_DECKBUILDING_RULES.md`**: The source of truth for power level brackets and "Game Changers".
*   **`GEMINI.md`**: Context and instructions for AI agents.
*   **`history.md`**: Chronological log of major decisions and match history.
*   **`collection.csv`**: Database of card collection data.

### 🛡️ `/commander_decks`
Organized by ownership status and project type.

#### 📁 `/Owned`
Decks physically built and ready for play.
*   **The Hive (Slivers):** 5-Color tribal (The First Sliver).
*   **Karametra Angels:** Selesnya ramp and tribal synergy.
*   **Captain America:** Jeskai Equipment Voltron.
*   **Meren Reanimator:** Golgari graveyard value.
*   **Sauron Midrange:** Grixis Amass and Ring Temptation.
*   **The Ur-Dragon (Kibler's Flight):** 5-Color Dragon Tribal. Bracket 2 Mid-Budget version.
*   **Preconstructed Decks:** Original and modified PreCons (Ashling, Bello, Disa, Ulalek, etc.).

#### 📁 `/External`
Completed decks built for family and friends.
*   **John:**
    *   **Rafiq Voltron:** Bant Exalted/Commander damage.
*   **Christina:**
    *   **Alela Faerie Rogues:** Dimir "Flash" shell (Cunning Conqueror).

#### 📁 `/Planning`
Decks under development, research, or being optimized.
*   **Potential Future Commanders:** A list of ideas for **Jamie** (Wife) and **Mark**.
*   **Omnath Landfall:** 4-Color value engine (Locus of Creation).
*   **Thalia & Gitrog:** Abzan Landfall & Hatebears.
*   **Yidris Cascade:** 4-Color "Value Cascade".
*   **Henzie Blitz:** Jund sacrifice and aggro.
*   **Ulamog Ramp:** Colorless high-power ramp.
*   **Zimone Engine:** Simic Landfall for **Christina**.

### 🎮 `/arena_decks`
Optimized lists for MTG Arena formats (Standard, Brawl, Timeless).
*   **Dimir Midrange:** Current Tier 1 Standard engine.
*   **The First Sliver:** Various Brawl and Combo builds.
*   **Glarb Brawl:** Sultai value.
*   **Omniscience Combo:** Simic and Temur variations.
*   **Golgari Foundations & Jeskai Artifacts:** Synergy-focused builds.

---

## 🤖 AI-Assisted Deck Building: Card Research Workflow

### Background

Deck building sessions in this project are collaborative — Mark describes what he needs, and Claude researches and recommends cards. The original workflow relied on Claude's training knowledge to suggest card names, then verified them afterward using `scripts/scryfall_lookup.py`. This works but has one structural weakness: Claude can occasionally hallucinate a card name that sounds plausible but doesn't exist, and verification only catches it after the suggestion has already been made.

### The ID-Based Recommendation Workflow (Added 2026-05-01)

A new script — `scripts/scryfall_recommend.py` — was added as an **optional, experimental** alternative for the card discovery phase. It was inspired by a technique used in the [deckbuilder-rag](https://github.com/Rgaliant/deckbuilder-rag) project, adapted for this repo's human-in-the-loop, cross-machine workflow.

**The core idea:** Instead of asking Claude to name cards from memory, Claude runs a Scryfall search first, which returns a numbered list of verified real cards. Claude then selects by ID number only. A second resolve step confirms every chosen ID maps to an actual card before anything is added to a deck. Hallucination becomes structurally impossible — Claude can only pick from what Scryfall returned.

**The workflow from Mark's perspective is unchanged.** You describe what you need in plain English ("find me ramp cards for Grolnok under $2"). Claude writes the Scryfall query, runs the search, picks IDs, resolves them, and presents confirmed cards with reasoning. You never touch the terminal or write a query.

### How It Works — Step by Step

```
You:   "Find me self-mill creatures for Grolnok, budget, green or blue"

Claude runs:
  python3 scripts/scryfall_recommend.py \
    --search "o:mill id<=UBG commander:legal t:creature cmc<=4" \
    --label "Grolnok self-mill creatures" \
    --limit 30

  → Scryfall returns up to 30 real cards
  → Each gets a temp ID: R001, R002, R003...
  → Session saved to cache/recommend_session.json

Claude reads the list, picks the best fits:
  "I'd go with R004 (Aftermath Analyst), R016 (Blanchwood Prowler),
   R018 (Blossoming Tortoise) — here's why for each..."

Claude runs:
  python3 scripts/scryfall_recommend.py --resolve R004 R016 R018

  → Full card details printed and confirmed
  → Any invalid ID flagged as [WARNING] — hallucination guard fires

Claude presents confirmed cards, you approve, Triple Update proceeds.
```

### Session File

Each search overwrites `cache/recommend_session.json` with the current candidate list. Like all other cache files, this is committed to the repo and shared across machines — `git pull` on a different computer restores the session. Resolve IDs from a search before running a new one if you need results from both.

### Relationship to Existing Scripts

| Script | Role | Status |
|--------|------|--------|
| `scripts/scryfall_lookup.py` | Named lookups, oracle text verification, batch lookups | **Unchanged — still primary** |
| `scripts/scryfall_recommend.py` | Card discovery via ID-based search | **New — optional experiment** |
| `scripts/manapool_price_deck.py` | Deck pricing via Manapool | **Unchanged** |

`scryfall_recommend.py` imports `scryfall_lookup.py` as a library. It adds no new API dependencies and uses the same rate limiting, caching, and retry logic.

### How to Revert to the Old Workflow

If the ID-based workflow turns out to be slower, more cumbersome, or less useful than the original approach, reverting is simple — nothing in the old workflow was changed:

1. **Stop using `scryfall_recommend.py`** — just don't run it. `scryfall_lookup.py` and all existing scripts are completely untouched.
2. **Tell Claude to go back to the old approach** — say "stop using the recommend script, just look up cards the old way." Claude will revert to suggesting cards from training knowledge and verifying with `scryfall_lookup.py` afterward.
3. **Optionally remove the script** — delete `scripts/scryfall_recommend.py` and `cache/recommend_session.json`, and remove the entries added to `CLAUDE.md` and `API_REFERENCE.md` in the "ID-Based Card Recommendation" sections. The rest of both files is unaffected.

No deck files, no Moxfield imports, no goldfish scripts, and no history was changed as part of this addition.

---

## 🔄 Maintenance & Synchronization

**CRITICAL:** All changes made to this project must be committed and pushed to the [GitHub repository](https://github.com/chayde/mtg-deck-collection) to maintain synchronization across environments.

When updating decks, ensure:
1.  **Changelog is updated** with the date and reason for changes.
2.  **Bracket compliance** is verified against the ruleset.
3.  **Moxfield Import** sections are updated for easy export.