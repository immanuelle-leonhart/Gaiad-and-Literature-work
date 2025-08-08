#!/usr/bin/env python3
"""
Robust GEDCOM Trimmer
Trims a GEDCOM file to keep only individuals born after a specified year,
with proper BC date handling and support for various date formats.
"""

import re
import sys
from typing import Optional, Set, List

def parse_gedcom_date_for_year(date_str: str) -> Optional[int]:
    """Parse a GEDCOM date string and return the year (negative for BC)."""
    if not date_str:
        return None
    
    # Handle parenthetical dates like "(260000000 B.C.)" or "(400MYA)"
    if date_str.startswith('(') and date_str.endswith(')'):
        date_str = date_str[1:-1]  # Remove parentheses
    
    # Handle million years ago (MYA) - convert to BC
    mya_match = re.search(r'([\d.]+)\s*MYA', date_str.upper())
    if mya_match:
        mya = float(mya_match.group(1))
        return int(-mya * 1000000)  # Convert to BC years
    
    # Handle B.C. dates with numbers
    bc_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:000\s*)?B\.?C\.?', date_str.upper())
    if bc_match:
        bc_year = float(bc_match.group(1))
        return int(-bc_year)
    
    # Remove common GEDCOM date qualifiers
    clean_date = re.sub(r'^(ABT|EST|CAL|AFT|BEF|BET|FROM|TO)\s+', '', date_str.upper())
    clean_date = re.sub(r'\s+AND\s+.*$', '', clean_date)  # Remove "AND" clauses
    
    # Handle standard BC dates
    if 'B.C.' in clean_date or ' BC' in clean_date:
        # Extract year from BC date
        year_match = re.search(r'(\d+)', clean_date)
        if year_match:
            return -int(year_match.group(1))
    
    # Handle AD dates or assume AD if no BC marker
    # Look for 4-digit year
    year_match = re.search(r'\b(\d{4})\b', clean_date)
    if year_match:
        year = int(year_match.group(1))
        # Handle obvious BC years (like year 1 which was meant to be 1 BC)
        if year == 1 and ('B.C.' in date_str.upper() or 'BC' in date_str.upper()):
            return -1
        return year
    
    # Look for 3-digit year (might be shorthand)
    year_match = re.search(r'\b(\d{3})\b', clean_date)
    if year_match:
        return int(year_match.group(1))
    
    return None

