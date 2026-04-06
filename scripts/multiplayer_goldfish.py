#!/usr/bin/env python3
"""
Multiplayer Goldfish Simulator — Scryfall-powered, deck-agnostic

Simulates 4 parallel games to model a Commander pod. Card behavior is
auto-classified via the Scryfall API and cached locally — works with any deck.

Usage:
  python3 scripts/multiplayer_goldfish.py <deck_file> [--sims N] [--turns N] [--tapped F]
"""

import random, re, sys, time, json, argparse, urllib.request, urllib.parse
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict
from typing import List, Optional

CACHE_FILE = Path('cache') / 'scryfall_cards.json'
SCRYFALL_BASE = 'https://api.scryfall.com/cards/named'
API_DELAY = 0.5    # seconds between Scryfall calls (2/sec limit on /cards/named)
CARD_CACHE_TTL = 365 * 24 * 3600   # 1 year — oracle text changes only via errata

HELLKITE = 'Hellkite Courser'   # special deck card that cheats the commander into play


# ---------------------------------------------------------------------------
# Card data
# ---------------------------------------------------------------------------

@dataclass
class CardData:
    name: str
    cmc: int = 0
    pips: dict = field(default_factory=dict)       # colored pip requirements e.g. {'R':1,'G':1}

    # Land
    is_land: bool = False
    land_produces: List[str] = field(default_factory=list)  # ['R','G'] or ['EXOTIC'] or ['C']
    land_tapped: bool = False
    land_amount: int = 1                            # 2 for Gruul Turf style

    # Mana permanent (dork / rock / enchantment)
    is_mana_perm: bool = False
    perm_produces: List[str] = field(default_factory=list)
    perm_amount: int = 1
    perm_needs_untap: bool = False                  # True for creatures (summoning sickness)
    perm_reducer: bool = False                      # reduces spell costs by {1}

    # Ramp (puts lands into play)
    is_ramp: bool = False
    ramp_tapped: int = 0
    ramp_untapped: int = 0

    # Burst mana (generates mana when cast, e.g. Seething Song / Mana Geyser)
    is_burst: bool = False
    burst_produces: List[str] = field(default_factory=list)
    burst_amount: int = 0
    burst_opp_tapped: bool = False                  # Mana Geyser: scales with opponent lands

    # MDFC: front is spell, back is land
    is_mdfc_land: bool = False
    mdfc_produces: List[str] = field(default_factory=list)
    mdfc_tapped: bool = False


# ---------------------------------------------------------------------------
# Scryfall API + local cache
# ---------------------------------------------------------------------------

_cache: dict = {}

def _load_cache():
    global _cache
    if CACHE_FILE.exists():
        try:
            _cache = json.loads(CACHE_FILE.read_text())
        except Exception:
            _cache = {}

def _save_cache():
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(_cache, indent=2))
    except Exception:
        pass

def _fetch_scryfall(name: str) -> Optional[dict]:
    url = SCRYFALL_BASE + '?exact=' + urllib.parse.quote(name)
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'MTGGoldfishSim/2.0',
            'Accept': 'application/json',
        })
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception:
        return None

def get_scryfall(name: str) -> Optional[dict]:
    key = name.lower()
    entry = _cache.get(key)
    if entry and (time.time() - entry.get('cached_at', 0)) < CARD_CACHE_TTL:
        return entry['data']
    time.sleep(API_DELAY)
    data = _fetch_scryfall(name)
    _cache[key] = {'data': data, 'cached_at': time.time()}
    _save_cache()
    return data


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def parse_mana_cost(cost_str: str):
    """'{2}{R}{G}' -> (4, {'R':1,'G':1})"""
    if not cost_str:
        return 0, {}
    pips = {}
    cmc = 0
    for tok in re.findall(r'\{([^}]+)\}', cost_str):
        if tok.isdigit():
            cmc += int(tok)
        elif tok in 'RGWUBC':
            pips[tok] = pips.get(tok, 0) + 1
            cmc += 1
        elif '/' in tok:
            c = tok[0]
            if c in 'RGWUBC':
                pips[c] = pips.get(c, 0) + 1
                cmc += 1
        # X, S → ignore
    return cmc, pips


