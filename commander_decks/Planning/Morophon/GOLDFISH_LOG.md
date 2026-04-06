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
Commander cast rate: 175/200 (88%)
Range:     T2 - T10
Average:   T6.2
Distribution:
  T 2: # (1)
  T 3: ##### (5)
  T 4: ################ (16)
  T 5: ################################## (34)
  T 6: ################################################ (48)
  T 7: ###################################### (38)
  T 8: ############## (14)
  T 9: ############## (14)
  T10: ##### (5)

Multiplayer card value (end T10):
  Mana Geyser:    ~11R  (vs 0R solo goldfish)
  Exotic Orchard: {U, G, B, W, R}  (vs dead solo goldfish)
```

**Notes:**
88% cast rate across 200 player-seats, average T6.2. Modal window is T6 (48 casts), with a strong early cluster — T4-T6 accounts for 98 of 175 casts (56%). T2-T3 outliers reflect Sol Ring / Urza's Incubator + heavy ramp draws. The remaining 12% misses are genuine mana drought variance: players who draw 5-6 lands in 10 turns even after mulliganing. Realistic floor for a 7-CMC commander with no colored pip requirements. Priest of Titania and Marwyn scale multiplicatively with the creature count — their real-table upside is likely higher than the simulator can model since it doesn't sequence around maximizing their triggers.
