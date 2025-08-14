#!/usr/bin/env python3
"""
Check which individuals from the missing list still don't have QID mappings
"""

def load_missing_individuals():
    missing = set()
    try:
        with open('missing_individuals_report.txt', 'r', encoding='utf-8') as f:
            reading_ids = False
            for line in f:
                line = line.strip()
                if line == "MISSING INDIVIDUAL IDs:":
                    reading_ids = True
                    continue
                if reading_ids and line.startswith('@I') and line.endswith('@'):
                    missing.add(line)
    except FileNotFoundError:
        print("missing_individuals_report.txt not found!")
        return set()
    return missing

def load_current_mappings():
    mappings = set()
    try:
        with open('gedcom_to_qid_mapping.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '\t' in line:
                    gedcom_id, qid = line.split('\t', 1)
                    if gedcom_id.startswith('@I') and gedcom_id.endswith('@'):
                        mappings.add(gedcom_id)
    except FileNotFoundError:
        print("gedcom_to_qid_mapping.txt not found!")
        return set()
    return mappings

def main():
    print("Checking remaining missing individuals...")
    
    missing_individuals = load_missing_individuals()
    current_mappings = load_current_mappings()
    
    print(f"Original missing: {len(missing_individuals)}")
    print(f"Current mappings: {len(current_mappings)}")
    
    # Find which ones are still missing
    still_missing = missing_individuals - current_mappings
    newly_added = missing_individuals - still_missing
    
    print(f"Still missing: {len(still_missing)}")
    print(f"Successfully added: {len(newly_added)}")
    
    if still_missing:
        print(f"\nFirst 20 still missing:")
        for i, individual_id in enumerate(sorted(still_missing)):
            if i >= 20:
                break
            print(f"  {individual_id}")
    
    if newly_added:
        print(f"\nFirst 10 successfully added:")
        for i, individual_id in enumerate(sorted(newly_added)):
            if i >= 10:
                break
            print(f"  {individual_id}")

if __name__ == '__main__':
    main()