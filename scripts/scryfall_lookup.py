"""
scryfall_lookup.py
------------------
Reusable Scryfall card lookup utility with local disk cache.

Cache files (in cache/ directory relative to working directory):
  cache/scryfall_cards.json   — named card lookups    (TTL: 30 days)
  cache/scryfall_search.json  — search query results  (TTL: 7 days)

Cache is checked before every API call. Results are written to cache after
every successful API response. Run with --no-cache to bypass the cache and
force fresh API calls (also refreshes cached entries).

Rate limits (per Scryfall API docs):
  /cards/search, /cards/named — 2/sec (500ms between requests)
  All other endpoints         — 10/sec (100ms)

Usage:
    # Look up one card
    python scripts/scryfall_lookup.py "Sol Ring"

    # Look up multiple cards
    python scripts/scryfall_lookup.py "Sol Ring" "Command Tower" "Morophon, the Boundless"

    # Look up from a text file (one card name per line)
    python scripts/scryfall_lookup.py --file cards.txt

    # Search by query (Scryfall syntax)
    python scripts/scryfall_lookup.py --search "t:shapeshifter game:paper"

    # Search and show all printings
    python scripts/scryfall_lookup.py --search "!\"Sol Ring\" game:paper" --unique prints

    # Bypass cache and force fresh API calls
    python scripts/scryfall_lookup.py --no-cache "Sol Ring"
"""

import sys
import json
import time
import os
import urllib.request
import urllib.parse

HEADERS = {"User-Agent": "MTGDeckCollection/1.0", "Accept": "application/json"}
NAMED_DELAY = 0.5    # 500ms — /cards/named limit: 2/sec
SEARCH_DELAY = 0.5   # 500ms — /cards/search limit: 2/sec
RETRY_BASE = 2.0
MAX_RETRIES = 5

# Cache settings
CACHE_DIR = "cache"
CARD_CACHE_FILE = os.path.join(CACHE_DIR, "scryfall_cards.json")
SEARCH_CACHE_FILE = os.path.join(CACHE_DIR, "scryfall_search.json")
CARD_CACHE_TTL  = 30 * 24 * 3600   # 30 days — oracle text changes rarely
SEARCH_CACHE_TTL = 7 * 24 * 3600   # 7 days  — search results more volatile

# Module-level cache state — loaded once, saved at end
_card_cache = None
_search_cache = None


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def _load_cache(path):
    """Load a JSON cache file from disk. Returns empty dict on missing/corrupt."""
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"  [cache] Warning: could not load {path}: {e}", file=sys.stderr)
    return {}


def _save_cache(path, data):
    """Write a JSON cache dict to disk."""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"  [cache] Warning: could not save {path}: {e}", file=sys.stderr)


def _cache_get(cache, key, ttl):
    """Return cached data if present and within TTL, else None."""
    entry = cache.get(key.lower())
    if entry and (time.time() - entry.get("cached_at", 0)) < ttl:
        return entry["data"]
    return None


def _cache_set(cache, key, data):
    """Store data in cache dict with current timestamp."""
    cache[key.lower()] = {"data": data, "cached_at": time.time()}


def _init_caches():
    """Load both cache files into module-level dicts (called once)."""
    global _card_cache, _search_cache
    if _card_cache is None:
        _card_cache = _load_cache(CARD_CACHE_FILE)
    if _search_cache is None:
        _search_cache = _load_cache(SEARCH_CACHE_FILE)


def _flush_caches():
    """Write both in-memory caches back to disk."""
    if _card_cache is not None:
        _save_cache(CARD_CACHE_FILE, _card_cache)
    if _search_cache is not None:
        _save_cache(SEARCH_CACHE_FILE, _search_cache)


# ---------------------------------------------------------------------------
# Network helpers
# ---------------------------------------------------------------------------

