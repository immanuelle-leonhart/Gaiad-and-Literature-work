#!/usr/bin/env python3
import requests
import json
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Master Notes Repair Bot/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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

def parse_gedcom_individual(lines):
    individual = {'id': '', 'data': {}}
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
            
        parts = line.split(' ', 2)
        if len(parts) < 2:
            i += 1
            continue
            
        level = int(parts[0])
        tag = parts[1]
        value = parts[2] if len(parts) > 2 else ''
        
        if level == 0 and tag.startswith('@I') and tag.endswith('@'):
            individual['id'] = tag
        elif level == 1:
            if tag == 'REFN':
                if i + 1 < len(lines) and '2 TYPE WIKIDATA' in lines[i + 1]:
                    individual['data']['gedcom_refn'] = value
                    i += 1
            elif tag == 'NOTE':
                individual['data']['notes_page'] = value
        
        i += 1
    
    return individual

def parse_master_gedcom():
    individuals = {}
    
    with open('new_gedcoms/source gedcoms/master_combined.ged', 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    current_individual = []
    
    for line in lines:
        if line.startswith('0 @I') and line.endswith('@ INDI'):
            if current_individual:
                individual = parse_gedcom_individual(current_individual)
                if individual['id'] and individual['data']:
                    individuals[individual['id']] = individual['data']
            current_individual = [line]
        elif current_individual:
            if line.startswith('0 ') and not line.endswith('@ INDI'):
                individual = parse_gedcom_individual(current_individual)
                if individual['id'] and individual['data']:
                    individuals[individual['id']] = individual['data']
                current_individual = []
            else:
                current_individual.append(line)
    
    if current_individual:
        individual = parse_gedcom_individual(current_individual)
        if individual['id'] and individual['data']:
            individuals[individual['id']] = individual['data']
    
    return individuals

def load_gedcom_mappings():
    mappings = {}
    try:
        with open('gedcom_to_qid_mapping.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('@I') and '\t' in line:
                    parts = line.strip().split('\t')
                    if len(parts) == 2:
                        mappings[parts[0]] = parts[1]
    except FileNotFoundError:
        pass
    return mappings

def get_item_data(session, qid):
    params = {
        'action': 'wbgetentities',
        'ids': qid,
        'format': 'json'
    }
    response = session.get('https://evolutionism.miraheze.org/w/api.php', params=params)
    result = response.json()
    return result.get('entities', {}).get(qid)

def update_statement(session, qid, property_id, value, csrf_token):
    params = {
        'action': 'wbcreateclaim',
        'entity': qid,
        'property': property_id,
        'snaktype': 'value',
        'value': json.dumps(str(value)),
        'format': 'json',
        'token': csrf_token,
        'bot': 1
    }
    
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
    return response.json()

def main():
    print("Starting repair of master GEDCOM notes and reference numbers...")
    
    # Parse GEDCOM to get correct data
    print("Parsing master GEDCOM...")
    individuals = parse_master_gedcom()
    print(f"Found {len(individuals)} individuals with notes/refn data")
    
    # Load mappings
    mappings = load_gedcom_mappings()
    print(f"Loaded {len(mappings)} existing mappings")
    
    session = create_session()
    if not login_to_wiki(session):
        print("Failed to login. Exiting.")
        return
    
    csrf_token = get_csrf_token(session)
    
    repaired_count = 0
    error_count = 0
    
    for gedcom_id, data in individuals.items():
        if gedcom_id not in mappings:
            continue
            
        qid = mappings[gedcom_id]
        print(f"\nRepairing {gedcom_id} -> {qid}")
        
        try:
            # Get current item data
            item_data = get_item_data(session, qid)
            if not item_data:
                print(f"  Item {qid} not found")
                continue
            
            claims = item_data.get('claims', {})
            
            # Check if notes page needs repair
            if 'notes_page' in data:
                notes_claims = claims.get('P15', [])
                needs_repair = False
                
                for claim in notes_claims:
                    current_value = claim.get('mainsnak', {}).get('datavalue', {}).get('value', '')
                    if current_value == 'REFERENCE_NUMBERS:' or not current_value.strip():
                        needs_repair = True
                        break
                
                if needs_repair:
                    print(f"  Fixing notes page: {data['notes_page']}")
                    update_statement(session, qid, 'P15', data['notes_page'], csrf_token)
            
            # Check if GEDCOM REFN needs repair
            if 'gedcom_refn' in data:
                refn_claims = claims.get('P41', [])
                needs_refn_repair = True
                
                for claim in refn_claims:
                    current_value = claim.get('mainsnak', {}).get('datavalue', {}).get('value', '')
                    if current_value and current_value != 'REFERENCE_NUMBERS:':
                        needs_refn_repair = False
                        break
                
                if needs_refn_repair:
                    print(f"  Adding GEDCOM REFN: {data['gedcom_refn']}")
                    update_statement(session, qid, 'P41', data['gedcom_refn'], csrf_token)
            
            repaired_count += 1
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"  ERROR: {e}")
            error_count += 1
    
    print(f"\nRepair complete!")
    print(f"Repaired: {repaired_count}")
    print(f"Errors: {error_count}")

if __name__ == '__main__':
    main()