#!/usr/bin/env python3
"""
Fast GEDCOM Trimmer
Efficient trimming that processes the file in a single pass.
"""

import re
import sys
from typing import Optional

def extract_year_from_date(date_str: str) -> Optional[int]:
    """Extract year from various GEDCOM date formats."""
    if not date_str:
        return None
    
    # Handle MYA (Million Years Ago)
    mya_match = re.search(r'(\d+(?:\.\d+)?)\s*MYA', date_str.upper())
    if mya_match:
        mya = float(mya_match.group(1))
        return int(-mya * 1000000)
    
    # Handle BC dates - look for B.C. at the end and extract the year before it
    if 'B.C.' in date_str.upper() or ' BC' in date_str.upper():
        # Find the last number before B.C./BC
        bc_year_match = re.search(r'(\d+)\s*B\.?C\.?', date_str.upper())
        if bc_year_match:
            return -int(bc_year_match.group(1))
    
    # Handle regular years (AD or assumed AD)
    year_match = re.search(r'\b(\d{3,4})\b', date_str)
    if year_match:
        year = int(year_match.group(1))
        # Double-check this isn't actually a BC date we missed
        if 'B.C.' in date_str.upper() or ' BC' in date_str.upper():
            return -year
        return year
    
    return None

def fast_trim_gedcom(input_file: str, output_file: str, cutoff_year: int):
    """Fast single-pass trimming."""
    print(f"Fast trimming {input_file} with cutoff year {cutoff_year}")
    print(f"(Keeping ALL BC people and AD people born up to {cutoff_year} AD)")
    
    # Step 1: Single pass to identify individuals to keep
    individuals_to_keep = set()
    individuals_rejected = set()
    
    print("Pass 1: Identifying individuals to keep...")
    with open(input_file, 'r', encoding='utf-8') as f:
        current_individual = None
        birth_year = None
        found_birth_date = False
        
        for line_num, line in enumerate(f):
            if line_num % 1000000 == 0:
                print(f"  Processed {line_num // 1000000}M lines...")
            
            line = line.strip()
            
            if line.startswith('0 @') and line.endswith(' INDI'):
                # Finalize previous individual
                if current_individual:
                    # Keep ALL BC people (negative years) and AD people born before or on cutoff_year
                    if birth_year is not None and birth_year > 0 and birth_year > cutoff_year:
                        individuals_rejected.add(current_individual)
                    else:
                        # Keep if: no birth date, BC date (negative), or AD date <= cutoff_year
                        individuals_to_keep.add(current_individual)
                
                # Start new individual
                current_individual = line.split()[1].strip('@')
                birth_year = None
                found_birth_date = False
                
            elif current_individual and line == '1 BIRT':
                found_birth_date = True
                
            elif current_individual and found_birth_date and ' DATE ' in line:
                date_part = line.split(' DATE ', 1)[1].strip()
                birth_year = extract_year_from_date(date_part)
                found_birth_date = False  # We found the date, no need to look further
        
        # Handle last individual
        if current_individual:
            # Keep ALL BC people (negative years) and AD people born before or on cutoff_year
            if birth_year is not None and birth_year > 0 and birth_year > cutoff_year:
                individuals_rejected.add(current_individual)
            else:
                individuals_to_keep.add(current_individual)
    
    print(f"Keeping {len(individuals_to_keep)} individuals, rejecting {len(individuals_rejected)}")
    
    # Step 2: Collect referenced IDs from kept individuals
    print("Pass 2: Finding referenced records...")
    referenced_ids = set()
    
    with open(input_file, 'r', encoding='utf-8') as f:
        current_record = None
        keep_current = False
        
        for line_num, line in enumerate(f):
            if line_num % 1000000 == 0:
                print(f"  Processed {line_num // 1000000}M lines...")
            
            line = line.strip()
            
            if line.startswith('0 @'):
                current_record = line.split()[1].strip('@')
                keep_current = current_record in individuals_to_keep
            elif keep_current:
                refs = re.findall(r'@([^@]+)@', line)
                for ref in refs:
                    if ref != current_record:
                        referenced_ids.add(ref)
    
    all_ids_to_keep = individuals_to_keep | referenced_ids
    print(f"Total records to keep: {len(all_ids_to_keep)}")
    
    # Step 3: Write output
    print("Pass 3: Writing output file...")
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        
        current_record = None
        current_record_lines = []
        keep_record = False
        
        for line_num, line in enumerate(infile):
            if line_num % 1000000 == 0:
                print(f"  Processed {line_num // 1000000}M lines...")
            
            line = line.strip()
            
            if line.startswith('0 @'):
                # Write previous record if keeping it
                if keep_record and current_record_lines:
                    for record_line in current_record_lines:
                        outfile.write(record_line + '\n')
                
                # Start new record
                current_record = line.split()[1].strip('@')
                keep_record = current_record in all_ids_to_keep
                current_record_lines = [line]
                
            elif line.startswith('0 '):
                # Write previous record if keeping it
                if keep_record and current_record_lines:
                    for record_line in current_record_lines:
                        outfile.write(record_line + '\n')
                
                # Write header/trailer lines
                outfile.write(line + '\n')
                current_record = None
                current_record_lines = []
                keep_record = False
                
            else:
                if current_record:
                    current_record_lines.append(line)
        
        # Write final record if needed
        if keep_record and current_record_lines:
            for record_line in current_record_lines:
                outfile.write(record_line + '\n')
    
    print(f"Trimmed GEDCOM saved to {output_file}")

def main():
    if len(sys.argv) != 4:
        print("Usage: python gedcom_fast_trimmer.py <input_file> <output_file> <cutoff_year>")
        print("Example: python gedcom_fast_trimmer.py input.ged output.ged -1000")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    cutoff_year = int(sys.argv[3])
    
    try:
        fast_trim_gedcom(input_file, output_file, cutoff_year)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()