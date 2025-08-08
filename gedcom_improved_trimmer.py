#!/usr/bin/env python3
"""
Improved GEDCOM Trimmer
Trims a GEDCOM file to keep only individuals born after a specified year,
with proper BC date handling and support for various date formats.
"""

import re
import sys
from typing import Optional, Set, List, Dict

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

def parse_gedcom_file(filename: str) -> Dict[str, Dict]:
    """Parse GEDCOM file and return record information."""
    records = {}
    
    with open(filename, 'r', encoding='utf-8') as f:
        current_record_id = None
        current_record = {
            'type': None,
            'lines': [],
            'birth_year': None
        }
        
        for line in f:
            line = line.strip()
            
            if line.startswith('0 @') and line.endswith('@'):
                # Save previous record
                if current_record_id:
                    records[current_record_id] = current_record
                
                # Start new record
                parts = line.split()
                current_record_id = parts[1].strip('@')
                record_type = parts[2] if len(parts) > 2 else 'UNKNOWN'
                
                current_record = {
                    'type': record_type,
                    'lines': [line],
                    'birth_year': None
                }
                
            elif line.startswith('0 '):
                # Save previous record
                if current_record_id:
                    records[current_record_id] = current_record
                
                # Handle non-ID records
                current_record_id = None
                current_record = {'type': None, 'lines': [], 'birth_year': None}
                
            else:
                if current_record_id:
                    current_record['lines'].append(line)
                    
                    # Look for birth dates in INDI records
                    if current_record['type'] == 'INDI' and ' DATE ' in line:
                        # Check if this is a birth date by looking at previous lines
                        prev_lines = current_record['lines'][-5:]  # Look at last few lines
                        if any('BIRT' in prev_line for prev_line in prev_lines):
                            date_part = line.split(' DATE ', 1)[1].strip()
                            birth_year = parse_gedcom_date_for_year(date_part)
                            if birth_year is not None:
                                current_record['birth_year'] = birth_year
        
        # Save the last record
        if current_record_id:
            records[current_record_id] = current_record
    
    return records

def get_all_referenced_ids(records: Dict[str, Dict], individuals_to_keep: Set[str]) -> Set[str]:
    """Get all IDs referenced by the individuals we're keeping."""
    referenced_ids = set()
    
    for record_id in individuals_to_keep:
        if record_id in records:
            for line in records[record_id]['lines']:
                # Look for @ID@ references
                refs = re.findall(r'@([^@]+)@', line)
                for ref in refs:
                    if ref != record_id:  # Don't include self-reference
                        referenced_ids.add(ref)
    
    return referenced_ids

def trim_gedcom(input_filename: str, output_filename: str, cutoff_year: int):
    """Trim the GEDCOM file to keep only individuals born after cutoff_year."""
    print(f"Trimming {input_filename} to keep individuals born after {cutoff_year}")
    if cutoff_year < 0:
        print(f"(Cutoff year is {abs(cutoff_year)} BC)")
    print("=" * 60)
    
    # Parse the entire file
    print("Parsing GEDCOM file...")
    records = parse_gedcom_file(input_filename)
    
    # Count individuals and find those to keep
    individuals = {rid: rec for rid, rec in records.items() if rec['type'] == 'INDI'}
    print(f"Found {len(individuals)} individual records")
    
    individuals_to_keep = set()
    birth_years_found = 0
    bc_individuals = 0
    kept_bc = 0
    
    for record_id, record in individuals.items():
        if record['birth_year'] is not None:
            birth_years_found += 1
            if record['birth_year'] < 0:
                bc_individuals += 1
            if record['birth_year'] >= cutoff_year:
                individuals_to_keep.add(record_id)
                if record['birth_year'] < 0:
                    kept_bc += 1
        else:
            # If no birth date found, keep the individual (conservative approach)
            individuals_to_keep.add(record_id)
    
    print(f"Individuals with parseable birth dates: {birth_years_found}")
    print(f"Individuals born in BC: {bc_individuals}")
    print(f"BC individuals kept: {kept_bc}")
    print(f"Individuals to keep: {len(individuals_to_keep)} out of {len(individuals)}")
    
    # Get all referenced IDs (families, sources, etc.)
    print("Finding referenced records...")
    referenced_ids = get_all_referenced_ids(records, individuals_to_keep)
    all_ids_to_keep = individuals_to_keep | referenced_ids
    print(f"Total records to keep: {len(all_ids_to_keep)} (individuals + referenced records)")
    
    # Write the trimmed file
    print(f"Writing trimmed file to {output_filename}...")
    records_written = 0
    
    with open(output_filename, 'w', encoding='utf-8') as outfile:
        # Write header
        outfile.write("0 HEAD\\n")
        
        # Write kept records
        for record_id in all_ids_to_keep:
            if record_id in records:
                for line in records[record_id]['lines']:
                    outfile.write(line + '\\n')
                records_written += 1
        
        # Write trailer
        outfile.write("0 TRLR\\n")
    
    print(f"Successfully wrote {records_written} records to {output_filename}")
    print("Trimming complete!")
    
    # Show some sample BC dates kept
    bc_samples = []
    for record_id in individuals_to_keep:
        if record_id in records and records[record_id]['birth_year'] and records[record_id]['birth_year'] < 0:
            bc_samples.append((record_id, records[record_id]['birth_year']))
    
    if bc_samples:
        bc_samples.sort(key=lambda x: x[1])  # Sort by year
        print(f"\\nSample BC dates kept (showing up to 10):")
        for i, (record_id, year) in enumerate(bc_samples[:10]):
            print(f"  {record_id}: {abs(year)} BC")

def main():
    if len(sys.argv) != 4:
        print("Usage: python gedcom_improved_trimmer.py <input_file> <output_file> <cutoff_year>")
        print("Example: python gedcom_improved_trimmer.py input.ged output.ged 1000")
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