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
        'User-Agent': 'Chinese GEDCOM Creator Bot/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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
    existing = set()
    try:
        with open('chinese_gedcom_to_qid_mapping.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('@I') and '\t' in line:
                    gedcom_id = line.split('\t')[0]
                    existing.add(gedcom_id)
    except FileNotFoundError:
        pass
    return existing

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

def parse_chinese_gedcom():
    individuals = {}
    
    with open('new_gedcoms/source gedcoms/chinese_genealogy_sample.ged', 'r', encoding='utf-8') as f:
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
        # Create basic item structure
        labels = {}
        if 'full_name' in data:
            labels['en'] = {'language': 'en', 'value': data['full_name']}
        elif 'given_name' in data:
            labels['en'] = {'language': 'en', 'value': data['given_name']}
        
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
        
        # Add other properties
        for prop_name, value in data.items():
            if prop_name == 'full_name':
                claims['P5'] = [{
                    'mainsnak': {
                        'snaktype': 'value',
                        'property': 'P5',
                        'datavalue': {
                            'value': {'text': str(value), 'language': 'en'},
                            'type': 'monolingualtext'
                        }
                    },
                    'type': 'statement'
                }]
            elif prop_name == 'given_name':
                claims['P3'] = [{
                    'mainsnak': {
                        'snaktype': 'value',
                        'property': 'P3',
                        'datavalue': {
                            'value': {'text': str(value), 'language': 'en'},
                            'type': 'monolingualtext'
                        }
                    },
                    'type': 'statement'
                }]
            elif prop_name == 'surname':
                claims['P4'] = [{
                    'mainsnak': {
                        'snaktype': 'value',
                        'property': 'P4',
                        'datavalue': {
                            'value': {'text': str(value), 'language': 'en'},
                            'type': 'monolingualtext'
                        }
                    },
                    'type': 'statement'
                }]
            elif prop_name == 'sex':
                # Sex property expects monolingualtext, not item reference
                sex_text = 'male' if value == 'Q6581097' else 'female'
                claims['P11'] = [{
                    'mainsnak': {
                        'snaktype': 'value',
                        'property': 'P11',
                        'datavalue': {
                            'value': {'text': sex_text, 'language': 'en'},
                            'type': 'monolingualtext'
                        }
                    },
                    'type': 'statement'
                }]
            elif prop_name == 'birth_date':
                claims['P7'] = [{
                    'mainsnak': {
                        'snaktype': 'value',
                        'property': 'P7',
                        'datavalue': {
                            'value': {'text': str(value), 'language': 'en'},
                            'type': 'monolingualtext'
                        }
                    },
                    'type': 'statement'
                }]
            elif prop_name == 'death_date':
                claims['P8'] = [{
                    'mainsnak': {
                        'snaktype': 'value',
                        'property': 'P8',
                        'datavalue': {
                            'value': {'text': str(value), 'language': 'en'},
                            'type': 'monolingualtext'
                        }
                    },
                    'type': 'statement'
                }]
            elif prop_name == 'gedcom_refn':
                claims['P41'] = [{
                    'mainsnak': {
                        'snaktype': 'value',
                        'property': 'P41',
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
            'summary': 'Creating Chinese genealogy individual'
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
        with open('chinese_gedcom_to_qid_mapping.txt', 'a', encoding='utf-8') as f:
            f.write(f"{gedcom_id}\t{qid}\n")
    except Exception as e:
        print(f"Error updating mapping file: {e}")

def main():
    print("Starting Chinese GEDCOM individual creation process...")
    
    existing_mappings = load_existing_mappings()
    print(f"Found {len(existing_mappings)} existing mappings to skip")
    
    individuals = parse_chinese_gedcom()
    print(f"Parsed {len(individuals)} individuals from Chinese GEDCOM")
    
    # Find starting point - highest existing ID + 1
    start_id = 121  # Last was @I120@
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
    skipped_count = 0
    
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
        if gedcom_id in existing_mappings:
            skipped_count += 1
            if skipped_count % 100 == 0:
                print(f"Skipped {skipped_count} existing individuals...")
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
    print(f"Skipped existing: {skipped_count}")

if __name__ == '__main__':
    main()