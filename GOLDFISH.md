# Goldfish Testing Protocol

This file defines the full protocol for running "Honest Goldfish" simulations on Commander decks in this repository. It governs how sub-agents are dispatched, how each game is played, what decisions are made, and how results are reported back and summarized.

> **API Reference:** All card lookups and pricing queries must follow the rules in `API_REFERENCE.md`. That file is the authoritative reference for Scryfall and Manapool API usage, rate limits, permanent scripts, and error handling. Read it before performing any API calls.

---

## MANDATORY: Card Research Requirement

**Every sub-agent running a goldfish game MUST look up any card it does not know with certainty before making play decisions based on it.**

This is not optional. Oracle text is exact rules language. A card that "seems like" it does something may have a restriction, an exception, or a timing rule that changes the correct play. An incorrect assumption invalidates the entire game's data.

### When you MUST look up a card:
- You are unsure of the card's exact oracle text
- You are unsure of the card's mana cost, color identity, or type
- You are deciding whether or how to play the card this turn
- The card has a triggered ability, activated ability, or replacement effect and you are not certain of the exact wording
- The card interacts with another card and you are not certain how the interaction resolves

### How to look up a card:
Use the permanent Scryfall lookup script. Do not write inline Python. Do not guess.

```
python scripts/scryfall_lookup.py "Card Name"
```

Multiple cards at once:
```
python scripts/scryfall_lookup.py "Kindred Discovery" "Maskwood Nexus" "Morophon, the Boundless"
```

The output shows exact oracle text, mana cost, type line, and current USD price. Rate limit is 500ms between requests — the script handles this automatically.

See `API_REFERENCE.md` for full Scryfall and Manapool documentation including query syntax, rate limits, and all usage examples.

---

## Overview

A goldfish simulation is a solo playtest — no opponents, no interaction from other players. The goal is to evaluate the deck's consistency, mana development, and ability to execute its game plan within a given number of turns. Each game is played honestly: no foresight, no take-backs, strict mana rules.

Goldfish tests are run using sub-agents. The orchestrating agent (the main Claude session) dispatches one sub-agent per game in parallel, collects their reports, verifies correctness, and delivers a consolidated summary to the user.

---

## Orchestrator Responsibilities (Main Agent)

When a user requests a goldfish run, the main agent must:

1. **Identify the deck** — locate the correct `moxfield_import.txt` file in the deck's directory.
2. **Identify the test goal** — what is being measured (e.g., "Morophon cast by turn 7", "engine assembled by turn 5"). Record this explicitly in sub-agent prompts.
3. **Dispatch sub-agents in parallel** — one agent per game (default 5 games). Each agent receives a complete, self-contained prompt with all context it needs (see Sub-Agent Prompt Template below).
4. **Verify each report** — check that:
   - The correct number of cards was drawn each turn.
   - Mana math is accurate (lands tapped correctly, shocks paid for, tapped lands not used).
   - Play decisions are reasonable given the stated goal (not optimal — honest).
   - The specific metric being tracked was recorded correctly.
5. **Correlate results** — identify patterns across games: common early hands, how often the goal was achieved, what prevented it when it wasn't.
6. **Deliver summary** — present findings to the user in the Summary Format defined below.
7. **Log results** — write the full session to `GOLDFISH_LOG.md` in the deck's directory.

---

## Sub-Agent Instructions

Each sub-agent is responsible for playing one complete goldfish game. When you receive your prompt you will be told:

- The path to the deck's `moxfield_import.txt`
- The specific metric to track (e.g., "record the turn Morophon is cast and creatures on board at that moment")
- Your game number

### Step 1 — Generate the Shuffled Deck

Run the shuffler script:

```
python scripts/goldfish_shuffler.py "<path_to_moxfield_import.txt>"
```

This outputs 20 cards (opening hand + early draws). Record all 20. If you need more cards during play (due to draw spells triggering), note that you have run out of visible cards and report which draw effects fired.

The script output gives you a shuffled deck. The first 7 cards are your opening hand. Cards 8+ are drawn in order, one per turn (plus any additional draws from spell/ability effects).

### Step 2 — Mulligan Decision

Evaluate your 7-card opening hand using these rules:

**Keep if:**
- Hand contains 2–5 lands AND at least one of: Llanowar Elves, Elvish Mystic, Fyndhorn Elves, Sol Ring, Arcane Signet, Fellwar Stone, Chromatic Lantern, Cultivate, Nature's Lore
- OR: hand contains 3+ lands and multiple playable spells that advance the game plan

**Mulligan if:**
- 0 or 1 lands
- 6 or 7 lands with fewer than 2 spells
- No way to produce green mana in the first 2 turns (elf ramp requires green T1)

If you mulligan to 6: draw 6 new cards from position 1 of the shuffled deck (shifting all card positions down by 1 accordingly). Note the mulligan in your report. Maximum one mulligan per game — keep the 6-card hand regardless.

### Step 3 — Play Turns 1 through 7 (or until the test goal is achieved)

Play each turn following these rules strictly:

**Each turn:**
1. Draw your card for the turn (except turn 1 — in Commander you draw on turn 1).
2. Play a land if you have one. Follow tapped/untapped rules:
   - Shock lands enter untapped if you pay 2 life. Pay it if the mana is needed this turn; otherwise let it enter tapped.
   - Fetch lands: crack immediately if a dual land is needed. Shuffle the remaining unseen library mentally — treat the next card you draw as still random (do not assume what it fetches into).
   - Triomes always enter tapped.
   - All other lands follow their printed rules.