def _parse_mana_production(oracle: str):
    """
    Parse '{T}: Add ...' and similar patterns.
    Returns (colors: list, amount: int, is_opp_tapped: bool)
    """
    # Mana Geyser: scales with opponent tapped lands
    if re.search(r'[Aa]dd \{[RGWUBC]\}.*for each tapped land your opponents', oracle):
        m = re.search(r'[Aa]dd \{([RGWUBC])\}', oracle)
        return ([m.group(1)] if m else ['R']), 0, True

    for sentence in re.split(r'(?<=[.!])\s', oracle):
        if not re.search(r'\bAdd\b', sentence, re.I):
            continue
        # Skip "add a counter" / "add +1/+1" type sentences
        if re.search(r'add a |add an? |\badd \+', sentence, re.I):
            if not re.search(r'add.*\{[RGWUBC]\}|add.*mana', sentence, re.I):
                continue

        # "Add one mana of any color"
        if re.search(r'one mana of any color', sentence, re.I):
            return ['R', 'G', 'W', 'U', 'B'], 1, False

        # "Add {R} or {G}" — choice (1 mana)
        choice_m = re.search(r'[Aa]dd \{([RGWUBC])\} or \{([RGWUBC])\}', sentence)
        if choice_m:
            return [choice_m.group(1), choice_m.group(2)], 1, False

        # "Add {G}{G}{G}" — multiple mana
        multi_m = re.search(r'[Aa]dd ((?:\{[RGWUBCS]\})+)', sentence)
        if multi_m:
            tokens = re.findall(r'\{([RGWUBC])\}', multi_m.group(1))
            snow   = re.findall(r'\{S\}', multi_m.group(1))
            colors = tokens + (['C'] * len(snow))
            if colors:
                return colors, len(colors), False

    return [], 0, False


def _parse_ramp(oracle: str):
    """Returns (ramp_tapped, ramp_untapped) lands put into play by this spell."""
    has_search = re.search(r'search your library', oracle, re.I)
    has_put    = re.search(r'put.*land.*onto the battlefield|put.*onto the battlefield.*land', oracle, re.I)
    if not has_search and not has_put:
        return 0, 0

    # How many lands?
    count = 1
    if re.search(r'up to two|two basic land|two land', oracle, re.I):
        count = 2
    elif re.search(r'up to three|three basic land', oracle, re.I):
        count = 3

    if re.search(r'onto the battlefield tapped', oracle, re.I):
        return count, 0
    elif re.search(r'onto the battlefield', oracle, re.I):
        return 0, count
    return count, 0   # default: tapped


# ---------------------------------------------------------------------------
# Card classification
# ---------------------------------------------------------------------------

def classify_card(name: str) -> CardData:
    card = CardData(name=name)
    data = get_scryfall(name)

    if not data or data.get('object') == 'error':
        return card   # unknown → generic, 0 cmc

    faces     = data.get('card_faces')
    oracle    = data.get('oracle_text', '')
    type_line = data.get('type_line', '')
    mana_cost = data.get('mana_cost', '')

    if faces:
        face0 = faces[0]
        face1 = faces[1] if len(faces) > 1 else {}
        oracle    = face0.get('oracle_text', '')
        type_line = face0.get('type_line', '')
        mana_cost = face0.get('mana_cost', '') or mana_cost

        # MDFC: front is spell, back is land
        if 'Land' in face1.get('type_line', '') and 'Land' not in type_line:
            card.is_mdfc_land = True
            land_oracle = face1.get('oracle_text', '')
            prod = data.get('produced_mana', [])
            card.mdfc_produces = prod if prod else ['C']
            card.mdfc_tapped   = bool(re.search(r'enters.*tapped', land_oracle, re.I))
            card.cmc, card.pips = parse_mana_cost(mana_cost)
            # Also check if spell face is a ramp spell
            rt, ru = _parse_ramp(oracle)
            if rt + ru > 0:
                card.is_ramp = True
                card.ramp_tapped   = rt
                card.ramp_untapped = ru
            return card

    card.cmc, card.pips = parse_mana_cost(mana_cost)

    # ── Land ─────────────────────────────────────────────────────────────────
    if 'Land' in type_line:
        card.is_land = True
        prod = data.get('produced_mana', [])
        card.land_produces = prod if prod else ['C']

        # Exotic Orchard — copies opponent land production
        if name == 'Exotic Orchard' or re.search(
                r'could produce.*opponents|opponents.*could produce', oracle, re.I):
            card.land_produces = ['EXOTIC']

        card.land_tapped = bool(re.search(
            r'enters the battlefield tapped|enters tapped', oracle, re.I))

        # Bounce lands (Gruul Turf): produce 2 mana
        if re.search(r'[Aa]dd \{[RGWUBC]\}\{[RGWUBC]\}', oracle):
            card.land_amount = 2

        return card

    # ── Mana permanent ───────────────────────────────────────────────────────
    colors, amount, is_opp = _parse_mana_production(oracle)
    if colors and amount >= 0:
        if is_opp:
            # Mana Geyser style — treat as burst spell
            card.is_burst = True
            card.burst_produces  = colors
            card.burst_opp_tapped = True
        elif amount > 0:
            card.is_mana_perm    = True
            card.perm_produces   = colors
            card.perm_amount     = amount
            card.perm_needs_untap = 'Creature' in type_line
            if re.search(r'costs? \{1\} less|the first.*spell.*costs? \{1\} less', oracle, re.I):
                card.perm_reducer = True
        return card

    # Fixed burst mana: instant/sorcery that adds 2+ mana when cast
    if 'Instant' in type_line or 'Sorcery' in type_line:
        m = re.search(r'[Aa]dd ((?:\{[RGWUBC]\}){2,})', oracle)
        if m:
            tokens = re.findall(r'\{([RGWUBC])\}', m.group(1))
            if tokens:
                card.is_burst      = True
                card.burst_produces = tokens
                card.burst_amount  = len(tokens)
                return card

    # ── Ramp spell ───────────────────────────────────────────────────────────
    rt, ru = _parse_ramp(oracle)
    if rt + ru > 0:
        card.is_ramp       = True
        card.ramp_tapped   = rt
        card.ramp_untapped = ru
        return card

    # ── Generic ──────────────────────────────────────────────────────────────
    return card


