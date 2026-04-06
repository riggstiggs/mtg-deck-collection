#!/usr/bin/env python3
"""
Manapool Price Deck — Automated Pricing & Availability Checker

This script calculates the cost of a deck by searching for real-world 
prices on Manapool.com. It works in three phases:
1. Find every physical printing of each card via Scryfall.
2. Check Manapool to see which printings are actually in stock.
3. Select the cheapest 'Acceptable' version (e.g. Near Mint over Damaged).

It includes complex logic for 'Rate Limiting' (waiting between web calls)
and 'Caching' (remembering data so we don't ask the same question twice).
"""

import sys
import json
import time
import os
import urllib.request
import urllib.parse
from collections import defaultdict

# --- Configuration & Labels ---
SCRYFALL_HEADERS = {"User-Agent": "MTGDeckCollection/1.0", "Accept": "application/json"}
MANAPOOL_BASE = "https://manapool.com/api/v1"

# We skip basic lands because they are usually free/pennies and clutter the report.
BASIC_LANDS = {"Plains", "Island", "Swamp", "Mountain", "Forest"}

# Human-readable labels for card conditions and foil finishes
CONDITION_LABELS = {"NM": "NM", "LP": "LP", "MP": "MP", "HP": "HP", "DMG": "DMG"}
FINISH_LABELS = {"NF": "", "FO": " (Foil)", "ET": " (Etched)"}

# Priority Order: If we have multiple choices, we prefer Near Mint (NM) 
# over Lightly Played (LP), etc. We avoid Damaged (DMG) by default.
CONDITION_PREFERENCE = ["NM", "LP", "MP", "HP"]

# --- Network & Performance Settings ---
# APIs have 'Rate Limits'. If we call them too fast, they will block us.
SCRYFALL_DELAY = 0.5       # Wait 0.5 seconds between Scryfall calls (2 per second limit)
MANAPOOL_DELAY = 0.3       # Wait 0.3 seconds between Manapool batches
RETRY_BASE_DELAY = 2.0     # If the server is busy, wait this long before trying again
MAX_RETRIES = 5            # Give up after 5 failed attempts

# --- Caching Logic ---
# 'Caching' means saving results to a file. This makes the script 
# run 100x faster the second time because it doesn't need to use the internet.
CACHE_DIR = "cache"
PRINTINGS_CACHE_FILE = os.path.join(CACHE_DIR, "scryfall_printings.json")
PRINTINGS_CACHE_TTL = 120 * 24 * 3600  # Data is considered 'fresh' for 120 days

_printings_cache = None

def _load_printings_cache():
    """Reads the saved card IDs from the disk into memory."""
    global _printings_cache
    if _printings_cache is not None:
        return
    if os.path.exists(PRINTINGS_CACHE_FILE):
        try:
            with open(PRINTINGS_CACHE_FILE, encoding="utf-8") as f:
                _printings_cache = json.load(f)
            return
        except Exception as e:
            print(f"  [cache] Warning: could not load {PRINTINGS_CACHE_FILE}: {e}")
    _printings_cache = {}

def _save_printings_cache():
    """Writes the current memory cache to a JSON file."""
    if _printings_cache is None:
        return
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(PRINTINGS_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_printings_cache, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"  [cache] Warning: could not save {PRINTINGS_CACHE_FILE}: {e}")

def _get_cached_ids(name):
    """Checks if we already know the Scryfall IDs for a specific card name."""
    _load_printings_cache()
    entry = _printings_cache.get(name.lower())
    if entry and (time.time() - entry.get("cached_at", 0)) < PRINTINGS_CACHE_TTL:
        return entry["ids"]
    return None

def _set_cached_ids(name, ids):
    """Saves Scryfall IDs for a card name into our memory cache."""
    _load_printings_cache()
    _printings_cache[name.lower()] = {"ids": ids, "cached_at": time.time()}

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def fetch_with_retry(url, headers, label="request"):
    """
    Makes a web request. If it fails due to being 'too fast' (HTTP 429), 
    it waits and tries again automatically.
    """
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            # 429 = Too many requests, 5xx = Server error
            if e.code == 429 or e.code >= 500:
                wait = RETRY_BASE_DELAY * (2 ** attempt) # Exponential backoff: 2s, 4s, 8s...
                print(f"  [rate limit] {label} got HTTP {e.code}, waiting {wait:.1f}s before retry...")
                time.sleep(wait)
            else:
                print(f"  [error] {label} failed with HTTP {e.code}")
                return None
        except Exception as e:
            print(f"  [error] {label} failed: {e}")
            return None
    return None

def parse_decklist(path):
    """
    Reads a Moxfield export text file and extracts just the card names.
    It handles sections like 'Commander' and 'Deck'.
    """
    cards = []
    seen = set()
    in_deck = False
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Look for headers
            if line.lower().rstrip(":") in ("deck", "commander"):
                in_deck = True
                continue
            if not in_deck or not line:
                continue
            # Moxfield format is "1 Card Name"
            parts = line.split(" ", 1)
            if len(parts) < 2:
                continue
            name = parts[1].replace(" *CMDR*", "").strip()
            if name in BASIC_LANDS:
                continue
            if name not in seen:
                cards.append(name)
                seen.add(name)
    return cards

