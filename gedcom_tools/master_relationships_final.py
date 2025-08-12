#!/usr/bin/env python3
"""
MASTER FAMILY RELATIONSHIPS - FINAL VERSION

Uses correct property IDs that exist in Evolutionism Wikibase:
- P47: Father
- P48: Mother  
- P42: Spouse
- P20: Child

Includes safeguards for missing spouses/children and a 6-hour startup delay.
"""

import requests
import json
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Master Relationships Final/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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
    individual = {'id': '', 'name': '', 'sex': ''}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        parts = line.split(' ', 2)
        if len(parts) < 2:
            continue
            
        level = int(parts[0])
        tag = parts[1]
        value = parts[2] if len(parts) > 2 else ''
        
        if level == 0 and tag.startswith('@I') and tag.endswith('@'):
            individual['id'] = tag
        elif level == 1 and tag == 'NAME':
            individual['name'] = value
        elif level == 1 and tag == 'SEX':
            individual['sex'] = value
    
    return individual

def parse_family(lines):
    family = {'id': '', 'husband': '', 'wife': '', 'children': []}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        parts = line.split(' ', 2)
        if len(parts) < 2:
            continue
            
        level = int(parts[0])
        tag = parts[1]
        value = parts[2] if len(parts) > 2 else ''
        
        if level == 0 and tag.startswith('@F') and tag.endswith('@'):
            family['id'] = tag
        elif level == 1 and tag == 'HUSB':
            family['husband'] = value
        elif level == 1 and tag == 'WIFE':
            family['wife'] = value
        elif level == 1 and tag == 'CHIL':
            family['children'].append(value)
    
    return family

def add_relationship_using_wbeditentity(session, individual_qid, property_id, related_qid_list, csrf_token):
    # Build claims for the property with multiple related individuals
    claims = []
    for related_qid in related_qid_list:
        claims.append({
            'mainsnak': {
                'snaktype': 'value',
                'property': property_id,
                'datavalue': {
                    'value': {'entity-type': 'item', 'numeric-id': int(related_qid[1:])},
                    'type': 'wikibase-entityid'
                }
            },
            'type': 'statement'
        })
    
    statement_data = {
        'claims': {
            property_id: claims
        }
    }
    
    params = {
        'action': 'wbeditentity',
        'id': individual_qid,
        'data': json.dumps(statement_data),
        'format': 'json',
        'token': csrf_token,
        'bot': 1
    }
    
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
    return response.json()

def main():
    print("Master relationships script starting in 6 hours...")
    print("Current time:", time.strftime('%Y-%m-%d %H:%M:%S'))
    print("Will start at:", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() + 6*3600)))
    
    # Wait 6 hours (21600 seconds)
    time.sleep(21600)
    
    print("Starting Master relationships with correct property IDs...")
    print("Property mappings:")
    print("  P47: Father")
    print("  P48: Mother") 
    print("  P42: Spouse")
    print("  P20: Child")
    
    # Load mappings and parse GEDCOM
    individual_mappings = load_existing_mappings()
    individuals, families = parse_master_gedcom()
    
    print(f"Loaded {len(individual_mappings)} individual mappings")
    print(f"Parsed {len(individuals)} individuals and {len(families)} families from GEDCOM")
    
    session = create_session()
    if not login_to_wiki(session):
        print("Failed to login. Exiting.")
        return
    print("Successfully logged in!")
    
    csrf_token = get_csrf_token(session)
    
    success_count = 0
    error_count = 0
    skip_count = 0
    
    for family_id, family in families.items():
        print(f"\nProcessing family {family_id}")
        
        # Get QIDs for family members (with safety checks)
        husband_qid = None
        wife_qid = None
        child_qids = []
        
        if family['husband'] and family['husband'] in individual_mappings:
            husband_qid = individual_mappings[family['husband']]
        
        if family['wife'] and family['wife'] in individual_mappings:
            wife_qid = individual_mappings[family['wife']]
        
        for child_id in family['children']:
            if child_id and child_id in individual_mappings:
                child_qids.append(individual_mappings[child_id])
        
        # Add spouse relationships (only if both exist)
        if husband_qid and wife_qid:
            print(f"  Adding spouse relationship: {family['husband']} <-> {family['wife']}")
            
            # Add wife to husband's spouse property (P42)
            result = add_relationship_using_wbeditentity(session, husband_qid, 'P42', [wife_qid], csrf_token)
            if 'success' in result:
                success_count += 1
            else:
                print(f"    Error adding wife to husband: {result}")
                error_count += 1
            
            time.sleep(1)
            
            # Add husband to wife's spouse property (P42)
            result = add_relationship_using_wbeditentity(session, wife_qid, 'P42', [husband_qid], csrf_token)
            if 'success' in result:
                success_count += 1
            else:
                print(f"    Error adding husband to wife: {result}")
                error_count += 1
            
            time.sleep(1)
        else:
            if not husband_qid and not wife_qid:
                print(f"  Skipping spouse relationship: both husband and wife missing from mappings")
            elif not husband_qid:
                print(f"  Skipping spouse relationship: husband {family['husband']} missing from mappings")
            else:
                print(f"  Skipping spouse relationship: wife {family['wife']} missing from mappings")
            skip_count += 1
        
        # Add parent-child relationships (only for children that exist)
        for child_id in family['children']:
            if not child_id or child_id not in individual_mappings:
                print(f"  Skipping child {child_id}: not in mappings")
                skip_count += 1
                continue
                
            child_qid = individual_mappings[child_id]
            print(f"  Adding parent-child relationships for {child_id}")
            
            # Add father relationship (P47) if husband exists
            if husband_qid:
                result = add_relationship_using_wbeditentity(session, child_qid, 'P47', [husband_qid], csrf_token)
                if 'success' in result:
                    success_count += 1
                else:
                    print(f"    Error adding father: {result}")
                    error_count += 1
                time.sleep(1)
                
                # Add child to father's children (P20)
                result = add_relationship_using_wbeditentity(session, husband_qid, 'P20', [child_qid], csrf_token)
                if 'success' in result:
                    success_count += 1
                else:
                    print(f"    Error adding child to father: {result}")
                    error_count += 1
                time.sleep(1)
            else:
                print(f"    Skipping father relationship: husband not in mappings")
                skip_count += 1
            
            # Add mother relationship (P48) if wife exists
            if wife_qid:
                result = add_relationship_using_wbeditentity(session, child_qid, 'P48', [wife_qid], csrf_token)
                if 'success' in result:
                    success_count += 1
                else:
                    print(f"    Error adding mother: {result}")
                    error_count += 1
                time.sleep(1)
                
                # Add child to mother's children (P20)
                result = add_relationship_using_wbeditentity(session, wife_qid, 'P20', [child_qid], csrf_token)
                if 'success' in result:
                    success_count += 1
                else:
                    print(f"    Error adding child to mother: {result}")
                    error_count += 1
                time.sleep(1)
            else:
                print(f"    Skipping mother relationship: wife not in mappings")
                skip_count += 1
    
    print(f"\nMaster relationships creation complete!")
    print(f"Success: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Skipped: {skip_count}")

if __name__ == '__main__':
    main()