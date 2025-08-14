#!/usr/bin/env python3
"""
Debug version to see why families processor added 0 relationships
"""

import requests
import json

def identify_newly_added_individuals():
    """Identify individuals that were just added/repaired (Q152xxx and Q153xxx range)"""
    newly_added = set()
    
    try:
        with open('gedcom_to_qid_mapping.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '\t' in line:
                    gedcom_id, qid = line.split('\t', 1)
                    # Check if this is a newly added individual (Q152xxx or Q153xxx range)
                    if (qid.startswith('Q152') or qid.startswith('Q153')) and gedcom_id.startswith('@I') and gedcom_id.endswith('@'):
                        newly_added.add(gedcom_id)
        
        print(f"Found {len(newly_added)} newly added individuals")
        sample_individuals = list(newly_added)[:10]
        print(f"Sample: {sample_individuals}")
        return newly_added
        
    except FileNotFoundError:
        print("gedcom_to_qid_mapping.txt not found")
        return set()

def load_gedcom_data():
    """Load family and individual data from GEDCOM - just first few families"""
    families = {}
    individuals = {}
    
    family_count = 0
    
    with open('new_gedcoms/source gedcoms/master_combined.ged', 'r', encoding='utf-8') as f:
        current_record = None
        current_type = None
        
        for line in f:
            line = line.strip()
            
            # Start of new record
            if line.startswith('0 @') and (line.endswith('@ INDI') or line.endswith('@ FAM')):
                parts = line.split()
                record_id = parts[1]  # @I123@ or @F123@
                record_type = parts[2]  # INDI or FAM
                
                if record_type == 'INDI':
                    current_record = record_id
                    current_type = 'INDI'
                    individuals[record_id] = {'families': []}
                elif record_type == 'FAM':
                    current_record = record_id
                    current_type = 'FAM' 
                    families[record_id] = {'husband': None, 'wife': None, 'children': []}
                    family_count += 1
                    if family_count > 5:  # Only process first 5 families for debugging
                        break
                
            elif current_record and current_type:
                # Family membership for individuals
                if current_type == 'INDI':
                    if line.startswith('1 FAMC ') or line.startswith('1 FAMS '):
                        family_id = line.split()[2]  # Extract @F123@
                        individuals[current_record]['families'].append(family_id)
                
                # Family structure
                elif current_type == 'FAM':
                    if line.startswith('1 HUSB '):
                        families[current_record]['husband'] = line.split()[1]
                    elif line.startswith('1 WIFE '):
                        families[current_record]['wife'] = line.split()[1]
                    elif line.startswith('1 CHIL '):
                        families[current_record]['children'].append(line.split()[1])
    
    print(f"Loaded {len(individuals)} individuals and {len(families)} families from GEDCOM")
    return families, individuals

def load_mappings():
    """Load GEDCOM ID to QID mappings"""
    mappings = {}
    try:
        with open('gedcom_to_qid_mapping.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '\t' in line:
                    gedcom_id, qid = line.split('\t', 1)
                    mappings[gedcom_id] = qid
        print(f"Loaded {len(mappings)} ID mappings")
    except FileNotFoundError:
        print("gedcom_to_qid_mapping.txt not found")
    return mappings

def debug_family_processing():
    print("=== DEBUG FAMILIES PROCESSOR ===")
    
    # Step 1: Get newly added individuals
    newly_added = identify_newly_added_individuals()
    
    # Step 2: Load GEDCOM data (limited)
    families, individuals = load_gedcom_data()
    
    # Step 3: Load mappings
    mappings = load_mappings()
    
    # Step 4: Check which families contain newly added individuals
    families_with_new_individuals = set()
    
    for individual_id in newly_added:
        if individual_id in individuals:
            for family_id in individuals[individual_id]['families']:
                families_with_new_individuals.add(family_id)
    
    print(f"\nFound {len(families_with_new_individuals)} families with newly added individuals")
    print(f"Sample families: {list(families_with_new_individuals)[:5]}")
    
    # Step 5: Debug specific families
    for family_id in list(families_with_new_individuals)[:3]:
        print(f"\n=== DEBUGGING FAMILY {family_id} ===")
        if family_id in families:
            family_data = families[family_id]
            print(f"Husband: {family_data.get('husband')} -> QID: {mappings.get(family_data.get('husband'), 'NOT FOUND')}")
            print(f"Wife: {family_data.get('wife')} -> QID: {mappings.get(family_data.get('wife'), 'NOT FOUND')}")
            print(f"Children: {family_data.get('children', [])}")
            for child in family_data.get('children', []):
                print(f"  {child} -> QID: {mappings.get(child, 'NOT FOUND')}")
        else:
            print(f"Family {family_id} not found in families dict")

if __name__ == '__main__':
    debug_family_processing()