def trim_gedcom(input_filename: str, output_filename: str, cutoff_year: int):
    """Trim the GEDCOM file to keep only individuals born after cutoff_year."""
    print(f"Trimming {input_filename} to keep individuals born after {cutoff_year}")
    if cutoff_year < 0:
        print(f"(Cutoff year is {abs(cutoff_year)} BC)")
    print("=" * 60)
    
    # First pass: find individuals to keep
    individuals_to_keep = set()
    all_individuals = set()
    birth_years_found = 0
    bc_individuals = 0
    kept_bc = 0
    
    with open(input_filename, 'r', encoding='utf-8') as f:
        current_record_id = None
        current_record_type = None
        looking_for_birth = False
        
        for line in f:
            line = line.strip()
            
            # Start of a new record
            if line.startswith('0 @') and ('@' in line):
                parts = line.split()
                if len(parts) >= 3:
                    current_record_id = parts[1].strip('@')
                    current_record_type = parts[2]
                    looking_for_birth = False
                    
                    if current_record_type == 'INDI':
                        all_individuals.add(current_record_id)
            
            # Birth event
            elif line.startswith('1 BIRT'):
                looking_for_birth = True
            
            # Date line - could be birth date
            elif ' DATE ' in line and looking_for_birth and current_record_type == 'INDI':
                date_part = line.split(' DATE ', 1)[1].strip()
                birth_year = parse_gedcom_date_for_year(date_part)
                
                if birth_year is not None:
                    birth_years_found += 1
                    if birth_year < 0:
                        bc_individuals += 1
                    
                    if birth_year >= cutoff_year:
                        individuals_to_keep.add(current_record_id)
                        if birth_year < 0:
                            kept_bc += 1
                else:
                    # If we can't parse the birth date, keep the individual
                    individuals_to_keep.add(current_record_id)
                
                looking_for_birth = False
            
            # Any other event resets birth looking
            elif line.startswith('1 ') and line != '1 BIRT':
                looking_for_birth = False
    
    # Add individuals without birth dates (keep them)
    individuals_without_dates = all_individuals - {ind for ind in all_individuals if any(ind in individuals_to_keep for _ in [1])}
    for ind_id in all_individuals:
        if ind_id not in individuals_to_keep:
            # Check if we found any birth info for this individual
            found_birth_info = False
            with open(input_filename, 'r', encoding='utf-8') as f:
                in_individual = False
                for line in f:
                    line = line.strip()
                    if line == f'0 @{ind_id}@ INDI':
                        in_individual = True
                    elif line.startswith('0 @') or line.startswith('0 TRLR'):
                        in_individual = False
                    elif in_individual and '1 BIRT' in line:
                        found_birth_info = True
                        break
            
            if not found_birth_info:
                individuals_to_keep.add(ind_id)
    
    print(f"Found {len(all_individuals)} individual records")
    print(f"Individuals with parseable birth dates: {birth_years_found}")
    print(f"Individuals born in BC: {bc_individuals}")
    print(f"BC individuals kept: {kept_bc}")
    print(f"Individuals to keep: {len(individuals_to_keep)} out of {len(all_individuals)}")
    
    # Second pass: find all referenced IDs
    print("Finding referenced records...")
    referenced_ids = set()
    
    with open(input_filename, 'r', encoding='utf-8') as f:
        current_record_id = None
        in_kept_individual = False
        
        for line in f:
            line = line.strip()
            
            if line.startswith('0 @') and line.endswith('@'):
                current_record_id = line.split()[1].strip('@')
                in_kept_individual = current_record_id in individuals_to_keep
            elif in_kept_individual:
                # Find all @ID@ references in this line
                refs = re.findall(r'@([^@]+)@', line)
                for ref in refs:
                    if ref != current_record_id:
                        referenced_ids.add(ref)
    
    all_ids_to_keep = individuals_to_keep | referenced_ids
    print(f"Total records to keep: {len(all_ids_to_keep)} (individuals + referenced records)")
    
    # Third pass: write the output file
    print(f"Writing trimmed file to {output_filename}...")
    records_written = 0
    
    with open(input_filename, 'r', encoding='utf-8') as infile, \
         open(output_filename, 'w', encoding='utf-8') as outfile:
        
        current_record_id = None
        current_record_lines = []
        keep_current_record = False
        
        for line in infile:
            line = line.strip()
            
            if line.startswith('0 @') and line.endswith('@'):
                # Write previous record if it should be kept
                if keep_current_record and current_record_lines:
                    for record_line in current_record_lines:
                        outfile.write(record_line + '\\n')
                    records_written += 1
                
                # Start new record
                current_record_id = line.split()[1].strip('@')
                keep_current_record = current_record_id in all_ids_to_keep
                current_record_lines = [line]
                
            elif line.startswith('0 '):
                # Write previous record if it should be kept
                if keep_current_record and current_record_lines:
                    for record_line in current_record_lines:
                        outfile.write(record_line + '\\n')
                    records_written += 1
                
                # Write non-record lines (like TRLR)
                outfile.write(line + '\\n')
                current_record_id = None
                current_record_lines = []
                keep_current_record = False
                
            else:
                if current_record_id:
                    current_record_lines.append(line)
        
        # Write the last record if it should be kept
        if keep_current_record and current_record_lines:
            for record_line in current_record_lines:
                outfile.write(record_line + '\\n')
            records_written += 1
    
    print(f"Successfully wrote {records_written} records to {output_filename}")
    print("Trimming complete!")

def main():
    if len(sys.argv) != 4:
        print("Usage: python gedcom_robust_trimmer.py <input_file> <output_file> <cutoff_year>")
        print("Example: python gedcom_robust_trimmer.py input.ged output.ged 1000")
        print("Note: cutoff_year should be positive for AD, negative for BC")
        print("      -1000 means keep individuals born after 1000 BC")
        sys.exit(1)
    
    input_filename = sys.argv[1]
    output_filename = sys.argv[2]
    
    try:
        cutoff_year = int(sys.argv[3])
    except ValueError:
        print("Error: cutoff_year must be an integer")
        sys.exit(1)
    
    try:
        trim_gedcom(input_filename, output_filename, cutoff_year)
    except FileNotFoundError:
        print(f"Error: Input file '{input_filename}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()