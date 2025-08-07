#!/usr/bin/env python3
"""
Properly add Geni ID notes to GEDCOM file.
For every individual with a REFN line containing "geni:", add a "1 NOTE geni:XXXXX" line.
Preserve ALL original data including REFN lines.
"""

import re
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_gedcom_properly(input_file: str, output_file: str):
    """Process GEDCOM to add Geni NOTE lines while preserving everything"""
    
    logger.info(f"Processing: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    logger.info(f"Read {len(lines):,} lines")
    
    output_lines = []
    geni_notes_added = 0
    current_individual_lines = []
    current_geni_ids = []
    in_individual = False
    
    for line in lines:
        stripped = line.strip()
        
        # Check if starting new individual
        if stripped.startswith('0 @') and stripped.endswith('@ INDI'):
            # Process previous individual if any
            if in_individual:
                # Add all lines for previous individual
                output_lines.extend(current_individual_lines)
                
                # Add Geni NOTE lines at the end
                for geni_id in current_geni_ids:
                    output_lines.append(f"1 NOTE {geni_id}\n")
                    geni_notes_added += 1
                
                output_lines.append("\n")  # Empty line after individual
            
            # Start new individual
            in_individual = True
            current_individual_lines = [line]
            current_geni_ids = []
            
        elif stripped.startswith('0 '):
            # End of individual, start of new record type
            if in_individual:
                # Process the individual we just finished
                output_lines.extend(current_individual_lines)
                
                # Add Geni NOTE lines
                for geni_id in current_geni_ids:
                    output_lines.append(f"1 NOTE {geni_id}\n")
                    geni_notes_added += 1
                
                output_lines.append("\n")  # Empty line after individual
                
            # Add the new record line
            output_lines.append(line)
            in_individual = False
            current_individual_lines = []
            current_geni_ids = []
            
        elif in_individual:
            # Line within individual record
            current_individual_lines.append(line)
            
            # Check for Geni REFN
            if stripped.startswith('1 REFN ') or stripped.startswith('2 REFN '):
                refn_value = stripped.split(' ', 2)
                if len(refn_value) >= 3 and refn_value[2].startswith('geni:'):
                    current_geni_ids.append(refn_value[2])
                    
        else:
            # Not in individual, just copy line
            output_lines.append(line)
    
    # Handle last individual if file doesn't end with new record
    if in_individual:
        output_lines.extend(current_individual_lines)
        for geni_id in current_geni_ids:
            output_lines.append(f"1 NOTE {geni_id}\n")
            geni_notes_added += 1
    
    # Write output
    logger.info(f"Writing to: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)
    
    logger.info(f"Complete! Added {geni_notes_added} Geni NOTE lines")
    logger.info(f"Output has {len(output_lines):,} lines")

def main():
    input_file = "C:\\Users\\Immanuelle\\Documents\\Github\\Gaiad-Genealogy\\geni plus wikidata after merge.ged"
    output_file = "C:\\Users\\Immanuelle\\Documents\\Github\\Gaiad-Genealogy\\geni_plus_wikidata_FIXED_with_notes.ged"
    
    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        return
    
    print("=== Proper Geni Notes Fixer ===")
    print(f"Input: {input_file}")
    print(f"Size: {os.path.getsize(input_file) / (1024*1024):.1f} MB")
    print(f"Output: {output_file}")
    print()
    
    process_gedcom_properly(input_file, output_file)
    
    if os.path.exists(output_file):
        print(f"Output file size: {os.path.getsize(output_file) / (1024*1024):.1f} MB")

if __name__ == "__main__":
    main()