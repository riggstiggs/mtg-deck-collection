#!/usr/bin/env python3
"""
Multiplayer Goldfish Simulator — Scryfall-powered, deck-agnostic

This script simulates a 4-player Commander game (a "pod") to see how fast 
a deck can gold-fish its commander. It uses the Scryfall API to automatically
understand what cards do (ramp, rocks, dorks, etc.) so you don't have to 
manually tag them.

Usage:
  python3 scripts/multiplayer_goldfish.py <deck_file> [--sims N] [--turns N] [--tapped F]
"""

import random, re, sys, time, json, argparse, urllib.request, urllib.parse
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict
from typing import List, Optional

# --- Configuration & Constants ---
CACHE_FILE = Path('cache') / 'scryfall_cards.json' # Stores card data so we don't spam the API
SCRYFALL_BASE = 'https://api.scryfall.com/cards/named'
API_DELAY = 0.5    # Scryfall asks for no more than 2-10 requests per second
CARD_CACHE_TTL = 365 * 24 * 3600   # Cache cards for 1 year (Oracle text rarely changes)

HELLKITE = 'Hellkite Courser'   # A specific card that needs special logic to "cheat" the commander


# ---------------------------------------------------------------------------
# Card Data Structure
# ---------------------------------------------------------------------------

@dataclass
class CardData:
    """
    This is a 'blueprint' for a card. Instead of just a name, we store 
    specific attributes the simulator needs to calculate mana and timing.
    If you want the simulator to track a new mechanic (like 'Ward' or 'Stax'),
    you would start by adding a field here.
    """
    name: str
    cmc: int = 0
    pips: dict = field(default_factory=dict)       # colored mana needs, e.g. {'R':1,'G':1}

    # Land logic
    is_land: bool = False
    land_produces: List[str] = field(default_factory=list)  # ['R','G'] or ['EXOTIC']
    land_tapped: bool = False
    land_amount: int = 1                            # Usually 1, but 2 for "Bounce Lands"

    # Mana permanent logic (Mana Dorks, Mana Rocks, Enchantments like Wild Growth)
    is_mana_perm: bool = False
    perm_produces: List[str] = field(default_factory=list)
    perm_amount: int = 1
    perm_needs_untap: bool = False                  # True for creatures (summoning sickness)
    perm_reducer: bool = False                      # Does it make spells cheaper (e.g. Goblin Anarchomancer)

    # Creature info (Used for scaling cards like Priest of Titania)
    is_creature: bool = False                       
    is_titania: bool = False                        # Taps for G per Elf
    is_marwyn_card: bool = False                    # Taps for G equal to power

    # Ramp logic (Spells that put lands into play from library)
    is_ramp: bool = False
    ramp_tapped: int = 0
    ramp_untapped: int = 0

    # Burst mana logic (One-time mana like Seething Song or Mana Geyser)
    is_burst: bool = False
    burst_produces: List[str] = field(default_factory=list)
    burst_amount: int = 0
    burst_opp_tapped: bool = False                  # Scales with opponent lands (Mana Geyser)

    # Modal Double-Faced Cards (MDFCs)
    is_mdfc_land: bool = False                      # Can be played as a land if needed
    mdfc_produces: List[str] = field(default_factory=list)
    mdfc_tapped: bool = False


# ---------------------------------------------------------------------------
# Scryfall API + Local Caching
# ---------------------------------------------------------------------------

_cache: dict = {}

def _load_cache():
    """Reads the local JSON cache into memory at the start of the script."""
    global _cache
    if CACHE_FILE.exists():
        try:
            _cache = json.loads(CACHE_FILE.read_text())
        except Exception:
            _cache = {}

def _save_cache():
    """Writes the current memory cache to the JSON file to save API results."""
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(_cache, indent=2))
    except Exception:
        pass

