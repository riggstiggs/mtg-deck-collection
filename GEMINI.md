# Project Context: Magic: The Gathering Deck Collection

## 1. Project Overview
This project serves as a comprehensive knowledge base and tracker for the user's Magic: The Gathering (MTG) activities. It manages deck lists, strategy guides, upgrade paths, and collection data for both **Paper Magic (Commander/EDH)** and **MTG Arena** (Standard, Historic, Timeless, Brawl).

**Primary Goals:**
*   Organize and refine deck ideas and lists.
*   Track meta changes and deck evolution over time.
*   Plan card crafting (Arena Wildcards) and purchasing (Paper) decisions.
*   Ensure Commander decks adhere to specific power-level constraints (The Bracket System).

**GitHub Repository:** [mtg-deck-collection](https://github.com/chayde/mtg-deck-collection)

## 2. Directory Structure & Key Files

### 📂 Root Directory
*   **`README.md`**: The primary index of the project, listing all active and planned decks.
*   **`history.md`**: A chronological log of conversations, major decisions, and match history. **Always check this first** to understand recent choices.
*   **`COMMANDER_DECKBUILDING_RULES.md`**: Source of truth for power-level compliance and the "Game Changers" list.
*   **`COMMANDER_TEMPLATE.md`**: Standard card category ratios (The "New Era" Template) for building consistent decks.
*   **`GEMINI.md`**: This file. Context for AI agents.
*   **`collection.csv`**: Database of the user's digital/physical card collection.

### 📂 `/commander_decks`
*   **`/Owned`**: Decks the user physically owns (e.g., `TheHive-Slivers.md`, `KarametraAngels`).
*   **`/Planning`**: Decks under development (e.g., `OmnathLocusOfCreation`, `ThaliaGitrog`).
*   **`/PreCons`**: Original and modified Preconstructed deck lists.

### 📂 `/arena_decks`
*   **`dimir_midrange.md`**: Current primary Standard deck.
*   **`*.md`**: Archetypes like `GlarbBrawl`, `JeskaiArtifacts`, `Omniscience`.

## 3. Usage & Maintenance Guidelines

### Reading & Creating Deck Lists
*   **Format:** Deck files are Markdown (`.md`).
*   **Structure:** Typically include strategy, categorized card lists (Core, Payoffs, Interaction), Mana Base, and a **Moxfield Import** section for easy copying.
*   **Versions:** Track **"Budget" vs "Premium"** versions to assist with financial/wildcard planning.
*   **GFM Line Breaks:** **CRITICAL:** In the "Plain Text Copy/Paste" section, add **two spaces** at the end of every line (including "COMMANDER:", "DECK:", and every card name) to ensure GitHub renders them as individual lines instead of a single paragraph.

### Maintenance Conventions
*   **GitHub Synchronization:** **CRITICAL:** All changes made to this project must be committed and pushed to the GitHub repository to maintain synchronization across environments.
*   **Deck Changelog:** Maintain a `## Deck Changelog` section in every deck file. Document all card changes (In/Out) with a date and a brief reason. Format must match `commander_decks/Planning/OmnathLocusOfCreation/omnath_locus_of_creation_landfall.md`.
*   **Bracket Compliance:** When modifying Commander decks, verify the "Game Changers" count against `COMMANDER_DECKBUILDING_RULES.md`.
*   **History Updates:** Summarize significant decisions or deck overhauls in `history.md`.

## 4. User Preferences & Context

### MTG Preferences
*   **Playstyle:** Enjoys complex interactions (Cascade, Landfall), Tribal strategies (Slivers), and Midrange/Control (Dimir).
*   **Dislikes:** Linear Aggro (e.g., Mono-Red).
*   **Resources:** "Wildcard Rich" on Arena. Has a **paid subscription to Untapped.gg** for gathering decklists and meta information.
