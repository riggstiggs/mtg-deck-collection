import json
import sys
import os

def get_cheapest_prices(deck_file, db_file):
    if not os.path.exists(deck_file):
        print(f"Error: Deck file {deck_file} not found.")
        return
    if not os.path.exists(db_file):
        print(f"Error: Database file {db_file} not found.")
        return

    # 1. Extract card names from the deck file
    with open(deck_file, 'r') as f:
        lines = f.readlines()

    start_collecting = False
    card_counts = {}
    for line in lines:
        line = line.strip()
        if line == 'COMMANDER:' or line == 'DECK:':
            start_collecting = True
            continue
        if start_collecting and line:
            if line.startswith('---'): 
                break
            parts = line.split(' ', 1)
            if len(parts) == 2:
                try:
                    count = int(parts[0])
                    name = parts[1].strip()
                    if name not in ['Forest', 'Island', 'Mountain', 'Swamp', 'Plains']:
                        card_counts[name] = count
                except ValueError:
                    continue

    # 2. Search Database
    cheapest_versions = {}
    with open(db_file, 'r') as f:
        try:
            data = json.load(f)
            for card in data:
                name = card.get('name')
                if not name: continue
                
                possible_names = [name]
                if ' // ' in name:
                    possible_names.append(name.split(' // ')[0])
                
                for n in possible_names:
                    if n in card_counts:
                        usd = card.get('prices', {}).get('usd')
                        if usd:
                            price = float(usd)
                            set_name = card.get('set_name')
                            if n not in cheapest_versions or price < cheapest_versions[n]['price']:
                                cheapest_versions[n] = {'price': price, 'set': set_name}
        except Exception as e:
            print(f"Error reading database: {e}")
            return

    # 3. Output Markdown Table
    total = 0
    print(f"## 💰 Price Audit for: {os.path.basename(deck_file)}")
    print(f"**Date:** 2/23/2026")
    print("| Card Name | Price (USD) | Set |")
    print("| :--- | :--- | :--- |")
    for name in sorted(card_counts.keys()):
        info = cheapest_versions.get(name, {'price': 0.0, 'set': 'N/A'})
        print(f"| {name} | ${info['price']:.2f} | {info['set']} |")
        total += info['price'] * card_counts[name]

    print(f"\n**Estimated Total Cost:** ${total:.2f}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/price_audit.py <path_to_deck_file>")
    else:
        get_cheapest_prices(sys.argv[1], 'db/mtg_database.json')
