#!/usr/bin/env python3
"""
Forge Deck Exporter — Convert Markdown to Forge .dck

Forge is an MTG software that uses a specific file format (.dck).
Our project uses Markdown (.md) for readability. This script bridges
the two, allowing you to export your deck guides directly into Forge.

It scans for the 'Plain Text Copy/Paste' section at the bottom of our files.
"""

import re
import sys
import os

# ---------------------------------------------------------------------------
# Extraction Logic
# ---------------------------------------------------------------------------

def parse_md_deck(file_path):
    """
    Reads a Markdown deck file and extracts the card names for the 
    Commander, Main Deck, and Sideboard.
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None

    # Extraction Strategy:
    # We use Regular Expressions (re) to find text between specific markers.
    # Pattern explanation:
    # (?=...) is a 'lookahead' — it says "stop before you hit these words".
    # re.DOTALL makes the dot (.) match newlines, allowing us to capture multiple lines.
    
    # 1. Extract Commander(s)
    # Looks for text after 'COMMANDER:' but before 'DECK:', 'SIDEBOARD:', or a '# ' header.
    commander_match = re.search(r'COMMANDER:\s*(.*?)(?=DECK:|SIDEBOARD:|#|\Z)', content, re.DOTALL | re.IGNORECASE)
    commanders = []
    if commander_match:
        lines = commander_match.group(1).strip().split('\n')
        # Clean up each line (remove leading/trailing spaces) and ignore empty lines
        commanders = [line.strip() for line in lines if line.strip()]

    # 2. Extract Main Deck
    # Looks for text after 'DECK:' but before 'SIDEBOARD:' or a '# ' header.
    deck_match = re.search(r'DECK:\s*(.*?)(?=SIDEBOARD:|#|\Z)', content, re.DOTALL | re.IGNORECASE)
    main_deck = []
    if deck_match:
        lines = deck_match.group(1).strip().split('\n')
        main_deck = [line.strip() for line in lines if line.strip()]

    # 3. Extract Sideboard
    # Looks for text after 'SIDEBOARD:' until the end of the file or a '# ' header.
    sideboard_match = re.search(r'SIDEBOARD:\s*(.*?)(?=#|\Z)', content, re.DOTALL | re.IGNORECASE)
    sideboard = []
    if sideboard_match:
        lines = sideboard_match.group(1).strip().split('\n')
        sideboard = [line.strip() for line in lines if line.strip()]

    # Return a structured 'dictionary' of the deck data
    return {
        "name": os.path.splitext(os.path.basename(file_path))[0], # The filename without '.md'
        "commanders": commanders,
        "main": main_deck,
        "sideboard": sideboard
    }

# ---------------------------------------------------------------------------
# Output Logic
# ---------------------------------------------------------------------------

def export_to_forge(deck_data, output_path):
    """
    Takes our clean deck data and writes it into the exact format Forge needs.
    """
    lines = []
    
    # Forge metadata section
    lines.append("[metadata]")
    lines.append(f"Name={deck_data['name']}")
    
    # If there's a commander, tell Forge it's a Commander deck
    if deck_data['commanders']:
        lines.append("Deck Type=Commander")

    # [Commander] section
    if deck_data['commanders']:
        lines.append("[Commander]")
        for c in deck_data['commanders']:
            lines.append(c)

    # [Main] section
    if deck_data['main']:
        lines.append("[Main]")
        for c in deck_data['main']:
            lines.append(c)

    # [Sideboard] section
    if deck_data['sideboard']:
        lines.append("[Sideboard]")
        for c in deck_data['sideboard']:
            lines.append(c)

    try:
        # Write the lines to the new file, separated by newline characters
        with open(output_path, 'w') as f:
            f.write('\n'.join(lines))
        print(f"Successfully exported Forge deck to: {output_path}")
    except Exception as e:
        print(f"Error writing .dck file: {e}")

# ---------------------------------------------------------------------------
# CLI Management
# ---------------------------------------------------------------------------

def main():
    """
    The entry point. It validates the user's input and starts the process.
    """
    # sys.argv is a list of words typed in the terminal. 
    # argv[0] is the script name, argv[1] is the deck file path.
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/forge_exporter.py <path_to_deck_file.md>")
        return

    input_file = sys.argv[1]
    
    # Safety check: is this actually a Markdown file?
    if not input_file.endswith('.md'):
        print("Error: Please provide a .md deck file.")
        return

    # Phase 1: Parse the Markdown
    deck_data = parse_md_deck(input_file)
    
    if deck_data:
        # Phase 2: Export to .dck
        # os.path.splitext splits "deck.md" into ("deck", ".md")
        output_file = os.path.splitext(input_file)[0] + ".dck"
        export_to_forge(deck_data, output_file)

if __name__ == "__main__":
    main()
