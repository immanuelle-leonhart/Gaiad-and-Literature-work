#!/usr/bin/env python3
"""
EXTRACT Geni and Wikidata links from the broken CONT/CONC notes.
Parse the messy broken lines to recover the actual links.
"""

import re
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_broken_links(input_file: str, output_file: str):
    """Extract links from broken CONT/CONC notes"""
    
    logger.info(f"Extracting from: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    logger.info(f"Read {len(lines):,} lines")
    
    output_lines = []
    current_individual_lines = []
    current_note_continuation = ""
    in_individual = False
    
    extracted_geni = 0
    extracted_wikidata = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Check if starting new individual
        if stripped.startswith('0 @') and stripped.endswith('@ INDI'):
            # Process previous individual
            if in_individual:
                output_lines.extend(current_individual_lines)
                output_lines.append("\n")
            
            # Start new individual  
            in_individual = True
            current_individual_lines = [line]
            current_note_continuation = ""
            
        elif stripped.startswith('0 '):
            # End of individual
            if in_individual:
                output_lines.extend(current_individual_lines)
                output_lines.append("\n")
            
            output_lines.append(line)
            in_individual = False
            current_individual_lines = []
            current_note_continuation = ""
            
        elif in_individual:
            # Line within individual record
            
            # Check for start of broken note with mixed URLs
            if (stripped.startswith('1 NOTE') and 
                ('Wikidata: https://www.wikidata.org/wiki/' in stripped or
                 'geni.com' in stripped)):
                
                # Start collecting the broken note
                current_note_continuation = stripped[6:].strip()  # Remove "1 NOTE"
                continue  # Don't add the broken line yet
                
            # Check for CONT/CONC continuation lines
            elif (stripped.startswith('2 CONT') or stripped.startswith('2 CONC')):
                # Add to continuation
                if stripped.startswith('2 CONT'):
                    continuation_text = stripped[6:].strip()  # Remove "2 CONT"
                else:
                    continuation_text = stripped[6:].strip()  # Remove "2 CONC"
                
                current_note_continuation += continuation_text
                continue  # Don't add the broken line yet
                
            else:
                # Process any accumulated continuation before adding this line
                if current_note_continuation:
                    # Extract links from the accumulated text
                    full_text = current_note_continuation
                    
                    # Extract Wikidata Q-IDs
                    wikidata_matches = re.findall(r'https://www\.wikidata\.org/wiki/(Q\d+)', full_text)
                    for qid in wikidata_matches:
                        current_individual_lines.append(f"1 NOTE Wikidata: {qid}\n")
                        extracted_wikidata += 1
                    
                    # Extract Geni profile IDs
                    geni_matches = re.findall(r'geni\.com/people/[^/]+/(\d+)', full_text)
                    for geni_id in geni_matches:
                        current_individual_lines.append(f"1 NOTE geni:{geni_id}\n")
                        extracted_geni += 1
                    
                    # Also look for direct geni: patterns
                    direct_geni_matches = re.findall(r'geni:(\d+)', full_text)
                    for geni_id in direct_geni_matches:
                        if geni_id not in geni_matches:  # Avoid duplicates
                            current_individual_lines.append(f"1 NOTE geni:{geni_id}\n")
                            extracted_geni += 1
                    
                    current_note_continuation = ""
                
                # Add the current line
                current_individual_lines.append(line)
                
        else:
            # Not in individual, just copy
            output_lines.append(line)
    
    # Handle last individual
    if in_individual:
        # Process any final continuation
        if current_note_continuation:
            full_text = current_note_continuation
            
            wikidata_matches = re.findall(r'https://www\.wikidata\.org/wiki/(Q\d+)', full_text)
            for qid in wikidata_matches:
                current_individual_lines.append(f"1 NOTE Wikidata: {qid}\n")
                extracted_wikidata += 1
            
            geni_matches = re.findall(r'geni\.com/people/[^/]+/(\d+)', full_text)
            for geni_id in geni_matches:
                current_individual_lines.append(f"1 NOTE geni:{geni_id}\n")
                extracted_geni += 1
            
            direct_geni_matches = re.findall(r'geni:(\d+)', full_text)
            for geni_id in direct_geni_matches:
                if geni_id not in geni_matches:
                    current_individual_lines.append(f"1 NOTE geni:{geni_id}\n")
                    extracted_geni += 1
        
        output_lines.extend(current_individual_lines)
    
    # Write output
    logger.info(f"Writing to: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)
    
    logger.info(f"Extraction complete!")
    logger.info(f"  Input lines: {len(lines):,}")
    logger.info(f"  Output lines: {len(output_lines):,}")
    logger.info(f"  Extracted Geni IDs: {extracted_geni}")
    logger.info(f"  Extracted Wikidata Q-IDs: {extracted_wikidata}")

def main():
    # Use the ORIGINAL file, not the cleaned one I fucked up
    input_file = "C:\\Users\\Immanuelle\\Documents\\Github\\Gaiad-Genealogy\\comprehensive_genealogy.ged"
    output_file = "C:\\Users\\Immanuelle\\Documents\\Github\\Gaiad-Genealogy\\comprehensive_genealogy_PROPERLY_FIXED.ged"
    
    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        return
    
    print("=== Link Extractor (Fixing My Fuckup) ===")
    print(f"Input: {input_file}")
    print(f"Size: {os.path.getsize(input_file) / (1024*1024):.1f} MB")
    print(f"Output: {output_file}")
    print()
    
    extract_broken_links(input_file, output_file)
    
    if os.path.exists(output_file):
        print(f"Output size: {os.path.getsize(output_file) / (1024*1024):.1f} MB")

if __name__ == "__main__":
    main()