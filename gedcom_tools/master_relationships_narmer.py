#!/usr/bin/env python3
"""
MASTER FAMILY RELATIONSHIPS - NARMER VERSION
Start from family 21850 to reach Narmer (F21876) quickly

Uses correct property IDs that exist in Evolutionism Wikibase:
- P47: Father
- P48: Mother  
- P42: Spouse
- P20: Child
"""

import requests
import json
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Master Relationships Narmer/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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

def load_existing_mappings():
    individual_mappings = {}
    try:
        with open('gedcom_to_qid_mapping.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '\t' in line and line.startswith('@I'):
                    parts = line.split('\t')
                    if len(parts) == 2:
                        gedcom_id, qid = parts
                        individual_mappings[gedcom_id] = qid
    except FileNotFoundError:
        print("Error: gedcom_to_qid_mapping.txt not found!")
        return {}
    return individual_mappings

def parse_master_gedcom():
    individuals = {}
    families = {}
    
    with open('new_gedcoms/source gedcoms/master_combined.ged', 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    current_record = []
    record_type = None
    
    for line in lines:
        if line.startswith('0 @I') and line.endswith('@ INDI'):
            if current_record and record_type:
                if record_type == 'INDI':
                    individual = parse_individual(current_record)
                    if individual['id']:
                        individuals[individual['id']] = individual
                elif record_type == 'FAM':
                    family = parse_family(current_record)
                    if family['id']:
                        families[family['id']] = family
            current_record = [line]
            record_type = 'INDI'
        elif line.startswith('0 @F') and line.endswith('@ FAM'):
            if current_record and record_type:
                if record_type == 'INDI':
                    individual = parse_individual(current_record)
                    if individual['id']:
                        individuals[individual['id']] = individual
                elif record_type == 'FAM':
                    family = parse_family(current_record)
                    if family['id']:
                        families[family['id']] = family
            current_record = [line]
            record_type = 'FAM'
        elif current_record:
            if line.startswith('0 ') and not (line.endswith('@ INDI') or line.endswith('@ FAM')):
                if record_type == 'INDI':
                    individual = parse_individual(current_record)
                    if individual['id']:
                        individuals[individual['id']] = individual
                elif record_type == 'FAM':
                    family = parse_family(current_record)
                    if family['id']:
                        families[family['id']] = family
                current_record = []
                record_type = None
            else:
                current_record.append(line)
    
    # Handle last record
    if current_record and record_type:
        if record_type == 'INDI':
            individual = parse_individual(current_record)
            if individual['id']:
                individuals[individual['id']] = individual
        elif record_type == 'FAM':
            family = parse_family(current_record)
            if family['id']:
                families[family['id']] = family
    
    return individuals, families

def parse_individual(lines):
    individual = {'id': '', 'name': '', 'spouse_families': [], 'parent_family': ''}
    
    for line in lines:
        line = line.strip()
        if line.startswith('0 @I') and line.endswith('@ INDI'):
            individual['id'] = line.split()[1]
        elif line.startswith('1 NAME '):
            individual['name'] = line[7:].strip()
        elif line.startswith('1 FAMS '):
            individual['spouse_families'].append(line[7:].strip())
        elif line.startswith('1 FAMC '):
            individual['parent_family'] = line[7:].strip()
    
    return individual

def parse_family(lines):
    family = {'id': '', 'husband': '', 'wife': '', 'children': []}
    
    for line in lines:
        line = line.strip()
        if line.startswith('0 @F') and line.endswith('@ FAM'):
            family['id'] = line.split()[1]
        elif line.startswith('1 HUSB '):
            family['husband'] = line[7:].strip()
        elif line.startswith('1 WIFE '):
            family['wife'] = line[7:].strip()
        elif line.startswith('1 CHIL '):
            family['children'].append(line[7:].strip())
    
    return family

def add_relationship(session, qid, property_id, value_qid, csrf_token):
    params = {
        'action': 'wbcreateclaim',
        'entity': qid,
        'property': property_id,
        'snaktype': 'value',
        'value': json.dumps({'entity-type': 'item', 'numeric-id': int(value_qid[1:])}),
        'format': 'json',
        'token': csrf_token,
        'bot': 1
    }
    
    try:
        response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
        return response.json()
    except Exception as e:
        print(f"    Error adding relationship: {e}")
        return {'error': str(e)}

def main():
    print("Starting Master relationships from @F21850@ (Narmer focus)...")
    print("Property mappings:")
    print("  P47: Father")
    print("  P48: Mother") 
    print("  P42: Spouse")
    print("  P20: Child")
    
    # Create session and login
    session = create_session()
    if not login_to_wiki(session):
        print("Login failed!")
        return
    
    csrf_token = get_csrf_token(session)
    print("Login successful!")
    
    # Load mappings and parse GEDCOM
    print("Loading individual mappings...")
    individual_mappings = load_existing_mappings()
    print(f"Loaded {len(individual_mappings)} individual mappings")
    
    print("Parsing master GEDCOM file...")
    individuals, families = parse_master_gedcom()
    print(f"Parsed {len(individuals)} individuals and {len(families)} families")
    
    # Process families starting from @F21850@
    success_count = 0
    skip_count = 0
    restart_from_family = 21850  # START FROM FAMILY 21850 TO REACH NARMER QUICKLY
    
    for family_id, family in families.items():
        # Skip until we reach the restart point
        if family_id.startswith('@F') and family_id.endswith('@'):
            try:
                f_num = int(family_id[2:-1])
                if f_num < restart_from_family:
                    continue
            except ValueError:
                continue
        
        print(f"\nProcessing family {family_id}")
        
        # Special highlight for Narmer's family
        if family_id == '@F21876@':
            print(f"*** NARMER'S FAMILY @F21876@ FOUND! ***")
        
        # Get QIDs for family members
        husband_qid = individual_mappings.get(family['husband'])
        wife_qid = individual_mappings.get(family['wife'])
        
        # Add spouse relationships
        if husband_qid and wife_qid:
            print(f"  Adding spouse relationship: {family['husband']} <-> {family['wife']}")
            
            # Add wife to husband's spouse property (P42)
            result = add_relationship(session, husband_qid, 'P42', wife_qid, csrf_token)
            if 'success' in result:
                print(f"    SUCCESS: Added wife to husband")
                success_count += 1
            elif 'error' in result and 'already has' in str(result.get('error', '')):
                print(f"    SKIP: Wife already added to husband")
            else:
                print(f"    ERROR: Failed to add wife to husband - {result}")
            time.sleep(0.5)
            
            # Add husband to wife's spouse property (P42)
            result = add_relationship(session, wife_qid, 'P42', husband_qid, csrf_token)
            if 'success' in result:
                print(f"    SUCCESS: Added husband to wife")
                success_count += 1
            elif 'error' in result and 'already has' in str(result.get('error', '')):
                print(f"    SKIP: Husband already added to wife")
            else:
                print(f"    ERROR: Failed to add husband to wife - {result}")
            time.sleep(0.5)
        
        # Add parent-child relationships
        for child_gedcom in family['children']:
            child_qid = individual_mappings.get(child_gedcom)
            if child_qid:
                print(f"  Adding parent-child relationships for {child_gedcom}")
                
                # Add father relationship (P47) if husband exists
                if husband_qid:
                    result = add_relationship(session, child_qid, 'P47', husband_qid, csrf_token)
                    if 'success' in result:
                        print(f"    SUCCESS: Added father relationship")
                        success_count += 1
                    elif 'error' in result and 'already has' in str(result.get('error', '')):
                        print(f"    SKIP: Father relationship already exists")
                    else:
                        print(f"    ERROR: Failed to add father relationship - {result}")
                    time.sleep(0.5)
                    
                    # Add child to father's children (P20)
                    result = add_relationship(session, husband_qid, 'P20', child_qid, csrf_token)
                    if 'success' in result:
                        print(f"    SUCCESS: Added child to father")
                        success_count += 1
                    elif 'error' in result and 'already has' in str(result.get('error', '')):
                        print(f"    SKIP: Child already added to father")
                    else:
                        print(f"    ERROR: Failed to add child to father - {result}")
                    time.sleep(0.5)
                
                # Add mother relationship (P48) if wife exists
                if wife_qid:
                    result = add_relationship(session, child_qid, 'P48', wife_qid, csrf_token)
                    if 'success' in result:
                        print(f"    SUCCESS: Added mother relationship")
                        success_count += 1
                    elif 'error' in result and 'already has' in str(result.get('error', '')):
                        print(f"    SKIP: Mother relationship already exists")
                    else:
                        print(f"    ERROR: Failed to add mother relationship - {result}")
                    time.sleep(0.5)
                    
                    # Add child to mother's children (P20)
                    result = add_relationship(session, wife_qid, 'P20', child_qid, csrf_token)
                    if 'success' in result:
                        print(f"    SUCCESS: Added child to mother")
                        success_count += 1
                    elif 'error' in result and 'already has' in str(result.get('error', '')):
                        print(f"    SKIP: Child already added to mother")
                    else:
                        print(f"    ERROR: Failed to add child to mother - {result}")
                    time.sleep(0.5)
            else:
                skip_count += 1
    
    print(f"\nMaster relationships creation complete!")
    print(f"Successful relationships added: {success_count}")
    print(f"Skipped (missing mappings): {skip_count}")

if __name__ == '__main__':
    main()