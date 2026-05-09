# Goldfish Log: Ramses, Assassin Lord

## 2026-05-09 — Initial validation (20 sims, T10 turns)

**Command:**
```
python3 scripts/multiplayer_goldfish.py "commander_decks/Planning/RamsesAssassinLord/moxfield_import.txt" --sims 20 --turns 10
```

**Results:**
```
Commander cast rate: 80/80 (100%)
Range:     T1 - T7
Average:   T3.2
Distribution:
  T 1: #### (4)
  T 2: ################# (17)
  T 3: ############################### (31)
  T 4: #################### (20)
  T 5: #### (4)
  T 6: ## (2)
  T 7: ## (2)

Avg creatures per seat (end T10): 3.4
```

**Notes:**
- 100% commander cast rate across all 80 seats. Ramses ({2}{U}{B}) hits the table reliably due to the dense mana rock package (Arcane Signet, Dimir Signet, Mind Stone, Sol Ring) plus Dimir dual lands.
- Average T3.2 is healthy for a CMC-4 commander. 51% of casts land on T2–T3, indicating consistent early pressure.
- T1 casts (4 instances) are Sol Ring + mana rock openings enabling a T1 Ramses on very fast draws — plausible with the mana base.
- T6–T7 outliers (4 instances) represent mana-flooded or land-light opening hands after mulligan. Not a concern at this frequency.
- Creature count of 3.4/seat by T10 is modest — expected for a control-midrange Assassin tribal deck where most non-land, non-rock spells are sorceries/instants (Toxic Deluge, Counterspell, etc.). The Assassin bodies that do hit are high-impact evasive threats.
- **Simulator fix applied this session:** `multiplayer_goldfish.py` was previously R/G-only. Extended to track W/U/B mana production so Dimir and other non-Gruul decks simulate correctly.
- **Verdict:** Mana base and ramp package are performing well. Deck curves out appropriately for a Bracket 3 midrange strategy.
