#!/usr/bin/env python3
"""
GEDCOM ALIASES UPLOADER

Parses the master_combined.ged file directly to find individuals with multiple names
and adds all names as aliases to their corresponding Wikibase entities.
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
        'User-Agent': 'GEDCOM Aliases Uploader/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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
    """Load GEDCOM ID to QID mappings"""
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

def parse_gedcom_for_multiple_names():
    """Parse master_combined.ged to find individuals with multiple NAME entries"""
    multiple_names = {}
    
    try:
        with open('new_gedcoms/source gedcoms/master_combined.ged', 'r', encoding='utf-8') as f:
            current_individual = None
            names = []
            
            for line in f:
                line = line.strip()
                
                # Start of new individual
                if line.startswith('0 @I') and line.endswith('@ INDI'):
                    # Save previous individual if it had multiple names
                    if current_individual and len(names) > 1:
                        multiple_names[current_individual] = names
                    
                    # Start new individual
                    current_individual = line.split()[1]  # Extract @I12345@
                    names = []
                
                # Found a NAME entry
                elif line.startswith('1 NAME ') and current_individual:
                    name = line[7:]  # Remove "1 NAME "
                    # Clean the name - remove // and extra spaces
                    cleaned_name = name.replace('//', '').replace('/', '').strip()
                    if cleaned_name and cleaned_name not in names:
                        names.append(cleaned_name)
                
                # End of individual (start of new record)
                elif line.startswith('0 ') and not line.endswith('@ INDI') and current_individual:
                    # Save current individual if it had multiple names
                    if len(names) > 1:
                        multiple_names[current_individual] = names
                    current_individual = None
                    names = []
            
            # Handle last individual
            if current_individual and len(names) > 1:
                multiple_names[current_individual] = names
                
    except FileNotFoundError:
        print("Error: master_combined.ged not found!")
        return {}
    
    return multiple_names

def add_alias(session, qid, language, alias, csrf_token):
    """Add an alias to a Wikibase entity"""
    params = {
        'action': 'wbsetaliases',
        'id': qid,
        'language': language,
        'add': alias,
        'format': 'json',
        'token': csrf_token,
        'summary': f'Adding alias from GEDCOM: {alias}',
        'bot': 1
    }
    
    try:
        response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params, timeout=30)
        return response.json()
    except Exception as e:
        print(f"    Error adding alias: {e}")
        return {'error': {'info': str(e)}}

def main():
    print("GEDCOM Aliases Uploader")
    print("Parsing master_combined.ged for individuals with multiple names...")
    
    # Load data
    qid_mappings = load_qid_mappings()
    multiple_names = parse_gedcom_for_multiple_names()
    
    print(f"Loaded {len(qid_mappings)} QID mappings")
    print(f"Found {len(multiple_names)} individuals with multiple names")
    
    if not multiple_names:
        print("No individuals with multiple names found!")
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
    processed_count = 0
    skipped_count = 0
    
    # Process individuals with multiple names
    for gedcom_id, names in multiple_names.items():
        qid = qid_mappings.get(gedcom_id)
        if not qid:
            print(f"No QID found for {gedcom_id}, skipping")
            skipped_count += 1
            continue
        
        processed_count += 1
        print(f"\n[{processed_count}/{len(multiple_names)}] Processing {gedcom_id} -> {qid}")
        
        try:
            print(f"  Names: {', '.join(names)}")
        except UnicodeEncodeError:
            print(f"  Names: [Unicode names - {len(names)} total]")
        
        # Add each name as an English alias
        for name in names:
            if name:  # Skip empty names
                try:
                    print(f"  Adding alias: '{name}'")
                except UnicodeEncodeError:
                    print(f"  Adding alias: [Unicode name]")
                
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
        
        # Progress update every 100 individuals
        if processed_count % 100 == 0:
            print(f"\n--- Progress: {processed_count}/{len(multiple_names)} processed, {success_count} aliases added, {error_count} errors ---")
    
    print(f"\n=== GEDCOM ALIASES UPLOAD COMPLETE ===")
    print(f"Individuals processed: {processed_count}")
    print(f"Individuals skipped (no QID): {skipped_count}")
    print(f"Successful alias additions: {success_count}")
    print(f"Errors: {error_count}")

if __name__ == '__main__':
    main()