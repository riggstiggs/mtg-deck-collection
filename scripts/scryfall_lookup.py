"""
scryfall_lookup.py
------------------
Reusable Scryfall card lookup utility.

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
"""

import sys
import json
import time
import urllib.request
import urllib.parse

HEADERS = {"User-Agent": "MTGDeckCollection/1.0", "Accept": "application/json"}
NAMED_DELAY = 0.5    # 500ms — /cards/named limit: 2/sec
SEARCH_DELAY = 0.5   # 500ms — /cards/search limit: 2/sec
RETRY_BASE = 2.0
MAX_RETRIES = 5


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


def lookup_named(name):
    """Look up a single card by exact name."""
    safe = urllib.parse.quote(name)
    url = f"https://api.scryfall.com/cards/named?exact={safe}"
    time.sleep(NAMED_DELAY)
    return fetch(url, label=f"named '{name}'")


def lookup_search(query, unique="cards", order="name"):
    """Search cards using Scryfall query syntax. Returns all pages."""
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
    return results


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    # -- Search mode
    if "--search" in args:
        idx = args.index("--search")
        query = args[idx + 1]
        unique = "cards"
        if "--unique" in args:
            uidx = args.index("--unique")
            unique = args[uidx + 1]
        results = lookup_search(query, unique=unique)
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
        card = lookup_named(name)
        if card:
            print(format_card(card))
        else:
            not_found.append(name)
            print(f"--- NOT FOUND: {name}")

    if not_found:
        print(f"\nNot found ({len(not_found)}): {', '.join(not_found)}")


if __name__ == "__main__":
    main()