# ---------------------------------------------------------------------------
# Player
# ---------------------------------------------------------------------------

class Player:
    def __init__(self, pid: int, deck: List[CardData], commander: CardData):
        self.pid = pid
        lib = deck[:]
        random.shuffle(lib)
        self.hand: List[CardData]  = [lib.pop(0) for _ in range(7)]
        self.library: List[CardData] = lib
        self.lands: List[CardData] = []
        self.mana_perms: List[tuple] = []   # (CardData, ready_turn)
        self.reducer_active = False
        self.turn_log: List[str] = []
        self.mana_per_turn: List[int] = []
        # Commander zone — always available, never in library
        self.commander: CardData = commander
        self.commander_tax: int = 0          # increases by 2 each cast
        self.commander_cast_turn: Optional[int] = None
        self.hellkite_cast_turn: Optional[int] = None

    def draw(self):
        if self.library:
            self.hand.append(self.library.pop(0))


# ---------------------------------------------------------------------------
# Mana helpers
# ---------------------------------------------------------------------------

def exotic_colors(opponents: List[Player]) -> List[str]:
    colors = set()
    for opp in opponents:
        for land in opp.lands:
            for c in land.land_produces:
                if c not in ('C', 'EXOTIC'):
                    colors.add(c)
    return list(colors)


def mana_geyser_val(opponents: List[Player], frac: float) -> int:
    return int(sum(len(o.lands) for o in opponents) * frac)


def compute_mana(player: Player, turn: int, opponents: List[Player], frac: float):
    """Returns (total, r, g) available from lands and ready mana permanents."""
    total = r = g = 0

    for land in player.lands:
        amt      = land.land_amount
        produces = land.land_produces
        if 'EXOTIC' in produces:
            ec = exotic_colors(opponents)
            if ec:
                total += amt
                if 'R' in ec: r += amt
                if 'G' in ec: g += amt
        else:
            total += amt
            if 'R' in produces: r += amt
            if 'G' in produces: g += amt

    for (cd, ready) in player.mana_perms:
        if turn < ready:
            continue
        amt = cd.perm_amount
        total += amt
        if 'R' in cd.perm_produces: r += amt
        if 'G' in cd.perm_produces: g += amt

    return total, r, g


def burst_bonus(player: Player, turn: int, opponents: List[Player], frac: float,
                base_total: int, base_r: int, base_g: int):
    """Net mana gain from castable burst spells in hand."""
    bonus_t = bonus_r = bonus_g = 0
    for cd in player.hand:
        if not cd.is_burst:
            continue
        cur_t = base_total + bonus_t
        cur_r = base_r + bonus_r
        cur_g = base_g + bonus_g
        if not _can_cast(cd, cur_t, cur_r, cur_g, player.reducer_active):
            continue
        if cd.burst_opp_tapped:
            produced = mana_geyser_val(opponents, frac)
            net = produced - cd.cmc
            bonus_t += net
            bonus_r += produced
        else:
            net = cd.burst_amount - cd.cmc
            bonus_t += net
            for c in cd.burst_produces:
                if c == 'R': bonus_r += 1
                elif c == 'G': bonus_g += 1
    return bonus_t, bonus_r, bonus_g


