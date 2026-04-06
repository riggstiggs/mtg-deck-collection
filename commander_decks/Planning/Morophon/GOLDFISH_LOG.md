# Morophon, the Boundless — Goldfish Log

Simulations run via `scripts/multiplayer_goldfish.py`.
Commander rules in effect: all players draw on T1, free first mulligan (redraw 7), subsequent mulligans -1 card.
Priest of Titania and Marwyn, the Nurturer produce mana equal to creatures in play / power respectively.

---

## 2026-04-05 — Baseline (50 sims, 10 turns, 4-player pod)

**Deck version:** Ramp overhaul (Birds of Paradise, Bloom Tender, Priest of Titania, Marwyn the Nurturer in; Cultivate, Nature's Lore, Patriarch's Bidding, Feed the Swarm out)

**Command:**
```
python scripts/multiplayer_goldfish.py "commander_decks/Planning/Morophon/morophon_changeling_moxfield_import.txt" --sims 50 --turns 10
```

**Results:**
```
Commander cast rate: 180/200 (90%)
Range:     T2 - T10
Average:   T6.4
Distribution:
  T 2: # (1)
  T 3: ##### (5)
  T 4: ################## (18)
  T 5: ############################# (29)
  T 6: ######################################## (40)
  T 7: ############################################## (46)
  T 8: ##################### (21)
  T 9: ############# (13)
  T10: ####### (7)

Creatures cast per seat (end T10):
  Average: 3.7  |  Range: 0-9
  Distribution:
     0 creatures: ### (3)
     1 creatures: ########### (11)
     2 creatures: ####################################### (39)
     3 creatures: ####################################### (39)
     4 creatures: ############################################# (45)
     5 creatures: ##################################### (37)
     6 creatures: ##################### (21)
     7 creatures: ### (3)
     8 creatures: # (1)
     9 creatures: # (1)

Multiplayer card value (end T10):
  Mana Geyser:    ~11R  (vs 0R solo goldfish)
  Exotic Orchard: {U, G, B, W, R}  (vs dead solo goldfish)
```

**Notes:**
90% cast rate across 200 player-seats, average T6.4. Modal window is T6-T7 (40+46 casts). T4-T6 early cluster accounts for 87 of 180 casts (48%). T2-T3 outliers reflect Sol Ring / Urza's Incubator + heavy ramp draws. Average 3.7 creatures per seat by T10, with the most common outcome being 4 creatures (45 seats). The 0-creature seats (3) are pure land/rock draws. The remaining 10% commander miss rate is genuine mana drought variance after mulliganing. Priest of Titania and Marwyn's real-table upside is likely higher than the simulator models since it doesn't sequence around maximizing their triggers (e.g. casting multiple creatures the same turn Morophon lands for free/reduced cost).
