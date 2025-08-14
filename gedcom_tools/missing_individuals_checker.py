#!/usr/bin/env python3
"""
MISSING INDIVIDUALS CHECKER

Compares individuals in master_combined.ged with those in gedcom_to_qid_mapping.txt
to find any individuals that are missing from the mapping.
"""

import re

def extract_individual_ids_from_gedcom():
    """Extract all individual IDs from master_combined.ged"""
    individual_ids = set()
    
    print("Extracting individual IDs from master_combined.ged...")
    
    with open('new_gedcoms/source gedcoms/master_combined.ged', 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Look for individual records: 0 @I12345@ INDI
            if line.startswith('0 @I') and line.endswith('@ INDI'):
                # Extract the @I12345@ part
                match = re.match(r'0 (@I\d+@) INDI', line)
                if match:
                    individual_id = match.group(1)
                    individual_ids.add(individual_id)
            
            # Progress indicator every 100k lines
            if line_num % 100000 == 0:
                print(f"  Processed {line_num:,} lines, found {len(individual_ids):,} individuals so far...")
    
    print(f"Found {len(individual_ids):,} total individuals in GEDCOM")
    return individual_ids

def load_mapped_individuals():
    """Load individual IDs that already have QID mappings"""
    mapped_individuals = set()
    
    print("Loading existing QID mappings...")
    
    try:
        with open('gedcom_to_qid_mapping.txt', 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if '\t' in line:
                    gedcom_id, qid = line.split('\t', 1)
                    # Only include individual IDs (start with @I)
                    if gedcom_id.startswith('@I') and gedcom_id.endswith('@'):
                        mapped_individuals.add(gedcom_id)
                
                # Progress indicator
                if line_num % 10000 == 0:
                    print(f"  Processed {line_num:,} mapping lines...")
        
        print(f"Found {len(mapped_individuals):,} individuals with existing QID mappings")
        
    except FileNotFoundError:
        print("gedcom_to_qid_mapping.txt not found!")
        return set()
    
    return mapped_individuals

def find_missing_individuals():
    """Find individuals in GEDCOM but not in mapping"""
    print("=== MISSING INDIVIDUALS CHECKER ===\n")
    
    # Get all individuals from GEDCOM
    gedcom_individuals = extract_individual_ids_from_gedcom()
    
    # Get individuals that already have QID mappings
    mapped_individuals = load_mapped_individuals()
    
    # Find missing individuals
    missing_individuals = gedcom_individuals - mapped_individuals
    
    print(f"\n=== ANALYSIS RESULTS ===")
    print(f"Total individuals in GEDCOM: {len(gedcom_individuals):,}")
    print(f"Individuals with QID mappings: {len(mapped_individuals):,}")
    print(f"Missing individuals (no QID): {len(missing_individuals):,}")
    
    if missing_individuals:
        print(f"\nCoverage: {(len(mapped_individuals) / len(gedcom_individuals)) * 100:.1f}%")
        
        # Sort missing individuals by ID number for easier analysis
        sorted_missing = sorted(missing_individuals, key=lambda x: int(x[2:-1]))  # Extract number from @I123@
        
        print(f"\n=== SAMPLE OF MISSING INDIVIDUALS ===")
        print("First 20 missing individuals:")
        for individual_id in sorted_missing[:20]:
            print(f"  {individual_id}")
        
        if len(missing_individuals) > 20:
            print(f"  ... and {len(missing_individuals) - 20:,} more")
        
        # Write full list to file
        with open('missing_individuals_report.txt', 'w', encoding='utf-8') as f:
            f.write(f"MISSING INDIVIDUALS REPORT\n")
            f.write(f"Generated: {__import__('datetime').datetime.now()}\n\n")
            f.write(f"Total individuals in GEDCOM: {len(gedcom_individuals):,}\n")
            f.write(f"Individuals with QID mappings: {len(mapped_individuals):,}\n")
            f.write(f"Missing individuals: {len(missing_individuals):,}\n")
            f.write(f"Coverage: {(len(mapped_individuals) / len(gedcom_individuals)) * 100:.1f}%\n\n")
            f.write(f"MISSING INDIVIDUAL IDs:\n")
            for individual_id in sorted_missing:
                f.write(f"{individual_id}\n")
        
        print(f"\nFull report written to: missing_individuals_report.txt")
        
        # Check for patterns in missing IDs
        print(f"\n=== MISSING ID PATTERNS ===")
        missing_numbers = [int(id[2:-1]) for id in missing_individuals]  # Extract numbers
        min_missing = min(missing_numbers)
        max_missing = max(missing_numbers)
        print(f"Missing ID range: @I{min_missing}@ to @I{max_missing}@")
        
        # Check for gaps in sequence
        mapped_numbers = [int(id[2:-1]) for id in mapped_individuals]
        if mapped_numbers:
            min_mapped = min(mapped_numbers)
            max_mapped = max(mapped_numbers)
            print(f"Mapped ID range: @I{min_mapped}@ to @I{max_mapped}@")
            
            # Check if missing individuals are mostly at the end
            high_range_missing = len([n for n in missing_numbers if n > max_mapped])
            if high_range_missing > len(missing_individuals) * 0.8:
                print(f"NOTE: {high_range_missing:,} ({high_range_missing/len(missing_individuals)*100:.1f}%) of missing individuals have IDs higher than the highest mapped ID")
                print("This suggests the mapping process may have stopped before completing all individuals.")
    
    else:
        print("\n✅ All individuals in GEDCOM have QID mappings!")
    
    return missing_individuals

if __name__ == '__main__':
    missing = find_missing_individuals()