# Goldfish Testing Protocol

This file defines the protocol for running goldfish simulations on Commander decks in this repository. All simulations use `scripts/multiplayer_goldfish.py` — a fully automated 4-player pod simulator powered by Scryfall card classification.

> **API Reference:** All card lookups follow the rules in `API_REFERENCE.md`. The goldfish script uses its own local cache at `scripts/.card_cache.json` and respects Scryfall rate limits automatically.

---

## The Script

```
python scripts/multiplayer_goldfish.py <deck_file> [--sims N] [--turns N] [--tapped F]
```

**Arguments:**

| Argument | Default | Description |
|----------|---------|-------------|
| `deck_file` | required | Path to the deck's `moxfield_import.txt` file |
| `--sims N` | 1 | Number of simulations to run (use 20+ for meaningful statistics) |
| `--turns N` | 15 | Number of turns to simulate per game |
| `--tapped F` | 0.60 | Fraction of opponent lands assumed tapped (for Mana Geyser-style cards) |
| `--commander-back` | off | For a **transform DFC commander**, measure deployment of the BACK face (its hard-cast / flip cost) instead of the cheap front face |
| `--commander-cost "{..}"` | none | Manually override the commander cost used for the cast check, e.g. `"{2}{R}{R}{G}{G}"`. Takes priority over `--commander-back` |

**Example — standard 20-sim run:**
```
python scripts/multiplayer_goldfish.py "commander_decks/Planning/Morophon/morophon_changeling_moxfield_import.txt" --sims 20 --turns 10
```

### Flip / Double-Faced Commanders
For a transform DFC commander whose meaningful threat is the **back** face (e.g. **Bruce Banner // The Incredible Hulk** — a {U} front that flips/hard-casts into a `{2}{R}{R}{G}{G}` back), the default run only measures dropping the cheap front face, which is not the real deployment clock. The simulator auto-detects these and prints a `[commander] NOTE:` telling you to rerun with `--commander-back` (uses the back face's cost) or `--commander-cost "{..}"` (any explicit cost). Log both numbers when relevant: the front tells you when the early-game piece lands, the back tells you when the payoff comes online.
```
python scripts/multiplayer_goldfish.py "commander_decks/Owned/IncredibleHulk/moxfield_import.txt" --sims 20 --turns 12 --commander-back
```

---

## How It Works

The script auto-classifies every card via Scryfall on first run (results cached locally — subsequent runs are instant). It then simulates a full 4-player pod with one copy of the deck per seat.

**Each turn, the engine prioritizes:**
1. Play a land (untapped duals first, then untapped singles, tapped last)
2. Cast mana permanents (rocks, dorks) while affordable
3. Cast ramp spells while affordable
4. Cast the commander from the command zone if mana allows
5. Cast generic spells with remaining mana

**Pod assumptions:**
- All 4 players run the same deck — opponents' lands cover the full color identity
- Exotic Orchard and Fellwar Stone produce any color (opponents have all 5 colors)
- Mana Geyser scales with opponent tapped lands using the `--tapped` fraction
- Commander tax is tracked and applied on subsequent casts

---

## Deck File Format

The script requires `COMMANDER:` and `DECK:` section headers. The standard `moxfield_import.txt` format already satisfies this:

```
COMMANDER:
1 Morophon, the Boundless

DECK:
1 Sol Ring
1 Command Tower
...
```

---

## Running a Goldfish Session

Default recommendation for a new deck or after significant changes:

```
python scripts/multiplayer_goldfish.py "<path_to_moxfield_import.txt>" --sims 20 --turns 10
```

For a quick sanity check (single verbose game showing every turn):
```
python scripts/multiplayer_goldfish.py "<path_to_moxfield_import.txt>" --sims 1 --turns 10
```

---

## Reading the Output

**Per-sim lines** show commander cast rate and earliest cast turn across the 4-seat pod:
```
  Sim 3: Commander cast 3/4  |  Earliest: T5   |  Turns: [5, 6, 7]
```

**Aggregate block** shows overall statistics across all simulations:
```
  Commander cast rate: 76/80 (95%)
  Range:     T4 – T9
  Average:   T6.1
  Distribution:
    T4:  ██ (2)
    T5:  ████████ (8)
    T6:  ██████████████ (14)
    T7:  ████████████ (12)
```

**Multiplayer card value snapshot** shows context-adjusted values for cards that scale with opponents:
```
  Mana Geyser:    ~9R  (vs 0R solo goldfish)
  Exotic Orchard: {'R','G','W','U','B'}  (vs dead solo goldfish)
```

---

## Logging Results

After running a session, append results to `GOLDFISH_LOG.md` in the deck's directory. Each session gets a dated header. Do not overwrite prior sessions.

```markdown
## [YYYY-MM-DD] — [Test goal] ([N] sims, T[X] turns)

**Command:**
\`\`\`
python scripts/multiplayer_goldfish.py "..." --sims N --turns N
\`\`\`

**Results:**
[Paste the full aggregate output block from the script]

**Notes:**
[Any observations about what the data shows — patterns, concerns, recommendations]
```

---

## Cache

The script maintains its own card classification cache at `scripts/.card_cache.json`. This is committed to the repo so cached lookups are shared across machines. First run on a new deck fetches from Scryfall; all subsequent runs are instant.

If you need to force a fresh classification for a card (e.g. after an errata), delete its entry from `scripts/.card_cache.json` manually.