def _fetch_scryfall(name: str) -> Optional[dict]:
    """
    Actually makes the network call to Scryfall. 
    It uses a custom User-Agent as requested by Scryfall's API rules.
    """
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
    """
    The main entry point for getting card data. 
    It checks the cache first. If missing or old, it calls the API.
    """
    key = name.lower()
    entry = _cache.get(key)
    # Check if we have it and if it's not expired
    if entry and (time.time() - entry.get('cached_at', 0)) < CARD_CACHE_TTL:
        return entry['data']
    
    # Respect API rate limits
    time.sleep(API_DELAY)
    data = _fetch_scryfall(name)
    
    # Update cache
    _cache[key] = {'data': data, 'cached_at': time.time()}
    _save_cache()
    return data


# ---------------------------------------------------------------------------
# Text Parsing Helpers (The Regex Engine)
# ---------------------------------------------------------------------------

def parse_mana_cost(cost_str: str):
    """
    Turns a string like '{2}{R}{G}' into (CMC: 4, Pips: {'R':1, 'G':1}).
    This helps the simulator know if we have the right COLORS to cast a spell.
    """
    if not cost_str:
        return 0, {}
    pips = {}
    cmc = 0
    # Find everything inside curly braces {}
    for tok in re.findall(r'\{([^}]+)\}', cost_str):
        if tok.isdigit():
            cmc += int(tok)
        elif tok in 'RGWUBC':
            pips[tok] = pips.get(tok, 0) + 1
            cmc += 1
        elif '/' in tok: # Handle hybrid mana like {G/P} or {B/G}
            c = tok[0]
            if c in 'RGWUBC':
                pips[c] = pips.get(c, 0) + 1
                cmc += 1
    return cmc, pips


def _parse_mana_production(oracle: str):
    """
    Reads the 'Oracle Text' (card rules) to figure out if it produces mana.
    It looks for phrases like '{T}: Add {G}' or 'Add one mana of any color'.
    """
    # Special Check: Mana Geyser (scales with opponents)
    if re.search(r'[Aa]dd \{[RGWUBC]\}.*for each tapped land your opponents', oracle):
        m = re.search(r'[Aa]dd \{([RGWUBC])\}', oracle)
        return ([m.group(1)] if m else ['R']), 0, True

    # Split text into sentences and check each one
    for sentence in re.split(r'(?<=[.!])\s', oracle):
        if not re.search(r'\bAdd\b', sentence, re.I):
            continue
        
        # Avoid false positives like "Add a +1/+1 counter"
        if re.search(r'add a |add an? |\badd \+', sentence, re.I):
            if not re.search(r'add.*\{[RGWUBC]\}|add.*mana', sentence, re.I):
                continue

        # "Add one mana of any color"
        if re.search(r'one mana of any color', sentence, re.I):
            return ['R', 'G', 'W', 'U', 'B'], 1, False

        # "Add {R} or {G}" — choice between colors
        choice_m = re.search(r'[Aa]dd \{([RGWUBC])\} or \{([RGWUBC])\}', sentence)
        if choice_m:
            return [choice_m.group(1), choice_m.group(2)], 1, False

        # "Add {G}{G}{G}" — multiple of same or different colors
        multi_m = re.search(r'[Aa]dd ((?:\{[RGWUBCS]\})+)', sentence)
        if multi_m:
            tokens = re.findall(r'\{([RGWUBC])\}', multi_m.group(1))
            snow   = re.findall(r'\{S\}', multi_m.group(1)) # Snow mana counts as Colorless
            colors = tokens + (['C'] * len(snow))
            if colors:
                return colors, len(colors), False

    return [], 0, False


def _parse_ramp(oracle: str):
    """
    Checks if a card is a 'Ramp' spell (Cultivate, Rampant Growth, etc.).
    Returns (how many enter tapped, how many enter untapped).
    """
    has_search = re.search(r'search your library', oracle, re.I)
    has_put    = re.search(r'put.*land.*onto the battlefield|put.*onto the battlefield.*land', oracle, re.I)
    if not has_search and not has_put:
        return 0, 0

    # Determine quantity (default 1)
    count = 1
    if re.search(r'up to two|two basic land|two land', oracle, re.I):
        count = 2
    elif re.search(r'up to three|three basic land', oracle, re.I):
        count = 3

    # Determine if they enter tapped
    if re.search(r'onto the battlefield tapped', oracle, re.I):
        return count, 0
    elif re.search(r'onto the battlefield', oracle, re.I):
        return 0, count
    
    return count, 0   # Default to tapped if unspecified


