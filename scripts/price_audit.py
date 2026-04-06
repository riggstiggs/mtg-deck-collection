#!/usr/bin/env python3
"""
Price Audit — Local Database Pricing Tool

This script calculates the estimated cost of a deck by comparing your 
deck list against a local database of MTG cards (stored in the 'db/' folder).
It helps you find the cheapest 'printing' (version) of every card in your deck.

It can handle both standard JSON files and compressed .json.gz files.
"""

import json
import sys
import os
import gzip

# ---------------------------------------------------------------------------
# Core Logic: Pricing Engine
# ---------------------------------------------------------------------------

def get_cheapest_prices(deck_file, db_file):
    """
    Finds the lowest available price for every card in a specific deck.
    """
    # Safety Check: Does the deck file even exist?
    if not os.path.exists(deck_file):
        print(f"Error: Deck file {deck_file} not found.")
        return
    
    # 1. Database Detection
    # MTG databases are HUGE. We often compress them into '.gz' files to save space.
    # This section checks if we should use 'mtg_database.json' or 'mtg_database.json.gz'.
    json_db = db_file
    gz_db = db_file + ".gz"
    
    is_gz = False
    if os.path.exists(json_db):
        current_db = json_db
    elif os.path.exists(gz_db):
        current_db = gz_db
        is_gz = True
    else:
        print(f"Error: Database file not found ({json_db} or {gz_db})")
        return

    # 2. Extract Card Names from the Deck File
    # We read your Markdown deck and look for the 'COMMANDER:' and 'DECK:' sections.
    with open(deck_file, 'r') as f:
        lines = f.readlines()

    start_collecting = False
    card_counts = {} # A dictionary to store { 'Card Name': quantity }
    for line in lines:
        line = line.strip()
        # Start reading when we hit one of these headers
        if line == 'COMMANDER:' or line == 'DECK:':
            start_collecting = True
            continue
        
        if start_collecting and line:
            # Stop if we hit the '---' separator at the bottom of the file
            if line.startswith('---'): 
                break
            
            # Lines are usually "1 Sol Ring". We split on the first space.
            parts = line.split(' ', 1)
            if len(parts) == 2:
                try:
                    count = int(parts[0]) # Get the "1"
                    name = parts[1].strip() # Get the "Sol Ring"
                    
                    # Ignore basic lands (we assume you have them or they are free)
                    if name not in ['Forest', 'Island', 'Mountain', 'Swamp', 'Plains']:
                        card_counts[name] = count
                except ValueError:
                    # If the first part isn't a number, skip this line
                    continue

    # 3. Search Database
    # Now we loop through the THOUSANDS of cards in the database to find matches.
    cheapest_versions = {}
    
    # If it's a .gz file, we use 'gzip.open'. If it's a normal file, we use 'open'.
    open_func = gzip.open if is_gz else open
    
    try:
        # 'rt' means 'Read as Text'
        with open_func(current_db, 'rt', encoding='utf-8') as f:
            data = json.load(f) # Load the giant list of card objects
            
            for card in data:
                name = card.get('name')
                if not name: continue
                
                # Logic for Double-Faced Cards:
                # If a card is named "Delver of Secrets // Insectile Aberration",
                # we also want to match just "Delver of Secrets".
                possible_names = [name]
                if ' // ' in name:
                    possible_names.append(name.split(' // ')[0])
                
                for n in possible_names:
                    # If this card is in our deck:
                    if n in card_counts:
                        usd = card.get('prices', {}).get('usd')
                        if usd:
                            price = float(usd)
                            set_name = card.get('set_name')
                            
                            # Keep track of ONLY the lowest price found so far
                            if n not in cheapest_versions or price < cheapest_versions[n]['price']:
                                cheapest_versions[n] = {'price': price, 'set': set_name}
    except Exception as e:
        print(f"Error reading database: {e}")
        return

    # 4. Output Results as a Markdown Table
    # This prints text that you can copy right into a GitHub README.
    total = 0
    print(f"## 💰 Price Audit for: {os.path.basename(deck_file)}")
    print(f"**Date:** 2/23/2026") # Note: This is a static date from original script
    print("| Card Name | Price (USD) | Set |")
    print("| :--- | :--- | :--- |")
    
    for name in sorted(card_counts.keys()):
        # Get the cheapest version we found, or default to $0 if not found
        info = cheapest_versions.get(name, {'price': 0.0, 'set': 'N/A'})
        print(f"| {name} | ${info['price']:.2f} | {info['set']} |")
        
        # Calculate running total (Price * Quantity)
        total += info['price'] * card_counts[name]

    print(f"\n**Estimated Total Cost:** ${total:.2f}")

# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Check if the user typed a deck path
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/price_audit.py <path_to_deck_file>")
    else:
        # Default database path is assumed to be 'db/mtg_database.json'
        get_cheapest_prices(sys.argv[1], 'db/mtg_database.json')
