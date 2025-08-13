#!/usr/bin/env python3
import requests
import json
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Master Notes Creator Bot/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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

def load_master_mappings():
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

def parse_gedcom_notes():
    notes_data = {}
    
    with open('new_gedcoms/source gedcoms/master_combined.ged', 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    current_individual = []
    
    for line in lines:
        if line.startswith('0 @I') and line.endswith('@ INDI'):
            if current_individual:
                individual = parse_individual_notes(current_individual)
                if individual['id'] and individual['notes']:
                    notes_data[individual['id']] = individual['notes']
            current_individual = [line]
        elif current_individual:
            if line.startswith('0 ') and not line.endswith('@ INDI'):
                individual = parse_individual_notes(current_individual)
                if individual['id'] and individual['notes']:
                    notes_data[individual['id']] = individual['notes']
                current_individual = []
            else:
                current_individual.append(line)
    
    if current_individual:
        individual = parse_individual_notes(current_individual)
        if individual['id'] and individual['notes']:
            notes_data[individual['id']] = individual['notes']
    
    return notes_data

def parse_individual_notes(lines):
    individual = {'id': '', 'notes': []}
    
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
        elif level == 1 and tag == 'NOTE':
            individual['notes'].append(value)
        elif level == 2 and tag == 'CONT':
            if individual['notes']:
                individual['notes'][-1] += '\n' + value
        elif level == 2 and tag == 'CONC':
            if individual['notes']:
                individual['notes'][-1] += value
    
    return individual

def remove_old_notes_property(session, qid, csrf_token):
    # Get current item data to find P15 claims
    params = {
        'action': 'wbgetentities',
        'ids': qid,
        'format': 'json'
    }
    response = session.get('https://evolutionism.miraheze.org/w/api.php', params=params)
    result = response.json()
    
    if 'entities' not in result or qid not in result['entities']:
        return False
    
    entity = result['entities'][qid]
    claims = entity.get('claims', {})
    
    # Remove all P15 (old notes page) claims
    if 'P15' in claims:
        for claim in claims['P15']:
            claim_id = claim['id']
            remove_params = {
                'action': 'wbremoveclaims',
                'claim': claim_id,
                'token': csrf_token,
                'format': 'json',
                'summary': 'Removing old P15 notes property',
                'bot': 1
            }
            session.post('https://evolutionism.miraheze.org/w/api.php', data=remove_params)
            time.sleep(0.2)
    
    return True

def add_notes_page_property(session, qid, notes_url, csrf_token):
    params = {
        'action': 'wbcreateclaim',
        'entity': qid,
        'property': 'P46',
        'snaktype': 'value',
        'value': json.dumps(notes_url),
        'format': 'json',
        'token': csrf_token,
        'summary': 'Adding notes page URL (P46)',
        'bot': 1
    }
    
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
    return response.json()

def create_or_update_notes_page(session, qid, notes_content, csrf_token):
    page_title = f"Notes:{qid}"
    
    # Create the wiki page content
    wiki_content = f"""== Notes for [[Item:{qid}|{qid}]] ==

{notes_content}

[[Category:GEDCOM Notes Pages]]"""
    
    # Edit the page (creates if doesn't exist, overwrites if it does)
    params = {
        'action': 'edit',
        'title': page_title,
        'text': wiki_content,
        'token': csrf_token,
        'format': 'json',
        'summary': f'Creating/updating notes page for {qid}',
        'bot': 1
    }
    
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
    result = response.json()
    
    return 'edit' in result and result['edit'].get('result') == 'Success'

def main():
    print("Starting master GEDCOM notes pages creation...")
    
    # Load mappings and notes data
    mappings = load_master_mappings()
    notes_data = parse_gedcom_notes()
    
    print(f"Loaded {len(mappings)} individual mappings")
    print(f"Found {len(notes_data)} individuals with notes in GEDCOM")
    
    session = create_session()
    if not login_to_wiki(session):
        print("Failed to login. Exiting.")
        return
    
    csrf_token = get_csrf_token(session)
    
    success_count = 0
    error_count = 0
    processed_count = 0
    
    # Process all individuals with QID mappings
    for gedcom_id, qid in mappings.items():
        processed_count += 1
        print(f"\nProcessing {gedcom_id} -> {qid} ({processed_count}/{len(mappings)})")
        
        try:
            # Step 1: Remove old P15 notes property
            print(f"  Removing old P15 property")
            remove_old_notes_property(session, qid, csrf_token)
            time.sleep(0.5)
            
            # Step 2: Add P46 notes page URL property
            notes_url = f"https://evolutionism.miraheze.org/wiki/Notes:{qid}"
            print(f"  Adding P46 property: {notes_url}")
            result = add_notes_page_property(session, qid, notes_url, csrf_token)
            
            if 'success' not in result:
                print(f"    Error adding P46: {result}")
                error_count += 1
                continue
            
            time.sleep(0.5)
            
            # Step 3: Create/update the notes page
            if gedcom_id in notes_data:
                notes_content = '\n\n'.join(notes_data[gedcom_id])
                print(f"  Creating/updating notes page with content")
            else:
                notes_content = "No notes found in GEDCOM file."
                print(f"  Creating notes page with placeholder content")
            
            page_created = create_or_update_notes_page(session, qid, notes_content, csrf_token)
            
            if page_created:
                print(f"  Successfully created/updated notes page")
                success_count += 1
            else:
                print(f"  Failed to create/update notes page")
                error_count += 1
            
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"  ERROR processing {gedcom_id}: {e}")
            error_count += 1
    
    print(f"\nMaster notes pages creation complete!")
    print(f"Processed: {processed_count}")
    print(f"Success: {success_count}")
    print(f"Errors: {error_count}")

if __name__ == '__main__':
    main()