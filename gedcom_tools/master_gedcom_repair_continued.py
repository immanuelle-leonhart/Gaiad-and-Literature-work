#!/usr/bin/env python3
import requests
import json
import time
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Master GEDCOM Repair Bot/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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
        print(f"Login token failed: {response.status_code}")
        return False
    token_data = response.json()
    login_token = token_data['query']['tokens']['logintoken']
    
    login_data = {'action': 'login', 'lgname': 'Immanuelle', 'lgpassword': '1996ToOmega!', 'lgtoken': login_token, 'format': 'json'}
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=login_data)
    result = response.json()
    success = result.get('login', {}).get('result') == 'Success'
    if not success:
        print(f"Login failed: {result}")
    return success

def get_csrf_token(session):
    response = session.get('https://evolutionism.miraheze.org/w/api.php', params={'action': 'query', 'meta': 'tokens', 'format': 'json'})
    result = response.json()
    if 'query' not in result:
        print(f"CSRF token error: {result}")
    return result['query']['tokens']['csrftoken']

def load_mapping_file():
    mapping = {}
    properties = {}
    with open('gedcom_to_qid_mapping.txt', 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
        in_properties = False
        in_individuals = False
        
        for line in lines:
            line = line.strip()
            if line == '# Properties':
                in_properties = True
                continue
            elif line == '# Individuals':
                in_properties = False
                in_individuals = True
                continue
            elif line.startswith('#') or not line:
                continue
            
            if in_properties and '\t' in line:
                prop, pid = line.split('\t', 1)
                properties[prop] = pid
            elif in_individuals and '\t' in line:
                gedcom_id, qid = line.split('\t', 1)
                mapping[gedcom_id] = qid
    
    return mapping, properties

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
            if tag == 'NAME':
                individual['data']['full_name'] = value
                name_parts = value.split('/')
                if len(name_parts) >= 2:
                    individual['data']['given_name'] = name_parts[0].strip()
                    individual['data']['surname'] = name_parts[1].strip()
                else:
                    individual['data']['given_name'] = value
            elif tag == 'SEX':
                individual['data']['sex'] = 'Q6581097' if value == 'M' else 'Q6581072'
            elif tag == 'BIRT':
                if i + 1 < len(lines) and '2 DATE' in lines[i + 1]:
                    date_line = lines[i + 1].strip()
                    date_value = date_line.split('DATE', 1)[1].strip()
                    individual['data']['birth_date'] = date_value
                    i += 1
            elif tag == 'DEAT':
                if i + 1 < len(lines) and '2 DATE' in lines[i + 1]:
                    date_line = lines[i + 1].strip()
                    date_value = date_line.split('DATE', 1)[1].strip()
                    individual['data']['death_date'] = date_value
                    i += 1
            elif tag == 'REFN':
                if i + 1 < len(lines) and '2 TYPE WIKIDATA' in lines[i + 1]:
                    individual['data']['gedcom_refn'] = value
                    i += 1
        
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
                if individual['id']:
                    individuals[individual['id']] = individual['data']
            current_individual = [line]
        elif current_individual:
            if line.startswith('0 ') and not line.endswith('@ INDI'):
                individual = parse_gedcom_individual(current_individual)
                if individual['id']:
                    individuals[individual['id']] = individual['data']
                current_individual = []
            else:
                current_individual.append(line)
    
    if current_individual:
        individual = parse_gedcom_individual(current_individual)
        if individual['id']:
            individuals[individual['id']] = individual['data']
    
    return individuals

def add_statement_to_item(session, qid, property_pid, value, value_type, csrf_token):
    try:
        if value_type == 'string':
            datavalue = {'value': str(value), 'type': 'string'}
        elif value_type == 'monolingualtext':
            datavalue = {'value': {'text': str(value), 'language': 'en'}, 'type': 'monolingualtext'}
        elif value_type == 'item':
            if isinstance(value, str) and value.startswith('Q'):
                numeric_id = int(value[1:])
            else:
                numeric_id = int(value)
            datavalue = {'value': {'entity-type': 'item', 'numeric-id': numeric_id}, 'type': 'wikibase-entityid'}
        else:
            datavalue = {'value': {'text': str(value), 'language': 'en'}, 'type': 'monolingualtext'}
        
        statement_data = {
            'claims': [
                {
                    'mainsnak': {'snaktype': 'value', 'property': property_pid, 'datavalue': datavalue},
                    'type': 'statement'
                }
            ]
        }
        
        params = {
            'action': 'wbeditentity',
            'id': qid,
            'data': json.dumps(statement_data),
            'format': 'json',
            'token': csrf_token,
            'summary': 'Adding data from master GEDCOM file',
            'bot': 1
        }
        
        response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params, timeout=30)
        result = response.json()
        
        if 'error' in result:
            print(f"      API Error: {result['error']}")
            return False
        
        return 'entity' in result
    
    except Exception as e:
        print(f"      Exception: {e}")
        return False

def update_individual(session, qid, updates, properties, csrf_token):
    if not updates:
        return True
        
    print(f"Updating {qid} with {len(updates)} properties...")
    
    success = True
    for prop_name, value in updates.items():
        if prop_name in properties:
            pid = properties[prop_name]
            print(f"  Adding {prop_name} ({pid}): {value}")
            
            if prop_name == 'gedcom_refn':
                value_type = 'string'
            else:
                value_type = 'monolingualtext'
            
            if add_statement_to_item(session, qid, pid, value, value_type, csrf_token):
                print(f"    Successfully added {prop_name}")
            else:
                print(f"    Failed to add {prop_name}")
                success = False
                
            time.sleep(0.5)
    
    return success

def main():
    print("Starting master GEDCOM repair process (continuing from @I54001@)...")
    
    mapping, properties = load_mapping_file()
    print(f"Loaded {len(mapping)} mappings and {len(properties)} properties")
    
    individuals = parse_master_gedcom()
    print(f"Parsed {len(individuals)} individuals from master GEDCOM")
    
    session = create_session()
    if not login_to_wiki(session):
        print("Failed to login. Exiting.")
        return
    print("Successfully logged in!")
    
    csrf_token = get_csrf_token(session)
    
    success_count = 0
    error_count = 0
    started = False
    
    for gedcom_id, data in individuals.items():
        # Start from @I54001@ (after María Manrique de Lara)
        if not started:
            if gedcom_id == '@I54001@':
                started = True
                print(f"Starting from {gedcom_id}...")
            continue
        
        if gedcom_id in mapping:
            qid = mapping[gedcom_id]
            print(f"\nProcessing {gedcom_id} -> {qid}")
            
            try:
                updates = {k: v for k, v in data.items() if v and v.strip()}
                
                if updates:
                    if update_individual(session, qid, updates, properties, csrf_token):
                        success_count += 1
                    else:
                        error_count += 1
                    time.sleep(1)
            except Exception as e:
                print(f"  ERROR processing {gedcom_id}: {e}")
                error_count += 1
        else:
            print(f"Skipping {gedcom_id} - not in mapping file")
    
    print(f"\nRepair complete! Success: {success_count}, Errors: {error_count}")

if __name__ == '__main__':
    main()