# ---------------------------------------------------------------------------
# Card Classification (The "Brain")
# ---------------------------------------------------------------------------

def classify_card(name: str) -> CardData:
    """
    This is the core logic that transforms a Scryfall JSON response into 
    our internal CardData object. It uses the parsing helpers above.
    """
    card = CardData(name=name)
    data = get_scryfall(name)

    if not data or data.get('object') == 'error':
        return card   # If we can't find it, treat it as a dead card

    faces     = data.get('card_faces')
    oracle    = data.get('oracle_text', '')
    type_line = data.get('type_line', '')
    mana_cost = data.get('mana_cost', '')

    # Handle Double-Faced Cards (Transforms or MDFCs)
    if faces:
        face0 = faces[0]
        face1 = faces[1] if len(faces) > 1 else {}
        oracle    = face0.get('oracle_text', '')
        type_line = face0.get('type_line', '')
        mana_cost = face0.get('mana_cost', '') or mana_cost

        # MDFC Logic: Check if the back face is a Land (like Glasspool Mimic)
        if 'Land' in face1.get('type_line', '') and 'Land' not in type_line:
            card.is_mdfc_land = True
            land_oracle = face1.get('oracle_text', '')
            prod = data.get('produced_mana', [])
            card.mdfc_produces = prod if prod else ['C']
            card.mdfc_tapped   = bool(re.search(r'enters.*tapped', land_oracle, re.I))
            card.cmc, card.pips = parse_mana_cost(mana_cost)
            
            # Check if the front face is ALSO a ramp spell (uncommon but possible)
            rt, ru = _parse_ramp(oracle)
            if rt + ru > 0:
                card.is_ramp = True
                card.ramp_tapped   = rt
                card.ramp_untapped = ru
            return card

    # Standard card processing
    card.cmc, card.pips = parse_mana_cost(mana_cost)
    card.is_creature = 'Creature' in type_line

    # Special handling for cards with dynamic mana scaling
    if name == 'Priest of Titania':
        card.is_titania = True
    elif name == 'Marwyn, the Nurturer':
        card.is_marwyn_card = True

    # --- Land Classification ---
    if 'Land' in type_line:
        card.is_land = True
        prod = data.get('produced_mana', [])
        card.land_produces = prod if prod else ['C']

        # Special Case: Exotic Orchard (needs opponent info)
        if name == 'Exotic Orchard' or re.search(
                r'could produce.*opponents|opponents.*could produce', oracle, re.I):
            card.land_produces = ['EXOTIC']

        card.land_tapped = bool(re.search(
            r'enters the battlefield tapped|enters tapped', oracle, re.I))

        # Check for lands that produce 2 mana (Ravnica bounce lands)
        if re.search(r'[Aa]dd \{[RGWUBC]\}\{[RGWUBC]\}', oracle):
            card.land_amount = 2

        return card

    # --- Mana Permanent (Dorks/Rocks) Classification ---
    colors, amount, is_opp = _parse_mana_production(oracle)
    if colors and amount >= 0:
        if is_opp:
            # Mana Geyser style (one-time burst)
            card.is_burst = True
            card.burst_produces  = colors
            card.burst_opp_tapped = True
        elif amount > 0:
            card.is_mana_perm    = True
            card.perm_produces   = colors
            card.perm_amount     = amount
            # Creatures have summoning sickness
            card.perm_needs_untap = 'Creature' in type_line
            # Check for cost reducers
            if re.search(r'costs? \{1\} less|the first.*spell.*costs? \{1\} less', oracle, re.I):
                card.perm_reducer = True
        return card

    # --- Burst Mana Spell (Rituals) Classification ---
    if 'Instant' in type_line or 'Sorcery' in type_line:
        m = re.search(r'[Aa]dd ((?:\{[RGWUBC]\}){2,})', oracle)
        if m:
            tokens = re.findall(r'\{([RGWUBC])\}', m.group(1))
            if tokens:
                card.is_burst      = True
                card.burst_produces = tokens
                card.burst_amount  = len(tokens)
                return card

    # --- Ramp Spell Classification ---
    rt, ru = _parse_ramp(oracle)
    if rt + ru > 0:
        card.is_ramp       = True
        card.ramp_tapped   = rt
        card.ramp_untapped = ru
        return card

    return card


