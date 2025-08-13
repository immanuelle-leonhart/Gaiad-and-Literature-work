#!/usr/bin/env python3
"""
MASTER ALIASES UPLOADER

Reads the master_multiple_names.csv file and the QID mappings,
then adds all the multiple names as aliases to the corresponding entities.
Strips / characters from names before adding them as aliases.
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
        'User-Agent': 'Master Aliases Uploader Bot/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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

def load_qid_mappings():
    mappings = {}
    try:
        with open('gedcom_to_qid_mapping.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('@I') and '\t' in line:
                    parts = line.strip().split('\t')
                    if len(parts) == 2:
                        mappings[parts[0]] = parts[1]
    except FileNotFoundError:
        print("Error: gedcom_to_qid_mapping.txt not found!")
        return {}
    return mappings

def load_multiple_names():
    multiple_names = {}
    try:
        with open('master_multiple_names.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                gedcom_id = row['GEDCOM_ID']
                primary_name = row['PRIMARY_NAME']
                additional_names = row['ADDITIONAL_NAMES']
                
                # Combine all names
                all_names = [primary_name]
                if additional_names:
                    all_names.extend([name.strip() for name in additional_names.split(';')])
                
                # Strip / characters and remove empty names
                cleaned_names = []
                for name in all_names:
                    cleaned_name = name.replace('/', '').strip()
                    if cleaned_name and cleaned_name not in cleaned_names:  # Avoid duplicates
                        cleaned_names.append(cleaned_name)
                
                multiple_names[gedcom_id] = cleaned_names
    except FileNotFoundError:
        print("Error: master_multiple_names.csv not found!")
        return {}
    return multiple_names

def add_alias(session, qid, language, alias, csrf_token):
    params = {
        'action': 'wbsetaliases',
        'id': qid,
        'language': language,
        'add': alias,
        'format': 'json',
        'token': csrf_token,
        'summary': f'Adding alias from GEDCOM multiple names: {alias}',
        'bot': 1
    }
    
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
    return response.json()

def main():
    print("Starting master aliases uploader...")
    
    # Load data
    qid_mappings = load_qid_mappings()
    multiple_names = load_multiple_names()
    
    print(f"Loaded {len(qid_mappings)} QID mappings")
    print(f"Found {len(multiple_names)} individuals with multiple names")
    
    # Create session and login
    session = create_session()
    if not login_to_wiki(session):
        print("Failed to login. Exiting.")
        return
    
    csrf_token = get_csrf_token(session)
    
    success_count = 0
    error_count = 0
    processed_count = 0
    
    # Process individuals with multiple names
    for gedcom_id, names in multiple_names.items():
        qid = qid_mappings.get(gedcom_id)
        if not qid:
            print(f"No QID found for {gedcom_id}, skipping")
            continue
        
        processed_count += 1
        print(f"\nProcessing {gedcom_id} -> {qid} ({processed_count}/{len(multiple_names)})")
        try:
            print(f"  Names to add as aliases: {', '.join(names)}")
        except UnicodeEncodeError:
            print(f"  Names to add as aliases: [Unicode names - {len(names)} total]")
        
        try:
            # Add each name as an English alias
            for name in names:
                if name:  # Skip empty names
                    print(f"  Adding alias: {name}")
                    result = add_alias(session, qid, 'en', name, csrf_token)
                    
                    if 'success' in result:
                        success_count += 1
                        print(f"    SUCCESS")
                    elif 'error' in result:
                        if 'already' in result['error'].get('info', '').lower():
                            print(f"    SKIPPED (already exists)")
                        else:
                            print(f"    ERROR: {result['error']}")
                            error_count += 1
                    else:
                        print(f"    UNKNOWN RESULT: {result}")
                        error_count += 1
                    
                    time.sleep(0.3)  # Rate limiting between aliases
            
            time.sleep(1)  # Rate limiting between individuals
            
        except Exception as e:
            print(f"  ERROR processing {gedcom_id}: {e}")
            error_count += 1
    
    print(f"\nMaster aliases upload complete!")
    print(f"Processed individuals: {processed_count}")
    print(f"Successful alias additions: {success_count}")
    print(f"Errors: {error_count}")

if __name__ == '__main__':
    main()