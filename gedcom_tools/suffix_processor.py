#!/usr/bin/env python3
"""
SUFFIX PROCESSOR FOR MASTER GEDCOM

1. Creates a suffix property in the wikibase
2. Extracts NSFX (suffix) values from master_combined.ged
3. Updates English labels to append suffixes
4. Adds suffix property claims to individuals

Uses existing mappings from gedcom_to_qid_mapping.txt
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
        'User-Agent': 'Suffix Processor Bot/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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

def create_suffix_property(session, csrf_token):
    """Create the suffix property if it doesn't exist"""
    # First check if suffix property already exists
    search_params = {
        'action': 'wbsearchentities',
        'search': 'suffix',
        'language': 'en',
        'type': 'property',
        'format': 'json'
    }
    response = session.get('https://evolutionism.miraheze.org/w/api.php', params=search_params)
    results = response.json().get('search', [])
    
    for result in results:
        if result.get('label', '').lower() == 'suffix':
            print(f"Suffix property already exists: {result['id']}")
            return result['id']
    
    # Create new property
    print("Creating new suffix property...")
    params = {
        'action': 'wbeditentity',
        'new': 'property',
        'data': json.dumps({
            'labels': {'en': {'language': 'en', 'value': 'suffix'}},
            'descriptions': {'en': {'language': 'en', 'value': 'name suffix (Jr., Sr., III, etc.)'}},
            'datatype': 'string'
        }),
        'format': 'json',
        'token': csrf_token,
        'bot': 1
    }
    
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
    result = response.json()
    
    if 'entity' in result:
        property_id = result['entity']['id']
        print(f"Created suffix property: {property_id}")
        return property_id
    else:
        print(f"Error creating suffix property: {result}")
        return None

def load_gedcom_to_qid_mapping():
    """Load the mapping from GEDCOM IDs to QIDs"""
    mapping = {}
    try:
        with open('gedcom_to_qid_mapping.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '\t' in line:
                    gedcom_id, qid = line.split('\t', 1)
                    mapping[gedcom_id] = qid
        print(f"Loaded {len(mapping)} GEDCOM to QID mappings")
    except FileNotFoundError:
        print("gedcom_to_qid_mapping.txt not found")
    return mapping

def extract_suffixes_from_gedcom():
    """Extract individuals with NSFX (suffix) from master_combined.ged"""
    individuals_with_suffixes = {}
    
    with open('new_gedcoms/source gedcoms/master_combined.ged', 'r', encoding='utf-8') as f:
        current_individual = None
        current_name = None
        
        for line in f:
            line = line.strip()
            
            # Start of new individual
            if line.startswith('0 @I') and line.endswith('@ INDI'):
                current_individual = line.split()[1]  # Extract @I12345@
                current_name = None
                
            # Name line
            elif line.startswith('1 NAME ') and current_individual:
                current_name = line[7:]  # Remove "1 NAME "
                
            # Suffix line
            elif line.startswith('2 NSFX ') and current_individual and current_name:
                suffix = line[7:]  # Remove "2 NSFX "
                individuals_with_suffixes[current_individual] = {
                    'name': current_name,
                    'suffix': suffix
                }
                try:
                    print(f"Found suffix: {current_individual}")
                except UnicodeEncodeError:
                    print(f"Found suffix: {current_individual} (Unicode chars)")
    
    print(f"Found {len(individuals_with_suffixes)} individuals with suffixes")
    return individuals_with_suffixes

def get_current_label(session, qid):
    """Get current English label for a QID"""
    params = {
        'action': 'wbgetentities',
        'ids': qid,
        'format': 'json'
    }
    response = session.get('https://evolutionism.miraheze.org/w/api.php', params=params)
    data = response.json()
    
    if 'entities' in data and qid in data['entities']:
        labels = data['entities'][qid].get('labels', {})
        if 'en' in labels:
            return labels['en']['value']
    return None

def update_label(session, qid, new_label, csrf_token):
    """Update English label for a QID"""
    params = {
        'action': 'wbsetlabel',
        'id': qid,
        'language': 'en',
        'value': new_label,
        'format': 'json',
        'token': csrf_token,
        'bot': 1
    }
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
    return response.json()

def add_suffix_claim(session, qid, suffix, suffix_property_id, csrf_token):
    """Add suffix claim to an individual"""
    params = {
        'action': 'wbcreateclaim',
        'entity': qid,
        'property': suffix_property_id,
        'snaktype': 'value',
        'value': json.dumps(suffix),
        'format': 'json',
        'token': csrf_token,
        'bot': 1
    }
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
    return response.json()

def main():
    print("Starting suffix processing...")
    
    # Create session and login
    session = create_session()
    if not login_to_wiki(session):
        print("Failed to login. Exiting.")
        return
    
    csrf_token = get_csrf_token(session)
    
    # Step 1: Create suffix property
    suffix_property_id = create_suffix_property(session, csrf_token)
    if not suffix_property_id:
        print("Failed to create/find suffix property. Exiting.")
        return
    
    time.sleep(1)
    
    # Step 2: Load mappings and extract suffixes
    qid_mapping = load_gedcom_to_qid_mapping()
    individuals_with_suffixes = extract_suffixes_from_gedcom()
    
    # Step 3: Process each individual with suffix
    success_count = 0
    error_count = 0
    
    for gedcom_id, suffix_data in individuals_with_suffixes.items():
        if gedcom_id not in qid_mapping:
            print(f"No QID found for {gedcom_id}")
            error_count += 1
            continue
            
        qid = qid_mapping[gedcom_id]
        name = suffix_data['name']
        suffix = suffix_data['suffix']
        
        try:
            try:
                print(f"Processing {qid}")
            except UnicodeEncodeError:
                print(f"Processing {qid} (Unicode)")
            
            # Get current label
            current_label = get_current_label(session, qid)
            if not current_label:
                print(f"  No current English label for {qid}")
                error_count += 1
                continue
            
            # Update label to include suffix if not already there
            if not current_label.endswith(f" {suffix}"):
                new_label = f"{current_label} {suffix}"
                result = update_label(session, qid, new_label, csrf_token)
                if 'success' in result:
                    print(f"  Updated label successfully")
                else:
                    print(f"  Error updating label: {result}")
                time.sleep(0.5)
            
            # Add suffix property claim
            result = add_suffix_claim(session, qid, suffix, suffix_property_id, csrf_token)
            if 'claim' in result:
                print(f"  Added suffix claim: {suffix}")
                success_count += 1
            else:
                print(f"  Error adding suffix claim: {result}")
                error_count += 1
            
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"Error processing {qid}: {e}")
            error_count += 1
    
    print(f"\nSuffix processing complete!")
    print(f"Successfully processed: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Suffix property ID: {suffix_property_id}")

if __name__ == '__main__':
    main()