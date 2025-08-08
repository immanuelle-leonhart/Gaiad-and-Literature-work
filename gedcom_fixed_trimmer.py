#!/usr/bin/env python3
"""
Fixed GEDCOM Trimmer
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

def should_keep_individual(individual_lines: List[str], cutoff_year: int) -> bool:
    """Determine if an individual should be kept based on birth year."""
    for line in individual_lines:
        if 'BIRT' in line:
            # Look for the date line after BIRT
            continue
        if ' DATE ' in line and any('BIRT' in prev_line for prev_line in individual_lines[:individual_lines.index(line)]):
            date_part = line.split(' DATE ', 1)[1].strip()
            birth_year = parse_gedcom_date_for_year(date_part)
            if birth_year is not None:
                return birth_year >= cutoff_year
    
    # If no parseable birth date found, keep the individual (conservative approach)
    return True

def get_all_referenced_ids(filename: str, individuals_to_keep: Set[str]) -> Set[str]:
    """Get all IDs referenced by the individuals we're keeping."""
    referenced_ids = set()
    
    with open(filename, 'r', encoding='utf-8') as f:
        current_record_id = None
        current_record_lines = []
        keep_current = False
        
        for line in f:
            line = line.strip()
            
            if line.startswith('0 @') and line.endswith('@'):
                # Process previous record if it was an individual we're keeping
                if current_record_id and keep_current and current_record_id in individuals_to_keep:
                    # Extract all referenced IDs from this record
                    for record_line in current_record_lines:
                        # Look for @ID@ references
                        refs = re.findall(r'@([^@]+)@', record_line)
                        for ref in refs:
                            if ref != current_record_id:  # Don't include self-reference
                                referenced_ids.add(ref)
                
                # Start new record
                current_record_id = line.split()[1].strip('@')
                current_record_lines = [line]
                keep_current = current_record_id in individuals_to_keep
            else:
                if current_record_id:
                    current_record_lines.append(line)
        
        # Process the last record
        if current_record_id and keep_current and current_record_id in individuals_to_keep:
            for record_line in current_record_lines:
                refs = re.findall(r'@([^@]+)@', record_line)
                for ref in refs:
                    if ref != current_record_id:
                        referenced_ids.add(ref)
    
    return referenced_ids

def trim_gedcom(input_filename: str, output_filename: str, cutoff_year: int):
    """Trim the GEDCOM file to keep only individuals born after cutoff_year."""
    print(f"Trimming {input_filename} to keep individuals born after {cutoff_year}")
    print("=" * 60)
    
    # First pass: identify individuals to keep
    individuals_to_keep = set()
    total_individuals = 0
    
    with open(input_filename, 'r', encoding='utf-8') as f:
        current_record_id = None
        current_record_lines = []
        
        for line in f:
            line = line.strip()
            
            if line.startswith('0 @') and line.endswith('@'):
                # Process previous individual record
                if current_record_id and current_record_lines and '1 SEX' in ' '.join(current_record_lines):
                    total_individuals += 1
                    if should_keep_individual(current_record_lines, cutoff_year):
                        individuals_to_keep.add(current_record_id)
                
                # Start new record
                current_record_id = line.split()[1].strip('@')
                current_record_lines = [line]
            else:
                if current_record_id:
                    current_record_lines.append(line)
        
        # Process the last record
        if current_record_id and current_record_lines and '1 SEX' in ' '.join(current_record_lines):
            total_individuals += 1
            if should_keep_individual(current_record_lines, cutoff_year):
                individuals_to_keep.add(current_record_id)
    
    print(f"Individuals to keep: {len(individuals_to_keep)} out of {total_individuals}")
    
    # Second pass: get all referenced IDs (families, sources, etc.)
    print("Finding referenced records...")
    referenced_ids = get_all_referenced_ids(input_filename, individuals_to_keep)
    all_ids_to_keep = individuals_to_keep | referenced_ids
    print(f"Total records to keep: {len(all_ids_to_keep)} (individuals + referenced records)")
    
    # Third pass: write the trimmed file
    print(f"Writing trimmed file to {output_filename}...")
    records_written = 0
    
    with open(input_filename, 'r', encoding='utf-8') as infile, \
         open(output_filename, 'w', encoding='utf-8') as outfile:
        
        current_record_id = None
        current_record_lines = []
        
        for line in infile:
            line = line.strip()
            
            if line.startswith('0 @') and line.endswith('@'):
                # Write previous record if it should be kept
                if current_record_id and current_record_id in all_ids_to_keep:
                    for record_line in current_record_lines:
                        outfile.write(record_line + '\n')
                    records_written += 1
                
                # Start new record
                current_record_id = line.split()[1].strip('@')
                current_record_lines = [line]
            elif line.startswith('0 '):
                # Write previous record if it should be kept
                if current_record_id and current_record_id in all_ids_to_keep:
                    for record_line in current_record_lines:
                        outfile.write(record_line + '\n')
                    records_written += 1
                
                # This is a non-ID record (like TRLR), write it directly
                outfile.write(line + '\n')
                current_record_id = None
                current_record_lines = []
            else:
                if current_record_id:
                    current_record_lines.append(line)
        
        # Write the last record if it should be kept
        if current_record_id and current_record_id in all_ids_to_keep:
            for record_line in current_record_lines:
                outfile.write(record_line + '\n')
            records_written += 1
    
    print(f"Successfully wrote {records_written} records to {output_filename}")
    print("Trimming complete!")

def main():
    if len(sys.argv) != 4:
        print("Usage: python gedcom_fixed_trimmer.py <input_file> <output_file> <cutoff_year>")
        print("Example: python gedcom_fixed_trimmer.py input.ged output.ged 1000")
        print("Note: cutoff_year should be positive for AD, negative for BC")
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