# ---------------------------------------------------------------------------
# Player State Tracking
# ---------------------------------------------------------------------------

class Player:
    """
    Maintains the state of a single player in the pod.
    Handles mulligans, library, hand, and battlefield.
    """
    def __init__(self, pid: int, deck: List[CardData], commander: CardData):
        self.pid = pid
        lib = deck[:]
        random.shuffle(lib)

        # --- Commander Mulligan Logic ---
        # 1. First mulligan is free (draw 7).
        # 2. Subsequent mulligans draw one fewer card (6, 5, 4...).
        # 3. Simulator triggers mulligan if < 2 lands are found (greedy setting).
        def _land_count(hand):
            return sum(1 for c in hand if c.is_land or c.is_mdfc_land)

        hand_size = 7
        self.hand = [lib.pop(0) for _ in range(hand_size)]
        mull_count = 0
        while _land_count(self.hand) < 2 and mull_count < 3:
            lib2 = self.hand + lib
            random.shuffle(lib2)
            if mull_count == 0:
                new_size = 7
            else:
                new_size = 7 - mull_count
            self.hand = [lib2.pop(0) for _ in range(new_size)]
            lib = lib2
            mull_count += 1

        self.library: List[CardData] = lib
        self.lands: List[CardData] = []
        self.mana_perms: List[tuple] = []   # Format: (CardData, turn_it_becomes_ready)
        self.reducer_active = False         # Tracks if a cost reducer is on board
        self.turn_log: List[str] = []       # For the verbose output
        self.mana_per_turn: List[int] = []
        
        # Commander zone - always available
        self.commander: CardData = commander
        self.commander_tax: int = 0          
        self.commander_cast_turn: Optional[int] = None
        self.hellkite_cast_turn: Optional[int] = None
        
        # Scaling creature tracking
        self.creature_count: int = 0         
        self.marwyn_cast_turn: Optional[int] = None
        self.creatures_after_marwyn: int = 0  

    def draw(self):
        """Draws one card from library to hand."""
        if self.library:
            self.hand.append(self.library.pop(0))


# ---------------------------------------------------------------------------
# Mana Calculation Engine
# ---------------------------------------------------------------------------

def exotic_colors(opponents: List[Player]) -> List[str]:
    """Determines what colors Exotic Orchard can produce based on opponents' lands."""
    colors = set()
    for opp in opponents:
        for land in opp.lands:
            for c in land.land_produces:
                if c not in ('C', 'EXOTIC'):
                    colors.add(c)
    return list(colors)


def mana_geyser_val(opponents: List[Player], frac: float) -> int:
    """Estimates how much mana 'Mana Geyser' produces based on total opponent lands."""
    # We multiply by 'frac' because not all opponent lands are tapped every turn.
    return int(sum(len(o.lands) for o in opponents) * frac)


