# Project History: MTG Deck Collection

## 🗓️ March 2026: Expansion & Physical Integration
*Focus on acquiring and building physical decks from planning.*

### 2026-03-09: The Ur-Dragon Physical Build Progress
*   **Physical Integration:** Received a massive shipment (Package #820923 - TinyMaru TCG).
*   **Key Arrivals:** **Breeding Pool**, **Guardian Project**, **Nature's Lore**, **Three Visits**, and a significant chunk of the mana base (Adarkar Wastes, Glacial Fortress, Shivan Reef, etc.) and Dragon staples (**Dragon Tempest**, **Dragonlord Dromoka**, **Hellkite Courser**).
*   **Status:** 6/10 packages received.

### 2026-03-06: The Ur-Dragon Physical Build Progress
*   **Physical Integration:** Received the first of 9 shipments (Package #820926 - The Feisty Goblin).
*   **Key Arrivals:** **Dragonlord Kolaghan**, **Savage Ventmaw**, and 4 essential mana/ramp pieces (Command Tower, Rootbound Crag, Sulfur Falls, Cultivate).
*   **Status:** 1/9 packages received.

### 2026-03-03: Sauron Final Physical Integration (High-Power Mana & Finishers)
*   **Physical Integration:** Successfully received and integrated the **Final 17 cards** from order #210555.
*   **Mana Base:** Fully upgraded to a high-power mana base with **Fetch Lands** (Polluted Delta, Bloodstained Mire, Scalding Tarn), **Bond Lands** (Morphic Pool, Luxury Suite), and **Check/Slow Lands**.
*   **Win-Con Strategy:** Integrated the "Fling/Ignition" win-condition package (**Chandra's Ignition**, **Gravitic Punch**, **Soul's Fire**, **Widespread Brutality**) to turn the massive Orc Army into direct player damage.
*   **Recursion:** Added **Kess, Dissident Mage** to allow double-casting of powerful discard/draw and finisher spells.
*   **Status:** Sauron, the Dark Lord is now **Physically Complete** and optimized for Bracket 3.

### 2026-03-02: The Ur-Dragon Promotion (Owned)
*   **Promotion:** Promoted **The Ur-Dragon (Kibler's Flight)** from Planning to Owned.
*   **Acquisition:** Placed a major order (#223065) for the remaining 99 cards + Commander. 
*   **Tracking:** Established `order_tracking.md` in `commander_decks/Owned/UrDragonKibler/` to monitor 9 separate packages from various sellers.
*   **Status:** 0/9 packages received.

## 🗓️ February 2026: The "New Era" & Grixis Optimization
*Focus shifted to high-power Paper Commander optimization, centering on the "New Era" template (38 lands, high-impact synergy).*

### 2026-02-28: Kibler's Ur-Dragon Planning (The Fair Flight)
*   **New Project:** Started planning for **The Ur-Dragon** based on Brian Kibler's optimized list.
*   **Strategy Pivot:** Created a "Fair" Bracket 2 version of the deck. Replaced the $3,000+ mana base (ABUR Duals/Fetches) with a robust but budget-friendly suite of Check, Pain, and Tri-lands.
*   **Optimization:** Executed a "Dragon-First" pivot, increasing creature density to 28. Swapped generic interaction for synergistic Dragons (**Steel Hellkite**, **Dromoka the Eternal**, **Knollspine Dragon**).
*   **Kibler Engine:** Integrated **Morophon, the Boundless** and a high-efficiency ramp package (**Birds of Paradise**, **Bloom Tender**, **Sylvan Caryatid**) to mirror Kibler's consistency in a Bracket 2 environment.
*   **Deliverables:** Created `kibler_urdragon_ideal.dck` for reference and `ur_dragon_bracket2.md` for the active build. Established `moxfield_import.txt` for easy testing.

### 2026-02-28: Zangief Overhaul & Goldfish Protocol
*   **New Project:** Started planning for **Zangief, the Red Cyclone** (Jund Forced-Combat Attrition). Defined the "Siberian Blizzard" strategy using Keyword Soup (Deathtouch/Trample) and Lure effects.
*   **Documentation:** Established the **Goldfish Validation Protocol** in `COMMANDER_TEMPLATE.md`. Mandatory 5-game "Honest" simulation for all new builds to verify mana stability and synergy.
*   **Tooling:** Developed `scripts/goldfish_shuffler.py` to automate deck parsing and timestamp-seeded shuffling for simulations.
*   **Status:** Zangief build completed for Strong Bracket 2. 5-game Goldfish trial passed with high resilience scores.

### 2026-02-28: Marchesa Overhaul (The Iron Throne)
*   **Strategy Shift:** Moved to an "Entry-Insured" model for **Marchesa, the Black Rose**. Replaced combat-dependent Dethrone triggers with passive enablers (**Graft, Undying, Persist**) to ensure creatures are protected the moment they hit the battlefield.
*   **Key Swaps:**
    *   **In:** Vigean Graftmage, Metallic Mimic, Mikaeus the Unhallowed, Iron Apprentice, Murderous Redcap.
    *   **Out:** Sower of Temptation, Dack's Duplicate, Hostage Taker, Drana, Liberator of Malakir, Vindictive Lich.
*   **Outcome:** The deck is now significantly more resilient and independent of life-total management.

### 2026-02-27: Sauron Physical Integration & Win-Con Strategy
*   **Physical Integration:** Successfully integrated the **Discard/Evasion Package** (Lazotep Chancellor, Anger, Bone Miser, Archfiend of Ifnir, Living Death, Whispersilk Cloak, The Black Gate, Rogue's Passage).
*   **Maintenance:** Removed **Sedraxis Alchemist** and **Glóin, Dwarf Emissary** for 1x Swamp and 1x Island to hit the 38-land goal for improved consistency.
*   **Strategy Finalization:** Finalized the "Fling/Ignition" win-condition plan for the next shipment.
    *   **Planned In:** Chandra's Ignition, Gravitic Punch, Soul's Fire, Kess, Dissident Mage, Widespread Brutality.
    *   **Planned Out:** Soothing of Sméagol, Orcish Medicine, Warg Rider, Grishnákh, Brash Instigator, Languish.
*   **Collection Audit:** Conducted a global audit of the `commander_decks` folder. Ensured all 50+ deck lists have a `## 📜 Deck Changelog` section and an "Initial deck creation" entry for consistency.
*   **Status:** Physical Sauron deck is at 100 cards with 38 lands.

### 2026-02-21: The "New Era" Audit & Planning
*   **Alela (Christina's Shell) - Note: Zimone is for Jamie:** Branched into three versions: **Budget** (<$100), **Upgraded Budget** ($150-$200), and **Optimized Shell**. Focused on resilience (Bastion of Remembrance) and static win conditions (Gravitational Shift).
*   **Zimone Landfall:** Branched into **Budget Engine** (saving $250+ via luxury swaps) and **"Math Class" (Thematic)** build. Conducted a comprehensive audit of the Landfall Engine, adding graveyard recovery (Six, Conduit of Worlds) and top-end power (Reshape the Earth).
*   **Sauron Army Fling:** Branched a specialized "Fling" list for planning. Replaced budget tapped lands with full Fetch/Shock/Bond suite.
*   **Sauron Midrange:** Finalized the list for the "Core Engine" (Lazotep Chancellor, Archfiend) to maximize Sauron's discard-draw triggers.

### 2026-02-20: Deck Maintenance & Resilience
*   **Karametra:** Swapped *Harmonize* for *Angelic Arbiter* in the main list and Pilot's Handbook. This increase in board-taxing creatures aligns with the deck's goal of out-valuing aggressive strategies like Slivers.
*   **Sauron:** Replaced *Uglúk of the White Hand* with *Dread Return* (from Sideboard) to improve recovery from mandatory discard triggers.

### 2026-02-08: Tribal Synergy
*   **Sauron:** Added 5 key synergy pieces including *Dreadhorde Invasion* and *Dark Deal*.

---

## 🗓️ January 2026: Arena Foundations & Omnath
*Focus on establishing the MTG Arena collection and refining high-power planning.*

### 2026-01-31: Omnath Bracket 3 Calibration
*   **Decisions:** Adjusted *Omnath, Locus of Creation* for "Bracket 3" power levels.
*   **Changes:** Swapped generic staples (Rhystic Study, Jeska's Will) for landfall engines (Kodama of the East Tree, Emeria Shepherd, Omnath, Locus of Rage).

### 2026-01-02: MTG Arena Launch
*   **Milestone:** Built **Dimir Midrange** (Tier 1) on MTG Arena.
*   **Strategy:** Focused on a "Flash" engine using *Kaito, Bane of Nightmares* and *Enduring Curiosity*.
*   **Economy:** Established the "Foundations" pack-buying strategy to maximize Golden Pack progress. Established preference for interactive Midrange/Control over linear Aggro.

---
