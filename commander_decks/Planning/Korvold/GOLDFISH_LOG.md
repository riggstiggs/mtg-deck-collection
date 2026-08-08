## 2026-08-08 — First validation of finalized 100-card list (20 sims, T10 turns)

**Command:**
```
python3 scripts/multiplayer_goldfish.py "commander_decks/Planning/Korvold/moxfield_import.txt" --sims 20 --turns 10
```

**Results:**
```
====================================================================
RUNNING 20 x 4-PLAYER SIMULATIONS
Commander: Korvold, Fae-Cursed King (CMC 5)
====================================================================

  Sim 1: Commander cast 4/4  |  Earliest: T5    |  Turns: [10, 5, 10, 5]  |  Avg creatures: 5.8
  Sim 2: Commander cast 4/4  |  Earliest: T3    |  Turns: [3, 5, 6, 5]  |  Avg creatures: 3.5
  Sim 3: Commander cast 4/4  |  Earliest: T4    |  Turns: [4, 8, 6, 4]  |  Avg creatures: 6.0
  Sim 4: Commander cast 4/4  |  Earliest: T5    |  Turns: [5, 5, 5, 5]  |  Avg creatures: 5.0
  Sim 5: Commander cast 4/4  |  Earliest: T4    |  Turns: [8, 4, 4, 5]  |  Avg creatures: 5.0
  Sim 6: Commander cast 4/4  |  Earliest: T3    |  Turns: [5, 5, 4, 3]  |  Avg creatures: 5.2
  Sim 7: Commander cast 4/4  |  Earliest: T3    |  Turns: [7, 6, 4, 3]  |  Avg creatures: 3.8
  Sim 8: Commander cast 4/4  |  Earliest: T3    |  Turns: [6, 4, 3, 4]  |  Avg creatures: 3.8
  Sim 9: Commander cast 3/4  |  Earliest: T2    |  Turns: [4, 4, 2]  |  Avg creatures: 5.0
  Sim 10: Commander cast 3/4  |  Earliest: T3    |  Turns: [4, 5, 3]  |  Avg creatures: 4.2
  Sim 11: Commander cast 4/4  |  Earliest: T4    |  Turns: [4, 4, 4, 5]  |  Avg creatures: 3.8
  Sim 12: Commander cast 4/4  |  Earliest: T4    |  Turns: [4, 10, 5, 5]  |  Avg creatures: 5.0
  Sim 13: Commander cast 4/4  |  Earliest: T3    |  Turns: [4, 5, 5, 3]  |  Avg creatures: 4.0
  Sim 14: Commander cast 3/4  |  Earliest: T3    |  Turns: [4, 4, 3]  |  Avg creatures: 4.0
  Sim 15: Commander cast 4/4  |  Earliest: T4    |  Turns: [9, 4, 4, 5]  |  Avg creatures: 3.2
  Sim 16: Commander cast 4/4  |  Earliest: T3    |  Turns: [6, 5, 3, 5]  |  Avg creatures: 5.2
  Sim 17: Commander cast 4/4  |  Earliest: T3    |  Turns: [5, 4, 5, 3]  |  Avg creatures: 4.5
  Sim 18: Commander cast 4/4  |  Earliest: T4    |  Turns: [9, 4, 4, 4]  |  Avg creatures: 3.2
  Sim 19: Commander cast 4/4  |  Earliest: T3    |  Turns: [5, 6, 7, 3]  |  Avg creatures: 4.0
  Sim 20: Commander cast 4/4  |  Earliest: T3    |  Turns: [5, 3, 3, 4]  |  Avg creatures: 3.8

--------------------------------------------------------------------
AGGREGATE
--------------------------------------------------------------------
  Commander cast rate: 77/80 (96%)
  Range:     T2 - T10
  Average:   T4.8
  Distribution:
    T 2: # (1)
    T 3: ############ (12)
    T 4: ######################### (25)
    T 5: ######################## (24)
    T 6: ###### (6)
    T 7: ## (2)
    T 8: ## (2)
    T 9: ## (2)
    T10: ### (3)

  Avg creatures per seat (end T10): 4.4
```

**Notes:**
- First goldfish run against the fully reconciled 100-card list (post 2026-08-08
  cut/add batch — see Deck Changelog). 96% commander cast rate by T10, average
  T4.8, is a solid mana-stability result for a Bracket 3 three-color deck — the
  8 ramp pieces (5 land-fetch/dorks + 3 "any commander-color" rocks) are pulling
  their weight getting to {2}{B}{R}{G} on curve.
- Distribution clusters T3-T5 (61/80 seats), which lines up with the Bracket 3
  "earliest win turn 7" expectation — Korvold consistently arriving turns
  3-5 gives several turns of the sac-engine running before the bracket's
  win-turn floor, which is the intended pace for this deck.
- Two outlier T9-T10 casts and the single T2 cast are within normal variance
  for a 3-color commander with no guaranteed T1 rock.
- Avg creatures per seat at T10 (4.4) is a reasonable board-state baseline —
  worth revisiting once/if Mass Disruption gets bumped from its current
  3/6 template gap, since more wipes would suppress this number by design.
- No red flags. Deck is validated as mana-stable and on-curve for its
  intended bracket. Land count (39, +1 over the 38 template target from
  Castle Embereth) did not appear to cause any observable stall pattern in
  this run.
