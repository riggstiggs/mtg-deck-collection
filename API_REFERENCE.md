# API Reference

This file is the authoritative reference for all external API interactions in this repository. All agents — sub-agents, orchestrators, and the main session — must follow the rules here when looking up card data or pricing. Do not write inline Python API calls. Always use the permanent scripts documented below.

---

## General Rules

1. **Always use the permanent scripts.** `scripts/scryfall_lookup.py` for card lookups. `scripts/manapool_price_deck.py` for deck pricing. Never write one-off inline Python for these tasks.
2. **Respect rate limits.** Both APIs enforce limits. Exceeding them causes 429 errors and degrades performance for all subsequent calls. The scripts handle rate limiting automatically — do not bypass delays.
3. **Use exponential backoff.** On 429 or 5xx errors, both scripts retry with exponential backoff (base 2s, max 5 retries). Do not retry manually on top of this.
4. **Unknown card = mandatory lookup.** If you are uncertain about any card's oracle text, mana cost, type line, or abilities, you MUST look it up before making decisions based on it. Do not rely on memory or assumption for card rules.
5. **Cache is automatic.** Both scripts check a local disk cache before making API calls. You do not need to manage the cache manually — it is populated and read transparently. Use `--no-cache` on `scryfall_lookup.py` only when you specifically need fresh data (e.g., checking an updated price or a newly spoiled card).

---

## Local Cache

Both scripts maintain a local JSON cache in the `cache/` directory (gitignored — local only, not committed to the repo). The cache prevents redundant API calls across sessions and is especially valuable for goldfish simulations where the same cards are looked up repeatedly across multiple games.

| Cache file | Used by | Keyed by | TTL |
|------------|---------|----------|-----|
| `cache/scryfall_cards.json` | `scryfall_lookup.py` | Lowercase card name (named lookups) | 30 days |
| `cache/scryfall_search.json` | `scryfall_lookup.py` | Query string + unique parameter | 7 days |
| `cache/scryfall_printings.json` | `manapool_price_deck.py` | Lowercase card name (printing ID lists) | 7 days |

**TTL rationale:**
- 30 days for named card objects — oracle text, type lines, and mana costs change only via errata, which is rare.
- 7 days for search results and printing lists — new set releases and new printings happen on a regular schedule; weekly refresh keeps data reasonably current.

**Cache hit output:** When a result is served from cache, the scripts print `[cache hit] Card Name` to stderr. This does not appear in normal stdout output and will not pollute piped results.

**Bypassing the cache:** Pass `--no-cache` to `scryfall_lookup.py` to force fresh API calls and overwrite stale cache entries:
```
python scripts/scryfall_lookup.py --no-cache "Sol Ring"
```
The `manapool_price_deck.py` script does not currently support `--no-cache`; delete `cache/scryfall_printings.json` manually if you need to force a refresh.

---

## Scryfall API

### Purpose
Scryfall is the authoritative source for card oracle text, mana costs, type lines, prices (USD), and printing metadata. Use it any time you need to understand what a card does.

### Rate Limits
These are enforced by Scryfall and must be respected:

| Endpoint | Limit | Minimum delay between requests |
|----------|-------|-------------------------------|
| `/cards/named` | 2 per second | **500ms** |
| `/cards/search` | 2 per second | **500ms** |
| All other endpoints | 10 per second | 100ms |

The scripts use 500ms delays for all calls to stay safely within limits.

### Permanent Script: `scripts/scryfall_lookup.py`

This script handles named lookups, batch lookups, file-based lookups, and search queries. It respects rate limits automatically and uses exponential backoff on errors.

**Look up one card by exact name:**
```
python scripts/scryfall_lookup.py "Sol Ring"
```

**Look up multiple cards at once:**
```
python scripts/scryfall_lookup.py "Sol Ring" "Command Tower" "Morophon, the Boundless"
```

**Look up from a text file (one card name per line):**
```
python scripts/scryfall_lookup.py --file cards.txt
```

**Search using Scryfall query syntax:**
```
python scripts/scryfall_lookup.py --search "t:shapeshifter game:paper"
python scripts/scryfall_lookup.py --search "t:elf t:warrior game:paper"
```

**Search all printings of a specific card:**
```
python scripts/scryfall_lookup.py --search "!\"Sol Ring\" game:paper" --unique prints
```

### Output Format
Each result shows:
```
--- Card Name {mana_cost} [Type Line]  P/T  $price  [Set #collector_number]
    Oracle text here
```

### Key Query Syntax
| Query | Meaning |
|-------|---------|
| `t:shapeshifter` | Creature type is Shapeshifter |
| `t:elf t:warrior` | Creature type includes both Elf and Warrior |
| `game:paper` | Paper printings only (excludes MTGO/Arena exclusive cards) |
| `!"Card Name"` | Exact card name match (use with `--unique prints` for all printings) |
| `is:changeling` | Cards with the changeling keyword |
| `o:"changeling"` | Cards with "changeling" in oracle text |
| `c:g` | Green cards |
| `cmc=3` | Converted mana cost exactly 3 |
| `-is:digital` | Exclude digital-only cards |

