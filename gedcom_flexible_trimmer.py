#!/usr/bin/env python3
"""
Flexible GEDCOM Trimmer
Allows different cutoff years (1000, 1100, 1200, etc.)
Preserves all GENI-linked people and pre-cutoff individuals
"""

import re
import os
from datetime import datetime

def should_keep_individual(birth_year, has_geni, has_wikidata, cutoff_year):
    """Determine if individual should be kept based on trimming rules"""
    # Keep if born before cutoff year (essential antiquity)
    if birth_year is None or birth_year < cutoff_year:
        return True
    
    # Keep if has GENI identifier (your priority)
    if has_geni:
        return True
    
    # Remove if born after cutoff year and no GENI identifier
    return False

def trim_gedcom_flexible(input_file, output_file, cutoff_year):
    """Trim GEDCOM file using flexible cutoff year with GENI preservation"""
    print(f"Trimming GEDCOM: {input_file}")
    print(f"Output file: {output_file}")
    print(f"Cutoff year: {cutoff_year} CE")
    print(f"Rules: Keep pre-{cutoff_year} CE + all GENI identifiers")
    
    individuals_kept = 0
    individuals_removed = 0
    families_kept = 0
    
    kept_individual_ids = set()
    current_person_data = {}
    
    # First pass: identify which individuals to keep
    print("\nFirst pass: Analyzing individuals...")
    
    try:
        with open(input_file, 'r', encoding='latin1') as f:
            current_person_id = None
            current_person_birth_year = None
            current_person_has_geni = False
            current_person_has_wikidata = False
            in_individual = False
            in_birth_event = False
            line_count = 0
            
            for line in f:
                line_count += 1
                if line_count % 500000 == 0:
                    print(f"  Processed {line_count:,} lines...")
                
                line = line.strip()
                if not line:
                    continue
                
                # Individual record start
                if re.match(r'^0\s+(@I\d+@)\s+INDI', line):
                    # Process previous individual
                    if in_individual and current_person_id:
                        keep = should_keep_individual(
                            current_person_birth_year, 
                            current_person_has_geni, 
                            current_person_has_wikidata,
                            cutoff_year
                        )
                        
                        if keep:
                            kept_individual_ids.add(current_person_id)
                            individuals_kept += 1
                        else:
                            individuals_removed += 1
                    
                    # Extract new individual ID
                    match = re.match(r'^0\s+(@I\d+@)\s+INDI', line)
                    current_person_id = match.group(1) if match else None
                    
                    # Reset for new individual
                    in_individual = True
                    current_person_birth_year = None
                    current_person_has_geni = False
                    current_person_has_wikidata = False
                    in_birth_event = False
                
                elif in_individual:
                    # Birth event detection
                    if line.startswith('1 BIRT'):
                        in_birth_event = True
                    elif line.startswith('1 ') and not line.startswith('1 BIRT'):
                        in_birth_event = False
                    
                    # Birth date extraction
                    elif in_birth_event and line.startswith('2 DATE '):
                        date_str = line[7:]
                        if ' BC' in date_str:
                            year_match = re.search(r'(\d+)\s+BC', date_str)
                            if year_match:
                                current_person_birth_year = -int(year_match.group(1))
                        else:
                            year_match = re.search(r'\b(\d{4})\b', date_str)
                            if year_match:
                                current_person_birth_year = int(year_match.group(1))
                    
                    # Identifier detection
                    elif (line.startswith('1 NOTE ') or 
                          line.startswith('2 CONT ') or 
                          line.startswith('1 REFN ') or
                          line.startswith('1 _GENI_ID') or
                          line.startswith('1 REFN geni:') or
                          '_geni' in line.lower() or
                          '{geni:' in line.lower()):
                        
                        if (line.startswith('1 REFN geni:') or
                            'geni.com' in line.lower() or 
                            '_geni_id' in line.lower() or
                            '_geni' in line.lower() or
                            '{geni:' in line.lower()):
                            current_person_has_geni = True
                        elif ('wikidata.org' in line.lower() or 
                              'wikidata' in line.lower() or 
                              line.startswith('1 REFN Q')):
                            current_person_has_wikidata = True
                
                # End of individuals section
                elif in_individual and line.startswith('0 '):
                    in_individual = False
            
            # Process last individual
            if in_individual and current_person_id:
                keep = should_keep_individual(
                    current_person_birth_year, 
                    current_person_has_geni, 
                    current_person_has_wikidata,
                    cutoff_year
                )
                
                if keep:
                    kept_individual_ids.add(current_person_id)
                    individuals_kept += 1
                else:
                    individuals_removed += 1
    
    except Exception as e:
        print(f"Error in first pass: {e}")
        return False
    
    print(f"\nFirst pass complete:")
    print(f"  Individuals to keep: {individuals_kept:,}")
    print(f"  Individuals to remove: {individuals_removed:,}")
    print(f"  Estimated reduction: {(individuals_removed/(individuals_kept+individuals_removed)*100):.1f}%")
    
    # Second pass: write trimmed file
    print(f"\nSecond pass: Writing trimmed file...")
    
    try:
        with open(input_file, 'r', encoding='latin1') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:
            
            in_individual = False
            in_family = False
            current_individual_id = None
            current_family_valid = True
            skip_current_record = False
            line_count = 0
            buffered_family_lines = []
            
            for line in infile:
                line_count += 1
                if line_count % 500000 == 0:
                    print(f"  Written {line_count:,} lines...")
                
                stripped_line = line.strip()
                
                # Individual record
                if re.match(r'^0\s+(@I\d+@)\s+INDI', stripped_line):
                    match = re.match(r'^0\s+(@I\d+@)\s+INDI', stripped_line)
                    current_individual_id = match.group(1) if match else None
                    
                    if current_individual_id in kept_individual_ids:
                        skip_current_record = False
                        in_individual = True
                        outfile.write(line)
                    else:
                        skip_current_record = True
                        in_individual = False
                
                # Family record
                elif stripped_line.startswith('0 ') and ' FAM ' in stripped_line:
                    # Finish any buffered family
                    if in_family and buffered_family_lines:
                        if current_family_valid:
                            for fam_line in buffered_family_lines:
                                outfile.write(fam_line)
                            families_kept += 1
                        buffered_family_lines = []
                    
                    in_individual = False
                    in_family = True
                    skip_current_record = False
                    current_family_valid = False
                    buffered_family_lines = [line]
                
                # Other level 0 records (HEAD, SUBM, SOUR, TRLR, etc.)
                elif stripped_line.startswith('0 '):
                    # Finish any buffered family
                    if in_family and buffered_family_lines:
                        if current_family_valid:
                            for fam_line in buffered_family_lines:
                                outfile.write(fam_line)
                            families_kept += 1
                        buffered_family_lines = []
                    
                    in_individual = False
                    in_family = False
                    skip_current_record = False
                    outfile.write(line)
                
                # Content within records
                elif not skip_current_record:
                    if in_individual:
                        outfile.write(line)
                    
                    elif in_family:
                        buffered_family_lines.append(line)
                        
                        # Check if family references kept individuals
                        if (stripped_line.startswith('1 HUSB ') or 
                            stripped_line.startswith('1 WIFE ') or 
                            stripped_line.startswith('1 CHIL ')):
                            
                            ref_match = re.search(r'(@I\d+@)', stripped_line)
                            if ref_match and ref_match.group(1) in kept_individual_ids:
                                current_family_valid = True
                    
                    else:
                        outfile.write(line)
            
            # Handle final family if exists
            if in_family and buffered_family_lines and current_family_valid:
                for fam_line in buffered_family_lines:
                    outfile.write(fam_line)
                families_kept += 1
    
    except Exception as e:
        print(f"Error in second pass: {e}")
        return False
    
    print(f"\nTrimming complete!")
    print(f"  Cutoff year: {cutoff_year} CE")
    print(f"  Individuals kept: {individuals_kept:,}")
    print(f"  Individuals removed: {individuals_removed:,}")
    print(f"  Families kept: {families_kept:,}")
    
    # File size comparison
    try:
        orig_size = os.path.getsize(input_file)
        new_size = os.path.getsize(output_file)
        reduction = ((orig_size - new_size) / orig_size * 100)
        print(f"  File size reduction: {reduction:.1f}%")
        print(f"  Original: {orig_size:,} bytes")
        print(f"  Trimmed: {new_size:,} bytes")
    except:
        pass
    
    return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 4:
        print("Usage: python gedcom_flexible_trimmer.py <input_gedcom> <output_gedcom> <cutoff_year>")
        print("Example: python gedcom_flexible_trimmer.py merged_attempt_cleaned.ged gaiad_trimmed_1100.ged 1100")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    cutoff_year = int(sys.argv[3])
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist")
        sys.exit(1)
    
    if os.path.exists(output_file):
        print(f"Output file '{output_file}' already exists. Overwriting...")
    
    success = trim_gedcom_flexible(input_file, output_file, cutoff_year)
    if success:
        print(f"\nTrimming completed successfully for {cutoff_year} CE cutoff!")
    else:
        print(f"\nTrimming failed for {cutoff_year} CE cutoff!")
        sys.exit(1)