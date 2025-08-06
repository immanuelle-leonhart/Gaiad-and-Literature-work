#!/usr/bin/env python3
"""
Apply English names from names_for_manual_review.txt to the GEDCOM file
"""

import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_english_names_from_translations_file():
    """Extract Q-ID to English name mappings from the translations file"""
    logger.info("Extracting English names from translations file...")
    
    qid_to_name = {}
    translations_file = r"C:\Users\Immanuelle\Documents\Github\Gaiad-Genealogy\geni\wikidata gedcoms\Translations.txt"
    
    with open(translations_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
                
            # Parse lines like "Q104668239 — Sam Syuni"
            if ' — ' in line:
                parts = line.split(' — ', 1)
                if len(parts) == 2:
                    qid = parts[0].strip()
                    english_name = parts[1].strip()
                    
                    if qid.startswith('Q') and english_name:
                        qid_to_name[qid] = english_name
                        logger.debug(f"Found: {qid} -> {english_name}")
                    else:
                        logger.warning(f"Line {line_num}: Invalid format: {line}")
                else:
                    logger.warning(f"Line {line_num}: Could not split: {line}")
            else:
                logger.warning(f"Line {line_num}: No separator found: {line}")
    
    logger.info(f"Extracted {len(qid_to_name)} English names")
    return qid_to_name

def apply_names_to_gedcom(qid_to_name):
    """Apply English names to GEDCOM file"""
    logger.info("Applying English names to GEDCOM...")
    
    # Read the GEDCOM file
    with open('wikidata_combined.ged', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Create backup
    backup_file = 'wikidata_combined_names_updated_backup.ged'
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    logger.info(f"Backup created: {backup_file}")
    
    updates_made = 0
    
    for i, line in enumerate(lines):
        # Look for NAME lines with Q-IDs
        match = re.match(r'1 NAME (Q\d+) //', line.strip())
        if match:
            qid = match.group(1)
            if qid in qid_to_name:
                english_name = qid_to_name[qid]
                
                # Parse the name into given and surname
                name_parts = english_name.split(' ', 1)
                given_name = name_parts[0]
                surname = name_parts[1] if len(name_parts) > 1 else ""
                
                # Update the NAME line
                lines[i] = f"1 NAME {given_name} /{surname}/\n"
                updates_made += 1
                logger.info(f"Updated {qid} -> {english_name}")
                
                # Find and update the GIVN line if it exists
                j = i + 1
                while j < len(lines) and not lines[j].startswith('1 '):
                    if lines[j].strip().startswith('2 GIVN '):
                        lines[j] = f"2 GIVN {given_name}\n"
                        break
                    j += 1
            else:
                logger.warning(f"No English name found for {qid}")
    
    # Write updated GEDCOM
    with open('wikidata_combined.ged', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    logger.info(f"Applied {updates_made} English names to GEDCOM")
    logger.info(f"Backup saved as: {backup_file}")
    
    return updates_made

def main():
    logger.info("Starting English names application...")
    
    # Extract names from translations file
    qid_to_name = extract_english_names_from_translations_file()
    
    if not qid_to_name:
        logger.error("No English names found in review file!")
        logger.error("Make sure you've filled in the 'SUGGESTED ENGLISH NAME:' fields")
        return
    
    # Apply names to GEDCOM
    updates_made = apply_names_to_gedcom(qid_to_name)
    
    logger.info("English names application completed!")
    logger.info(f"Total updates: {updates_made}")

if __name__ == "__main__":
    main()