def get_all_scryfall_ids(card_name):
    """
    Asks Scryfall for every single paper printing of a card.
    One card name (like 'Sol Ring') has dozens of IDs (one for each set).
    """
    cached = _get_cached_ids(card_name)
    if cached is not None:
        return cached

    ids = []
    # Search for the exact name, paper cards only, no digital-only cards.
    safe = urllib.parse.quote(f'!"{card_name}" game:paper -is:digital')
    url = f"https://api.scryfall.com/cards/search?q={safe}&order=usd&unique=prints"
    
    while url:
        time.sleep(SCRYFALL_DELAY)
        data = fetch_with_retry(url, SCRYFALL_HEADERS, label=f"Scryfall '{card_name}'")
        if not data:
            break
        for card in data.get("data", []):
            ids.append(card["id"])
        # Handle multi-page results
        url = data.get("next_page") if data.get("has_more") else None

    if ids:
        _set_cached_ids(card_name, ids)
    return ids

def query_manapool_batch(scryfall_ids):
    """
    Manapool allows us to check 100 cards at once. This is much faster
    than checking them one by one.
    """
    if not scryfall_ids:
        return []
    # Join all IDs into a single web link
    params = "&".join(f"scryfall_ids={sid}" for sid in scryfall_ids)
    url = f"{MANAPOOL_BASE}/products/singles?{params}"
    data = fetch_with_retry(url, {"Accept": "application/json"}, label="Manapool batch")
    return data.get("data", []) if data else []

def best_available_variant(product):
    """
    Given a card on Manapool, find the specific listing we want.
    
    Logic:
    1. Filter out variants that are out of stock.
    2. Ignore 'Damaged' cards unless specified.
    3. Find the cheapest 'Near Mint' version.
    4. If no NM, find the next best condition (LP, MP...).
    """
    url = product.get("url", "")
    if not product.get("available_quantity"):
        return None, None, url

    acceptable = []
    dmg_only = False

    for v in product.get("variants", []):
        if v.get("available_quantity", 0) <= 0:
            continue
        price = v.get("low_price", 0)
        if not price or price <= 0:
            continue
            
        condition = v.get("condition_id", "")
        if condition == "DMG":
            dmg_only = True
        else:
            acceptable.append(v)

    if not acceptable:
        # If we only found Damaged cards, return a special flag
        return (None, "DMG_ONLY", url) if dmg_only else (None, None, url)

    # Search for cheapest Near Mint
    nm_variants = [v for v in acceptable if v.get("condition_id") == "NM"]
    if nm_variants:
        best = min(nm_variants, key=lambda v: v["low_price"])
    else:
        # If no NM, sort by our Condition Preference list
        def sort_key(v):
            cond = v.get("condition_id", "")
            pref = CONDITION_PREFERENCE.index(cond) if cond in CONDITION_PREFERENCE else 99
            return (pref, v["low_price"])
        best = min(acceptable, key=sort_key)

    # Format the price and label (e.g. "NM (Foil)")
    price_dollars = best["low_price"] / 100.0
    condition = CONDITION_LABELS.get(best.get("condition_id", ""), "?")
    finish = FINISH_LABELS.get(best.get("finish_id", "NF"), "")
    return price_dollars, f"{condition}{finish}", url

# ---------------------------------------------------------------------------
# Main Execution
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/manapool_price_deck.py <moxfield_import.txt>")
        sys.exit(1)

    deck_path = sys.argv[1]
    cards = parse_decklist(deck_path)
    print(f"Loaded {len(cards)} unique non-basic cards.\n")

    # PHASE 1: Find all printings for each card
    print("Step 1: Finding all card IDs on Scryfall...")
    card_to_ids = {}
    for i, name in enumerate(cards):
        ids = get_all_scryfall_ids(name)
        card_to_ids[name] = ids
        print(f"  [{i+1}/{len(cards)}] {name}: {len(ids)} printing(s)")

    # PHASE 2: Map those IDs back to card names for the results
    id_to_card = {}
    all_ids = []
    for name, ids in card_to_ids.items():
        for sid in ids:
            id_to_card[sid] = name
            all_ids.append(sid)

    # PHASE 3: Query Manapool in batches of 100
    print(f"\nStep 2: Checking live inventory on Manapool...")
    card_products = defaultdict(list)
    for i in range(0, len(all_ids), 100):
        batch = all_ids[i:i+100]
        products = query_manapool_batch(batch)
        for product in products:
            name = id_to_card.get(product.get("scryfall_id", ""), "?")
            card_products[name].append(product)
        time.sleep(MANAPOOL_DELAY)

    # PHASE 4: Final Selection & Reporting
    print("\n" + "=" * 65)
    print(f"{'DECK PRICING SUMMARY':^65}")
    print("=" * 65)

    results = []
    out_of_stock, dmg_only, not_found = [], [], []

    for name in cards:
        products = card_products.get(name, [])
        if not products:
            not_found.append(name)
            continue

        # Look through all printings we found to find the best price
        best_price, best_label, best_url = None, None, None
        has_dmg_only = False

        for product in products:
            price, label, url = best_available_variant(product)
            if label == "DMG_ONLY":
                has_dmg_only = True
                continue
            if price is not None:
                if best_price is None or price < best_price:
                    best_price, best_label, best_url = price, label, url

        if best_price is None:
            if has_dmg_only: dmg_only.append(name)
            else: out_of_stock.append(name)
        else:
            results.append((name, best_price, best_label, best_url))

    # Sort results so the most expensive cards are at the top
    results.sort(key=lambda x: x[1], reverse=True)
    total = sum(r[1] for r in results)

    for name, price, label, url in results:
        print(f"  ${price:>6.2f}  [{label:>12}]  {name}")
        print(f"             {url}")

    # Summary Stats
    print("\n" + "=" * 65)
    print(f"  Total (in stock): ${total:.2f}")
    print("=" * 65)

    # Save results to a log file for later viewing
    _save_printings_cache()

if __name__ == "__main__":
    main()
