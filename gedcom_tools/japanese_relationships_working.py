#!/usr/bin/env python3
import requests
import json
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Japanese Relationships Working Bot/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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
        with open('japanese_gedcom_to_qid_mapping.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '\t' in line and line.startswith('@I'):
                    parts = line.split('\t')
                    if len(parts) == 2:
                        gedcom_id, qid = parts
                        individual_mappings[gedcom_id] = qid
    except FileNotFoundError:
        pass
    return individual_mappings

def parse_japanese_gedcom():
    individuals = {}
    families = {}
    
    with open('new_gedcoms/source gedcoms/japan_genealogy_sample.ged', 'r', encoding='utf-8') as f:
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
    individual = {'id': '', 'family_spouse': [], 'family_child': []}
    
    for line in lines:
        parts = line.strip().split(' ', 2)
        if len(parts) < 2:
            continue
        
        level = int(parts[0])
        tag = parts[1]
        value = parts[2] if len(parts) > 2 else ''
        
        if level == 0 and tag.startswith('@I'):
            individual['id'] = tag
        elif level == 1:
            if tag == 'FAMS':
                individual['family_spouse'].append(value)
            elif tag == 'FAMC':
                individual['family_child'].append(value)
    
    return individual

def parse_family(lines):
    family = {'id': '', 'husband': '', 'wife': '', 'children': []}
    
    for line in lines:
        parts = line.strip().split(' ', 2)
        if len(parts) < 2:
            continue
        
        level = int(parts[0])
        tag = parts[1]
        value = parts[2] if len(parts) > 2 else ''
        
        if level == 0 and tag.startswith('@F'):
            family['id'] = tag
        elif level == 1:
            if tag == 'HUSB':
                family['husband'] = value
            elif tag == 'WIFE':
                family['wife'] = value
            elif tag == 'CHIL':
                family['children'].append(value)
    
    return family

def add_relationship_statement(session, individual_qid, related_qid, property_id, csrf_token):
    """Add relationship using wbeditentity API like the working uploader"""
    
    # Extract numeric ID from QID 
    numeric_id = int(related_qid[1:])
    
    datavalue = {
        'value': {'entity-type': 'item', 'numeric-id': numeric_id},
        'type': 'wikibase-entityid'
    }
    
    statement_data = {
        'claims': [
            {
                'mainsnak': {
                    'snaktype': 'value',
                    'property': property_id,
                    'datavalue': datavalue
                },
                'type': 'statement'
            }
        ]
    }
    
    params = {
        'action': 'wbeditentity',
        'id': individual_qid,
        'data': json.dumps(statement_data),
        'format': 'json',
        'token': csrf_token
    }
    
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
    return response.json()

def main():
    print("Starting Japanese relationships using working wbeditentity API...")
    
    individual_mappings = load_existing_mappings()
    print(f"Loaded {len(individual_mappings)} individual mappings")
    
    individuals, families = parse_japanese_gedcom()
    print(f"Parsed {len(individuals)} individuals and {len(families)} families from GEDCOM")
    
    session = create_session()
    if not login_to_wiki(session):
        print("Failed to login. Exiting.")
        return
    
    csrf_token = get_csrf_token(session)
    
    success_count = 0
    error_count = 0
    
    # Process families that have mapped individuals
    for family_id, family_data in families.items():
        husband_id = family_data.get('husband', '')
        wife_id = family_data.get('wife', '')
        children = family_data.get('children', [])
        
        husband_qid = individual_mappings.get(husband_id, '')
        wife_qid = individual_mappings.get(wife_id, '')
        
        # Skip families where individuals don't have QIDs
        family_has_qids = husband_qid or wife_qid or any(individual_mappings.get(child_id) for child_id in children)
        if not family_has_qids:
            continue
            
        print(f"\nProcessing family {family_id}")
        
        # Add spouse relationships
        if husband_qid and wife_qid:
            print(f"  Adding spouse relationship: {husband_id} <-> {wife_id}")
            
            # Add wife to husband (P26 = spouse)
            result = add_relationship_statement(session, husband_qid, wife_qid, 'P26', csrf_token)
            if 'entity' in result:
                success_count += 1
                print(f"    SUCCESS: Added wife to husband")
            else:
                print(f"    ERROR: Adding wife to husband failed: {result}")
                error_count += 1
            time.sleep(0.5)
            
            # Add husband to wife (P26 = spouse)  
            result = add_relationship_statement(session, wife_qid, husband_qid, 'P26', csrf_token)
            if 'entity' in result:
                success_count += 1
                print(f"    SUCCESS: Added husband to wife")
            else:
                print(f"    ERROR: Error adding husband to wife: {result}")
                error_count += 1
            time.sleep(0.5)
        
        # Add parent-child relationships
        for child_id in children:
            child_qid = individual_mappings.get(child_id, '')
            if child_qid:
                print(f"  Adding parent-child relationships for {child_id}")
                
                # Add father relationship (P22 = father)
                if husband_qid:
                    result = add_relationship_statement(session, child_qid, husband_qid, 'P22', csrf_token)
                    if 'entity' in result:
                        success_count += 1
                        print(f"    SUCCESS: Added father relationship")
                    else:
                        print(f"    ERROR: Error adding father: {result}")
                        error_count += 1
                    time.sleep(0.5)
                    
                    # Add child to father (P40 = child)
                    result = add_relationship_statement(session, husband_qid, child_qid, 'P40', csrf_token)
                    if 'entity' in result:
                        success_count += 1
                        print(f"    SUCCESS: Added child to father")
                    else:
                        print(f"    ERROR: Error adding child to father: {result}")
                        error_count += 1
                    time.sleep(0.5)
                
                # Add mother relationship (P25 = mother)
                if wife_qid:
                    result = add_relationship_statement(session, child_qid, wife_qid, 'P25', csrf_token)
                    if 'entity' in result:
                        success_count += 1
                        print(f"    SUCCESS: Added mother relationship")
                    else:
                        print(f"    ERROR: Error adding mother: {result}")
                        error_count += 1
                    time.sleep(0.5)
                    
                    # Add child to mother (P40 = child)
                    result = add_relationship_statement(session, wife_qid, child_qid, 'P40', csrf_token)
                    if 'entity' in result:
                        success_count += 1
                        print(f"    SUCCESS: Added child to mother")
                    else:
                        print(f"    ERROR: Error adding child to mother: {result}")
                        error_count += 1
                    time.sleep(0.5)
    
    print(f"\nJapanese relationships complete!")
    print(f"Success: {success_count}")
    print(f"Errors: {error_count}")

if __name__ == '__main__':
    main()