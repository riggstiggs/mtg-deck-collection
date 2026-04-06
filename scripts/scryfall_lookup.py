#!/usr/bin/env python3
"""
Scryfall Lookup — Reusable Card Utility

This is a 'utility' script. It doesn't build a deck or run a simulation itself;
instead, it provides a set of functions that other scripts can use to talk 
to Scryfall. Think of it like a library or a toolbox.

Features:
- Look up cards by name.
- Search for cards using Scryfall syntax (e.g. "t:dragon color:red").
- Manages a local cache so we don't ask Scryfall for the same card twice.
"""

import sys
import json
import time
import os
import urllib.request
import urllib.parse

# --- Configuration & API Rules ---
HEADERS = {"User-Agent": "MTGDeckCollection/1.0", "Accept": "application/json"}
NAMED_DELAY = 0.5    # Wait 0.5s between 'named' calls
SEARCH_DELAY = 0.5   # Wait 0.5s between 'search' calls
RETRY_BASE = 2.0     # Base time to wait if the server is busy
MAX_RETRIES = 5      # Max number of attempts per card

# --- Cache Settings ---
# We store results in 'cache/' to make the script faster.
CACHE_DIR = "cache"
CARD_CACHE_FILE = os.path.join(CACHE_DIR, "scryfall_cards.json")
SEARCH_CACHE_FILE = os.path.join(CACHE_DIR, "scryfall_search.json")

# Time To Live (TTL): How long before we consider the cache 'stale'.
CARD_CACHE_TTL  = 365 * 24 * 3600   # 1 year (Oracle text rarely changes)
SEARCH_CACHE_TTL = 120 * 24 * 3600  # 120 days (Set lists change every few months)

# Module-level variables to hold the cache data while the script is running.
_card_cache = None
_search_cache = None

# ---------------------------------------------------------------------------
# Internal Cache Helpers
# ---------------------------------------------------------------------------

def _load_cache(path):
    """Reads a JSON file from the disk. Returns an empty dictionary if it fails."""
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"  [cache] Warning: could not load {path}: {e}", file=sys.stderr)
    return {}

def _save_cache(path, data):
    """Writes a dictionary to a JSON file on the disk."""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"  [cache] Warning: could not save {path}: {e}", file=sys.stderr)

def _cache_get(cache, key, ttl):
    """
    Checks if a 'key' (like a card name) is in the cache.
    Returns the data ONLY if it hasn't expired yet.
    """
    entry = cache.get(key.lower())
    if entry and (time.time() - entry.get("cached_at", 0)) < ttl:
        return entry["data"]
    return None

def _cache_set(cache, key, data):
    """Adds a result to the memory cache with the current time."""
    cache[key.lower()] = {"data": data, "cached_at": time.time()}

def _init_caches():
    """Starts the caching system by loading files into memory."""
    global _card_cache, _search_cache
    if _card_cache is None:
        _card_cache = _load_cache(CARD_CACHE_FILE)
    if _search_cache is None:
        _search_cache = _load_cache(SEARCH_CACHE_FILE)

def _flush_caches():
    """Saves the memory caches back to the disk files."""
    if _card_cache is not None:
        _save_cache(CARD_CACHE_FILE, _card_cache)
    if _search_cache is not None:
        _save_cache(SEARCH_CACHE_FILE, _search_cache)

# ---------------------------------------------------------------------------
# Network Logic
# ---------------------------------------------------------------------------

def fetch(url, label="request"):
    """
    Makes a web request to Scryfall. 
    Includes 'Retry' logic: if the server is busy, it waits and tries again.
    """
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                wait = RETRY_BASE * (2 ** attempt) # Wait longer each time
                print(f"  [rate limit] {label} busy, waiting {wait:.1f}s...", file=sys.stderr)
                time.sleep(wait)
            elif e.code == 404:
                return None # Card simply doesn't exist
            else:
                print(f"  [error] {label} failed: {e.reason}", file=sys.stderr)
                return None
        except Exception as e:
            print(f"  [error] {label} failed: {e}", file=sys.stderr)
            return None
    return None

# ---------------------------------------------------------------------------
# Formatting Logic
# ---------------------------------------------------------------------------

def format_card(c, verbose=True):
    """
    Turns a Scryfall JSON object into a pretty Markdown string.
    Example: '--- Sol Ring {1} [Artifact] $1.50 [Set Name #123]'
    """
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
# Core Search/Lookup Functions
# ---------------------------------------------------------------------------

def lookup_named(name, no_cache=False):
    """Finds one card by its exact name."""
    _init_caches()

    if not no_cache:
        # Check if we already have it in the file
        cached = _cache_get(_card_cache, name, CARD_CACHE_TTL)
        if cached is not None:
            return cached

    # Not in cache, so we call Scryfall
    safe = urllib.parse.quote(name)
    url = f"https://api.scryfall.com/cards/named?exact={safe}"
    time.sleep(NAMED_DELAY) # Respect the rate limit
    result = fetch(url, label=f"named '{name}'")

    if result is not None:
        _cache_set(_card_cache, name, result)

    return result

def lookup_search(query, unique="cards", order="name", no_cache=False):
    """Search for cards using Scryfall's powerful search syntax."""
    _init_caches()
    # Create a unique key for this search so we can cache it
    cache_key = f"{query}|unique={unique}|order={order}"

    if not no_cache:
        cached = _cache_get(_search_cache, cache_key, SEARCH_CACHE_TTL)
        if cached is not None:
            return cached

    results = []
    safe = urllib.parse.quote(query)
    url = f"https://api.scryfall.com/cards/search?q={safe}&unique={unique}&order={order}"
    
    # Scryfall returns 175 cards at a time. We loop through 'pages' to get them all.
    while url:
        time.sleep(SEARCH_DELAY)
        data = fetch(url, label=f"search page")
        if not data:
            break
        results.extend(data.get("data", []))
        # Check if there is a 'next_page' URL in the result
        url = data.get("next_page") if data.get("has_more") else None

    if results:
        _cache_set(_search_cache, cache_key, results)

    return results

# ---------------------------------------------------------------------------
# CLI Management
# ---------------------------------------------------------------------------

def main():
    """The command-line interface logic."""
    args = sys.argv[1:]
    if not args:
        print(__doc__) # Print the help text at the top of the script
        sys.exit(0)

    no_cache = "--no-cache" in args
    args = [a for a in args if a != "--no-cache"]

    try:
        # SEARCH MODE
        if "--search" in args:
            idx = args.index("--search")
            query = args[idx + 1]
            results = lookup_search(query, no_cache=no_cache)
            print(f"=== Search Results ({len(results)}) ===")
            for c in results:
                print(format_card(c))
            return

        # FILE MODE (Read a list of names from a .txt file)
        if "--file" in args:
            idx = args.index("--file")
            path = args[idx + 1]
            with open(path, encoding="utf-8") as f:
                names = [line.strip() for line in f if line.strip()]
        else:
            # DIRECT MODE (names typed directly in the terminal)
            names = [a for a in args if not a.startswith("--")]

        # PERFORM LOOKUPS
        not_found = []
        for name in names:
            card = lookup_named(name, no_cache=no_cache)
            if card:
                print(format_card(card))
            else:
                not_found.append(name)
                print(f"--- NOT FOUND: {name}")

        if not_found:
            print(f"\nCould not find: {', '.join(not_found)}")

    finally:
        # ALWAYS save the cache, even if there was an error
        _flush_caches()

if __name__ == "__main__":
    main()
