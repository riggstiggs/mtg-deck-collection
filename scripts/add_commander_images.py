#!/usr/bin/env python3
"""
Commander Image Linker — Scryfall-powered

This script automatically finds the name of the commander in your deck files,
fetches the correct image URL from the Scryfall API, and inserts it into 
your README.md and main deck files so they look great on GitHub.
"""

import os
import re
import subprocess
import json
import time
import urllib.parse

# --- Configuration ---

# Some cards have complex names or are double-faced. This dictionary
# tells the script exactly what name to search for if the one it 
# finds in the file isn't working or isn't the primary face.
NAME_OVERRIDES = {
    "Captain America Voltron": "Captain America, First Avenger",
    "The Emperor of Palamecia // The Lord Master of Hell": "The Emperor of Palamecia",
    "Norman Osborn / Green Goblin": "Norman Osborn",
    "Zangief, the Red Cyclone": "Zangief, the Red Cyclone",
    "Etali, Primal Conqueror": "Etali, Primal Conqueror"
}

# ---------------------------------------------------------------------------
# API Interaction
# ---------------------------------------------------------------------------

def get_scryfall_image(name):
    """
    Connects to Scryfall to get the 'normal' sized image for a card.
    
    How it works:
    1. Check if we have a manual override for the name.
    2. URL-encode the name (converts spaces/symbols so they work in a web link).
    3. Use 'curl' to send a request to Scryfall's 'fuzzy' search API.
    4. Parse the resulting JSON to find the image URL.
    """
    # Use override if exists, otherwise use the name as-is
    name = NAME_OVERRIDES.get(name, name)
    print(f"Fetching Scryfall image for: {name}")
    
    # Fuzzy search is used because it's better at finding cards even if 
    # the name isn't 100% perfect (e.g. missing a comma).
    safe_name = urllib.parse.quote(name)
    cmd = f"curl -s \"https://api.scryfall.com/cards/named?fuzzy={safe_name}\""
    
    try:
        # Run the curl command and capture the output
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error fetching {name}: {result.stderr}")
            return None
            
        # Convert the text output into a Python dictionary (JSON)
        data = json.loads(result.stdout)
        
        # Option A: Standard Card
        # Most cards have their images in a top-level 'image_uris' field.
        if 'image_uris' in data:
            return data['image_uris']['normal']
            
        # Option B: Double-Faced Card
        # Transform cards have multiple 'faces', each with its own image.
        # We grab the first face (face 0).
        elif 'card_faces' in data:
            if 'image_uris' in data['card_faces'][0]:
                return data['card_faces'][0]['image_uris']['normal']
        
        print(f"No image_uris found for {name}: {data.get('details', 'No details')}")
        return None
    except Exception as e:
        print(f"Exception for {name}: {e}")
        return None

# ---------------------------------------------------------------------------
# File Parsing
# ---------------------------------------------------------------------------

def extract_commander(filepath):
    """
    Reads a Markdown file and tries to figure out who the Commander is.
    
    It looks for two common patterns in this project:
    1. Inside a '## Commander Strategy' section where the name is in **bold**.
    2. The main H1 title of the file (e.g. '# Deck Guide: [Name]').
    """
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Pattern 1: Look for the **Name** right after 'Commander Strategy'
    # This is the most reliable way in our project structure.
    match = re.search(r'##\s+.*?Commander Strategy.*?\n\*\*([^*]+)\*\*', content, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # Pattern 2: Fallback to the main title of the document.
    header_match = re.search(r'#\s+(?:Deck Guide:\s+)?(.*?)(?:\s+-\s+.*|\s+\(.*|\s+Deck Guide|$)', content, re.IGNORECASE)
    if header_match:
        name = header_match.group(1).strip()
        # Clean up common title phrases so we just get the card name
        name = re.sub(r'^(?:Deck Guide:\s+)', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s+Deck Guide$', '', name, flags=re.IGNORECASE)
        return name
    
    return None

def update_file(filepath, image_url, name):
    """
    Inserts the image into the file if it's not already there.
    The image is placed right after the first H1 header (# Title).
    """
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Safety Check: Don't add the image if it's already in the file.
    if f"![]({image_url})" in content or f"![{name}]({image_url})" in content:
        print(f"Image already exists in {filepath}")
        return

    lines = content.splitlines()
    new_lines = []
    found_header = False
    image_inserted = False
    
    for line in lines:
        new_lines.append(line)
        # We look for the first line starting with '# ' (the main title)
        if not image_inserted and line.strip().startswith('# ') and not found_header:
            found_header = True
            # Add the Markdown image code on a new line after the title
            new_lines.append(f"\n![{name}]({image_url})")
            image_inserted = True
            
    # Save the file back to disk
    with open(filepath, 'w') as f:
        f.write('\n'.join(new_lines) + '\n')
    print(f"Updated {filepath}")

# ---------------------------------------------------------------------------
# Main Logic
# ---------------------------------------------------------------------------

def main():
    """
    The 'Manager' function that coordinates everything:
    1. Finds all relevant files.
    2. Identifies the commanders.
    3. Fetches the images.
    4. Updates the files.
    """
    targets = []
    # Walk through all folders starting from 'commander_decks'
    for root, dirs, files in os.walk('commander_decks'):
        # Skip 'PreCons' and 'External' folders as requested by project rules
        if 'PreCons' in root or 'External' in root:
            continue
            
        for file in files:
            if file.endswith('.md'):
                filepath = os.path.join(root, file)
                # We only want to update READMEs or the 'main' working deck lists
                with open(filepath, 'r') as f:
                    content = f.read()
                    if file == 'README.md' or 'deck_status: main' in content:
                        targets.append(filepath)
    
    # folder_images is a 'cache' so if we have two files in one folder 
    # (like README.md and deck.md), we only call the API once.
    folder_images = {}

    for target in targets:
        folder = os.path.dirname(target)
        if folder not in folder_images:
            name = extract_commander(target)
            if name:
                image_url = get_scryfall_image(name)
                if image_url:
                    folder_images[folder] = (image_url, name)
                else:
                    print(f"Could not find image for {name} in {target}")
                    folder_images[folder] = (None, None)
            else:
                print(f"Could not extract commander name from {target}")
                folder_images[folder] = (None, None)
        
        # If we successfully found an image for this folder, update the file.
        image_url, name = folder_images[folder]
        if image_url:
            update_file(target, image_url, name)
            # Short pause to be respectful to Scryfall's server
            time.sleep(0.05)

if __name__ == "__main__":
    main()
