"""
manapool_price_deck.py
----------------------
Prices a decklist using the Manapool API.
- Finds ALL paper printings for each card via Scryfall
- Queries Manapool for availability and price across every printing
- Reports the cheapest IN-STOCK option per card (any condition)
- Outputs a summary sorted by price descending with a deck total

Rate limiting:
- Scryfall: 100ms between requests, exponential backoff on 429/5xx (max 5 retries)
- Manapool: 300ms between batches of 100 IDs

Usage:
    python scripts/manapool_price_deck.py <moxfield_import.txt>

Example:
    python scripts/manapool_price_deck.py "commander_decks/Planning/MarchesaBlackRose/marchesa_budget_main_moxfield_import.txt"
"""

import sys
import json
import time
import urllib.request
import urllib.parse
from collections import defaultdict

SCRYFALL_HEADERS = {"User-Agent": "MTGDeckCollection/1.0", "Accept": "application/json"}
MANAPOOL_BASE = "https://manapool.com/api/v1"
BASIC_LANDS = {"Plains", "Island", "Swamp", "Mountain", "Forest"}
CONDITION_LABELS = {"NM": "NM", "LP": "LP", "MP": "MP", "HP": "HP", "DMG": "DMG"}
FINISH_LABELS = {"NF": "", "FO": " (Foil)", "ET": " (Etched)"}
# Condition preference order (lower index = more preferred)
CONDITION_PREFERENCE = ["NM", "LP", "MP", "HP"]
# DMG is intentionally excluded — flagged separately if it's the only option

# Rate limit settings
# Scryfall limits: /cards/search and /cards/named = 2/sec (500ms min between calls)
# Other Scryfall endpoints = 10/sec (100ms). We only use search and named, so use 500ms.
# Manapool: no published limit — 300ms between batches is conservative.
SCRYFALL_DELAY = 0.5       # 500ms between Scryfall requests (search/named limit: 2/sec)
MANAPOOL_DELAY = 0.3       # 300ms between Manapool batches
RETRY_BASE_DELAY = 2.0     # Base delay for exponential backoff on 429 (seconds)
MAX_RETRIES = 5


def fetch_with_retry(url, headers, label="request"):
    """GET a URL with exponential backoff on 429 or 5xx responses."""
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                wait = RETRY_BASE_DELAY * (2 ** attempt)
                print(f"  [rate limit] {label} got HTTP {e.code}, waiting {wait:.1f}s before retry {attempt+1}/{MAX_RETRIES}...")
                time.sleep(wait)
            else:
                print(f"  [error] {label} failed with HTTP {e.code}: {e.reason}")
                return None
        except Exception as e:
            print(f"  [error] {label} failed: {e}")
            return None
    print(f"  [error] {label} failed after {MAX_RETRIES} retries")
    return None


def parse_decklist(path):
    """Parse a Moxfield import txt file. Returns list of card names (no basics, no dupes)."""
    cards = []
    seen = set()
    in_deck = False
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.lower().rstrip(":") in ("deck", "commander"):
                in_deck = True
                continue
            if not in_deck or not line:
                continue
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
    """Return all paper Scryfall IDs for a card, sorted cheapest first."""
    ids = []
    safe = urllib.parse.quote(f'!"{card_name}" game:paper -is:digital')
    url = f"https://api.scryfall.com/cards/search?q={safe}&order=usd&dir=asc&unique=prints"
    page = 1
    while url:
        time.sleep(SCRYFALL_DELAY)
        data = fetch_with_retry(url, SCRYFALL_HEADERS, label=f"Scryfall search '{card_name}' p{page}")
        if not data:
            break
        for card in data.get("data", []):
            ids.append(card["id"])
        url = data.get("next_page") if data.get("has_more") else None
        page += 1

    # Fallback: if search returned nothing, try /cards/named for at least one canonical ID
    if not ids:
        time.sleep(SCRYFALL_DELAY)
        safe_name = urllib.parse.quote(card_name)
        fallback_url = f"https://api.scryfall.com/cards/named?exact={safe_name}"
        data = fetch_with_retry(fallback_url, SCRYFALL_HEADERS, label=f"Scryfall named fallback '{card_name}'")
        if data and "id" in data:
            ids.append(data["id"])
            print(f"    (used named fallback for '{card_name}')")

    return ids


def query_manapool_batch(scryfall_ids):
    """Query Manapool /products/singles for up to 100 scryfall IDs at once."""
    if not scryfall_ids:
        return []
    params = "&".join(f"scryfall_ids={sid}" for sid in scryfall_ids)
    url = f"{MANAPOOL_BASE}/products/singles?{params}"
    data = fetch_with_retry(url, {"Accept": "application/json"}, label=f"Manapool batch ({len(scryfall_ids)} IDs)")
    return data.get("data", []) if data else []