def _can_cast(cd: CardData, total: int, r: int, g: int, reducer: bool) -> bool:
    cost = max(0, cd.cmc - (1 if reducer else 0))
    if total < cost:
        return False
    if cd.pips.get('R', 0) > r:
        return False
    if cd.pips.get('G', 0) > g:
        return False
    for c in ('W', 'U', 'B'):
        if cd.pips.get(c, 0) > 0:
            return False    # can't produce off-color pips
    return True


# ---------------------------------------------------------------------------
# Turn engine
# ---------------------------------------------------------------------------

def simulate_turn(player: Player, turn: int, opponents: List[Player],
                  frac: float) -> str:
    log = []

    if turn > 1:
        player.draw()

    # 1. Play a land — prefer untapped duals, then untapped singles, last tapped
    def land_score(cd: CardData) -> int:
        dual    = sum(1 for c in cd.land_produces if c in 'RG') >= 2
        tapped  = cd.land_tapped
        if dual and not tapped: return 3
        if not tapped:          return 2
        return 1

    land_candidates = [(i, c) for i, c in enumerate(player.hand) if c.is_land]
    mdfc_candidates = [(i, c) for i, c in enumerate(player.hand)
                       if c.is_mdfc_land and not c.is_land]
    land_played = False

    if land_candidates:
        land_candidates.sort(key=lambda x: land_score(x[1]), reverse=True)
        idx, chosen = land_candidates[0]
        player.hand.pop(idx)
        player.lands.append(chosen)
        land_played = True
        note = ' (tapped)' if chosen.land_tapped else ''
        log.append(f"Land: {chosen.name}{note}")
    elif mdfc_candidates:
        idx, chosen = mdfc_candidates[0]
        proxy = CardData(name=f"{chosen.name} [land]", is_land=True,
                         land_produces=chosen.mdfc_produces,
                         land_tapped=chosen.mdfc_tapped)
        player.hand.pop(idx)
        player.lands.append(proxy)
        land_played = True
        log.append(f"Land: {chosen.name} (back face)")

    # 2. Play mana permanents (repeat until none affordable)
    changed = True
    while changed:
        changed = False
        t, r, g = compute_mana(player, turn, opponents, frac)
        for i, cd in enumerate(player.hand):
            if not cd.is_mana_perm:
                continue
            if _can_cast(cd, t, r, g, player.reducer_active):
                player.hand.pop(i)
                ready = turn + (1 if cd.perm_needs_untap else 0)
                player.mana_perms.append((cd, ready))
                if cd.perm_reducer:
                    player.reducer_active = True
                log.append(f"Cast: {cd.name}")
                changed = True
                break

    # 3. Play ramp spells (repeat until none affordable)
    changed = True
    while changed:
        changed = False
        t, r, g = compute_mana(player, turn, opponents, frac)
        for i, cd in enumerate(player.hand):
            if not cd.is_ramp:
                continue
            if _can_cast(cd, t, r, g, player.reducer_active):
                player.hand.pop(i)
                for _ in range(cd.ramp_untapped):
                    player.lands.append(CardData(name='Forest(ramp)', is_land=True,
                                                 land_produces=['G']))
                for _ in range(cd.ramp_tapped):
                    # Tapped lands are in play but tapped; still count for mana next turn.
                    # We add them directly — they contribute to total next turn automatically.
                    player.lands.append(CardData(name='Forest(ramp,tapped)', is_land=True,
                                                 land_produces=['G'], land_tapped=True))
                extra = cd.ramp_tapped + cd.ramp_untapped
                log.append(f"Cast: {cd.name} (+{extra} land)")
                changed = True
                break

    # Refresh mana after ramp
    t, r, g = compute_mana(player, turn, opponents, frac)

    # 4. Hellkite Courser — cheats commander onto battlefield via combat
    cmd_name = player.commander.name
    if player.commander_cast_turn is None and player.hellkite_cast_turn is None:
        hk = next((cd for cd in player.hand if cd.name == HELLKITE), None)
        if hk and _can_cast(hk, t, r, g, player.reducer_active):
            player.hand.remove(hk)
            player.hellkite_cast_turn = turn
            log.append(f"** CAST Hellkite Courser T{turn} → {cmd_name} enters T{turn+1} **")

    if player.hellkite_cast_turn == turn - 1 and player.commander_cast_turn is None:
        player.commander_cast_turn = turn
        log.append(f"** {cmd_name} ENTERS via Hellkite T{turn} **")

    # 5. Cast commander from command zone (always available, subject to commander tax)
    if player.commander_cast_turn is None:
        cmd = player.commander
        taxed_cmc = cmd.cmc + player.commander_tax
        # Build a taxed version for the can_cast check
        taxed = CardData(name=cmd.name, cmc=taxed_cmc, pips=cmd.pips)
        bt, br, bg = burst_bonus(player, turn, opponents, frac, t, r, g)
        if _can_cast(taxed, t + bt, r + br, g + bg, player.reducer_active):
            player.commander_cast_turn = turn
            tax_note = f" (tax +{player.commander_tax})" if player.commander_tax else ""
            burst_note = f" +{bt}burst" if bt > 0 else ""
            log.append(f"** CAST {cmd_name} T{turn}{tax_note} "
                       f"[{t}{burst_note}mana | {r}R {g}G] **")
            player.commander_tax += 2   # next cast costs 2 more

    # Informational: Mana Geyser / Exotic Orchard value
    gv = mana_geyser_val(opponents, frac)
    ec = exotic_colors(opponents)
    for cd in player.hand:
        if cd.burst_opp_tapped:
            log.append(f"  [Mana Geyser → {gv}R with {len(opponents)} opponents]")
            break
    if any('EXOTIC' in land.land_produces for land in player.lands):
        log.append(f"  [Exotic Orchard → {set(ec) if ec else 'dead'}]")

    # 6. Play generic spells if mana permits
    changed = True
    while changed:
        changed = False
        t, r, g = compute_mana(player, turn, opponents, frac)
        for i, cd in enumerate(player.hand):
            if cd.is_land or cd.is_mana_perm or cd.is_ramp or cd.is_burst:
                continue
            if cd.name == HELLKITE:
                continue
            if cd.cmc == 0:
                continue
            if _can_cast(cd, t, r, g, player.reducer_active):
                player.hand.pop(i)
                player.mana_perms.append((CardData(name=f'_spent_{cd.cmc}', cmc=cd.cmc,
                                                   is_mana_perm=True, perm_amount=0,
                                                   perm_produces=[]), turn))
                log.append(f"Cast: {cd.name} (generic)")
                changed = True
                break

    t, r, g = compute_mana(player, turn, opponents, frac)
    player.mana_per_turn.append(t)

    return f"  T{turn:2d}: " + (" | ".join(log) if log else "(no plays)")


