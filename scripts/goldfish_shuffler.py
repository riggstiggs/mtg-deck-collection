import random
import re
import sys
import time

"""
Goldfish Shuffler for Gemini CLI
-------------------------------
This script parses a standard Markdown deck file used in the mtg-deck-collection 
project and simulates an "Honest Goldfish" shuffle. It extracts the 'DECK:' 
section, validates the card counts, and provides a randomized sequence for 
testing mana stability and strategic flow.

Usage: python3 scripts/goldfish_shuffler.py <path_to_deck_file>
"""

def parse_deck_file(file_path):
    """
    Reads a deck file and extracts the individual cards from the DECK section.
    
    Args:
        file_path (str): The absolute or relative path to the .md deck file.
        
    Returns:
        list: A list containing 99 card names (strings), or None if an error occurs.
    """
    deck = []
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # REGEX EXPLANATION:
        # DECK:\s*      -> Look for the "DECK:" header and any following whitespace.
        # (.*?)         -> Capture everything (non-greedily) into group 1...
        # (?=\n\n|\n[A-Z]+:|\Z) -> ...until we hit a double newline, a new header (like SIDEBOARD:), or the end of the file.
        deck_section = re.search(r'DECK:\s*(.*?)(?=\n\n|\n[A-Z]+:|\Z)', content, re.DOTALL)
        
        if not deck_section:
            print(f"Error: Could not find the 'DECK:' section in {file_path}")
            print("Ensure the file follows the standard DECK_TEMPLATE.md format.")
            return None
            
        # Split the raw text into individual lines
        lines = deck_section.group(1).strip().split('\n')
        
        for line in lines:
            clean_line = line.strip()
            if not clean_line:
                continue # Skip empty lines
            
            # Match lines like "1 Sol Ring" or "12 Forest"
            # (\d+)  -> Captures the quantity (digits)
            # \s+    -> Matches the whitespace separator
            # (.+)   -> Captures the rest of the line as the card name
            match = re.match(r'(\d+)\s+(.+)', clean_line)
            
            if match:
                count = int(match.group(1))
                name = match.group(2).strip()
                # Add the card name to our list 'count' number of times
                deck.extend([name] * count)
                
        return deck
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def main():
    # Ensure a file path was provided as a command-line argument
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/goldfish_shuffler.py <path_to_deck_file>")
        return

    file_path = sys.argv[1]
    deck = parse_deck_file(file_path)
    
    if not deck:
        return

    # Standard Commander Validation
    # We check for 99 cards because the Commander (the 100th card) 
    # is usually handled separately in the 'COMMANDER:' section.
    if len(deck) != 99:
        print(f"---")
        print(f"VALIDATION NOTE: This deck contains {len(deck)} cards.")
        print(f"Standard Commander decks (excluding the commander) usually have 99.")
        print(f"---")

    # ENTROPY SEEDING:
    # Using time.time_ns() ensures that the random seed is unique down to 
    # the nanosecond, preventing "pseudo-random" loops where you see the 
    # same cards in the same order across different test sessions.
    random.seed(time.time_ns())
    random.shuffle(deck)

    # Output the results for the "Honest Goldfish" trial
    print(f"--- HONEST SHUFFLE: {file_path} ---")
    print(f"TIMESTAMP: {time.ctime()}")
    print(f"PARSED DECK SIZE: {len(deck)}")
    print("\nFIRST 20 CARDS (Top of Library / Opening Hand + Early Draws):")
    print("-" * 40)
    for i, card in enumerate(deck[:20]):
        # The first 7 cards are your opening hand
        # Card 8 is your first draw on Turn 1
        label = ""
        if i < 7:
            label = "[Opening Hand]"
        elif i == 7:
            label = "[Turn 1 Draw]"
            
        print(f"{i+1:2}: {card:<30} {label}")
    print("-" * 40)

if __name__ == "__main__":
    main()