def best_available_variant(product):
    """Return (price_cents, condition_label, url) for the best variant per user preferences:
    - Prefer NM; avoid DMG entirely
    - Among NM options, take cheapest (any finish)
    - If no NM, fall back to cheapest non-DMG variant (LP → MP → HP)
    - Returns (None, None, url) if only DMG is available or nothing is in stock
    - Returns (None, "DMG_ONLY", url) if DMG is the only in-stock option (flagged separately)
    """
    url = product.get("url", "")

    if not product.get("available_quantity"):
        return None, None, url

    # Collect all in-stock non-DMG variants
    acceptable = []
    dmg_only_candidates = []

    for v in product.get("variants", []):
        if v.get("available_quantity", 0) <= 0:
            continue
        price = v.get("low_price", 0)
        if not price or price <= 0:
            continue
        condition = v.get("condition_id", "")
        if condition == "DMG":
            dmg_only_candidates.append(v)
        else:
            acceptable.append(v)

    if not acceptable:
        # Only DMG available — flag it but don't price it
        if dmg_only_candidates:
            return None, "DMG_ONLY", url
        return None, None, url

    # Prefer NM variants first (cheapest NM across any finish)
    nm_variants = [v for v in acceptable if v.get("condition_id") == "NM"]
    if nm_variants:
        best = min(nm_variants, key=lambda v: v["low_price"])
    else:
        # Fallback: cheapest non-DMG variant, sorted by condition preference then price
        def sort_key(v):
            cond = v.get("condition_id", "")
            pref = CONDITION_PREFERENCE.index(cond) if cond in CONDITION_PREFERENCE else 99
            return (pref, v["low_price"])
        best = min(acceptable, key=sort_key)

    condition = CONDITION_LABELS.get(best.get("condition_id", ""), "?")
    finish = FINISH_LABELS.get(best.get("finish_id", "NF"), "")
    label = f"{condition}{finish}"
    return best["low_price"] / 100.0, label, url


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/manapool_price_deck.py <moxfield_import.txt>")
        sys.exit(1)

    deck_path = sys.argv[1]
    cards = parse_decklist(deck_path)
    print(f"Loaded {len(cards)} unique non-basic cards from {deck_path}\n")

    # Step 1: Collect all Scryfall IDs for every card
    print("Fetching all paper printings from Scryfall (500ms delay between requests — 2/sec limit)...")
    card_to_ids = {}
    for i, name in enumerate(cards):
        ids = get_all_scryfall_ids(name)
        card_to_ids[name] = ids
        status = f"{len(ids)} printing(s)" if ids else "NONE FOUND"
        print(f"  [{i+1:2}/{len(cards)}] {name}: {status}")

    # Step 2: Build reverse map scryfall_id -> card_name
    id_to_card = {}
    all_ids = []
    for name, ids in card_to_ids.items():
        for sid in ids:
            id_to_card[sid] = name
            all_ids.append(sid)

    total_batches = (len(all_ids) + 99) // 100
    print(f"\nQuerying Manapool for {len(all_ids)} printings across {total_batches} batches (300ms between batches)...")

    # Step 3: Batch query Manapool in groups of 100
    card_products = defaultdict(list)
    for i in range(0, len(all_ids), 100):
        batch = all_ids[i:i+100]
        batch_num = i // 100 + 1
        products = query_manapool_batch(batch)
        for product in products:
            name = id_to_card.get(product.get("scryfall_id", ""), product.get("name", "?"))
            card_products[name].append(product)
        print(f"  Batch {batch_num}/{total_batches}: {len(products)} results")
        time.sleep(MANAPOOL_DELAY)

    # Step 4: Find cheapest in-stock option per card
    print("\n" + "=" * 65)
    print(f"{'MARCHESA BUDGET — MANAPOOL PRICING':^65}")
    print("=" * 65)

    results = []
    out_of_stock = []
    dmg_only = []
    not_found = []

    for name in cards:
        products = card_products.get(name, [])
        if not products:
            not_found.append(name)
            continue

        best_price, best_label, best_url = None, None, None
        has_dmg_only = False

        for product in products:
            price, label, url = best_available_variant(product)
            if label == "DMG_ONLY":
                has_dmg_only = True
                continue
            if price is not None:
                if best_price is None or price < best_price:
                    best_price = price
                    best_label = label
                    best_url = url

        if best_price is None:
            if has_dmg_only:
                dmg_only.append(name)
            else:
                out_of_stock.append(name)
        else:
            results.append((name, best_price, best_label, best_url))

    # Sort by price descending
    results.sort(key=lambda x: x[1], reverse=True)
    total = sum(r[1] for r in results)

    for name, price, label, url in results:
        print(f"  ${price:>6.2f}  [{label:>12}]  {name}")
        print(f"             {url}")

    print()
    if dmg_only:
        print(f"DMG ONLY — skipped per preference ({len(dmg_only)}):")
        for name in dmg_only:
            print(f"  - {name}")
        print()

    if out_of_stock:
        print(f"OUT OF STOCK on Manapool ({len(out_of_stock)}):")
        for name in out_of_stock:
            print(f"  - {name}")
        print()

    if not_found:
        print(f"NOT FOUND on Manapool ({len(not_found)}):")
        for name in not_found:
            print(f"  - {name}")
        print()

    print("=" * 65)
    print(f"  Cards priced:     {len(results)}")
    print(f"  DMG only (skipped): {len(dmg_only)}")
    print(f"  Out of stock:     {len(out_of_stock)}")
    print(f"  Not found:        {len(not_found)}")
    print(f"  TOTAL (in stock): ${total:.2f}")
    print("=" * 65)

    # Save JSON output
    import os
    from datetime import datetime
    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    deck_slug = os.path.splitext(os.path.basename(deck_path))[0]
    out_path = f"logs/manapool_{deck_slug}_{timestamp}.json"
    output = {
        "deck": deck_path,
        "as_of": datetime.now().isoformat(),
        "total_usd": round(total, 2),
        "cards": [{"name": n, "price_usd": p, "condition": c, "url": u} for n, p, c, u in results],
        "dmg_only": dmg_only,
        "out_of_stock": out_of_stock,
        "not_found": not_found,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"\nFull results saved to {out_path}")


if __name__ == "__main__":
    main()
