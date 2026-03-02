import re
import sys
import os

"""
Forge Deck Exporter for Gemini CLI
-------------------------------
This script converts a standard Markdown deck file from this project into 
 a '.dck' file compatible with the Forge MTG game.

It parses the 'COMMANDER:', 'DECK:', and 'SIDEBOARD:' sections from the 
copy/paste area of our deck guides.

Usage: python3 scripts/forge_exporter.py <path_to_deck_file.md>
"""

def parse_md_deck(file_path):
    """
    Parses the Markdown file to extract Commander, Main Deck, and Sideboard.
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None

    # Extraction Logic
    # We look for the "Plain Text Copy/Paste" section specifically
    
    # 1. Extract Commander(s)
    # Pattern: COMMANDER:\s*(.*?)(?=DECK:|SIDEBOARD:|#|\Z)
    commander_match = re.search(r'COMMANDER:\s*(.*?)(?=DECK:|SIDEBOARD:|#|\Z)', content, re.DOTALL | re.IGNORECASE)
    commanders = []
    if commander_match:
        lines = commander_match.group(1).strip().split('
')
        commanders = [line.strip() for line in lines if line.strip()]

    # 2. Extract Main Deck
    # Pattern: DECK:\s*(.*?)(?=SIDEBOARD:|#|\Z)
    deck_match = re.search(r'DECK:\s*(.*?)(?=SIDEBOARD:|#|\Z)', content, re.DOTALL | re.IGNORECASE)
    main_deck = []
    if deck_match:
        lines = deck_match.group(1).strip().split('
')
        main_deck = [line.strip() for line in lines if line.strip()]

    # 3. Extract Sideboard
    # Pattern: SIDEBOARD:\s*(.*?)(?=#|\Z)
    sideboard_match = re.search(r'SIDEBOARD:\s*(.*?)(?=#|\Z)', content, re.DOTALL | re.IGNORECASE)
    sideboard = []
    if sideboard_match:
        lines = sideboard_match.group(1).strip().split('
')
        sideboard = [line.strip() for line in lines if line.strip()]

    return {
        "name": os.path.splitext(os.path.basename(file_path))[0],
        "commanders": commanders,
        "main": main_deck,
        "sideboard": sideboard
    }

def export_to_forge(deck_data, output_path):
    """
    Writes the parsed deck data into the Forge .dck format.
    """
    lines = []
    lines.append("[metadata]")
    lines.append(f"Name={deck_data['name']}")
    
    # Forge often likes to know if it's a Commander deck
    if deck_data['commanders']:
        lines.append("Deck Type=Commander")

    if deck_data['commanders']:
        lines.append("[Commander]")
        for c in deck_data['commanders']:
            lines.append(c)

    if deck_data['main']:
        lines.append("[Main]")
        for c in deck_data['main']:
            lines.append(c)

    if deck_data['sideboard']:
        lines.append("[Sideboard]")
        for c in deck_data['sideboard']:
            lines.append(c)

    try:
        with open(output_path, 'w') as f:
            f.write('
'.join(lines))
        print(f"Successfully exported Forge deck to: {output_path}")
    except Exception as e:
        print(f"Error writing .dck file: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/forge_exporter.py <path_to_deck_file.md>")
        return

    input_file = sys.argv[1]
    
    # Verify file extension
    if not input_file.endswith('.md'):
        print("Error: Please provide a .md deck file.")
        return

    deck_data = parse_md_deck(input_file)
    
    if deck_data:
        # Create output filename by replacing .md with .dck
        output_file = os.path.splitext(input_file)[0] + ".dck"
        export_to_forge(deck_data, output_file)

if __name__ == "__main__":
    main()
