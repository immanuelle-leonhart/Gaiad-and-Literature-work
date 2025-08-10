#!/usr/bin/env python3
"""
Extract Wikidata QIDs from NOTE fields and add them as REFNs to individuals.
Handles multiple REFNs per individual by preserving existing ones.
"""

import re
import sys
from typing import List, Dict, Set

def extract_wikidata_qids(text: str) -> Set[str]:
    """Extract all Wikidata QIDs from text."""
    qids = set()
    
    # Pattern for Q followed by digits
    qid_pattern = r'\bQ\d+\b'
    qids.update(re.findall(qid_pattern, text))
    
    # Pattern for full Wikidata URLs
    url_pattern = r'https?://www\.wikidata\.org/wiki/(Q\d+)'
    url_matches = re.findall(url_pattern, text)
    qids.update(url_matches)
    
    # Pattern for Wikidata entity URLs
    entity_pattern = r'https?://www\.wikidata\.org/entity/(Q\d+)'
    entity_matches = re.findall(entity_pattern, text)
    qids.update(entity_matches)
    
    return qids

def process_gedcom_file(input_file: str, output_file: str):
    """Process GEDCOM file to extract QIDs from notes and add as REFNs."""
    
    print(f"Processing {input_file}...")
    
    # Read file as binary to preserve exact line endings
    with open(input_file, 'rb') as f:
        content = f.read().decode('utf-8', errors='ignore')
    
    # Split preserving line endings
    if '\r\n' in content:
        lines = content.split('\r\n')
        line_ending = '\r\n'
    elif '\n' in content:
        lines = content.split('\n')
        line_ending = '\n'
    else:
        lines = [content]
        line_ending = '\n'
    
    processed_lines = []
    current_individual = None
    individual_qids = {}  # Store QIDs found for each individual
    existing_refns = {}   # Store existing REFNs for each individual
    stats = {
        'individuals_processed': 0,
        'qids_found': 0,
        'refns_added': 0
    }
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Track current individual
        if line.startswith('0 @') and line.endswith(' INDI'):
            current_individual = line.split()[1]  # Get the @I123@ part
            individual_qids[current_individual] = set()
            existing_refns[current_individual] = []
            stats['individuals_processed'] += 1
            
        # Track existing REFNs
        elif current_individual and line.startswith('1 REFN '):
            refn_value = line[7:].strip()
            existing_refns[current_individual].append(refn_value)
            
        # Process NOTE fields
        elif current_individual and line.startswith('1 NOTE '):
            note_content = line[7:]
            
            # Check for continuation lines
            j = i + 1
            while j < len(lines) and lines[j].startswith('2 CONT '):
                note_content += ' ' + lines[j][7:]
                j += 1
            while j < len(lines) and lines[j].startswith('2 CONC '):
                note_content += lines[j][7:]
                j += 1
            
            # Extract QIDs from note content
            qids = extract_wikidata_qids(note_content)
            if qids:
                individual_qids[current_individual].update(qids)
                stats['qids_found'] += len(qids)
                print(f"Found QIDs {qids} for {current_individual}")
        
        processed_lines.append(line)
        i += 1
    
    # Second pass: add REFNs for each individual after processing
    final_lines = []
    current_individual = None
    individual_lines = []
    existing_refns_for_current = []
    
    def process_individual():
        """Add QID REFNs for the current individual and append to final_lines."""
        nonlocal stats
        if (current_individual and 
            current_individual in individual_qids and 
            individual_qids[current_individual]):
            
            # Add QIDs as REFNs, avoiding duplicates
            for qid in sorted(individual_qids[current_individual]):
                if qid not in existing_refns_for_current:
                    individual_lines.append(f"1 REFN {qid}")
                    stats['refns_added'] += 1
        
        # Add all individual lines to final output
        final_lines.extend(individual_lines)
    
    for i, line in enumerate(processed_lines):
        # Start of new individual
        if line.startswith('0 @') and line.endswith(' INDI'):
            # Process previous individual if exists
            if current_individual:
                process_individual()
            
            # Start new individual
            current_individual = line.split()[1]
            individual_lines = [line]
            existing_refns_for_current = []
            
        # Start of new non-individual record
        elif line.startswith('0 ') and not line.endswith(' INDI'):
            # Process current individual before starting new record
            if current_individual:
                process_individual()
                current_individual = None
                individual_lines = []
                existing_refns_for_current = []
            
            final_lines.append(line)
            
        # Regular line within individual or other record
        else:
            if current_individual:
                individual_lines.append(line)
                # Track existing REFNs for this individual
                if line.startswith('1 REFN '):
                    refn_value = line[7:].strip()
                    existing_refns_for_current.append(refn_value)
            else:
                final_lines.append(line)
    
    # Process last individual if exists
    if current_individual:
        process_individual()
    
    # Write output file with original line endings
    with open(output_file, 'wb') as f:
        for line in final_lines:
            f.write(line.encode('utf-8') + line_ending.encode('utf-8'))
    
    print(f"\nProcessing complete!")
    print(f"Individuals processed: {stats['individuals_processed']}")
    print(f"QIDs found: {stats['qids_found']}")
    print(f"REFNs added: {stats['refns_added']}")
    print(f"Output written to: {output_file}")

def main():
    if len(sys.argv) != 3:
        print("Usage: python wikidata_qid_extractor.py input.ged output.ged")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        process_gedcom_file(input_file, output_file)
    except Exception as e:
        print(f"Error processing file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()