def compute_mana(player: Player, turn: int, opponents: List[Player], frac: float):
    """
    Calculates total mana available this turn.
    Returns (total_mana, r, g, w, u, b).
    """
    total = r = g = w = u = b = 0

    # 1. Process Lands
    for land in player.lands:
        amt      = land.land_amount
        produces = land.land_produces
        if 'EXOTIC' in produces:
            ec = exotic_colors(opponents)
            if ec:
                total += amt
                if 'R' in ec: r += amt
                if 'G' in ec: g += amt
                if 'W' in ec: w += amt
                if 'U' in ec: u += amt
                if 'B' in ec: b += amt
        else:
            total += amt
            if 'R' in produces: r += amt
            if 'G' in produces: g += amt
            if 'W' in produces: w += amt
            if 'U' in produces: u += amt
            if 'B' in produces: b += amt

    # 2. Process Ready Permanents (Dorks/Rocks)
    for (cd, ready) in player.mana_perms:
        if turn < ready: # Check for summoning sickness or 'enters tapped' rocks
            continue

        if cd.is_titania:
            amt = player.creature_count # priest taps for elf count
        elif cd.is_marwyn_card:
            amt = 1 + player.creatures_after_marwyn # marwyn taps for power
        else:
            amt = cd.perm_amount

        total += amt
        if 'R' in cd.perm_produces: r += amt
        if 'G' in cd.perm_produces: g += amt
        if 'W' in cd.perm_produces: w += amt
        if 'U' in cd.perm_produces: u += amt
        if 'B' in cd.perm_produces: b += amt

    return total, r, g, w, u, b


def burst_bonus(player: Player, turn: int, opponents: List[Player], frac: float,
                base_total: int, base_r: int, base_g: int, base_w: int, base_u: int,
                base_b: int):
    """
    Checks hand for Rituals (Seething Song, etc.).
    Returns how much extra mana we get if we cast them right now.
    """
    bonus_t = bonus_r = bonus_g = bonus_w = bonus_u = bonus_b = 0
    for cd in player.hand:
        if not cd.is_burst:
            continue

        # Check if we have enough mana to cast the ritual itself
        cur_t = base_total + bonus_t
        cur_r = base_r + bonus_r
        cur_g = base_g + bonus_g
        cur_w = base_w + bonus_w
        cur_u = base_u + bonus_u
        cur_b = base_b + bonus_b
        if not _can_cast(cd, cur_t, cur_r, cur_g, cur_w, cur_u, cur_b, player.reducer_active):
            continue

        if cd.burst_opp_tapped: # Mana Geyser
            produced = mana_geyser_val(opponents, frac)
            net = produced - cd.cmc
            bonus_t += net
            bonus_r += produced
        else: # Standard rituals
            net = cd.burst_amount - cd.cmc
            bonus_t += net
            for c in cd.burst_produces:
                if c == 'R': bonus_r += 1
                elif c == 'G': bonus_g += 1
                elif c == 'W': bonus_w += 1
                elif c == 'U': bonus_u += 1
                elif c == 'B': bonus_b += 1

    return bonus_t, bonus_r, bonus_g, bonus_w, bonus_u, bonus_b


def _can_cast(cd: CardData, total: int, r: int, g: int, w: int, u: int, b: int,
              reducer: bool) -> bool:
    """
    The 'Is it Legal?' check.
    Compares card CMC and Pips against available mana.
    """
    cost = max(0, cd.cmc - (1 if reducer else 0))
    if total < cost:
        return False
    if cd.pips.get('R', 0) > r:
        return False
    if cd.pips.get('G', 0) > g:
        return False
    if cd.pips.get('W', 0) > w:
        return False
    if cd.pips.get('U', 0) > u:
        return False
    if cd.pips.get('B', 0) > b:
        return False
    return True


# ---------------------------------------------------------------------------
# Turn Logic Engine (The "Player AI")
# ---------------------------------------------------------------------------

