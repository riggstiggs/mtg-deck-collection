# Goldfish Log — The Fantastic Four

## [2026-07-19] — Initial build validation (20 sims, T10 turns)

**Command:**
```
python scripts/multiplayer_goldfish.py "commander_decks/Planning/FantasticFour/moxfield_import.txt" --sims 20 --turns 10
```

**Results:**
```
AGGREGATE
  Commander cast rate: 75/80 (94%)
  Range:     T1 - T9
  Average:   T4.2
  Distribution:
    T 1: # (1)
    T 2: ######### (9)
    T 3: #################### (20)
    T 4: ##################### (21)
    T 5: ########## (10)
    T 6: ##### (5)
    T 7: #### (4)
    T 8: ## (2)
    T 9: ### (3)
  Avg creatures per seat (end T10): 3.3
```

**Notes:**
- 94% commander cast rate is strong, especially for a FOUR-color deck (4c usually
  trades consistency for color access — this one held).
- Average deploy T4.2, right on curve for a 4-MV commander. Distribution clusters
  T3-T4 → ramp package (10 pieces) + fetchable dual-heavy manabase are working.
- Range T1-T9: a few god-hands, only rare stumbles to T8-9. No systemic mana screw.
- 3.3 creatures/seat by T10 = healthy go-wide board, matches the deck's plan.
- Conclusion: manabase and curve validated. No changes indicated by this run.
- NOT yet tested: whether the "4s" trigger density actually fires in practice (the
  sim measures commander deployment + board width, not spell-cast-4 triggers). That's
  a play-pattern question for real games, not the goldfish.

## [2026-07-19] — 4-rule audit + tuning (no re-sim needed, same curve)

Audited every nonland/non-ramp spell against the 4-rule (power 4 OR toughness 4 OR
mana value 4 → triggers commander). Of ~51 such cards:
- **~27 directly HIT the 4-rule** (trigger the commander).
- **~5 CARE ABOUT 4s** (Colossal Majesty, Garruk's Uprising, Tribute to the World
  Tree, Reconnaissance Mission) — synergize with the many power-4 creatures even
  though they don't trigger. KEPT deliberately (Jamie's call — they cause lots of
  triggers via the 4-power creatures).
- **~13 are efficient interaction** (removal + board wipes) — correctly OFF-curve;
  not distorted to fit the theme (a 1-mana Swords shouldn't become 4 mana).
- **~6 top-end/value payoffs** incl. The Thing (KEPT — a member + his ability rewards
  the noncreature synergy).

**Swaps this pass:** The Great Henge (MV9, off-theme, $64) → Enduring Curiosity (P4,
triggers, go-wide combat draw); Cultivator Colossus (MV7) → Reconnaissance Mission
(cheap go-wide combat draw, cares about attackers). Deck still 100 / 38 lands / all
legal. Curve essentially unchanged (both swaps are cheaper), so the 20-sim result
above still holds.
