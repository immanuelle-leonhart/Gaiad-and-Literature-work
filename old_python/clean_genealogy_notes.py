#!/usr/bin/env python3
"""
Clean up genealogy GEDCOM file to keep only useful notes:
- Clean Wikidata Q-IDs (format: 1 NOTE Wikidata: Q12345)  
- Clean Geni profile IDs (format: 1 NOTE geni:123456789)
- Remove all messy mixed URL notes and CONT/CONC continuations
"""

import re
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_genealogy_notes(input_file: str, output_file: str):
    """Clean up the genealogy file notes"""
    
    logger.info(f"Cleaning: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    logger.info(f"Read {len(lines):,} lines")
    
    output_lines = []
    current_individual_lines = []
    in_individual = False
    skip_next_lines = 0
    
    geni_notes_added = 0
    wikidata_notes_added = 0
    messy_notes_removed = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Skip lines if we're in a continuation we want to remove
        if skip_next_lines > 0:
            skip_next_lines -= 1
            continue
        
        # Check if starting new individual
        if stripped.startswith('0 @') and stripped.endswith('@ INDI'):
            # Process previous individual
            if in_individual:
                output_lines.extend(current_individual_lines)
                output_lines.append("\n")
            
            # Start new individual  
            in_individual = True
            current_individual_lines = [line]
            
        elif stripped.startswith('0 '):
            # End of individual, start of new record
            if in_individual:
                output_lines.extend(current_individual_lines)
                output_lines.append("\n")
            
            output_lines.append(line)
            in_individual = False
            current_individual_lines = []
            
        elif in_individual:
            # Line within individual record
            
            # Check for messy mixed URL notes to skip
            if (stripped.startswith('1 NOTE') and 
                ('Wikidata: https://www.wikidata.org/wiki/' in stripped and 
                 '| Geni: https://www.g' in stripped)):
                # This is a messy mixed URL note - skip it and any continuations
                messy_notes_removed += 1
                
                # Look ahead for CONT/CONC lines to skip
                j = i + 1
                while j < len(lines) and (lines[j].strip().startswith('2 CONT') or 
                                        lines[j].strip().startswith('2 CONC')):
                    skip_next_lines += 1
                    j += 1
                continue
                
            # Check for other messy notes with URLs
            elif (stripped.startswith('1 NOTE') and 
                  ('http://' in stripped or 'https://' in stripped) and
                  ('geni.com' in stripped or 'wikidata.org' in stripped)):
                # Skip messy URL notes
                messy_notes_removed += 1
                
                # Look ahead for continuations to skip
                j = i + 1
                while j < len(lines) and (lines[j].strip().startswith('2 CONT') or 
                                        lines[j].strip().startswith('2 CONC')):
                    skip_next_lines += 1
                    j += 1
                continue
            
            # Check for clean Geni ID notes (already added by our previous script)
            elif (stripped.startswith('1 NOTE geni:') and 
                  re.match(r'1 NOTE geni:\d+$', stripped)):
                current_individual_lines.append(line)
                geni_notes_added += 1
                
            # Check for clean Wikidata Q-ID notes and convert to clean format
            elif stripped.startswith('1 NOTE') and 'Q' in stripped:
                # Extract Q-ID if present
                qid_match = re.search(r'Q\d+', stripped)
                if qid_match:
                    qid = qid_match.group(0)
                    clean_note = f"1 NOTE Wikidata: {qid}\n"
                    current_individual_lines.append(clean_note)
                    wikidata_notes_added += 1
                else:
                    # Other NOTE, keep as-is if it's not messy
                    if not ('http://' in stripped or 'https://' in stripped):
                        current_individual_lines.append(line)
                        
            # Check for REFN lines - extract Geni IDs and add clean notes
            elif stripped.startswith('1 REFN geni:'):
                current_individual_lines.append(line)  # Keep original REFN
                
                # Extract Geni ID and add clean note if not already present
                geni_match = re.search(r'geni:(\d+)', stripped)
                if geni_match:
                    geni_id = geni_match.group(0)
                    clean_note = f"1 NOTE {geni_id}\n"
                    
                    # Check if we already have this note
                    note_exists = False
                    for existing_line in current_individual_lines:
                        if f"1 NOTE {geni_id}" in existing_line.strip():
                            note_exists = True
                            break
                    
                    if not note_exists:
                        current_individual_lines.append(clean_note)
                        geni_notes_added += 1
                        
            # Skip CONT/CONC lines (they're messy continuations)
            elif stripped.startswith('2 CONT') or stripped.startswith('2 CONC'):
                continue
                
            else:
                # Keep other lines (names, dates, families, etc.)
                current_individual_lines.append(line)
                
        else:
            # Not in individual, just copy
            output_lines.append(line)
    
    # Handle last individual
    if in_individual:
        output_lines.extend(current_individual_lines)
    
    # Write output
    logger.info(f"Writing to: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)
    
    logger.info(f"Cleaning complete!")
    logger.info(f"  Input lines: {len(lines):,}")
    logger.info(f"  Output lines: {len(output_lines):,}")
    logger.info(f"  Clean Geni notes: {geni_notes_added}")
    logger.info(f"  Clean Wikidata notes: {wikidata_notes_added}")
    logger.info(f"  Messy notes removed: {messy_notes_removed}")

def main():
    input_file = "C:\\Users\\Immanuelle\\Documents\\Github\\Gaiad-Genealogy\\comprehensive_genealogy.ged"
    output_file = "C:\\Users\\Immanuelle\\Documents\\Github\\Gaiad-Genealogy\\comprehensive_genealogy_CLEANED.ged"
    
    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        return
    
    print("=== Genealogy Notes Cleaner ===")
    print(f"Input: {input_file}")
    print(f"Size: {os.path.getsize(input_file) / (1024*1024):.1f} MB")
    print(f"Output: {output_file}")
    print()
    
    clean_genealogy_notes(input_file, output_file)
    
    if os.path.exists(output_file):
        print(f"Output size: {os.path.getsize(output_file) / (1024*1024):.1f} MB")

if __name__ == "__main__":
    main()