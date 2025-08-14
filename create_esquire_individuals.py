#!/usr/bin/env python3
"""
Create the remaining missing individuals with " Esquire" suffix
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
        'User-Agent': 'Esquire Missing Individuals Creator/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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

def get_still_missing_individuals():
    missing = set()
    mappings = set()
    
    # Load original missing
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
        return []
    
    # Load current mappings
    try:
        with open('gedcom_to_qid_mapping.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '\t' in line:
                    gedcom_id, qid = line.split('\t', 1)
                    if gedcom_id.startswith('@I') and gedcom_id.endswith('@'):
                        mappings.add(gedcom_id)
    except FileNotFoundError:
        pass
    
    still_missing = missing - mappings
    return sorted(list(still_missing))

def extract_individual_data_from_gedcom(individual_id):
    individual_data = {
        'gedcom_id': individual_id,
        'other_fields': {},
        'dates': {},
        'refns': [],
        'notes': []
    }
    
    with open('new_gedcoms/source gedcoms/master_combined.ged', 'r', encoding='utf-8') as f:
        reading_individual = False
        current_note = []
        in_birth_date = False
        in_death_date = False
        
        for line in f:
            line = line.strip()
            
            if line == f"0 {individual_id} INDI":
                reading_individual = True
                continue
            elif line.startswith('0 @') and reading_individual:
                if current_note:
                    individual_data['notes'].append('\\n'.join(current_note))
                break
            elif reading_individual:
                if line.startswith('1 NAME '):
                    name = line[7:].strip()
                    if '/' in name:
                        parts = name.split('/')
                        individual_data['other_fields']['given_name'] = parts[0].strip()
                        if len(parts) > 1:
                            individual_data['other_fields']['surname'] = parts[1].strip()
                    individual_data['other_fields']['full_name'] = name.replace('/', ' ').strip()
                elif line.startswith('2 GIVN '):
                    individual_data['other_fields']['given_name'] = line[7:]
                elif line.startswith('2 SURN '):
                    individual_data['other_fields']['surname'] = line[7:]
                elif line.startswith('2 NSFX '):
                    individual_data['other_fields']['suffix'] = line[7:]
                elif line.startswith('1 SEX '):
                    individual_data['other_fields']['sex'] = line[6:].strip()
                elif line.startswith('1 BIRT'):
                    in_birth_date = True
                    in_death_date = False
                elif line.startswith('1 DEAT'):
                    in_birth_date = False  
                    in_death_date = True
                elif line.startswith('2 DATE '):
                    date_value = line[7:].strip()
                    if in_birth_date:
                        individual_data['dates']['birth_date'] = date_value
                    elif in_death_date:
                        individual_data['dates']['death_date'] = date_value
                elif line.startswith('1 NOTE '):
                    if current_note:
                        individual_data['notes'].append('\\n'.join(current_note))
                        current_note = []
                    current_note.append(line[7:])
                elif line.startswith('2 CONT '):
                    current_note.append(line[7:])
                elif line.startswith('2 CONC '):
                    if current_note:
                        current_note[-1] += line[7:]
                elif line.startswith('1 REFN '):
                    individual_data['refns'].append(line[7:])
                elif line.startswith('1 ') and not line.startswith('1 NOTE') and not line.startswith('1 REFN'):
                    in_birth_date = False
                    in_death_date = False
        
        if current_note:
            individual_data['notes'].append('\\n'.join(current_note))
    
    return individual_data

def create_wikibase_item(session, csrf_token, individual_data):
    labels = {}
    
    name_parts = []
    if 'given_name' in individual_data['other_fields']:
        name_parts.append(individual_data['other_fields']['given_name'])
    if 'surname' in individual_data['other_fields']:
        name_parts.append(individual_data['other_fields']['surname'])
    if 'suffix' in individual_data['other_fields']:
        name_parts.append(individual_data['other_fields']['suffix'])
    
    if not name_parts and 'full_name' in individual_data['other_fields']:
        name_parts.append(individual_data['other_fields']['full_name'])
    
    if name_parts:
        # Use " Esquire" suffix to force uniqueness and avoid wikibase duplicate detection
        labels['en'] = {'language': 'en', 'value': ' '.join(name_parts) + ' Esquire'}
    else:
        labels['en'] = {'language': 'en', 'value': f'Person {individual_data["gedcom_id"]} Esquire'}
    
    descriptions = {'en': {'language': 'en', 'value': 'Gaiad character with Esquire title'}}
    
    claims = {
        'P39': [{
            'mainsnak': {
                'snaktype': 'value',
                'property': 'P39',
                'datavalue': {
                    'value': {'entity-type': 'item', 'numeric-id': 279},
                    'type': 'wikibase-entityid'
                }
            },
            'type': 'statement',
            'rank': 'normal'
        }]
    }
    
    item_data = {
        'labels': labels,
        'descriptions': descriptions,
        'claims': claims
    }
    
    params = {
        'action': 'wbeditentity',
        'new': 'item',
        'data': json.dumps(item_data),
        'format': 'json',
        'token': csrf_token,
        'bot': 1
    }
    
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
    result = response.json()
    
    if 'entity' in result:
        return result['entity']['id']
    else:
        print(f"Error creating item for {individual_data['gedcom_id']}: {result}")
        return None

def add_all_properties_to_item(session, qid, individual_data, csrf_token):
    properties = {
        'gedcom_refn': 'P41',
        'given_name': 'P3',
        'surname': 'P4',
        'full_name': 'P5',
        'birth_date': 'P7',
        'death_date': 'P8',
        'sex': 'P11',
        'notes': 'P15'
    }
    
    success_count = 0
    
    # Add REFNs
    for refn in individual_data.get('refns', []):
        if add_statement_to_item(session, qid, properties['gedcom_refn'], refn, 'string', csrf_token):
            success_count += 1
    
    # Add name properties
    for field in ['full_name', 'given_name', 'surname']:
        if field in individual_data.get('other_fields', {}) and field in properties:
            if add_statement_to_item(session, qid, properties[field], 
                                   individual_data['other_fields'][field], 'monolingualtext', csrf_token):
                success_count += 1
    
    # Add date properties
    for field in ['birth_date', 'death_date']:
        if field in individual_data.get('dates', {}) and field in properties:
            if add_statement_to_item(session, qid, properties[field],
                                   individual_data['dates'][field], 'monolingualtext', csrf_token):
                success_count += 1
    
    # Add sex
    if 'sex' in individual_data.get('other_fields', {}):
        if add_statement_to_item(session, qid, properties['sex'],
                               individual_data['other_fields']['sex'], 'monolingualtext', csrf_token):
            success_count += 1
    
    return success_count

def add_statement_to_item(session, qid, property_id, value, value_type, csrf_token):
    try:
        if value_type == 'monolingualtext':
            value_data = json.dumps({
                'text': str(value),
                'language': 'en'
            })
        elif value_type == 'string':
            value_data = json.dumps(str(value))
        else:
            return False
        
        params = {
            'action': 'wbcreateclaim',
            'entity': qid,
            'property': property_id,
            'snaktype': 'value',
            'value': value_data,
            'format': 'json',
            'token': csrf_token,
            'bot': 1
        }
        
        response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
        result = response.json()
        
        return 'claim' in result
    except Exception as e:
        print(f"Error adding statement {property_id}={value}: {e}")
        return False

def update_mapping_file(individual_id, qid):
    with open('gedcom_to_qid_mapping.txt', 'a', encoding='utf-8') as f:
        f.write(f"{individual_id}\t{qid}\n")

def main():
    print("Creating remaining missing individuals with Esquire suffix...")
    
    session = create_session()
    if not login_to_wiki(session):
        print("Failed to login. Exiting.")
        return
    
    csrf_token = get_csrf_token(session)
    
    still_missing = get_still_missing_individuals()
    print(f"Found {len(still_missing)} individuals still missing")
    
    if not still_missing:
        print("No individuals to create!")
        return
    
    success_count = 0
    error_count = 0
    
    for i, individual_id in enumerate(still_missing, 1):
        try:
            print(f"[{i}/{len(still_missing)}] Processing {individual_id}...")
            
            individual_data = extract_individual_data_from_gedcom(individual_id)
            
            qid = create_wikibase_item(session, csrf_token, individual_data)
            if not qid:
                error_count += 1
                continue
            
            time.sleep(0.5)
            
            properties_added = add_all_properties_to_item(session, qid, individual_data, csrf_token)
            
            update_mapping_file(individual_id, qid)
            
            print(f"  CREATED: {qid} with {properties_added} properties")
            success_count += 1
            
            time.sleep(1)
            
        except Exception as e:
            print(f"  ERROR processing {individual_id}: {e}")
            error_count += 1
            time.sleep(2)
    
    print(f"\nEsquire individuals processing complete!")
    print(f"Successfully created: {success_count}")
    print(f"Errors: {error_count}")

if __name__ == '__main__':
    main()