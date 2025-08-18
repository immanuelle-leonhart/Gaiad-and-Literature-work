#!/usr/bin/env python3
"""
HEBREW NAMES PROCESSOR

Reads Hebrew_Names.csv and for each QID:
1. Gets current English label
2. Adds current English label as an English alias
3. Sets the new label from column 3 as the English label
"""

import requests
import json
import time
import csv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Hebrew Names Processor/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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

def get_entity_data(session, qid):
    """Get entity data including current labels"""
    params = {
        'action': 'wbgetentities',
        'ids': qid,
        'format': 'json'
    }
    
    response = session.get('https://evolutionism.miraheze.org/w/api.php', params=params, timeout=30)
    data = response.json()
    
    if 'entities' in data and qid in data['entities']:
        entity = data['entities'][qid]
        if 'missing' not in entity:
            return entity
    return None

def add_alias(session, qid, language, alias, csrf_token):
    """Add an alias to an entity"""
    params = {
        'action': 'wbsetaliases',
        'id': qid,
        'language': language,
        'add': alias,
        'format': 'json',
        'token': csrf_token,
        'summary': f'Moving current label to alias: {alias}',
        'bot': 1
    }
    
    try:
        response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params, timeout=30)
        return response.json()
    except Exception as e:
        return {'error': {'info': str(e)}}

def set_label(session, qid, language, label, csrf_token):
    """Set the label for an entity"""
    params = {
        'action': 'wbsetlabel',
        'id': qid,
        'language': language,
        'value': label,
        'format': 'json',
        'token': csrf_token,
        'summary': f'Setting new English label: {label}',
        'bot': 1
    }
    
    try:
        response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params, timeout=30)
        return response.json()
    except Exception as e:
        return {'error': {'info': str(e)}}

def process_hebrew_names():
    """Process the Hebrew_Names.csv file"""
    # Read the CSV file
    updates = []
    try:
        with open('Hebrew_Names.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                qid = row.get('id', '').strip()
                new_label = row.get('label_en', '').strip()
                
                if qid and new_label and qid.startswith('Q'):
                    updates.append((qid, new_label))
    except FileNotFoundError:
        print("Error: Hebrew_Names.csv not found!")
        return []
    
    return updates

def main():
    print("Hebrew Names Processor")
    print("Processing Hebrew_Names.csv...")
    
    # Load updates from CSV
    updates = process_hebrew_names()
    print(f"Found {len(updates)} entities to update")
    
    if not updates:
        print("No updates to process!")
        return
    
    # Create session and login
    session = create_session()
    if not login_to_wiki(session):
        print("Failed to login. Exiting.")
        return
    
    csrf_token = get_csrf_token(session)
    print("Login successful!")
    
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    for i, (qid, new_label) in enumerate(updates):
        print(f"\n[{i+1}/{len(updates)}] Processing {qid}")
        try:
            print(f"  New label: '{new_label}'")
        except UnicodeEncodeError:
            print(f"  New label: [Unicode label - {len(new_label)} chars]")
        
        # Get current entity data
        entity = get_entity_data(session, qid)
        if not entity:
            print(f"  ERROR: Could not get entity data for {qid}")
            error_count += 1
            continue
        
        # Get current English label
        current_label = None
        if 'labels' in entity and 'en' in entity['labels']:
            current_label = entity['labels']['en']['value']
            try:
                print(f"  Current label: '{current_label}'")
            except UnicodeEncodeError:
                print(f"  Current label: [Unicode label - {len(current_label)} chars]")
        else:
            print(f"  No current English label")
        
        # Check if new label is different from current
        if current_label == new_label:
            print(f"  SKIPPED: New label same as current")
            skipped_count += 1
            continue
        
        try:
            # Step 1: Add current label as alias (if it exists)
            if current_label:
                print(f"  Adding current label as alias...")
                alias_result = add_alias(session, qid, 'en', current_label, csrf_token)
                
                if 'success' in alias_result:
                    print(f"    Alias added successfully")
                elif 'error' in alias_result:
                    if 'already' in alias_result['error'].get('info', '').lower():
                        print(f"    Alias already exists")
                    else:
                        print(f"    Error adding alias: {alias_result['error']}")
                else:
                    print(f"    Unknown alias result: {alias_result}")
                
                time.sleep(0.2)
            
            # Step 2: Set new label
            print(f"  Setting new label...")
            label_result = set_label(session, qid, 'en', new_label, csrf_token)
            
            if 'success' in label_result:
                print(f"    Label set successfully")
                success_count += 1
            elif 'error' in label_result:
                print(f"    Error setting label: {label_result['error']}")
                error_count += 1
            else:
                print(f"    Unknown label result: {label_result}")
                error_count += 1
                
        except Exception as e:
            print(f"  Exception processing {qid}: {e}")
            error_count += 1
        
        time.sleep(0.5)  # Rate limiting
        
        # Progress update every 50 entities
        if (i + 1) % 50 == 0:
            print(f"\n--- Progress: {i+1}/{len(updates)} processed, {success_count} successful, {error_count} errors, {skipped_count} skipped ---")
    
    print(f"\n=== HEBREW NAMES PROCESSING COMPLETE ===")
    print(f"Total entities: {len(updates)}")
    print(f"Successful updates: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Skipped (same label): {skipped_count}")

if __name__ == '__main__':
    main()