3. Cast spells with available mana, prioritizing the game plan:
   - **Priority order for mana development:** Elf creatures (T1) → Mana rocks (T2) → Cultivate/Nature's Lore (T3) → Morophon (T7 or earlier if mana allows)
   - **Priority order for threats:** Morophon (when castable) → Lords that provide keywords → Changelings that trigger draw engines → Other spells
   - Do not hold mana open for protection unless you have a specific protective spell in hand (Heroic Intervention, Tamiyo's Safekeeping).
4. Record the full board state at end of each turn.

**Mana counting rules:**
- Count total available mana at the start of your main phase.
- Morophon costs {7}. Cast it the first turn you have 7+ mana.
- Elf ramp counts: each Llanowar Elves/Elvish Mystic/Fyndhorn Elves = +1 mana (green) if it survived from a prior turn.
- Sol Ring = +2 colorless. Arcane Signet / Fellwar Stone = +1 any color.
- Cultivate / Nature's Lore: put one Forest into play untapped, one to hand. Counts as your land drop for the turn.

### Step 4 — Report Format

Return your report in this exact format:

```
GAME [N] — [DECK NAME]
Shuffler timestamp: [from script output]
Mulligan: [Yes — kept 6 / No — kept 7]

OPENING HAND:
[List all 7 cards, one per line]

TURN-BY-TURN:

T1 | Mana available: [X] | Land played: [name] | Spells cast: [name or "none"] | Draw: [card name]
   Board: [list all permanents in play]
   Notes: [any relevant observations]

T2 | Mana available: [X] | Land played: [name] | Spells cast: [name or "none"] | Draw: [card name]
   Board: [list all permanents in play]
   Notes: [any relevant observations]

[...continue through T7 or until test goal achieved...]

RESULT:
- Morophon cast on turn: [T# or "not cast by T7"]
- Creatures on board when Morophon cast: [list names, or "N/A"]
- Total mana on turn Morophon was cast: [X]
- Notes: [anything notable — flooded, mana-screwed, draw engine firing, etc.]
```

---

## Sub-Agent Prompt Template

When the orchestrator dispatches a sub-agent, it should use this template:

```
You are running Game [N] of a Goldfish simulation for the [DECK NAME] Commander deck.

Deck file: [path to moxfield_import.txt]
Test goal: [specific metric — e.g., "record the turn Morophon, the Boundless is cast and list all other creatures on the battlefield at that moment"]

Instructions:
1. Read GOLDFISH.md and API_REFERENCE.md before starting. Both are in the project root.
2. Run: python scripts/goldfish_shuffler.py "[path to moxfield_import.txt]"
3. Before making any play decision involving a card, look up its oracle text if you are not 100% certain:
      python scripts/scryfall_lookup.py "Card Name"
   Do not guess. Do not assume. Look it up.
4. Follow the full goldfish protocol in GOLDFISH.md exactly.
5. Report your results in the exact format specified in GOLDFISH.md Step 4.
6. Do not skip turns or abbreviate — report each turn individually.
7. This is a research task only — do not modify any deck files.
8. All API usage must follow API_REFERENCE.md — rate limits, parameter formats, and script usage.
```

---

## Orchestrator Verification Checklist

Before accepting a sub-agent report, verify:

- [ ] Card draw count is correct each turn (1 per turn, more only if a draw effect fired)
- [ ] Mana math adds up: lands + rocks + elves = stated mana available
- [ ] Tapped lands were not used the turn they entered
- [ ] Shock land life payments were tracked
- [ ] Morophon's cost ({7}) was correctly identified — no misapplication of cost reductions not in hand
- [ ] The reported metric (turn cast, creatures on board) matches the turn-by-turn log
- [ ] Mulligan rule was applied correctly if taken

If a report fails verification, note the discrepancy in the summary but still include the game's data with a flag.

---

## Summary Format

After all games complete, the orchestrator delivers this summary to the user:

```
## Goldfish Results — [DECK NAME]
**Test goal:** [metric]
**Games run:** [N]
**Date:** [YYYY-MM-DD]

### Per-Game Results
| Game | Mulliganed | Morophon Turn | Creatures on Board | Notes |
|------|-----------|---------------|-------------------|-------|
| 1    | No        | T6            | 3 (Llanowar Elves, Taurean Mauler, Woodland Changeling) | Sol Ring T1 |
| ...  | ...       | ...           | ...               | ...   |

### Consistency Analysis
- **Morophon cast by T7:** [X/N games] ([%]%)
- **Average turn Morophon cast:** [X.X]
- **Average creatures on board at cast:** [X.X]
- **Common early ramp pieces:** [list]
- **Games with mana issues:** [X/N]

### Key Observations
[2-4 bullet points summarizing patterns, strengths, weaknesses observed]

### Recommendations
[Any deck adjustments suggested by the data — flagged for discussion, not automatically applied]
```

---

## Logging

After completing a goldfish session, write full results to `GOLDFISH_LOG.md` in the deck's directory. Each session gets a dated header. Append — do not overwrite prior sessions. Format:

```markdown
## [YYYY-MM-DD] — [Test Goal] ([N] games)

[Full summary block as above]

### Raw Game Logs
[Full turn-by-turn reports from all sub-agents, one per game]
```

---

## Notes and Limitations

- **20-card window:** The shuffler script shows only 20 cards. Games with heavy draw engine activity (Kindred Discovery, Guardian Project, Beast Whisperer) may run past this window. Sub-agents should note when they exhaust visible cards and report that draw effects fired but outcomes are unknown.
- **Fetch land shuffling:** When a fetch land is cracked, the sub-agent should treat subsequent card draws as still random — do not use foreknowledge of shuffler output to "predict" what the fetch gets.
- **No opponent interaction:** Goldfish is solitaire. Do not simulate opponent removal, counterspells, or attacks.
- **Commander Zone:** Morophon starts in the command zone. First cast costs {7}. Track commander tax if Morophon is recast ({9} on second cast, etc.).