# ---------------------------------------------------------------------------
# Simulation runners
# ---------------------------------------------------------------------------

def _run_one(deck_data: List[CardData], commander: CardData, num_turns: int,
             frac: float, verbose: bool) -> List[Player]:
    players = [Player(i + 1, deck_data, commander) for i in range(4)]
    for turn in range(1, num_turns + 1):
        for i, player in enumerate(players):
            opps = [p for j, p in enumerate(players) if j != i]
            entry = simulate_turn(player, turn, opps, frac)
            player.turn_log.append(entry)

    if verbose:
        for player in players:
            print(f"{'─'*68}")
            print(f"PLAYER {player.pid}")
            print(f"{'─'*68}")
            for entry in player.turn_log:
                print(entry)
            ct = f"T{player.commander_cast_turn}" if player.commander_cast_turn else "NOT CAST"
            print(f"  → {commander.name}: {ct}\n")

    return players


def run_sims(deck_data: List[CardData], commander: CardData,
             num_sims: int, num_turns: int, frac: float):
    all_turns = []
    last_players = []

    print(f"\n{'='*68}")
    print(f"RUNNING {num_sims} × 4-PLAYER SIMULATIONS")
    print(f"Commander: {commander.name} (CMC {commander.cmc})")
    print(f"{'='*68}\n")

    for sim in range(1, num_sims + 1):
        verbose = (num_sims == 1)
        players = _run_one(deck_data, commander, num_turns, frac, verbose)
        last_players = players
        sim_turns = [p.commander_cast_turn for p in players if p.commander_cast_turn]
        all_turns.extend(sim_turns)
        earliest = f"T{min(sim_turns)}" if sim_turns else "—"
        print(f"  Sim {sim}: Commander cast {len(sim_turns)}/4  |  "
              f"Earliest: {earliest:4s}  |  Turns: {sim_turns or ['none']}")

    total_slots = num_sims * 4
    print(f"\n{'─'*68}")
    print("AGGREGATE")
    print(f"{'─'*68}")
    print(f"  Commander cast rate: {len(all_turns)}/{total_slots} "
          f"({len(all_turns)/total_slots*100:.0f}%)")
    if all_turns:
        print(f"  Range:     T{min(all_turns)} – T{max(all_turns)}")
        print(f"  Average:   T{sum(all_turns)/len(all_turns):.1f}")
        buckets = defaultdict(int)
        for t in all_turns:
            buckets[t] += 1
        print("  Distribution:")
        for t in sorted(buckets):
            print(f"    T{t:2d}: {'█' * buckets[t]} ({buckets[t]})")

    # Final-turn multiplayer card value snapshot
    if last_players:
        avg_opp_lands = sum(len(p.lands) for p in last_players) / 4 * 3
        gv = int(avg_opp_lands * frac)
        ec = set()
        for p in last_players:
            ec |= set(exotic_colors([q for q in last_players if q.pid != p.pid]))
        print(f"\n  Multiplayer card value (end T{num_turns}):")
        print(f"    Mana Geyser:    ~{gv}R  (vs 0R solo goldfish)")
        print(f"    Exotic Orchard: {ec if ec else '{dead}'}  (vs dead solo goldfish)")


