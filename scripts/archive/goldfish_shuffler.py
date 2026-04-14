#!/usr/bin/env python3
"""
Goldfish Shuffler — Deck Parser & Randomizer

The "Honest Goldfish" is a method of testing a deck by yourself to see how
consistently it draws lands and key pieces. This script automates the 
shuffling and drawing process so you don't have to manually shuffle 
a stack of 100 cards over and over.

It reads the 'DECK:' section of your Markdown files and gives you 
the top 20 cards (Hand + Early Draws).
"""

import random
import re
import sys
import time

# ---------------------------------------------------------------------------
# File Parsing Logic
# ---------------------------------------------------------------------------

def parse_deck_file(file_path):
    """
    Reads a deck's Markdown file and converts the text list into a 
    Python 'list' of card names.
    """
    deck = []
    try:
        # Open the file for reading
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Extraction Strategy:
        # We look for the 'DECK:' header. 
        # The script captures everything after 'DECK:' until it hits a double 
        # newline (\n\n) or another header like 'SIDEBOARD:'.
        # re.DOTALL allows the search to span multiple lines.
        deck_section = re.search(r'DECK:\s*(.*?)(?=\n\n|\n[A-Z]+:|\Z)', content, re.DOTALL)
        
        if not deck_section:
            print(f"Error: Could not find the 'DECK:' section in {file_path}")
            print("Ensure the file follows the standard DECK_TEMPLATE.md format.")
            return None
            
        # .group(1) is the text captured by the parentheses in our regex search.
        # We split that text into individual lines.
        lines = deck_section.group(1).strip().split('\n')
        
        for line in lines:
            clean_line = line.strip()
            if not clean_line:
                continue # Skip any blank lines
            
            # Pattern Match: "1 Sol Ring" or "12 Forest"
            # (\d+) matches the number (quantity)
            # (.+) matches the name of the card
            match = re.match(r'(\d+)\s+(.+)', clean_line)
            
            if match:
                count = int(match.group(1)) # Convert "1" string to number 1
                name = match.group(2).strip()
                # Use .extend to add the card name to our deck list 'count' times
                deck.extend([name] * count)
                
        return deck
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    except Exception as e:
        # Generic error handling for unexpected issues
        print(f"An unexpected error occurred: {e}")
        return None

# ---------------------------------------------------------------------------
# Main Logic
# ---------------------------------------------------------------------------

def main():
    """
    Handles input, validates the deck size, and performs the shuffle.
    """
    # Check if the user typed a filename (e.g. python3 script.py path/to/deck.md)
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/goldfish_shuffler.py <path_to_deck_file>")
        return

    file_path = sys.argv[1]
    
    # Run the parser
    deck = parse_deck_file(file_path)
    
    if not deck:
        return

    # Validation: Commander decks (the 99)
    # The Commander themselves is usually in a separate section, so we look for 99 cards.
    if len(deck) != 99:
        print(f"---")
        print(f"VALIDATION NOTE: This deck contains {len(deck)} cards.")
        print(f"Standard Commander decks (excluding the commander) usually have 99.")
        print(f"---")

    # Shuffling Logic:
    # random.seed(time.time_ns()) makes sure the shuffle is truly different 
    # every time you run it, based on the current nanosecond.
    random.seed(time.time_ns())
    random.shuffle(deck)

    # Output Results
    print(f"--- HONEST SHUFFLE: {file_path} ---")
    print(f"TIMESTAMP: {time.ctime()}")
    print(f"PARSED DECK SIZE: {len(deck)}")
    print("\nFIRST 20 CARDS (Top of Library / Opening Hand + Early Draws):")
    print("-" * 40)
    
    # We loop through the first 20 cards of the shuffled list
    for i, card in enumerate(deck[:20]):
        # Label the phases of the game
        label = ""
        if i < 7:
            label = "[Opening Hand]"
        elif i == 7:
            label = "[Turn 1 Draw]"
            
        # Scryfall helper URL
        # We replace spaces with '+' so the URL works correctly in a browser
        scryfall_url = f"https://scryfall.com/search?q={card.replace(' ', '+')}"
            
        # Formatting the output string for readability
        print(f"{i+1:2}: {card:<25} {label:<15} -> {scryfall_url}")
    print("-" * 40)

if __name__ == "__main__":
    main()
