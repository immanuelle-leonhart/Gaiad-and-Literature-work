#!/usr/bin/env python3
"""
MISSING INDIVIDUALS FAMILIES PROCESSOR

Processes family relationships ONLY for families that contain individuals
who were just added/repaired by the missing_individuals_creator.py script.
This ensures their family relationships are properly established.

Identifies families containing individuals in the Q152xxx range and processes
their spouse, parent, and child relationships.
"""

import requests
import json
import time
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Missing Individuals Families Processor Bot/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
    })
    retry_strategy = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def login_to_wiki(session):
    token_params = {'action': 'query', 'meta': 'tokens', 'type': 'login', 'format': 'json'}
    response = session.get('https://evolutionism.miraheze.org/w/api.php', params=token_params, timeout=30)
    if response.status_code != 200:
        return False
    token_data = response.json()
    login_token = token_data['query']['tokens']['logintoken']
    
    login_data = {'action': 'login', 'lgname': 'Immanuelle', 'lgpassword': '1996ToOmega!', 'lgtoken': login_token, 'format': 'json'}
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=login_data)
    return response.json().get('login', {}).get('result') == 'Success'

def get_csrf_token(session):
    response = session.get('https://evolutionism.miraheze.org/w/api.php', params={'action': 'query', 'meta': 'tokens', 'format': 'json'})
    return response.json()['query']['tokens']['csrftoken']

def identify_newly_added_individuals():
    """Identify individuals that were just added/repaired (Q152xxx range)"""
    newly_added = set()
    
    # Based on the script output, newly added individuals are Q152392 and higher
    # The script processed 1,183 individuals with 133 repaired and 1,050 created
    # So we need to identify all Q152xxx individuals
    
    try:
        with open('gedcom_to_qid_mapping.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '\t' in line:
                    gedcom_id, qid = line.split('\t', 1)
                    # Check if this is a newly added individual (Q152xxx range)
                    if qid.startswith('Q152') and gedcom_id.startswith('@I') and gedcom_id.endswith('@'):
                        newly_added.add(gedcom_id)
        
        print(f"Identified {len(newly_added)} newly added/repaired individuals")
        # Debug: show first few
        sample_individuals = list(newly_added)[:5]
        print(f"Sample individuals: {sample_individuals}")
        return newly_added
        
    except FileNotFoundError:
        print("gedcom_to_qid_mapping.txt not found")
        return set()

def load_gedcom_data():
    """Load family and individual data from GEDCOM"""
    families = {}
    individuals = {}
    
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
                
            elif current_record and current_type:
                # Family membership for individuals
                if current_type == 'INDI':
                    if line.startswith('1 FAMC ') or line.startswith('1 FAMS '):
                        family_id = line.split()[2]  # Extract @F123@ (index 2, not 1!)
                        individuals[current_record]['families'].append(family_id)
                        # Debug: print first few family associations
                        if len(individuals[current_record]['families']) == 1:
                            print(f"  DEBUG: {current_record} -> {family_id}")
                
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

def identify_families_with_newly_added_individuals(families, individuals, newly_added):
    """Find families that contain newly added individuals"""
    families_to_process = set()
    
    for individual_id in newly_added:
        if individual_id in individuals:
            # Get all families this individual is part of
            for family_id in individuals[individual_id]['families']:
                families_to_process.add(family_id)
    
    print(f"Identified {len(families_to_process)} families containing newly added individuals")
    return families_to_process

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

def add_relationship(session, from_qid, property_id, to_qid, csrf_token):
    """Add a relationship between two individuals"""
    params = {
        'action': 'wbcreateclaim',
        'entity': from_qid,
        'property': property_id,
        'snaktype': 'value',
        'value': json.dumps({'entity-type': 'item', 'numeric-id': int(to_qid[1:])}),  # Remove Q prefix
        'format': 'json',
        'token': csrf_token,
        'bot': 1
    }
    
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
    result = response.json()
    return 'claim' in result

def process_family_relationships(session, family_id, family_data, mappings, csrf_token):
    """Process relationships for a single family"""
    husband_id = family_data.get('husband')
    wife_id = family_data.get('wife')
    children = family_data.get('children', [])
    
    husband_qid = mappings.get(husband_id) if husband_id else None
    wife_qid = mappings.get(wife_id) if wife_id else None
    
    relationships_added = 0
    
    # Add spouse relationships
    if husband_qid and wife_qid:
        if add_relationship(session, husband_qid, 'P42', wife_qid, csrf_token):  # P42 = Spouse
            relationships_added += 1
        time.sleep(0.1)
        if add_relationship(session, wife_qid, 'P42', husband_qid, csrf_token):
            relationships_added += 1
        time.sleep(0.1)
    
    # Add parent-child relationships
    for child_id in children:
        child_qid = mappings.get(child_id)
        if child_qid:
            # Add father relationship
            if husband_qid:
                if add_relationship(session, child_qid, 'P47', husband_qid, csrf_token):  # P47 = Father
                    relationships_added += 1
                time.sleep(0.1)
                if add_relationship(session, husband_qid, 'P20', child_qid, csrf_token):  # P20 = Child
                    relationships_added += 1
                time.sleep(0.1)
            
            # Add mother relationship  
            if wife_qid:
                if add_relationship(session, child_qid, 'P48', wife_qid, csrf_token):  # P48 = Mother
                    relationships_added += 1
                time.sleep(0.1)
                if add_relationship(session, wife_qid, 'P20', child_qid, csrf_token):  # P20 = Child
                    relationships_added += 1
                time.sleep(0.1)
    
    return relationships_added

def main():
    print("Starting Missing Individuals Families Processor...")
    
    # Create session and login
    session = create_session()
    if not login_to_wiki(session):
        print("Failed to login. Exiting.")
        return
    
    csrf_token = get_csrf_token(session)
    
    # Step 1: Identify newly added individuals (Q152xxx)
    newly_added_individuals = identify_newly_added_individuals()
    if not newly_added_individuals:
        print("No newly added individuals found. Exiting.")
        return
    
    # Step 2: Load GEDCOM data
    families, individuals = load_gedcom_data()
    
    # Step 3: Identify families containing newly added individuals
    families_to_process = identify_families_with_newly_added_individuals(families, individuals, newly_added_individuals)
    
    # Debug: show what families we found
    print(f"Families to process: {list(families_to_process)}")
    if not families_to_process:
        print("No families to process. Exiting.")
        return
    
    # Step 4: Load ID mappings
    mappings = load_mappings()
    
    # Step 5: Process family relationships
    print(f"Processing relationships for {len(families_to_process)} families...")
    
    total_relationships = 0
    processed_families = 0
    error_count = 0
    
    for i, family_id in enumerate(families_to_process, 1):
        if family_id not in families:
            print(f"  WARNING: Family {family_id} not found in GEDCOM data")
            continue
            
        try:
            print(f"[{i}/{len(families_to_process)}] Processing family {family_id}...")
            
            relationships_added = process_family_relationships(
                session, family_id, families[family_id], mappings, csrf_token
            )
            
            total_relationships += relationships_added
            processed_families += 1
            
            print(f"  Added {relationships_added} relationships")
            
            # Rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  ERROR processing {family_id}: {e}")
            error_count += 1
            time.sleep(1)
    
    print(f"\nMissing Individuals Families Processing Complete!")
    print(f"Families processed: {processed_families}")
    print(f"Total relationships added: {total_relationships}")
    print(f"Errors: {error_count}")

if __name__ == '__main__':
    main()