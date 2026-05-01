#!/usr/bin/env python3
"""
scryfall_recommend.py — ID-Based Card Recommendation Helper
============================================================

PURPOSE
-------
This script is an EXPERIMENT to test a technique called "ID-based card
selection" that is designed to prevent AI hallucination during deck-building
sessions.

It does NOT replace any existing workflow. Use it optionally alongside the
normal scryfall_lookup.py flow to try the new approach.

THE PROBLEM IT SOLVES
---------------------
When collaborating with Claude on deck building, Claude might suggest a card
like "Swamp King, Devourer of Souls" — a card that sounds plausible but
doesn't exist. This is called "hallucination." Even with verification steps,
hallucinated names can slip through and waste time.

THE SOLUTION: ID-BASED SELECTION
----------------------------------
Instead of asking Claude "suggest some ramp cards for this deck," the ID-based
approach works like this:

  Step 1 (YOU):  Run this script with a Scryfall search query.
                 The script fetches real, verified cards and assigns each one
                 a temporary numbered ID (R001, R002, R003...).

  Step 2 (YOU):  Paste the output into your chat with Claude.

  Step 3 (CLAUDE): Claude responds with ID numbers only — e.g., "R003, R011,
                   R024" — never inventing card names.

  Step 4 (YOU):  Run this script again with --resolve and those IDs.
                 The script looks them up in the saved session file, prints the
                 full card details, and confirms every choice is a real card.

Because Claude can only select from a pre-verified list, hallucination is
structurally impossible. If Claude references an ID that doesn't exist, the
script catches it immediately.

SESSION FILE
------------
Each run of this script (without --resolve) saves a session file:
  cache/recommend_session.json

This file maps ID numbers (R001, R002...) to full Scryfall card data.
It is committed to the repo and shared across machines — just like the other
cache files — so you can start a session on one computer and resolve it on
another after a git pull.

The session is OVERWRITTEN every time you run a new search. If you want to
keep a session, copy the file or note the IDs before running a new search.

USAGE
-----
  # Step 1: Search for candidates and save session
  python3 scripts/scryfall_recommend.py --search "t:instant o:'add' id<=RG commander:legal" --label "Grolnok ramp"

  # Step 2: (Paste the numbered list into your Claude chat and get IDs back)

  # Step 3: Resolve the IDs Claude chose back to full card details
  python3 scripts/scryfall_recommend.py --resolve R003 R011 R024

  # Optional: View the full session without resolving specific IDs
  python3 scripts/scryfall_recommend.py --list-session

  # Optional: Limit results to a manageable number (default: 30)
  python3 scripts/scryfall_recommend.py --search "t:land id<=RG" --limit 20

NOTES
-----
- This script imports scryfall_lookup.py as a library. Both files must be in
  the scripts/ directory.
- Run this script from the REPOSITORY ROOT, not from inside scripts/.
  Correct:   python3 scripts/scryfall_recommend.py ...
  Incorrect: cd scripts && python3 scryfall_recommend.py ...
"""

import sys
import json
import os
import time

# ---------------------------------------------------------------------------
# Import our existing Scryfall library.
#
# scryfall_lookup.py lives in the same directory as this script. We add the
# scripts/ directory to Python's path so we can import it like a module.
# This means all caching, rate limiting, and API logic is shared — we are
# not duplicating any of that work.
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(__file__))
import scryfall_lookup as scryfall

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Where the session file lives. Using cache/ keeps it alongside other
# transient data and ensures it is committed + shared across machines.
SESSION_FILE = os.path.join("cache", "recommend_session.json")

# Default maximum number of candidate cards to show.
# Keeping this low (30) makes the list readable in a chat window.
# Use --limit N on the command line to change it for a given run.
DEFAULT_LIMIT = 30

# The prefix used for IDs. R = Recommend. Short, distinctive, and easy
# to type. IDs look like: R001, R002, R003 ...
ID_PREFIX = "R"

# ---------------------------------------------------------------------------
# Session File Helpers
# ---------------------------------------------------------------------------

def save_session(session_data):
    """
    Saves the current session (the ID→card mapping) to disk as JSON.

    The session_data dict looks like:
      {
        "label": "Grolnok ramp",
        "query": "t:instant o:'add' ...",
        "created_at": 1714500000.0,
        "candidates": {
          "R001": { ...full Scryfall card object... },
          "R002": { ...full Scryfall card object... },
          ...
        }
      }
    """
    os.makedirs("cache", exist_ok=True)
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2, ensure_ascii=False)
    print(f"\n[session] Saved {len(session_data['candidates'])} candidates to {SESSION_FILE}")


def load_session():
    """
    Loads the most recently saved session from disk.
    Returns None if no session file exists yet.
    """
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[error] Could not load session file: {e}", file=sys.stderr)
        return None

