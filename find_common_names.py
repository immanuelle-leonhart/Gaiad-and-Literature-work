#!/usr/bin/env python3
"""
Find individuals with similar names between the two main files to create better test samples
"""

import logging
from difflib import SequenceMatcher
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_names_from_gedcom(filename: str, max_individuals: int = 1000):
    """Extract names from GEDCOM file"""
    individuals = {}
    current_id = None
    
    with open(filename, 'r', encoding='utf-8-sig', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if line.startswith('0 @I') and 'INDI' in line:
                current_id = line.split('@')[1]
            elif line.startswith('1 NAME ') and current_id:
                name = line[7:].strip()
                # Clean up the name
                name = re.sub(r'/[^/]*/', '', name).strip()  # Remove surname markers
                if name and len(name) > 3:  # Skip very short names
                    individuals[current_id] = name
                    if len(individuals) >= max_individuals:
                        break
                        
    return individuals

def find_similar_names(geni_names: dict, ftb_names: dict, min_similarity: float = 0.7):
    """Find similar names between the two files"""
    matches = []
    
    for geni_id, geni_name in geni_names.items():
        for ftb_id, ftb_name in ftb_names.items():
            similarity = SequenceMatcher(None, geni_name.lower(), ftb_name.lower()).ratio()
            if similarity >= min_similarity:
                matches.append((geni_id, geni_name, ftb_id, ftb_name, similarity))
                
    # Sort by similarity
    matches.sort(key=lambda x: x[4], reverse=True)
    return matches

def main():
    print("Finding similar names between files...")
    
    geni_names = extract_names_from_gedcom("new_gedcoms/geni_plus_wikidata_cleaned.ged", 5000)
    ftb_names = extract_names_from_gedcom("new_gedcoms/gaiad_ftb_export_2.ged", 5000)
    
    print(f"Extracted {len(geni_names)} names from Geni file")
    print(f"Extracted {len(ftb_names)} names from FTB file")
    
    matches = find_similar_names(geni_names, ftb_names, 0.6)
    
    print(f"\nFound {len(matches)} potential name matches:")
    for i, (geni_id, geni_name, ftb_id, ftb_name, similarity) in enumerate(matches[:20]):
        print(f"{i+1:2d}. {similarity:.2f} - Geni {geni_id}: '{geni_name}' ~ FTB {ftb_id}: '{ftb_name}'")
        
    if matches:
        print(f"\nBest matches suggest these individuals might be the same people.")
        print("You could create targeted samples around these to test merging.")
    else:
        print("\nNo similar names found. The files may contain completely different genealogical data.")

if __name__ == "__main__":
    main()