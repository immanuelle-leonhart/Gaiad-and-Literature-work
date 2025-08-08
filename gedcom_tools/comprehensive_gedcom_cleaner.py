#!/usr/bin/env python3
"""
Comprehensive GEDCOM Cleaner
1. Add notes with ALL reference numbers (each on separate lines) 
2. Delete all sources and source documents (cruft)
3. Delete all photos (not needed)
4. Trim file size significantly
"""

import sys
import re

def clean_gedcom_file(input_file, output_file):
    """Clean GEDCOM file by removing cruft and protecting reference numbers."""
    
    print(f"Cleaning GEDCOM file: {input_file} -> {output_file}")
    
    stats = {
        'individuals_processed': 0,
        'families_processed': 0,
        'sources_removed': 0,
        'photos_removed': 0,
        'reference_notes_added': 0,
        'lines_removed': 0,
        'lines_written': 0
    }
    
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as infile:
        with open(output_file, 'w', encoding='utf-8') as outfile:
            
            current_record = None
            current_record_lines = []
            current_record_type = None
            reference_numbers = []
            skip_record = False
            in_source_block = False
            in_photo_block = False
            
            for line_num, line in enumerate(infile, 1):
                if line_num % 500000 == 0:
                    print(f"Processed {line_num:,} lines...")
                
                original_line = line
                line = line.strip()
                
                # Detect record boundaries
                if line.startswith('0 '):
                    # Process previous record
                    if current_record and not skip_record:
                        stats[f'{current_record_type}_processed'] += 1
                        
                        # Add reference number notes for individuals
                        if current_record_type == 'individuals' and reference_numbers:
                            # Add comprehensive reference note
                            ref_note_lines = ["1 NOTE REFERENCE_NUMBERS:"]
                            for ref_num in reference_numbers:
                                ref_note_lines.append(f"2 CONT {ref_num}")
                            
                            # Insert before CHAN section or at end
                            insert_pos = len(current_record_lines)
                            for i, rline in enumerate(current_record_lines):
                                if rline.strip().startswith('1 CHAN'):
                                    insert_pos = i
                                    break
                            
                            for ref_line in reversed(ref_note_lines):
                                current_record_lines.insert(insert_pos, ref_line)
                            
                            stats['reference_notes_added'] += 1
                        
                        # Write the record
                        for rline in current_record_lines:
                            outfile.write(rline + '\n')
                            stats['lines_written'] += 1
                    
                    elif skip_record:
                        if current_record_type == 'sources':
                            stats['sources_removed'] += 1
                        elif current_record_type == 'photos':
                            stats['photos_removed'] += 1
                    
                    # Start new record
                    current_record_lines = []
                    reference_numbers = []
                    skip_record = False
                    in_source_block = False
                    in_photo_block = False
                    
                    # Determine record type
                    if '@I' in line and line.endswith('@ INDI'):
                        current_record_type = 'individuals'
                        current_record = line.split()[1].strip('@')
                    elif '@F' in line and line.endswith('@ FAM'):
                        current_record_type = 'families'
                        current_record = line.split()[1].strip('@')
                    elif '@S' in line and line.endswith('@ SOUR'):
                        # Skip source records entirely
                        current_record_type = 'sources'
                        skip_record = True
                        stats['lines_removed'] += 1
                        continue
                    elif line.startswith('0 TRLR'):
                        # Trailer - write as-is
                        outfile.write(original_line)
                        stats['lines_written'] += 1
                        continue
                    else:
                        # Header or other records
                        current_record_type = 'other'
                        current_record = None
                
                if skip_record:
                    stats['lines_removed'] += 1
                    continue
                
                # Detect and skip photo/media objects within records
                if line.startswith('1 OBJE') or in_photo_block:
                    if line.startswith('1 OBJE'):
                        in_photo_block = True
                        stats['photos_removed'] += 1
                    elif line.startswith('1 ') and not line.startswith('1 OBJE'):
                        in_photo_block = False
                    else:
                        # Skip photo block lines
                        stats['lines_removed'] += 1
                        continue
                    
                    if in_photo_block:
                        stats['lines_removed'] += 1
                        continue
                
                # Detect and skip source references within records
                if line.startswith('1 SOUR') or line.startswith('2 SOUR') or in_source_block:
                    if line.startswith('1 SOUR') or line.startswith('2 SOUR'):
                        in_source_block = True
                    elif re.match(r'^[12]\s+(?!(_TMPLT|CONT|CONC|NOTE|PAGE|QUAY|DATA|TEXT|_APID))', line):
                        in_source_block = False
                    else:
                        # Skip source block lines
                        stats['lines_removed'] += 1
                        continue
                    
                    if in_source_block:
                        stats['lines_removed'] += 1
                        continue
                
                # Collect reference numbers
                if line.startswith('1 REFN '):
                    refn_value = line[7:].strip()
                    reference_numbers.append(refn_value)
                
                # Add non-skipped lines to current record
                current_record_lines.append(original_line.rstrip())
            
            # Process final record
            if current_record and not skip_record:
                stats[f'{current_record_type}_processed'] += 1
                
                if current_record_type == 'individuals' and reference_numbers:
                    ref_note_lines = ["1 NOTE REFERENCE_NUMBERS:"]
                    for ref_num in reference_numbers:
                        ref_note_lines.append(f"2 CONT {ref_num}")
                    
                    insert_pos = len(current_record_lines)
                    for i, rline in enumerate(current_record_lines):
                        if rline.strip().startswith('1 CHAN'):
                            insert_pos = i
                            break
                    
                    for ref_line in reversed(ref_note_lines):
                        current_record_lines.insert(insert_pos, ref_line)
                    
                    stats['reference_notes_added'] += 1
                
                for rline in current_record_lines:
                    outfile.write(rline + '\n')
                    stats['lines_written'] += 1
    
    print(f"\nGEDCOM cleaning completed!")
    print(f"  Individuals processed: {stats['individuals_processed']:,}")
    print(f"  Families processed: {stats['families_processed']:,}")
    print(f"  Sources removed: {stats['sources_removed']:,}")
    print(f"  Photos removed: {stats['photos_removed']:,}")
    print(f"  Reference notes added: {stats['reference_notes_added']:,}")
    print(f"  Lines removed: {stats['lines_removed']:,}")
    print(f"  Lines written: {stats['lines_written']:,}")
    total_lines = stats['lines_removed'] + stats['lines_written']
    if total_lines > 0:
        print(f"  Estimated size reduction: {(stats['lines_removed'] / total_lines * 100):.1f}%")
    else:
        print(f"  No lines processed - check input file")
    
    return True

def main():
    if len(sys.argv) != 3:
        print("Usage: python comprehensive_gedcom_cleaner.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    success = clean_gedcom_file(input_file, output_file)
    
    if success:
        print(f"\nGEDCOM file successfully cleaned: {output_file}")
    else:
        print(f"\nFailed to clean GEDCOM file")
        sys.exit(1)

if __name__ == "__main__":
    main()