# ---------------------------------------------------------------------------
# ID Assignment
# ---------------------------------------------------------------------------

def assign_ids(cards):
    """
    Takes a list of Scryfall card objects and returns an OrderedDict mapping
    ID strings (R001, R002...) to card objects.

    The zero-padded three-digit format (001, 002...) keeps IDs the same
    width regardless of how many candidates there are, which makes the
    output table easier to read.
    """
    return {
        f"{ID_PREFIX}{str(i + 1).zfill(3)}": card
        for i, card in enumerate(cards)
    }

# ---------------------------------------------------------------------------
# Display Formatting
# ---------------------------------------------------------------------------

def format_candidate_row(id_str, card):
    """
    Formats a single candidate card as a concise one-line summary
    suitable for pasting into a chat window.

    Format:
      R001 | Cultivate {2}{G} | Sorcery | Scryfall: $0.25
           | Search your library for up to two basic land cards...

    We intentionally keep this compact so Claude can read a list of 30
    cards without the context window filling up with verbose oracle text.
    """
    name      = card.get("name", "?")
    cost      = card.get("mana_cost", "—")
    type_line = card.get("type_line", "?")
    oracle    = card.get("oracle_text", "").replace("\n", " | ")
    prices    = card.get("prices", {})
    usd       = f"${prices['usd']}" if prices.get("usd") else "—"

    # Truncate very long oracle text so rows don't wrap badly in a terminal.
    # 120 chars is wide enough to be useful and narrow enough to be readable.
    if len(oracle) > 120:
        oracle = oracle[:117] + "..."

    return (
        f"  {id_str} | {name} {cost} | {type_line} | {usd}\n"
        f"       {oracle}"
    )


def format_resolved_card(id_str, card):
    """
    Formats a resolved card with full detail — used when Claude has selected
    IDs and we want to confirm exactly what was chosen.

    This is more verbose than format_candidate_row because at this stage
    we want the full picture before committing to adding a card to a deck.
    """
    name      = card.get("name", "?")
    cost      = card.get("mana_cost", "—")
    type_line = card.get("type_line", "?")
    oracle    = card.get("oracle_text", "").replace("\n", "\n         ")
    prices    = card.get("prices", {})
    usd       = f"${prices['usd']}" if prices.get("usd") else "price unknown"
    set_name  = card.get("set_name", "?")
    col_num   = card.get("collector_number", "?")

    return (
        f"  [{id_str}] {name}\n"
        f"         Cost: {cost}  |  Type: {type_line}\n"
        f"         Set:  {set_name} #{col_num}  |  Price: {usd}\n"
        f"         Text: {oracle}\n"
    )

# ---------------------------------------------------------------------------
# Core Actions
# ---------------------------------------------------------------------------

def run_search(query, label, limit):
    """
    Performs a Scryfall search, assigns IDs to the results, saves the session,
    and prints the numbered candidate list.

    This is Step 1 of the ID-based workflow — the output is what you paste
    into your Claude chat.
    """
    print(f"\n[search] Query: {query}")
    if label:
        print(f"[search] Label: {label}")
    print(f"[search] Fetching up to {limit} candidates from Scryfall...\n")

    # Use the existing library function — benefits from caching automatically.
    all_cards = scryfall.lookup_search(query)

    if not all_cards:
        print("[error] No cards found. Check your Scryfall query syntax.")
        sys.exit(1)

    # Trim to the requested limit.
    candidates = all_cards[:limit]

    if len(all_cards) > limit:
        print(f"[info] {len(all_cards)} cards matched. Showing first {limit}. Use --limit N for more.\n")

    # Assign IDs and save the session.
    id_map = assign_ids(candidates)
    session = {
        "label":      label or query,
        "query":      query,
        "created_at": time.time(),
        "candidates": id_map,
    }
    save_session(session)

    # Print the candidate list — this is what you paste into Claude.
    print("=" * 70)
    print(f"CANDIDATE LIST — {session['label']}")
    print(f"({len(id_map)} cards — paste this into Claude, ask it to pick by ID)")
    print("=" * 70)
    for id_str, card in id_map.items():
        print(format_candidate_row(id_str, card))
        print()  # blank line between cards for readability

    print("=" * 70)
    print("NEXT STEP: Tell Claude to select from this list using IDs only.")
    print(f"Then run:  python3 scripts/scryfall_recommend.py --resolve R001 R005 ...")
    print("=" * 70)


