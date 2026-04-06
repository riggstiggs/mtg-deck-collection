import os
import re
import subprocess
import json
import time
import urllib.parse

# Manual overrides for commander names that are tricky to parse or find
NAME_OVERRIDES = {
    "Captain America Voltron": "Captain America, First Avenger",
    "The Emperor of Palamecia // The Lord Master of Hell": "The Emperor of Palamecia",
    "Norman Osborn / Green Goblin": "Norman Osborn",
    "Zangief, the Red Cyclone": "Zangief, the Red Cyclone",
    "Etali, Primal Conqueror": "Etali, Primal Conqueror"
}

def get_scryfall_image(name):
    # Use override if exists
    name = NAME_OVERRIDES.get(name, name)
    print(f"Fetching Scryfall image for: {name}")
    
    # Try fuzzy search first as it's more robust for split cards/transforms
    safe_name = urllib.parse.quote(name)
    cmd = f"curl -s \"https://api.scryfall.com/cards/named?fuzzy={safe_name}\""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error fetching {name}: {result.stderr}")
            return None
        data = json.loads(result.stdout)
        
        # Check standard image_uris
        if 'image_uris' in data:
            return data['image_uris']['normal']
        # Check card_faces for transform/split cards
        elif 'card_faces' in data:
            if 'image_uris' in data['card_faces'][0]:
                return data['card_faces'][0]['image_uris']['normal']
        
        print(f"No image_uris found for {name}: {data.get('details', 'No details')}")
        return None
    except Exception as e:
        print(f"Exception for {name}: {e}")
        return None

def extract_commander(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Try finding in ## Commander Strategy section (Standard for this project)
    match = re.search(r'##\s+.*?Commander Strategy.*?\n\*\*([^*]+)\*\*', content, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # Fallback to header (less reliable)
    header_match = re.search(r'#\s+(?:Deck Guide:\s+)?(.*?)(?:\s+-\s+.*|\s+\(.*|\s+Deck Guide|$)', content, re.IGNORECASE)
    if header_match:
        name = header_match.group(1).strip()
        name = re.sub(r'^(?:Deck Guide:\s+)', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s+Deck Guide$', '', name, flags=re.IGNORECASE)
        return name
    
    return None

def update_file(filepath, image_url, name):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Avoid double images
    if f"![]({image_url})" in content or f"![{name}]({image_url})" in content:
        print(f"Image already exists in {filepath}")
        return

    lines = content.splitlines()
    new_lines = []
    found_header = False
    image_inserted = False
    
    for line in lines:
        new_lines.append(line)
        if not image_inserted and line.strip().startswith('# ') and not found_header:
            found_header = True
            # Add image after the main title header
            new_lines.append(f"\n![{name}]({image_url})")
            image_inserted = True
            
    with open(filepath, 'w') as f:
        f.write('\n'.join(new_lines) + '\n')
    print(f"Updated {filepath}")

def main():
    targets = []
    for root, dirs, files in os.walk('commander_decks'):
        if 'PreCons' in root or 'External' in root:
            continue
            
        for file in files:
            if file.endswith('.md'):
                filepath = os.path.join(root, file)
                # Check if it's README.md or has deck_status: main
                with open(filepath, 'r') as f:
                    content = f.read()
                    if file == 'README.md' or 'deck_status: main' in content:
                        targets.append(filepath)
    
    # Use a cache to avoid redundant API calls for the same folder
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
        
        image_url, name = folder_images[folder]
        if image_url:
            update_file(target, image_url, name)
            time.sleep(0.05)

if __name__ == "__main__":
    main()
