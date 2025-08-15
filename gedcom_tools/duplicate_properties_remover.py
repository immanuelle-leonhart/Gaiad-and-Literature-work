#!/usr/bin/env python3
"""
DUPLICATE PROPERTIES REMOVER

Goes through database Q1-Q160000 and for each entity that has multiple identical 
property values, removes all but one of the set of identical properties.

This cleans up the database from duplicate relationships and properties that may 
have been added multiple times.
"""

import requests
import json
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Duplicate Properties Remover/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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
    """Get entity data with all claims"""
    params = {
        'action': 'wbgetentities',
        'ids': qid,
        'format': 'json',
        'props': 'claims'
    }
    
    try:
        response = session.get('https://evolutionism.miraheze.org/w/api.php', params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if 'entities' in data and qid in data['entities']:
                return data['entities'][qid]
    except Exception as e:
        print(f"    Error getting entity data: {e}")
    return None

def remove_claim(session, claim_id, csrf_token):
    """Remove a specific claim by ID"""
    params = {
        'action': 'wbremoveclaims',
        'claim': claim_id,
        'format': 'json',
        'token': csrf_token,
        'bot': 1
    }
    
    try:
        response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
        result = response.json()
        if 'success' in result:
            return True, result
        else:
            return False, result
    except Exception as e:
        return False, {'error': str(e)}

def find_duplicate_claims(claims_data):
    """Find duplicate claims in entity data"""
    duplicates = []
    
    for property_id, claims_list in claims_data.items():
        if len(claims_list) <= 1:
            continue
            
        # Group claims by their value
        value_groups = {}
        for claim in claims_list:
            if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
                # Create a string representation of the value for comparison
                value_str = json.dumps(claim['mainsnak']['datavalue'], sort_keys=True)
                if value_str not in value_groups:
                    value_groups[value_str] = []
                value_groups[value_str].append(claim)
        
        # Find groups with more than one claim (duplicates)
        for value_str, claims_group in value_groups.items():
            if len(claims_group) > 1:
                # Keep the first claim, mark others for removal
                claims_to_remove = claims_group[1:]  # Remove all but the first
                for claim in claims_to_remove:
                    if 'id' in claim:
                        duplicates.append({
                            'property': property_id,
                            'claim_id': claim['id'],
                            'value': value_str[:100] + '...' if len(value_str) > 100 else value_str
                        })
    
    return duplicates

def process_entity(session, qid, csrf_token):
    """Process a single entity to remove duplicate properties"""
    entity_data = get_entity_data(session, qid)
    if not entity_data or 'claims' not in entity_data:
        return 0, 0
    
    duplicates = find_duplicate_claims(entity_data['claims'])
    if not duplicates:
        return 0, 0
    
    print(f"  Found {len(duplicates)} duplicate claims in {qid}")
    
    removed_count = 0
    error_count = 0
    
    for duplicate in duplicates:
        success, result = remove_claim(session, duplicate['claim_id'], csrf_token)
        if success:
            removed_count += 1
            print(f"    REMOVED: {duplicate['property']} - {duplicate['value']}")
        else:
            error_count += 1
            print(f"    ERROR removing {duplicate['claim_id']}: {result}")
        
        # Rate limiting
        time.sleep(0.2)
    
    return removed_count, error_count

def main():
    print("Starting Duplicate Properties Remover for Q1-Q160000...")
    
    # Create session and login
    session = create_session()
    if not login_to_wiki(session):
        print("Login failed!")
        return
    
    csrf_token = get_csrf_token(session)
    print("Login successful!")
    
    total_removed = 0
    total_errors = 0
    entities_processed = 0
    entities_with_duplicates = 0
    
    # Process entities Q1 to Q160000
    start_qid = 2001
    end_qid = 160000
    
    print(f"Processing entities Q{start_qid} to Q{end_qid}...")
    
    for qid_num in range(start_qid, end_qid + 1):
        qid = f"Q{qid_num}"
        entities_processed += 1
        
        if entities_processed % 1000 == 0:
            print(f"\n[{entities_processed}/{end_qid}] Processed {entities_processed} entities")
            print(f"  Entities with duplicates: {entities_with_duplicates}")
            print(f"  Total duplicates removed: {total_removed}")
            print(f"  Total errors: {total_errors}")
        
        try:
            removed, errors = process_entity(session, qid, csrf_token)
            if removed > 0:
                entities_with_duplicates += 1
                total_removed += removed
            total_errors += errors
            
            # Rate limiting between entities
            time.sleep(0.1)
            
        except Exception as e:
            print(f"  ERROR processing {qid}: {e}")
            total_errors += 1
            continue
    
    print(f"\nDuplicate Properties Remover complete!")
    print(f"Entities processed: {entities_processed}")
    print(f"Entities with duplicates: {entities_with_duplicates}")
    print(f"Total duplicate properties removed: {total_removed}")
    print(f"Total errors: {total_errors}")

if __name__ == '__main__':
    main()