def simulate_turn(player: Player, turn: int, opponents: List[Player],
                  frac: float) -> str:
    """
    Executes a single turn for a player.
    It follows a prioritized 'Script':
    1. Land -> 2. Mana Dorks -> 3. Ramp Spells -> 4. Special Tech -> 5. Commander -> 6. Spells
    """
    log = []

    player.draw() 

    # --- 1. Play a Land ---
    # Prioritize: Untapped Duals > Untapped Singles > Tapped Lands
    def land_score(cd: CardData) -> int:
        dual    = sum(1 for c in cd.land_produces if c in 'RG') >= 2
        tapped  = cd.land_tapped
        if dual and not tapped: return 3
        if not tapped:          return 2
        return 1

    land_candidates = [(i, c) for i, c in enumerate(player.hand) if c.is_land]
    mdfc_candidates = [(i, c) for i, c in enumerate(player.hand)
                       if c.is_mdfc_land and not c.is_land]
    
    if land_candidates:
        land_candidates.sort(key=lambda x: land_score(x[1]), reverse=True)
        idx, chosen = land_candidates[0]
        player.hand.pop(idx)
        player.lands.append(chosen)
        note = ' (tapped)' if chosen.land_tapped else ''
        log.append(f"Land: {chosen.name}{note}")
    elif mdfc_candidates: # Play MDFC as land if no real lands available
        idx, chosen = mdfc_candidates[0]
        proxy = CardData(name=f"{chosen.name} [land]", is_land=True,
                         land_produces=chosen.mdfc_produces,
                         land_tapped=chosen.mdfc_tapped)
        player.hand.pop(idx)
        player.lands.append(proxy)
        log.append(f"Land: {chosen.name} (back face)")

    # --- 2. Cast Mana Permanents ---
    # We loop because playing one dork might enable playing another (if we have untapped mana)
    changed = True
    while changed:
        changed = False
        t, r, g, w, u, b = compute_mana(player, turn, opponents, frac)
        for i, cd in enumerate(player.hand):
            if not cd.is_mana_perm:
                continue
            if _can_cast(cd, t, r, g, w, u, b, player.reducer_active):
                player.hand.pop(i)
                # Mark when it becomes usable (next turn for creatures)
                ready = turn + (1 if cd.perm_needs_untap else 0)
                player.mana_perms.append((cd, ready))

                if cd.perm_reducer:
                    player.reducer_active = True
                if cd.perm_needs_untap:
                    player.creature_count += 1
                    if cd.is_marwyn_card:
                        player.marwyn_cast_turn = turn
                    elif player.marwyn_cast_turn is not None:
                        player.creatures_after_marwyn += 1
                log.append(f"Cast: {cd.name}")
                changed = True
                break

    # --- 3. Cast Ramp Spells ---
    changed = True
    while changed:
        changed = False
        t, r, g, w, u, b = compute_mana(player, turn, opponents, frac)
        for i, cd in enumerate(player.hand):
            if not cd.is_ramp:
                continue
            if _can_cast(cd, t, r, g, w, u, b, player.reducer_active):
                player.hand.pop(i)
                # Add the "ghost" lands put into play by the ramp spell
                for _ in range(cd.ramp_untapped):
                    player.lands.append(CardData(name='Forest(ramp)', is_land=True, land_produces=['G']))
                for _ in range(cd.ramp_tapped):
                    player.lands.append(CardData(name='Forest(ramp,tapped)', is_land=True,
                                                 land_produces=['G'], land_tapped=True))
                extra = cd.ramp_tapped + cd.ramp_untapped
                log.append(f"Cast: {cd.name} (+{extra} land)")
                changed = True
                break

    # Refresh mana pool after all ramp actions
    t, r, g, w, u, b = compute_mana(player, turn, opponents, frac)

    # --- 4. Hellkite Courser Tech ---
    cmd_name = player.commander.name
    if player.commander_cast_turn is None and player.hellkite_cast_turn is None:
        hk = next((cd for cd in player.hand if cd.name == HELLKITE), None)
        if hk and _can_cast(hk, t, r, g, w, u, b, player.reducer_active):
            player.hand.remove(hk)
            player.hellkite_cast_turn = turn
            log.append(f"** CAST Hellkite Courser T{turn} -> {cmd_name} enters T{turn+1} **")

    if player.hellkite_cast_turn == turn - 1 and player.commander_cast_turn is None:
        player.commander_cast_turn = turn
        log.append(f"** {cmd_name} ENTERS via Hellkite T{turn} **")

    # --- 5. Cast Commander ---
    if player.commander_cast_turn is None:
        cmd = player.commander
        taxed_cmc = cmd.cmc + player.commander_tax
        taxed = CardData(name=cmd.name, cmc=taxed_cmc, pips=cmd.pips)

        # Ritual check
        bt, br, bg, bw, bu, bb = burst_bonus(player, turn, opponents, frac, t, r, g, w, u, b)

        if _can_cast(taxed, t + bt, r + br, g + bg, w + bw, u + bu, b + bb,
                     player.reducer_active):
            player.commander_cast_turn = turn
            tax_note = f" (tax +{player.commander_tax})" if player.commander_tax else ""
            burst_note = f" +{bt}burst" if bt > 0 else ""
            log.append(f"** CAST {cmd_name} T{turn}{tax_note} "
                       f"[{t}{burst_note}mana | {r}R {g}G {w}W {u}U {b}B] **")
            player.commander_tax += 2

    # --- 6. Spend remaining mana on generic spells ---
    changed = True
    while changed:
        changed = False
        t, r, g, w, u, b = compute_mana(player, turn, opponents, frac)
        for i, cd in enumerate(player.hand):
            # Skip cards we already tried to play or can't play
            if cd.is_land or cd.is_mana_perm or cd.is_ramp or cd.is_burst:
                continue
            if cd.name == HELLKITE or cd.cmc == 0:
                continue

            if _can_cast(cd, t, r, g, w, u, b, player.reducer_active):
                player.hand.pop(i)
                # Record the mana as 'spent' so we don't double-dip
                player.mana_perms.append((CardData(name=f'_spent_{cd.cmc}', cmc=cd.cmc,
                                                   is_mana_perm=True, perm_amount=0), turn))
                if cd.is_creature:
                    player.creature_count += 1
                    if player.marwyn_cast_turn is not None:
                        player.creatures_after_marwyn += 1
                log.append(f"Cast: {cd.name} (generic)")
                changed = True
                break

    # Record turn-end stats
    t, r, g, w, u, b = compute_mana(player, turn, opponents, frac)
    player.mana_per_turn.append(t)

    return f"  T{turn:2d}: " + (" | ".join(log) if log else "(no plays)")