def run_resolve(id_list):
    """
    Given a list of ID strings (e.g. ["R001", "R005", "R012"]), looks them
    up in the saved session file and prints full card details.

    This is Step 3 of the ID-based workflow — confirming exactly what Claude
    chose before you add anything to a deck.

    Any IDs that don't exist in the session are flagged as errors. This is
    the hallucination guard: if Claude invented an ID, it will show up here
    as "NOT IN SESSION" and you'll know to discard it.
    """
    session = load_session()
    if not session:
        print(f"[error] No session file found at {SESSION_FILE}.")
        print("        Run a search first: python3 scripts/scryfall_recommend.py --search '...'")
        sys.exit(1)

    # Normalise IDs to uppercase (R001 and r001 both work).
    id_list = [id_str.upper() for id_str in id_list]

    print("\n" + "=" * 70)
    print(f"RESOLVED SELECTIONS — {session['label']}")
    print(f"(Session from: {time.strftime('%Y-%m-%d %H:%M', time.localtime(session['created_at']))})")
    print("=" * 70 + "\n")

    resolved   = []
    not_found  = []

    for id_str in id_list:
        card = session["candidates"].get(id_str)
        if card:
            resolved.append((id_str, card))
            print(format_resolved_card(id_str, card))
        else:
            not_found.append(id_str)

    # Summary
    print("=" * 70)
    print(f"Resolved {len(resolved)} of {len(id_list)} IDs successfully.")

    if not_found:
        # This is the hallucination guard firing.
        print(f"\n[WARNING] {len(not_found)} ID(s) NOT FOUND in session:")
        for bad_id in not_found:
            print(f"  {bad_id} — this ID does not exist. Do not add this card.")
        print("\n  This means Claude referenced an ID outside the candidate list.")
        print("  Discard these selections and ask Claude to choose only from valid IDs.")

    if resolved:
        print("\nCONFIRMED CARDS (safe to add to deck — all verified by Scryfall):")
        for id_str, card in resolved:
            name = card.get("name", "?")
            cost = card.get("mana_cost", "—")
            print(f"  {id_str}: {name} {cost}")


def run_list_session():
    """
    Prints a summary of the currently saved session without resolving any IDs.
    Useful for reviewing what's in the session file or picking it back up
    after switching computers.
    """
    session = load_session()
    if not session:
        print(f"[info] No session file found at {SESSION_FILE}.")
        print("       Run a search first: python3 scripts/scryfall_recommend.py --search '...'")
        sys.exit(0)

    created = time.strftime('%Y-%m-%d %H:%M', time.localtime(session['created_at']))
    candidates = session.get("candidates", {})

    print("\n" + "=" * 70)
    print(f"CURRENT SESSION: {session['label']}")
    print(f"Query:   {session['query']}")
    print(f"Created: {created}")
    print(f"Cards:   {len(candidates)}")
    print("=" * 70)
    for id_str, card in candidates.items():
        name = card.get("name", "?")
        cost = card.get("mana_cost", "—")
        print(f"  {id_str}: {name} {cost}")
    print("=" * 70)
    print(f"\nTo resolve specific IDs: python3 scripts/scryfall_recommend.py --resolve R001 R002 ...")

# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]

    # Show help if no arguments were provided.
    if not args:
        print(__doc__)
        sys.exit(0)

    # ------------------------------------------------------------------
    # MODE 1: --search  (build a new candidate list)
    # ------------------------------------------------------------------
    if "--search" in args:
        idx = args.index("--search")
        if idx + 1 >= len(args):
            print("[error] --search requires a query string after it.")
            sys.exit(1)
        query = args[idx + 1]

        # Optional --label "My Label" to give the session a human-readable name.
        label = None
        if "--label" in args:
            lidx = args.index("--label")
            if lidx + 1 < len(args):
                label = args[lidx + 1]

        # Optional --limit N to control how many candidates to show.
        limit = DEFAULT_LIMIT
        if "--limit" in args:
            limidx = args.index("--limit")
            if limidx + 1 < len(args):
                try:
                    limit = int(args[limidx + 1])
                except ValueError:
                    print("[error] --limit requires a number, e.g. --limit 50")
                    sys.exit(1)

        run_search(query, label, limit)

    # ------------------------------------------------------------------
    # MODE 2: --resolve  (confirm IDs Claude chose)
    # ------------------------------------------------------------------
    elif "--resolve" in args:
        idx = args.index("--resolve")
        id_list = args[idx + 1:]  # Everything after --resolve is treated as IDs.
        if not id_list:
            print("[error] --resolve requires at least one ID, e.g. --resolve R001 R005")
            sys.exit(1)
        run_resolve(id_list)

    # ------------------------------------------------------------------
    # MODE 3: --list-session  (inspect the saved session)
    # ------------------------------------------------------------------
    elif "--list-session" in args:
        run_list_session()

    else:
        print("[error] Unknown arguments. Run with no arguments to see usage.")
        sys.exit(1)

    # Always flush the Scryfall caches so any new data is persisted.
    scryfall._flush_caches()


if __name__ == "__main__":
    main()
