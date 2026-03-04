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

## 🔄 Maintenance & Synchronization

**CRITICAL:** All changes made to this project must be committed and pushed to the [GitHub repository](https://github.com/chayde/mtg-deck-collection) to maintain synchronization across environments.

When updating decks, ensure:
1.  **Changelog is updated** with the date and reason for changes.
2.  **Bracket compliance** is verified against the ruleset.
3.  **Moxfield Import** sections are updated for easy export.