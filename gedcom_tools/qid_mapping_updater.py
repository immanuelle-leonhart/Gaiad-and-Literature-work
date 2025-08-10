#!/usr/bin/env python3
"""
Update GEDCOM file with evolutionism QIDs after Wikibase upload.
Reads the QID mapping file and adds evolutionism QIDs as REFNs.
"""

import sys
from typing import Dict, List

def load_qid_mapping(mapping_file: str) -> Dict[str, str]:
    """Load the QID mapping from file."""
    mappings = {}
    
    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split('\t')
                    if len(parts) == 2:
                        gedcom_id, qid = parts
                        mappings[gedcom_id] = qid
    except FileNotFoundError:
        print(f"Error: Mapping file {mapping_file} not found")
        return {}
    
    print(f"Loaded {len(mappings)} QID mappings")
    return mappings

def update_gedcom_with_qids(input_file: str, output_file: str, qid_mappings: Dict[str, str]):
    """Update GEDCOM file with evolutionism QIDs as REFNs."""
    
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
    
    final_lines = []
    current_individual = None
    current_family = None
    individual_lines = []
    existing_refns = set()
    stats = {
        'individuals_processed': 0,
        'families_processed': 0,
        'evolutionism_refns_added': 0,
        'refns_skipped': 0
    }
    
    def process_current_record():
        """Process the current individual or family and add evolutionism QID if needed."""
        nonlocal stats
        
        record_id = current_individual or current_family
        if record_id and record_id in qid_mappings:
            evolutionism_qid = qid_mappings[record_id]
            
            # Check if this QID is already present
            if evolutionism_qid not in existing_refns:
                individual_lines.append(f"1 REFN {evolutionism_qid}")
                stats['evolutionism_refns_added'] += 1
            else:
                stats['refns_skipped'] += 1
        
        # Add all record lines to final output
        final_lines.extend(individual_lines)
    
    for line in lines:
        
        # Start of new individual
        if line.startswith('0 @') and line.endswith(' INDI'):
            # Process previous record if exists
            if current_individual or current_family:
                process_current_record()
            
            # Start new individual
            current_individual = line.split()[1]  # Get @I123@ part
            current_family = None
            individual_lines = [line]
            existing_refns.clear()
            stats['individuals_processed'] += 1
            
        # Start of new family
        elif line.startswith('0 @') and line.endswith(' FAM'):
            # Process previous record if exists
            if current_individual or current_family:
                process_current_record()
            
            # Start new family
            current_family = line.split()[1]  # Get @F123@ part
            current_individual = None
            individual_lines = [line]
            existing_refns.clear()
            stats['families_processed'] += 1
            
        # Start of new non-individual/family record
        elif line.startswith('0 '):
            # Process current record before starting new record
            if current_individual or current_family:
                process_current_record()
                current_individual = None
                current_family = None
                individual_lines = []
            
            final_lines.append(line)
            
        # Regular line within individual, family, or other record
        else:
            if current_individual or current_family:
                individual_lines.append(line)
                # Track existing REFNs
                if line.startswith('1 REFN '):
                    refn_value = line[7:].strip()
                    existing_refns.add(refn_value)
            else:
                final_lines.append(line)
    
    # Process last record if exists
    if current_individual or current_family:
        process_current_record()
    
    # Write output file with original line endings
    with open(output_file, 'wb') as f:
        for line in final_lines:
            f.write(line.encode('utf-8') + line_ending.encode('utf-8'))
    
    print(f"\nProcessing complete!")
    print(f"Individuals processed: {stats['individuals_processed']}")
    print(f"Families processed: {stats['families_processed']}")
    print(f"Evolutionism REFNs added: {stats['evolutionism_refns_added']}")
    print(f"REFNs skipped (duplicates): {stats['refns_skipped']}")
    print(f"Output written to: {output_file}")

def main():
    if len(sys.argv) != 4:
        print("Usage: python qid_mapping_updater.py input.ged output.ged mapping.txt")
        print("Example: python qid_mapping_updater.py master_combined.ged master_with_qids.ged gedcom_to_qid_mapping.txt")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    mapping_file = sys.argv[3]
    
    # Load QID mappings
    qid_mappings = load_qid_mapping(mapping_file)
    if not qid_mappings:
        print("No QID mappings loaded. Exiting.")
        sys.exit(1)
    
    try:
        update_gedcom_with_qids(input_file, output_file, qid_mappings)
    except Exception as e:
        print(f"Error processing file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()