#!/usr/bin/env python3
"""
DUPLICATE GEDCOM MAPPING FINDER AND CLEANER

This script finds duplicate GEDCOM ID mappings in the gedcom_to_qid_mapping.txt file
and creates a cleaned version keeping only the first occurrence of each GEDCOM ID.

The goal is to fix issues where one GEDCOM ID maps to multiple QIDs, which causes
relationship processing scripts to malfunction.
"""

def find_and_clean_duplicate_mappings():
    """Find duplicate GEDCOM mappings and create cleaned file"""
    
    # Read all mappings
    mappings = []
    duplicates = {}
    
    print("Reading gedcom_to_qid_mapping.txt...")
    
    with open('gedcom_to_qid_mapping.txt', 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if '\t' in line:
                parts = line.split('\t')
                if len(parts) == 2:
                    gedcom_id, qid = parts
                    mappings.append((gedcom_id, qid, line_num))
    
    print(f"Found {len(mappings)} total mappings")
    
    # Find duplicates
    seen_gedcom_ids = {}
    duplicate_lines = []
    
    for gedcom_id, qid, line_num in mappings:
        if gedcom_id in seen_gedcom_ids:
            # This is a duplicate
            first_qid, first_line = seen_gedcom_ids[gedcom_id]
            
            if gedcom_id not in duplicates:
                duplicates[gedcom_id] = {
                    'first': (first_qid, first_line),
                    'additional': []
                }
            
            duplicates[gedcom_id]['additional'].append((qid, line_num))
            duplicate_lines.append(line_num)
        else:
            seen_gedcom_ids[gedcom_id] = (qid, line_num)
    
    print(f"\nFound {len(duplicates)} GEDCOM IDs with duplicate mappings:")
    
    # Report duplicates
    for gedcom_id, info in duplicates.items():
        first_qid, first_line = info['first']
        print(f"\n{gedcom_id}:")
        print(f"  KEEP:   Line {first_line}: {gedcom_id} -> {first_qid}")
        for qid, line_num in info['additional']:
            print(f"  REMOVE: Line {line_num}: {gedcom_id} -> {qid}")
    
    # Create duplicate report
    print(f"\nWriting duplicate report to duplicate_mappings_report.txt...")
    with open('duplicate_mappings_report.txt', 'w', encoding='utf-8') as f:
        f.write("DUPLICATE GEDCOM MAPPINGS REPORT\n")
        f.write("="*50 + "\n\n")
        f.write(f"Total mappings: {len(mappings)}\n")
        f.write(f"Duplicate GEDCOM IDs: {len(duplicates)}\n")
        f.write(f"Total duplicate lines to remove: {len(duplicate_lines)}\n\n")
        
        for gedcom_id, info in duplicates.items():
            first_qid, first_line = info['first']
            f.write(f"{gedcom_id}:\n")
            f.write(f"  KEEP:   Line {first_line}: {gedcom_id} -> {first_qid}\n")
            for qid, line_num in info['additional']:
                f.write(f"  REMOVE: Line {line_num}: {gedcom_id} -> {qid}\n")
            f.write("\n")
    
    # Create cleaned mapping file
    print(f"\nCreating cleaned mapping file: gedcom_to_qid_mapping_cleaned.txt...")
    
    seen_in_clean = set()
    kept_count = 0
    removed_count = 0
    
    with open('gedcom_to_qid_mapping.txt', 'r', encoding='utf-8') as infile:
        with open('gedcom_to_qid_mapping_cleaned.txt', 'w', encoding='utf-8') as outfile:
            for line in infile:
                line = line.strip()
                if '\t' in line:
                    parts = line.split('\t')
                    if len(parts) == 2:
                        gedcom_id, qid = parts
                        if gedcom_id not in seen_in_clean:
                            # First occurrence - keep it
                            outfile.write(line + '\n')
                            seen_in_clean.add(gedcom_id)
                            kept_count += 1
                        else:
                            # Duplicate - skip it
                            removed_count += 1
                else:
                    # Keep non-mapping lines as-is
                    outfile.write(line + '\n')
    
    print(f"\nCleaning complete:")
    print(f"  Kept: {kept_count} unique mappings")
    print(f"  Removed: {removed_count} duplicate mappings")
    print(f"  Clean file: gedcom_to_qid_mapping_cleaned.txt")
    
    return duplicates

def backup_and_replace_mapping_file():
    """Backup original and replace with cleaned version"""
    import shutil
    import os
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"gedcom_to_qid_mapping_backup_{timestamp}.txt"
    
    print(f"\nBacking up original file to: {backup_name}")
    shutil.copy('gedcom_to_qid_mapping.txt', backup_name)
    
    print("Replacing original with cleaned version...")
    shutil.move('gedcom_to_qid_mapping_cleaned.txt', 'gedcom_to_qid_mapping.txt')
    
    print("✅ Mapping file cleaned and replaced!")
    print(f"   Original backed up as: {backup_name}")

if __name__ == '__main__':
    print("DUPLICATE GEDCOM MAPPING FINDER AND CLEANER")
    print("=" * 50)
    
    duplicates = find_and_clean_duplicate_mappings()
    
    if duplicates:
        print(f"\nFound {len(duplicates)} GEDCOM IDs with duplicates")
        
        while True:
            response = input("\nReplace original mapping file with cleaned version? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                backup_and_replace_mapping_file()
                break
            elif response in ['n', 'no']:
                print("Keeping original file. Cleaned version saved as gedcom_to_qid_mapping_cleaned.txt")
                break
            else:
                print("Please enter 'y' or 'n'")
    else:
        print("\n✅ No duplicates found! Mapping file is clean.")