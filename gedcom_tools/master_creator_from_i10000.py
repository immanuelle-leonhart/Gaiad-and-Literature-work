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
        'User-Agent': 'Master GEDCOM Creator Bot/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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

def generate_label(name_data):
    """Generate label from name data"""
    if 'full_name' in name_data:
        return name_data['full_name'].replace('/', ' ').strip()
    elif 'given_name' in name_data and 'surname' in name_data:
        return f"{name_data['given_name']} {name_data['surname']}"
    elif 'given_name' in name_data:
        return name_data['given_name']
    elif 'surname' in name_data:
        return name_data['surname']
    else:
        return "Unknown"

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
                individual['data']['sex'] = 'male' if value == 'M' else 'female'
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

def create_new_individual(session, data, csrf_token):
    try:
        # Generate label
        label_text = generate_label(data)
        
        # Create basic item structure
        labels = {'en': {'language': 'en', 'value': label_text}}
        
        claims = {}
        
        # Instance of human (P39 -> Q5)
        claims['P39'] = [{
            'mainsnak': {
                'snaktype': 'value',
                'property': 'P39',
                'datavalue': {
                    'value': {'entity-type': 'item', 'numeric-id': 5},
                    'type': 'wikibase-entityid'
                }
            },
            'type': 'statement'
        }]
        
        # Add other properties - use string type only (master system expects string)
        for prop_name, value in data.items():
            if prop_name in ['full_name', 'given_name', 'surname', 'birth_date', 'death_date', 'sex', 'notes_page', 'gedcom_refn']:
                prop_id = {'full_name': 'P5', 'given_name': 'P3', 'surname': 'P4', 'birth_date': 'P7', 'death_date': 'P8', 'sex': 'P11', 'notes_page': 'P15', 'gedcom_refn': 'P41'}[prop_name]
                claims[prop_id] = [{
                    'mainsnak': {
                        'snaktype': 'value',
                        'property': prop_id,
                        'datavalue': {
                            'value': str(value),
                            'type': 'string'
                        }
                    },
                    'type': 'statement'
                }]
        
        item_data = {'labels': labels, 'claims': claims}
        
        params = {
            'action': 'wbeditentity',
            'new': 'item',
            'data': json.dumps(item_data),
            'format': 'json',
            'token': csrf_token,
            'summary': 'Creating master genealogy individual (from I10000+)',
            'bot': 1
        }
        
        response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params, timeout=60)
        result = response.json()
        
        if 'entity' in result:
            qid = result['entity']['id']
            return qid
        else:
            print(f"      Error creating item: {result}")
            return None
    
    except Exception as e:
        print(f"      Exception creating item: {e}")
        return None

def update_mapping_file(gedcom_id, qid):
    try:
        with open('gedcom_to_qid_mapping.txt', 'a', encoding='utf-8') as f:
            f.write(f"{gedcom_id}\t{qid}\n")
    except Exception as e:
        print(f"Error updating mapping file: {e}")

def main():
    print("Starting master GEDCOM individual creation from @I10000@ onwards...")
    
    individuals = parse_master_gedcom()
    print(f"Parsed {len(individuals)} individuals from master GEDCOM")
    
    # Start from I10000 (after the highest existing I9999)
    start_id = 10000
    started = False
    print(f"Starting from @I{start_id}@ onwards...")
    
    session = create_session()
    if not login_to_wiki(session):
        print("Failed to login. Exiting.")
        return
    print("Successfully logged in!")
    
    csrf_token = get_csrf_token(session)
    
    success_count = 0
    error_count = 0
    
    for gedcom_id, data in individuals.items():
        # Extract numeric ID
        if gedcom_id.startswith('@I') and gedcom_id.endswith('@'):
            try:
                numeric_id = int(gedcom_id[2:-1])
                if not started:
                    if numeric_id >= start_id:
                        started = True
                        print(f"Starting processing at {gedcom_id}")
                    else:
                        continue
            except ValueError:
                continue
        else:
            continue
        
        print(f"\nCreating new individual {gedcom_id}")
        
        try:
            # Filter out empty values
            clean_data = {k: v for k, v in data.items() if v and v.strip()}
            
            if clean_data:
                qid = create_new_individual(session, clean_data, csrf_token)
                if qid:
                    print(f"  Successfully created {qid}")
                    update_mapping_file(gedcom_id, qid)
                    success_count += 1
                else:
                    print(f"  Failed to create individual")
                    error_count += 1
                
                # Rate limiting
                time.sleep(2)
            else:
                print(f"  No data to create individual")
                error_count += 1
        
        except Exception as e:
            print(f"  ERROR processing {gedcom_id}: {e}")
            error_count += 1
    
    print(f"\nCreation complete!")
    print(f"Created: {success_count}")
    print(f"Errors: {error_count}")

if __name__ == '__main__':
    main()