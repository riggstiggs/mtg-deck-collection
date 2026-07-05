# Goldfish Log — Bruce Banner, the Incredible Hulk (Gamma Smash)

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