### Direct API Endpoints (for reference — use scripts instead)
- Named lookup: `https://api.scryfall.com/cards/named?exact=Card+Name`
- Search: `https://api.scryfall.com/cards/search?q=QUERY&unique=cards&order=name`
- All printings: `https://api.scryfall.com/cards/search?q=!"Card+Name"+game:paper&unique=prints&order=usd&dir=asc`

---

## Manapool API

### Purpose
Manapool is used for finding the cheapest in-stock purchase price for cards, across all printings. Use it when you need to price cards for acquisition planning or deck budgeting.

### Rate Limits
Manapool has no published rate limit. The script uses conservative limits:

| Operation | Delay |
|-----------|-------|
| Between batch requests | **300ms** |

### How the Integration Works
Manapool uses Scryfall IDs to identify cards. The workflow is always:
1. Get all Scryfall IDs for a card (via Scryfall `/cards/search` with `unique=prints`)
2. Query Manapool `/products/singles` with those IDs
3. Find the cheapest in-stock option across all printings

This two-step process is handled automatically by `scripts/manapool_price_deck.py`.

### Permanent Script: `scripts/manapool_price_deck.py`

Prices an entire decklist. Input is a Moxfield import `.txt` file.

```
python scripts/manapool_price_deck.py "path/to/moxfield_import.txt"
```

**Example:**
```
python scripts/manapool_price_deck.py "commander_decks/Planning/Morophon/morophon_changeling_moxfield_import.txt"
```

Results are saved to `logs/manapool_<deckname>_<timestamp>.json` automatically.

### Manapool API Endpoint

**Base URL:** `https://manapool.com/api/v1`

**Endpoint:** `GET /products/singles`

**Parameters:** `scryfall_ids` — repeated parameter, one per Scryfall ID. Maximum 100 IDs per request.

```
/products/singles?scryfall_ids=ID1&scryfall_ids=ID2&scryfall_ids=ID3
```

**CRITICAL:** The parameter must be repeated without array notation. `scryfall_ids[]=ID` returns HTTP 400. Always use `scryfall_ids=ID` (no brackets).

### Manapool Response Format
```json
{
  "data": [
    {
      "name": "Card Name",
      "scryfall_id": "uuid",
      "url": "https://manapool.com/...",
      "available_quantity": 5,
      "price_cents": 149,
      "variants": [
        {
          "condition_id": "NM",
          "finish_id": "NF",
          "low_price": 149,
          "available_quantity": 3
        }
      ]
    }
  ]
}
```

**Key fields:**
- `price_cents` — pre-computed minimum price in cents across all in-stock variants. Divide by 100 for USD.
- `available_quantity` — total stock across all variants. 0 means out of stock.
- `variants[].condition_id` — condition: `NM`, `LP`, `MP`, `HP`, `DMG`
- `variants[].finish_id` — finish: `NF` (non-foil), `FO` (foil), `ET` (etched)
- `variants[].low_price` — price in cents for this specific variant
- `variants[].available_quantity` — stock for this specific variant

### Condition Preferences
When evaluating Manapool results, apply these preferences in order:

| Priority | Condition | Action |
|----------|-----------|--------|
| 1st | NM (Near Mint) | Always prefer — use cheapest NM option |
| 2nd | LP (Lightly Played) | Accept if no NM available |
| 3rd | MP (Moderately Played) | Accept if no NM or LP available |
| 4th | HP (Heavily Played) | Last resort |
| Excluded | DMG (Damaged) | Never purchase — flag separately as "DMG only" |

If a card is only available in DMG condition, report it as `DMG ONLY` and exclude it from the total. Do not count it as out-of-stock — it has a separate category.

### Basic Lands
Basic lands (Plains, Island, Swamp, Mountain, Forest) are excluded from all Manapool pricing queries. The collection contains many copies of all basic lands.

---

## Error Handling Reference

Both scripts implement the same retry strategy:

| Error | Action |
|-------|--------|
| HTTP 429 (rate limited) | Wait `2 * (2^attempt)` seconds, retry up to 5 times |
| HTTP 5xx (server error) | Same exponential backoff |
| HTTP 404 (not found) | Return None immediately — card not in database |
| HTTP 400 (bad request) | Log error, return None — check parameter format |
| Other HTTP errors | Log error, return None |
| Network exception | Log error, return None |

Maximum retries: 5. After 5 failures, the script logs the error and moves on — it does not crash.

---

## When Agents Must Look Up a Card

Any agent performing a task in this repository must look up a card using `scripts/scryfall_lookup.py` if any of the following are true:

- You are unsure of the card's exact oracle text
- You are unsure of the card's mana cost or color identity
- You are unsure whether the card is a creature, instant, sorcery, enchantment, artifact, or planeswalker
- You are making a play decision (goldfish simulation, deck advice) that depends on what the card does
- The card was printed or updated after your training data cutoff
- The card has an unusual or complex rules interaction

**Never assume.** Oracle text contains exact rules language. A card that "seems like" it does something may have an exception, a restriction, or a nuance that changes a play decision entirely. The lookup takes 500ms. Incorrect assumptions waste the entire game.