# ---------------------------------------------------------------------------
# Simulation Orchestration
# ---------------------------------------------------------------------------

def _run_one(deck_data: List[CardData], commander: CardData, num_turns: int,
             frac: float, verbose: bool) -> List[Player]:
    """Runs one full 4-player game simulation."""
    players = [Player(i + 1, deck_data, commander) for i in range(4)]
    for turn in range(1, num_turns + 1):
        for i, player in enumerate(players):
            # Pass other players as 'opponents' for Exotic Orchard/Mana Geyser logic
            opps = [p for j, p in enumerate(players) if j != i]
            entry = simulate_turn(player, turn, opps, frac)
            player.turn_log.append(entry)

    if verbose:
        for player in players:
            print(f"{'-'*68}\nPLAYER {player.pid}\n{'-'*68}")
            for entry in player.turn_log:
                print(entry)
            ct = f"T{player.commander_cast_turn}" if player.commander_cast_turn else "NOT CAST"
            print(f"  -> {commander.name}: {ct}  |  Creatures cast: {player.creature_count}\n")

    return players


def run_sims(deck_data: List[CardData], commander: CardData,
             num_sims: int, num_turns: int, frac: float):
    """
    Runs many simulations and aggregates the statistics.
    This is what calculates the 'Average Turn' and 'Cast Rate'.
    """
    all_turns = []
    all_creature_counts = []
    last_players = []

    print(f"\n{'='*68}\nRUNNING {num_sims} × 4-PLAYER SIMULATIONS")
    print(f"Commander: {commander.name} (CMC {commander.cmc})\n{'='*68}\n")

    for sim in range(1, num_sims + 1):
        # Verbose output only if running 1 simulation
        verbose = (num_sims == 1)
        players = _run_one(deck_data, commander, num_turns, frac, verbose)
        last_players = players
        
        sim_turns = [p.commander_cast_turn for p in players if p.commander_cast_turn]
        sim_creatures = [p.creature_count for p in players]
        
        all_turns.extend(sim_turns)
        all_creature_counts.extend(sim_creatures)
        
        earliest = f"T{min(sim_turns)}" if sim_turns else "-"
        avg_cr = sum(sim_creatures) / len(sim_creatures)
        print(f"  Sim {sim}: Commander cast {len(sim_turns)}/4  |  "
              f"Earliest: {earliest:4s}  |  Turns: {sim_turns or ['none']}  |  "
              f"Avg creatures: {avg_cr:.1f}")

    # --- Print Aggregate Stats ---
    total_slots = num_sims * 4
    print(f"\n{'-'*68}\nAGGREGATE\n{'-'*68}")
    print(f"  Commander cast rate: {len(all_turns)}/{total_slots} ({len(all_turns)/total_slots*100:.0f}%)")
    
    if all_turns:
        print(f"  Range:     T{min(all_turns)} - T{max(all_turns)}")
        print(f"  Average:   T{sum(all_turns)/len(all_turns):.1f}")
        buckets = defaultdict(int)
        for t in all_turns: buckets[t] += 1
        print("  Distribution:")
        for t in sorted(buckets):
            print(f"    T{t:2d}: {'#' * buckets[t]} ({buckets[t]})")

    if all_creature_counts:
        avg_cr = sum(all_creature_counts) / len(all_creature_counts)
        print(f"\n  Avg creatures per seat (end T{num_turns}): {avg_cr:.1f}")


