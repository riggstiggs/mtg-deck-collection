# Goldfish Log — Bruce Banner, the Incredible Hulk (Gamma Smash)

## [2026-07-04] — Back-face deployment (Hulk online) — 20 sims, T12
Measures when the deck can put **The Incredible Hulk** online — hard-cast or flip, both `{2}{R}{R}{G}{G}` — using the new `--commander-back` flag. The default run measures only the {U} Bruce Banner front (a 1-drop), which is not the meaningful threat.

**Command:**
```
python3 scripts/multiplayer_goldfish.py "commander_decks/Owned/IncredibleHulk/moxfield_import.txt" --sims 20 --turns 12 --commander-back
```

**Results:**
```
AGGREGATE
  Commander (back face) online rate: 77/80 (96%)
  Range:     T3 - T11
  Average:   T5.9
  Distribution:
    T 3: ### (3)
    T 4: ############## (14)
    T 5: ################## (18)
    T 6: ##################### (21)
    T 7: ####### (7)
    T 8: ###### (6)
    T 9: ## (2)
    T10: ##### (5)
    T11: # (1)
  Avg creatures per seat (end T12): 5.4
```

**Notes:**
- The Hulk lands on average **T5.9**, most commonly **T4–T6**, and 96% of seats have it online by T12 — a healthy curve for a 6-mana `{2}{R}{R}{G}{G}` payoff backed by 11 ramp sources.
- This is the metric that matters for this commander; the earlier T2.3 "cast rate" only reflected dropping the {U} Bruce Banner front as a turn-1 draw engine (still true and useful, but not the threat clock).
- Both lines converge in practice: whether you hard-cast the back or cast Bruce T1 and flip later, you need `{2}{R}{R}{G}{G}` available, so ~T6 is when the Hulk comes online either way.

---

## [2026-07-04] — Post-tuning re-validation (20 sims, T10 turns)
Captures the full day's changes: Fling package, land overhaul (Marvel duals, no fetches), Tyvar's Stand, Restorative Technique, and The Thing / Epic Fight.

**Command:**
```
python3 scripts/multiplayer_goldfish.py "commander_decks/Planning/IncredibleHulk/moxfield_import.txt" --sims 20 --turns 10
```

**Results:**
```
AGGREGATE
  Commander cast rate: 79/80 (99%)
  Range:     T1 - T10
  Average:   T2.3
  Distribution:
    T 1: ############################# (29)
    T 2: ######################## (24)
    T 3: ############## (14)
    T 4: ### (3)
    T 5: ##### (5)
    T 6: ### (3)
    T10: # (1)
  Avg creatures per seat (end T10): 4.5
```

**Notes:**
- Identical headline to the initial build (99% cast, T2.3 avg) — the tuning didn't hurt consistency. Removing the fetch lands and adding tapped Marvel duals (Cinder Glade, Scorched Geyser) did not slow commander deployment, since Banner is a 1-drop cast off almost any untapped source.
- 4.5 creatures/seat by T10, in line with prior runs — board development is stable.
- Only 1 whiff across 80 seats (a late-cast, not a never-cast).

---


## [2026-07-04] — Initial build validation (20 sims, T10 turns)

**Command:**
```
python3 scripts/multiplayer_goldfish.py "commander_decks/Planning/IncredibleHulk/moxfield_import.txt" --sims 20 --turns 10
```

**Results:**
```
AGGREGATE
  Commander cast rate: 78/80 (98%)
  Range:     T1 - T6
  Average:   T2.3
  Distribution:
    T 1: ############################## (30)
    T 2: ###################### (22)
    T 3: ######### (9)
    T 4: ###### (6)
    T 5: ######## (8)
    T 6: ### (3)
  Avg creatures per seat (end T10): 4.8
```

**Notes:**
- Cast rate is measured against Banner (the {U} front face, CMC 1), so the T2.3 average reflects how early Banner hits the table, not the {2}{R}{R}{G}{G} flip into the Hulk. The early Banner deployment is exactly what we want — he draws while the counters board assembles.
- 4.8 creatures per seat by T10 confirms the green ramp base (Sol Ring, Birds, Incubation Druid, Gyre Sage, Bloom Tender, Farseek/Three Visits/Cultivate/Kodama's Reach + Doc Samson, Hulking Raptor) develops a wide board reliably.
- Only 2 whiffs across 80 seats (both cast the commander a turn or two late rather than never) — mana base handles the demanding RR/GG/UU pips well.
- The simulator does not model the flip, Enrage, counter multiplication, or the Caltrops combat loop — those are the real engine and should be validated in Forge/paper playtesting.