def fetch(url, label="request"):
    """GET a URL with exponential backoff on 429/5xx."""
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                wait = RETRY_BASE * (2 ** attempt)
                print(f"  [rate limit] {label} got HTTP {e.code}, waiting {wait:.1f}s...", file=sys.stderr)
                time.sleep(wait)
            elif e.code == 404:
                return None
            else:
                print(f"  [error] {label} HTTP {e.code}: {e.reason}", file=sys.stderr)
                return None
        except Exception as e:
            print(f"  [error] {label}: {e}", file=sys.stderr)
            return None
    return None


# ---------------------------------------------------------------------------
# Card formatting
# ---------------------------------------------------------------------------

def format_card(c, verbose=True):
    """Format a card dict for display."""
    name = c.get("name", "?")
    cost = c.get("mana_cost", "")
    type_line = c.get("type_line", "")
    pt = f"  {c['power']}/{c['toughness']}" if "power" in c else ""
    oracle = c.get("oracle_text", "").replace("\n", " | ")
    prices = c.get("prices", {})
    usd = f"  ${prices['usd']}" if prices.get("usd") else ""
    set_name = f"  [{c.get('set_name', '')} #{c.get('collector_number', '')}]"

    lines = [f"--- {name} {cost} [{type_line}]{pt}{usd}{set_name}"]
    if verbose and oracle:
        lines.append(f"    {oracle}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Lookup functions
# ---------------------------------------------------------------------------

def lookup_named(name, no_cache=False):
    """Look up a single card by exact name. Checks local cache first."""
    _init_caches()

    if not no_cache:
        cached = _cache_get(_card_cache, name, CARD_CACHE_TTL)
        if cached is not None:
            print(f"  [cache hit] {name}", file=sys.stderr)
            return cached

    safe = urllib.parse.quote(name)
    url = f"https://api.scryfall.com/cards/named?exact={safe}"
    time.sleep(NAMED_DELAY)
    result = fetch(url, label=f"named '{name}'")

    if result is not None:
        _cache_set(_card_cache, name, result)

    return result


def lookup_search(query, unique="cards", order="name", no_cache=False):
    """Search cards using Scryfall query syntax. Returns all pages. Checks local cache."""
    _init_caches()
    cache_key = f"{query}|unique={unique}|order={order}"

    if not no_cache:
        cached = _cache_get(_search_cache, cache_key, SEARCH_CACHE_TTL)
        if cached is not None:
            print(f"  [cache hit] search: {query!r}", file=sys.stderr)
            return cached

    results = []
    safe = urllib.parse.quote(query)
    url = f"https://api.scryfall.com/cards/search?q={safe}&unique={unique}&order={order}"
    page = 1
    while url:
        time.sleep(SEARCH_DELAY)
        data = fetch(url, label=f"search '{query}' p{page}")
        if not data:
            break
        results.extend(data.get("data", []))
        url = data.get("next_page") if data.get("has_more") else None
        page += 1

    if results:
        _cache_set(_search_cache, cache_key, results)

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    no_cache = "--no-cache" in args
    args = [a for a in args if a != "--no-cache"]

    try:
        # -- Search mode
        if "--search" in args:
            idx = args.index("--search")
            query = args[idx + 1]
            unique = "cards"
            if "--unique" in args:
                uidx = args.index("--unique")
                unique = args[uidx + 1]
            results = lookup_search(query, unique=unique, no_cache=no_cache)
            print(f"=== Search: {query!r} ({len(results)} results) ===")
            for c in results:
                print(format_card(c))
            return

        # -- File mode
        if "--file" in args:
            idx = args.index("--file")
            path = args[idx + 1]
            with open(path, encoding="utf-8") as f:
                names = [line.strip() for line in f if line.strip()]
        else:
            names = [a for a in args if not a.startswith("--")]

        # -- Named lookup mode
        not_found = []
        for name in names:
            card = lookup_named(name, no_cache=no_cache)
            if card:
                print(format_card(card))
            else:
                not_found.append(name)
                print(f"--- NOT FOUND: {name}")

        if not_found:
            print(f"\nNot found ({len(not_found)}): {', '.join(not_found)}")

    finally:
        _flush_caches()


if __name__ == "__main__":
    main()
