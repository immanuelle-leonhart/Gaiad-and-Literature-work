#!/usr/bin/env python3
"""
Add evolutionism wiki QIDs as REFNs to all individuals in a GEDCOM file.
Assigns sequential QIDs starting from Q5 (or specified starting number).
Preserves existing REFNs and handles multiple REFNs per individual.
"""

import sys
from typing import Dict, List

def process_gedcom_file(input_file: str, output_file: str, start_qid: int = 5, prefix: str = "evolutionism"):
    """Process GEDCOM file to add evolutionism QIDs as REFNs."""
    
    print(f"Processing {input_file}...")
    print(f"Starting QID: {prefix}:Q{start_qid}")
    
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
    
    # First pass: identify all individuals and assign QIDs
    individuals = []
    current_individual = None
    
    for line in lines:
        if line.startswith('0 @') and line.endswith(' INDI'):
            current_individual = line.split()[1]  # Get the @I123@ part
            individuals.append(current_individual)
    
    # Create QID mapping
    qid_mapping = {}
    current_qid = start_qid
    
    for individual in individuals:
        qid_mapping[individual] = f"{prefix}:Q{current_qid}"
        current_qid += 1
    
    print(f"Found {len(individuals)} individuals")
    print(f"Will assign QIDs from {prefix}:Q{start_qid} to {prefix}:Q{current_qid-1}")
    
    # Second pass: add REFNs after processing each individual completely
    final_lines = []
    current_individual = None
    individual_lines = []
    existing_refns = set()
    stats = {
        'individuals_processed': 0,
        'refns_added': 0,
        'refns_skipped': 0
    }
    
    def process_current_individual():
        """Process the current individual and add evolutionism QID if needed."""
        nonlocal stats
        if current_individual and current_individual in qid_mapping:
            evolutionism_qid = qid_mapping[current_individual]
            if evolutionism_qid not in existing_refns:
                individual_lines.append(f"1 REFN {evolutionism_qid}")
                stats['refns_added'] += 1
            else:
                stats['refns_skipped'] += 1
        
        # Add all individual lines to final output
        final_lines.extend(individual_lines)
    
    for line in lines:
        
        # Start of new individual
        if line.startswith('0 @') and line.endswith(' INDI'):
            # Process previous individual if exists
            if current_individual:
                process_current_individual()
            
            # Start new individual
            current_individual = line.split()[1]
            individual_lines = [line]
            existing_refns.clear()
            stats['individuals_processed'] += 1
            
        # Start of new non-individual record
        elif line.startswith('0 ') and not line.endswith(' INDI'):
            # Process current individual before starting new record
            if current_individual:
                process_current_individual()
                current_individual = None
                individual_lines = []
            
            final_lines.append(line)
            
        # Regular line within individual or other record
        else:
            if current_individual:
                individual_lines.append(line)
                # Track existing REFNs
                if line.startswith('1 REFN '):
                    refn_value = line[7:].strip()
                    existing_refns.add(refn_value)
            else:
                final_lines.append(line)
    
    # Process last individual if exists
    if current_individual:
        process_current_individual()
    
    # Write output file with original line endings
    with open(output_file, 'wb') as f:
        for line in final_lines:
            f.write(line.encode('utf-8') + line_ending.encode('utf-8'))
    
    print(f"\nProcessing complete!")
    print(f"Individuals processed: {stats['individuals_processed']}")
    print(f"REFNs added: {stats['refns_added']}")
    print(f"REFNs skipped (duplicates): {stats['refns_skipped']}")
    print(f"Output written to: {output_file}")
    
    # Print some example mappings
    print(f"\nExample QID assignments:")
    for i, (individual, qid) in enumerate(list(qid_mapping.items())[:5]):
        print(f"  {individual} -> {qid}")
    if len(qid_mapping) > 5:
        print(f"  ... and {len(qid_mapping) - 5} more")

def main():
    if len(sys.argv) < 3:
        print("Usage: python evolutionism_qid_adder.py input.ged output.ged [start_qid] [prefix]")
        print("  start_qid: Starting QID number (default: 5)")
        print("  prefix: QID prefix (default: 'evolutionism')")
        print("Examples:")
        print("  python evolutionism_qid_adder.py input.ged output.ged")
        print("  python evolutionism_qid_adder.py input.ged output.ged 100")
        print("  python evolutionism_qid_adder.py input.ged output.ged 5 evolutionism")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    start_qid = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    prefix = sys.argv[4] if len(sys.argv) > 4 else "evolutionism"
    
    try:
        process_gedcom_file(input_file, output_file, start_qid, prefix)
    except Exception as e:
        print(f"Error processing file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()