# ---------------------------------------------------------------------------
# File Loading Logic
# ---------------------------------------------------------------------------

def _parse_card_names(section_text: str) -> List[str]:
    """Helper to extract names from Moxfield-style lists (e.g. '1 Sol Ring')."""
    names = []
    for line in section_text.strip().split('\n'):
        line = line.strip()
        if not line: continue
        match = re.match(r'(\d+)\s+(.+)', line)
        if match:
            count = int(match.group(1))
            name  = match.group(2).strip()
            names.extend([name] * count)
    return names


def parse_deck_file(file_path: str):
    """
    Reads the Markdown deck file and extracts the COMMANDER and DECK sections.
    """
    try:
        content = Path(file_path).read_text()
    except FileNotFoundError:
        print(f"Error: '{file_path}' not found.")
        return None, None

    # Use Regex to find sections
    cm = re.search(r'COMMANDER:\s*(.*?)(?=\n\n|\n[A-Z]+:|\Z)', content, re.DOTALL)
    commander_name = _parse_card_names(cm.group(1))[0] if cm else None
    
    dm = re.search(r'DECK:\s*(.*?)(?=\n\n|\n[A-Z]+:|\Z)', content, re.DOTALL)
    if not dm:
        print(f"Error: Could not find DECK: section in {file_path}")
        return None, None

    return commander_name, _parse_card_names(dm.group(1))


def preload_deck(names: List[str]) -> List[CardData]:
    """
    Fetches all unique cards in the deck once before starting simulations.
    This makes the actual simulation run extremely fast.
    """
    unique = list(dict.fromkeys(names))
    uncached = [n for n in unique if n.lower() not in _cache]
    if uncached:
        print(f"Fetching {len(uncached)} cards from Scryfall...")
    
    classified = {}
    for i, name in enumerate(unique):
        classified[name] = classify_card(name)
        if (i + 1) % 10 == 0 and uncached:
            print(f"  {i+1}/{len(unique)} done...")
    return [classified[n] for n in names]


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Multiplayer Goldfish Simulator')
    parser.add_argument('deck_file', help='Path to the deck Markdown file')
    parser.add_argument('--sims',   type=int,   default=1,  help='Number of 4-player games to run')
    parser.add_argument('--turns',  type=int,   default=15, help='Max turns per game')
    parser.add_argument('--tapped', type=float, default=0.60, help='Est % of opponent lands tapped')
    args = parser.parse_args()

    _load_cache()
    random.seed(time.time_ns()) # Ensure true randomness for every run

    commander_name, card_names = parse_deck_file(args.deck_file)
    if card_names is None: sys.exit(1)

    all_names = ([commander_name] if commander_name else []) + card_names
    all_data = preload_deck(all_names)

    commander_data = all_data[0] if commander_name else CardData(name='Unknown')
    deck_data = all_data[1:] if commander_name else all_data

    run_sims(deck_data, commander_data, args.sims, args.turns, args.tapped)


if __name__ == '__main__':
    main()
