#!/usr/bin/env python3
"""
Simple GEDCOM Trimmer
A straightforward approach to trim GEDCOM files by birth year.
"""

import re
import sys
from typing import Optional, Set

def extract_year_from_date(date_str: str) -> Optional[int]:
    """Extract year from various GEDCOM date formats."""
    if not date_str:
        return None
    
    # Handle MYA (Million Years Ago)
    mya_match = re.search(r'(\d+(?:\.\d+)?)\s*MYA', date_str.upper())
    if mya_match:
        mya = float(mya_match.group(1))
        return int(-mya * 1000000)  # Convert to BC years
    
    # Handle explicit BC dates
    bc_match = re.search(r'(\d+)\s*B\.?C\.?', date_str.upper())
    if bc_match:
        return -int(bc_match.group(1))
    
    # Handle regular years (assume AD if no BC marker)
    year_match = re.search(r'\b(\d{3,4})\b', date_str)
    if year_match:
        return int(year_match.group(1))
    
    return None

def trim_gedcom_simple(input_file: str, output_file: str, cutoff_year: int):
    """Simple trimming approach - keep individuals born after cutoff_year."""
    print(f"Trimming {input_file} with cutoff year {cutoff_year}")
    if cutoff_year < 0:
        print(f"(Keeping individuals born after {abs(cutoff_year)} BC)")
    
    # Step 1: Find individuals to keep
    individuals_to_keep = set()
    all_individuals = set()
    
    with open(input_file, 'r', encoding='utf-8') as f:
        current_individual = None
        in_birth_section = False
        
        for line in f:
            line = line.strip()
            
            # Individual record start
            if line.startswith('0 @') and line.endswith(' INDI'):
                individual_id = line.split()[1].strip('@')
                all_individuals.add(individual_id)
                current_individual = individual_id
                in_birth_section = False
            
            # Birth event
            elif line == '1 BIRT' and current_individual:
                in_birth_section = True
            
            # Other level 1 events end birth section
            elif line.startswith('1 ') and line != '1 BIRT':
                in_birth_section = False
            
            # Date in birth section
            elif in_birth_section and ' DATE ' in line and current_individual:
                date_part = line.split(' DATE ', 1)[1].strip()
                birth_year = extract_year_from_date(date_part)
                
                if birth_year is not None and birth_year >= cutoff_year:
                    individuals_to_keep.add(current_individual)
                elif birth_year is None:
                    # Keep individuals with unparseable birth dates
                    individuals_to_keep.add(current_individual)
                
                in_birth_section = False
    
    # Add individuals without any birth information (keep them)
    no_birth_info = all_individuals - {ind for ind in all_individuals 
                                      if any(ind in individuals_to_keep for _ in [1])}
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
        for individual_id in no_birth_info:
            individual_section = f'0 @{individual_id}@ INDI'
            if individual_section in content:
                # Extract this individual's section
                start = content.find(individual_section)
                if start != -1:
                    end = content.find('\n0 @', start + 1)
                    if end == -1:
                        end = content.find('\n0 TRLR', start + 1)
                    if end == -1:
                        end = len(content)
                    
                    individual_data = content[start:end]
                    if '1 BIRT' not in individual_data:
                        individuals_to_keep.add(individual_id)
    
    print(f"Keeping {len(individuals_to_keep)} out of {len(all_individuals)} individuals")
    
    # Step 2: Find referenced records
    referenced_ids = set()
    
    with open(input_file, 'r', encoding='utf-8') as f:
        current_record = None
        keep_current = False
        
        for line in f:
            line = line.strip()
            
            if line.startswith('0 @') and '@' in line:
                current_record = line.split()[1].strip('@')
                keep_current = current_record in individuals_to_keep
            elif keep_current:
                # Find all @ID@ references
                refs = re.findall(r'@([^@]+)@', line)
                for ref in refs:
                    if ref != current_record:
                        referenced_ids.add(ref)
    
    all_records_to_keep = individuals_to_keep | referenced_ids
    print(f"Total records to keep: {len(all_records_to_keep)}")
    
    # Step 3: Write output file
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        
        current_record = None
        current_record_lines = []
        keep_record = False
        
        for line in infile:
            line = line.strip()
            
            if line.startswith('0 @') and '@' in line:
                # Write previous record if we should keep it
                if keep_record and current_record_lines:
                    for record_line in current_record_lines:
                        outfile.write(record_line + '\n')
                
                # Start new record
                current_record = line.split()[1].strip('@')
                keep_record = current_record in all_records_to_keep
                current_record_lines = [line]
                
            elif line.startswith('0 '):
                # Write previous record if we should keep it
                if keep_record and current_record_lines:
                    for record_line in current_record_lines:
                        outfile.write(record_line + '\n')
                
                # Write non-record lines (like TRLR, HEAD)
                outfile.write(line + '\n')
                current_record = None
                current_record_lines = []
                keep_record = False
                
            else:
                if current_record:
                    current_record_lines.append(line)
        
        # Write last record if needed
        if keep_record and current_record_lines:
            for record_line in current_record_lines:
                outfile.write(record_line + '\n')
    
    print(f"Trimmed GEDCOM saved to {output_file}")

def main():
    if len(sys.argv) != 4:
        print("Usage: python gedcom_simple_trimmer.py <input_file> <output_file> <cutoff_year>")
        print("Example: python gedcom_simple_trimmer.py input.ged output.ged -1000")
        print("Use negative years for BC (e.g., -1000 = 1000 BC)")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    cutoff_year = int(sys.argv[3])
    
    try:
        trim_gedcom_simple(input_file, output_file, cutoff_year)
    except FileNotFoundError:
        print(f"Error: File {input_file} not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()