# ---------------------------------------------------------------------------
# Deck loading
# ---------------------------------------------------------------------------

def _parse_card_names(section_text: str) -> List[str]:
    names = []
    for line in section_text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        match = re.match(r'(\d+)\s+(.+)', line)
        if match:
            count = int(match.group(1))
            name  = match.group(2).strip()
            names.extend([name] * count)
    return names


def parse_deck_file(file_path: str):
    """Returns (commander_name: str, deck_names: List[str]) or (None, None) on error."""
    try:
        content = Path(file_path).read_text()
    except FileNotFoundError:
        print(f"Error: '{file_path}' not found.")
        return None, None

    # Parse COMMANDER: section
    cm = re.search(r'COMMANDER:\s*(.*?)(?=\n\n|\n[A-Z]+:|\Z)', content, re.DOTALL)
    commander_name = None
    if cm:
        names = _parse_card_names(cm.group(1))
        if names:
            commander_name = names[0]   # always 1 commander
    if not commander_name:
        print(f"Warning: Could not find COMMANDER: section in {file_path}")

    # Parse DECK: section (the 99)
    dm = re.search(r'DECK:\s*(.*?)(?=\n\n|\n[A-Z]+:|\Z)', content, re.DOTALL)
    if not dm:
        print(f"Error: Could not find DECK: section in {file_path}")
        return None, None

    return commander_name, _parse_card_names(dm.group(1))


def preload_deck(names: List[str]) -> List[CardData]:
    unique = list(dict.fromkeys(names))
    uncached = [n for n in unique if n not in _cache]
    if uncached:
        print(f"Fetching {len(uncached)} cards from Scryfall "
              f"({len(unique) - len(uncached)} cached)...")
        print("(Results cached locally — subsequent runs are instant)\n")
    classified = {}
    for i, name in enumerate(unique):
        classified[name] = classify_card(name)
        if (i + 1) % 10 == 0 and uncached:
            print(f"  {i+1}/{len(unique)} done...")
    if uncached:
        print()
    return [classified[n] for n in names]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Multiplayer Commander Goldfish Simulator (Scryfall-powered)'
    )
    parser.add_argument('deck_file')
    parser.add_argument('--sims',   type=int,   default=1)
    parser.add_argument('--turns',  type=int,   default=15)
    parser.add_argument('--tapped', type=float, default=0.60)
    args = parser.parse_args()

    _load_cache()
    random.seed(time.time_ns())

    commander_name, card_names = parse_deck_file(args.deck_file)
    if card_names is None:
        sys.exit(1)

    # Preload all cards including the commander
    all_names = ([commander_name] if commander_name else []) + card_names
    all_data = preload_deck(all_names)

    commander_data = all_data[0] if commander_name else CardData(name='Unknown Commander')
    deck_data = all_data[1:] if commander_name else all_data

    print(f"Deck: {args.deck_file}  |  Cards: {len(deck_data)}")
    print(f"Commander: {commander_data.name} (CMC {commander_data.cmc})")
    print(f"Turns: {args.turns}  |  Sims: {args.sims}  |  "
          f"Tapped fraction: {args.tapped:.0%}")

    run_sims(deck_data, commander_data, args.sims, args.turns, args.tapped)


if __name__ == '__main__':
    main()
