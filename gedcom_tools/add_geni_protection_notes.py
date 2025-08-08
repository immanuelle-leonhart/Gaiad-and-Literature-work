#!/usr/bin/env python3
"""
Add protective notes to all records with Geni reference numbers.
This ensures they won't be accidentally removed during trimming.
"""

import sys
import re

def add_geni_protection_notes(input_file, output_file):
    """Add protective notes to all individuals with Geni REFN numbers."""
    
    print(f"Adding Geni protection notes: {input_file} -> {output_file}")
    
    individuals_processed = 0
    geni_records_found = 0
    protection_notes_added = 0
    
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as infile:
        with open(output_file, 'w', encoding='utf-8') as outfile:
            current_individual = None
            current_individual_lines = []
            has_geni_refn = False
            geni_refn_value = ""
            has_protection_note = False
            
            for line_num, line in enumerate(infile, 1):
                if line_num % 500000 == 0:
                    print(f"Processed {line_num:,} lines, found {geni_records_found} Geni records...")
                
                line = line.strip()
                
                # Start of individual record
                if line.startswith('0 @I') and line.endswith('@ INDI'):
                    # Process previous individual
                    if current_individual:
                        individuals_processed += 1
                        
                        if has_geni_refn:
                            geni_records_found += 1
                            
                            # Add protection note if not already present
                            if not has_protection_note:
                                # Insert protection note before CHAN section or at end
                                protection_note = f"1 NOTE GENI_PROTECTED: This record has Geni ID {geni_refn_value} and should be preserved regardless of birth date"
                                
                                # Find insertion point (before CHAN or at end)
                                insert_pos = len(current_individual_lines)
                                for i, iline in enumerate(current_individual_lines):
                                    if iline.startswith('1 CHAN'):
                                        insert_pos = i
                                        break
                                
                                current_individual_lines.insert(insert_pos, protection_note)
                                protection_notes_added += 1
                        
                        # Write previous individual
                        for iline in current_individual_lines:
                            outfile.write(iline + '\n')
                    
                    # Start new individual
                    current_individual = line.split()[1].strip('@')
                    current_individual_lines = [line]
                    has_geni_refn = False
                    geni_refn_value = ""
                    has_protection_note = False
                
                elif current_individual:
                    current_individual_lines.append(line)
                    
                    # Check for Geni REFN
                    if line.startswith('1 REFN geni:'):
                        has_geni_refn = True
                        geni_refn_value = line[7:].strip()  # Remove "1 REFN "
                    
                    # Check if protection note already exists
                    elif line.startswith('1 NOTE GENI_PROTECTED:'):
                        has_protection_note = True
                
                else:
                    # Non-individual record, write as-is
                    outfile.write(line + '\n')
            
            # Process final individual
            if current_individual:
                individuals_processed += 1
                
                if has_geni_refn:
                    geni_records_found += 1
                    
                    if not has_protection_note:
                        protection_note = f"1 NOTE GENI_PROTECTED: This record has Geni ID {geni_refn_value} and should be preserved regardless of birth date"
                        
                        insert_pos = len(current_individual_lines)
                        for i, iline in enumerate(current_individual_lines):
                            if iline.startswith('1 CHAN'):
                                insert_pos = i
                                break
                        
                        current_individual_lines.insert(insert_pos, protection_note)
                        protection_notes_added += 1
                
                for iline in current_individual_lines:
                    outfile.write(iline + '\n')
    
    print(f"\nProtection notes added successfully!")
    print(f"  Individuals processed: {individuals_processed:,}")
    print(f"  Geni records found: {geni_records_found:,}")
    print(f"  Protection notes added: {protection_notes_added:,}")
    
    return True

def main():
    if len(sys.argv) != 3:
        print("Usage: python add_geni_protection_notes.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    success = add_geni_protection_notes(input_file, output_file)
    
    if success:
        print(f"\nGeni protection notes successfully added to: {output_file}")
    else:
        print(f"\nFailed to add Geni protection notes")
        sys.exit(1)

if __name__ == "__main__":
    main()