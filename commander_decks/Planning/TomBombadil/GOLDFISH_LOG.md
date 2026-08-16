## 2026-08-16 — V2 mana-base validation (20 sims, T10 turns)

**Command:**
```
python3 scripts/multiplayer_goldfish.py "commander_decks/Planning/TomBombadil/moxfield_import.txt" --sims 20 --turns 10
```

**Results:**
```
====================================================================
RUNNING 20 x 4-PLAYER SIMULATIONS
Commander: Tom Bombadil (CMC 5)
====================================================================

  Sim 1: Commander cast 4/4  |  Earliest: T3    |  Turns: [4, 3, 5, 3]  |  Avg creatures: 2.8
  Sim 2: Commander cast 4/4  |  Earliest: T4    |  Turns: [8, 9, 4, 8]  |  Avg creatures: 3.0
  Sim 3: Commander cast 4/4  |  Earliest: T2    |  Turns: [5, 2, 4, 5]  |  Avg creatures: 3.5
  Sim 4: Commander cast 4/4  |  Earliest: T3    |  Turns: [6, 3, 9, 4]  |  Avg creatures: 2.5
  Sim 5: Commander cast 4/4  |  Earliest: T2    |  Turns: [2, 5, 4, 3]  |  Avg creatures: 3.5
  Sim 6: Commander cast 4/4  |  Earliest: T3    |  Turns: [3, 6, 4, 3]  |  Avg creatures: 3.8
  Sim 7: Commander cast 4/4  |  Earliest: T3    |  Turns: [4, 7, 5, 3]  |  Avg creatures: 3.5
  Sim 8: Commander cast 4/4  |  Earliest: T4    |  Turns: [5, 6, 4, 7]  |  Avg creatures: 3.2
  Sim 9: Commander cast 4/4  |  Earliest: T3    |  Turns: [5, 4, 5, 3]  |  Avg creatures: 3.2
  Sim 10: Commander cast 3/4  |  Earliest: T4    |  Turns: [5, 4, 4]  |  Avg creatures: 3.2
  Sim 11: Commander cast 4/4  |  Earliest: T4    |  Turns: [4, 6, 4, 8]  |  Avg creatures: 4.0
  Sim 12: Commander cast 4/4  |  Earliest: T2    |  Turns: [5, 2, 3, 4]  |  Avg creatures: 3.2
  Sim 13: Commander cast 4/4  |  Earliest: T4    |  Turns: [5, 5, 5, 4]  |  Avg creatures: 2.8
  Sim 14: Commander cast 4/4  |  Earliest: T2    |  Turns: [7, 4, 2, 4]  |  Avg creatures: 3.0
  Sim 15: Commander cast 3/4  |  Earliest: T4    |  Turns: [5, 4, 9]  |  Avg creatures: 2.8
  Sim 16: Commander cast 3/4  |  Earliest: T4    |  Turns: [4, 4, 5]  |  Avg creatures: 3.8
  Sim 17: Commander cast 3/4  |  Earliest: T4    |  Turns: [4, 10, 5]  |  Avg creatures: 2.8
  Sim 18: Commander cast 4/4  |  Earliest: T4    |  Turns: [5, 4, 5, 6]  |  Avg creatures: 1.8
  Sim 19: Commander cast 4/4  |  Earliest: T4    |  Turns: [9, 4, 4, 5]  |  Avg creatures: 3.5
  Sim 20: Commander cast 4/4  |  Earliest: T4    |  Turns: [10, 7, 5, 4]  |  Avg creatures: 3.0

--------------------------------------------------------------------
AGGREGATE
--------------------------------------------------------------------
  Commander cast rate: 76/80 (95%)
  Range:     T2 - T10
  Average:   T4.9
  Distribution:
    T 2: #### (4)
    T 3: ######### (9)
    T 4: ######################### (25)
    T 5: #################### (20)
    T 6: ##### (5)
    T 7: #### (4)
    T 8: ### (3)
    T 9: #### (4)
    T10: ## (2)

  Avg creatures per seat (end T10): 3.1
```

**Notes:**
- First goldfish run on the V2 manabase rebuild (Triomes + typed snow duals replacing Draft
  1's Castles/check-lands/fetches — see Deck Changelog in README.md). 95% commander cast
  rate by T10, average T4.9, is right in line with the other 5-mana legendary commanders in
  this collection (compare Korvold at 96%/T4.8, a 3-color deck) despite Tom Bombadil being a
  full 5-color WUBRG commander — a strong result for the color-identity difficulty involved.
- The manabase's 24-of-35 lands carrying real basic land types (Three Visits/Nature's Lore
  targets) appears to be doing real work here: no simulation shows a commander-cast failure
  driven by color screw specifically, only the normal variance of a 5-drop commander in a
  4-player pod.
- Avg creatures per seat at end of T10 (3.1) is modest but expected — this deck's plan cards
  lean on Sagas and value engines more than a go-wide token strategy, so raw creature count
  understates board development (Sagas, Treasure/Food tokens, and enchantments aren't
  counted by this metric).
- No further tuning indicated by this run. Recommend a second validation pass once
  Jamie/Arlo make their first round of cuts from V2's "Active Acquisition List" candidates.
