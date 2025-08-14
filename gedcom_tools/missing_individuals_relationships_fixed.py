#!/usr/bin/env python3
"""
MISSING INDIVIDUALS FAMILY RELATIONSHIPS - FIXED VERSION

Based on working Chinese/Japanese/Master relationship scripts.
Uses correct property IDs that exist in Evolutionism Wikibase:
- P47: Father
- P48: Mother  
- P42: Spouse
- P20: Child

This script adds relationships for individuals who were previously absent from the database
but have now been created. It uses the working wbcreateclaim API pattern.
"""

import requests
import json
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Missing Individuals Relationships Fixed/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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

def load_qid_mapping():
    """Load QID mapping from file"""
    mappings = {}
    try:
        with open('gedcom_to_qid_mapping.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '\t' in line and line.startswith('@I'):
                    parts = line.split('\t')
                    if len(parts) == 2:
                        gedcom_id, qid = parts
                        mappings[gedcom_id] = qid
        print(f"Loaded {len(mappings)} GEDCOM ID to QID mappings")
        return mappings
    except FileNotFoundError:
        print("Error: gedcom_to_qid_mapping.txt not found")
        return {}

def load_missing_individuals():
    """Load list of missing individuals that were just created"""
    missing_individuals = set()
    try:
        with open('missing_individuals.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and line.startswith('@I'):
                    missing_individuals.add(line)
        print(f"Loaded {len(missing_individuals)} missing individuals")
        return missing_individuals
    except FileNotFoundError:
        print("Warning: missing_individuals.txt not found, processing all families")
        return set()

def parse_gedcom_families():
    """Parse family records from GEDCOM file"""
    families = {}
    
    try:
        with open('new_gedcoms/source gedcoms/master_combined.ged', 'r', encoding='utf-8', errors='ignore') as f:
            current_record = []
            record_type = None
            line_count = 0
            
            for line in f:
                line_count += 1
                if line_count % 100000 == 0:
                    print(f"  Processed {line_count} lines, found {len(families)} families...")
                
                line = line.strip()
                if not line:
                    continue
                
                # Start of new record
                if line.startswith('0 '):
                    # Process previous record
                    if current_record and record_type == 'FAM':
                        family = parse_family_record(current_record)
                        if family and family['id']:
                            families[family['id']] = family
                    
                    # Check if this is a family record
                    if ' FAM' in line and line.endswith('@ FAM'):
                        current_record = [line]
                        record_type = 'FAM'
                    else:
                        current_record = []
                        record_type = None
                elif current_record and record_type == 'FAM':
                    current_record.append(line)
            
            # Handle last record
            if current_record and record_type == 'FAM':
                family = parse_family_record(current_record)
                if family and family['id']:
                    families[family['id']] = family
                    
    except Exception as e:
        print(f"Error parsing GEDCOM: {e}")
        return {}
    
    print(f"Parsed {len(families)} families from GEDCOM")
    return families

def parse_family_record(lines):
    """Parse a single family record"""
    family = {'id': '', 'husband': '', 'wife': '', 'children': []}
    
    for line in lines:
        line = line.strip()
        if line.startswith('0 @F') and line.endswith('@ FAM'):
            parts = line.split(' ', 2)
            if len(parts) >= 2:
                family['id'] = parts[1]
        elif line.startswith('1 HUSB '):
            family['husband'] = line[7:].strip()
        elif line.startswith('1 WIFE '):
            family['wife'] = line[7:].strip()
        elif line.startswith('1 CHIL '):
            family['children'].append(line[7:].strip())
    
    return family

def add_relationship(session, qid, property_id, value_qid, csrf_token):
    """Add relationship using wbcreateclaim - same pattern as working scripts"""
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
        return {'error': str(e)}

def main():
    print("Starting Missing Individuals Relationships (FIXED VERSION)...")
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
    
    # Load data
    qid_mapping = load_qid_mapping()
    if not qid_mapping:
        return
    
    missing_individuals = load_missing_individuals()
    families = parse_gedcom_families()
    if not families:
        return
    
    success_count = 0
    error_count = 0
    skip_count = 0
    
    # Process only families that contain missing individuals
    relevant_families = 0
    
    for family_id, family in families.items():
        # Check if this family involves any missing individuals
        husband_is_missing = family['husband'] in missing_individuals
        wife_is_missing = family['wife'] in missing_individuals  
        children_missing = any(child in missing_individuals for child in family['children'])
        
        # If no missing individuals are in this family, skip
        if not (husband_is_missing or wife_is_missing or children_missing):
            continue
            
        relevant_families += 1
        print(f"\nProcessing family {family_id} (relevant family #{relevant_families})")
        
        # Get QIDs for family members
        husband_qid = qid_mapping.get(family['husband'])
        wife_qid = qid_mapping.get(family['wife'])
        
        # Add spouse relationships using P42
        if husband_qid and wife_qid and (husband_is_missing or wife_is_missing):
            print(f"  Adding spouse relationship: {family['husband']} <-> {family['wife']}")
            
            # Add wife to husband (P42 = spouse)
            result = add_relationship(session, husband_qid, 'P42', wife_qid, csrf_token)
            if 'success' in result:
                success_count += 1
                print(f"    SUCCESS: Added wife to husband")
            elif 'error' in result and 'already has' in str(result.get('error', '')):
                skip_count += 1
                print(f"    SKIP: Wife already added to husband")
            else:
                error_count += 1
                print(f"    ERROR: Failed to add wife to husband - {result}")
            time.sleep(0.5)
            
            # Add husband to wife (P42 = spouse)
            result = add_relationship(session, wife_qid, 'P42', husband_qid, csrf_token)
            if 'success' in result:
                success_count += 1
                print(f"    SUCCESS: Added husband to wife")
            elif 'error' in result and 'already has' in str(result.get('error', '')):
                skip_count += 1
                print(f"    SKIP: Husband already added to wife")
            else:
                error_count += 1
                print(f"    ERROR: Failed to add husband to wife - {result}")
            time.sleep(0.5)
        
        # Add parent-child relationships
        for child_gedcom in family['children']:
            child_qid = qid_mapping.get(child_gedcom)
            child_is_missing = child_gedcom in missing_individuals
            
            if child_qid and (child_is_missing or husband_is_missing or wife_is_missing):
                print(f"  Adding parent-child relationships for {child_gedcom}")
                
                # Add father relationship (P47) if husband exists
                if husband_qid:
                    result = add_relationship(session, child_qid, 'P47', husband_qid, csrf_token)
                    if 'success' in result:
                        success_count += 1
                        print(f"    SUCCESS: Added father relationship")
                    elif 'error' in result and 'already has' in str(result.get('error', '')):
                        skip_count += 1
                        print(f"    SKIP: Father relationship already exists")
                    else:
                        error_count += 1
                        print(f"    ERROR: Failed to add father relationship - {result}")
                    time.sleep(0.5)
                    
                    # Add child to father's children (P20)
                    result = add_relationship(session, husband_qid, 'P20', child_qid, csrf_token)
                    if 'success' in result:
                        success_count += 1
                        print(f"    SUCCESS: Added child to father")
                    elif 'error' in result and 'already has' in str(result.get('error', '')):
                        skip_count += 1
                        print(f"    SKIP: Child already added to father")
                    else:
                        error_count += 1
                        print(f"    ERROR: Failed to add child to father - {result}")
                    time.sleep(0.5)
                
                # Add mother relationship (P48) if wife exists
                if wife_qid:
                    result = add_relationship(session, child_qid, 'P48', wife_qid, csrf_token)
                    if 'success' in result:
                        success_count += 1
                        print(f"    SUCCESS: Added mother relationship")
                    elif 'error' in result and 'already has' in str(result.get('error', '')):
                        skip_count += 1
                        print(f"    SKIP: Mother relationship already exists")
                    else:
                        error_count += 1
                        print(f"    ERROR: Failed to add mother relationship - {result}")
                    time.sleep(0.5)
                    
                    # Add child to mother's children (P20)
                    result = add_relationship(session, wife_qid, 'P20', child_qid, csrf_token)
                    if 'success' in result:
                        success_count += 1
                        print(f"    SUCCESS: Added child to mother")
                    elif 'error' in result and 'already has' in str(result.get('error', '')):
                        skip_count += 1
                        print(f"    SKIP: Child already added to mother")
                    else:
                        error_count += 1
                        print(f"    ERROR: Failed to add child to mother - {result}")
                    time.sleep(0.5)
    
    print(f"\nMissing Individuals Relationships (FIXED) complete!")
    print(f"Processed {relevant_families} relevant families")
    print(f"Successful relationships added: {success_count}")
    print(f"Skipped (already exists): {skip_count}")
    print(f"Errors: {error_count}")

if __name__ == '__main__':
    main()