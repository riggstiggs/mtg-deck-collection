import random
import re
import sys
import time

def parse_deck_file(file_path):
    """
    Parses a standard Gemini CLI deck file to extract the 99-card deck.
    Assumes the file has a 'DECK:' section with card names.
    """
    deck = []
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Look for everything after DECK: up to the next heading or SIDEBOARD:
        deck_section = re.search(r'DECK:\s*(.*?)(?=\n\n|\n[A-Z]+:|\Z)', content, re.DOTALL)
        if not deck_section:
            print(f"Error: Could not find DECK section in {file_path}")
            return None
            
        lines = deck_section.group(1).strip().split('\n')
        for line in lines:
            # Clean the line and find "Quantity Name"
            clean_line = line.strip()
            if not clean_line:
                continue
            match = re.match(r'(\d+)\s+(.+)', clean_line)
            if match:
                count = int(match.group(1))
                name = match.group(2).strip()
                deck.extend([name] * count)
                
        return deck
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 goldfish_shuffler.py <path_to_deck_file>")
        return

    file_path = sys.argv[1]
    deck = parse_deck_file(file_path)
    
    if not deck:
        return

    # Standard Commander deck (minus commander) is 99 cards
    if len(deck) != 99:
        print(f"NOTE: Deck contains {len(deck)} cards. Standard Commander decks (minus commander) usually have 99.")

    # High-entropy seed
    random.seed(time.time_ns())
    random.shuffle(deck)

    print(f"--- HONEST SHUFFLE: {file_path} ---")
    print(f"PARSED DECK SIZE: {len(deck)}")
    print("\nFIRST 20 CARDS (Top of Library):")
    for i, card in enumerate(deck[:20]):
        print(f"{i+1}: {card}")

if __name__ == "__main__":
    main()
