#!/usr/bin/env python3
import requests
import json
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Chinese Family Creator Bot/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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
    family_mappings = {}
    try:
        with open('chinese_gedcom_to_qid_mapping.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '\t' in line:
                    parts = line.split('\t')
                    if len(parts) == 2:
                        gedcom_id, qid = parts
                        if gedcom_id.startswith('@I'):
                            individual_mappings[gedcom_id] = qid
                        elif gedcom_id.startswith('@F'):
                            family_mappings[gedcom_id] = qid
    except FileNotFoundError:
        pass
    return individual_mappings, family_mappings

def parse_chinese_gedcom():
    individuals = {}
    families = {}
    
    with open('new_gedcoms/source gedcoms/chinese_genealogy_sample.ged', 'r', encoding='utf-8') as f:
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

def create_family_item(session, family_data, csrf_token):
    try:
        family_id = family_data['id']
        labels = {'en': {'language': 'en', 'value': f'Chinese Family {family_id}'}}
        
        # Instance of Chinese family (Q280 - using same as master)
        claims = {
            'P39': [{
                'mainsnak': {
                    'snaktype': 'value',
                    'property': 'P39',
                    'datavalue': {
                        'value': {'entity-type': 'item', 'numeric-id': 280},
                        'type': 'wikibase-entityid'
                    }
                },
                'type': 'statement'
            }]
        }
        
        item_data = {'labels': labels, 'claims': claims}
        
        params = {
            'action': 'wbeditentity',
            'new': 'item',
            'data': json.dumps(item_data),
            'format': 'json',
            'token': csrf_token,
            'summary': 'Creating Chinese family item'
        }
        
        response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params, timeout=60)
        result = response.json()
        
        if 'entity' in result:
            return result['entity']['id']
        else:
            print(f"      Error creating family item: {result}")
            return None
    
    except Exception as e:
        print(f"      Exception creating family item: {e}")
        return None

def add_family_member_claim(session, individual_qid, family_qid, property_id, csrf_token):
    params = {
        'action': 'wbcreateclaim',
        'entity': individual_qid,
        'property': property_id,
        'snaktype': 'value',
        'value': json.dumps({'entity-type': 'item', 'numeric-id': int(family_qid[1:])}),
        'format': 'json',
        'token': csrf_token,
        'summary': 'Adding Chinese family relationship'
    }
    
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
    return response.json()

def update_mapping_file(gedcom_id, qid):
    try:
        with open('chinese_gedcom_to_qid_mapping.txt', 'a', encoding='utf-8') as f:
            f.write(f"{gedcom_id}\t{qid}\n")
    except Exception as e:
        print(f"Error updating mapping file: {e}")

def main():
    print("Starting Chinese family relationships creation...")
    
    individual_mappings, family_mappings = load_existing_mappings()
    print(f"Loaded {len(individual_mappings)} individual mappings and {len(family_mappings)} family mappings")
    
    individuals, families = parse_chinese_gedcom()
    print(f"Parsed {len(individuals)} individuals and {len(families)} families from GEDCOM")
    
    session = create_session()
    if not login_to_wiki(session):
        print("Failed to login. Exiting.")
        return
    
    csrf_token = get_csrf_token(session)
    
    success_count = 0
    error_count = 0
    
    # First: Create missing family items
    for family_id, family_data in families.items():
        if family_id not in family_mappings:
            print(f"\nCreating family item {family_id}")
            family_qid = create_family_item(session, family_data, csrf_token)
            if family_qid:
                family_mappings[family_id] = family_qid
                update_mapping_file(family_id, family_qid)
                print(f"  Created family {family_qid}")
                success_count += 1
            else:
                print(f"  Failed to create family")
                error_count += 1
            time.sleep(1)
    
    # Second: Link individuals to families
    for individual_id, individual_data in individuals.items():
        if individual_id not in individual_mappings:
            continue
            
        individual_qid = individual_mappings[individual_id]
        print(f"\nLinking individual {individual_id} -> {individual_qid}")
        
        try:
            # Add spouse family links
            for family_id in individual_data.get('family_spouse', []):
                if family_id in family_mappings:
                    family_qid = family_mappings[family_id]
                    print(f"  Adding spouse family link to {family_qid}")
                    result = add_family_member_claim(session, individual_qid, family_qid, 'P26', csrf_token)  # spouse family
                    if 'success' in result:
                        success_count += 1
                    else:
                        print(f"    Error: {result}")
                        error_count += 1
                    time.sleep(0.5)
            
            # Add child family links
            for family_id in individual_data.get('family_child', []):
                if family_id in family_mappings:
                    family_qid = family_mappings[family_id]
                    print(f"  Adding child family link to {family_qid}")
                    result = add_family_member_claim(session, individual_qid, family_qid, 'P25', csrf_token)  # child family
                    if 'success' in result:
                        success_count += 1
                    else:
                        print(f"    Error: {result}")
                        error_count += 1
                    time.sleep(0.5)
        
        except Exception as e:
            print(f"  ERROR linking individual: {e}")
            error_count += 1
    
    print(f"\nChinese family relationships complete!")
    print(f"Success: {success_count}")
    print(f"Errors: {error_count}")

if __name__ == '__main__':
    main()