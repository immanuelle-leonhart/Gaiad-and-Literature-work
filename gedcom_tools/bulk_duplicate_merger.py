#!/usr/bin/env python3
"""
BULK DUPLICATE MERGER

Process duplicate_mappings_report.txt and merge all REMOVE QIDs into their corresponding KEEP QIDs
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
        'User-Agent': 'Bulk Duplicate Merger/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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

def parse_duplicates_file():
    """Parse the duplicate_mappings_report.txt file"""
    duplicates = {}
    current_gedcom_id = None
    keep_qid = None
    
    with open('duplicate_mappings_report.txt', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Check for GEDCOM ID header (e.g., "@I10002@:")
            if line.startswith('@I') and line.endswith('@:'):
                current_gedcom_id = line[:-1]  # Remove the colon
                keep_qid = None
                duplicates[current_gedcom_id] = {'keep': None, 'remove': []}
            
            # Check for KEEP line
            elif line.startswith('KEEP:') and current_gedcom_id:
                match = re.search(r'-> (Q\d+)', line)
                if match:
                    keep_qid = match.group(1)
                    duplicates[current_gedcom_id]['keep'] = keep_qid
            
            # Check for REMOVE line
            elif line.startswith('REMOVE:') and current_gedcom_id:
                match = re.search(r'-> (Q\d+)', line)
                if match:
                    remove_qid = match.group(1)
                    duplicates[current_gedcom_id]['remove'].append(remove_qid)
    
    return duplicates

def get_entity_data(session, qid):
    """Get all data for an entity"""
    params = {
        'action': 'wbgetentities',
        'ids': qid,
        'format': 'json'
    }
    response = session.get('https://evolutionism.miraheze.org/w/api.php', params=params)
    data = response.json()
    
    if 'entities' in data and qid in data['entities']:
        return data['entities'][qid]
    return None

def copy_claims(session, from_qid, to_qid, csrf_token):
    """Copy all claims from one entity to another"""
    source_data = get_entity_data(session, from_qid)
    if not source_data or 'claims' not in source_data:
        return True
    
    success_count = 0
    
    for property_id, claims in source_data['claims'].items():
        for claim in claims:
            if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
                datavalue = claim['mainsnak']['datavalue']
                
                params = {
                    'action': 'wbcreateclaim',
                    'entity': to_qid,
                    'property': property_id,
                    'snaktype': 'value',
                    'value': json.dumps(datavalue['value']),
                    'format': 'json',
                    'token': csrf_token,
                    'bot': 1
                }
                
                try:
                    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
                    result = response.json()
                    
                    if 'success' in result:
                        success_count += 1
                    elif 'error' in result and 'already has' in str(result.get('error', '')):
                        pass  # Already exists, skip
                    
                    time.sleep(0.3)
                    
                except Exception as e:
                    print(f"      Error copying {property_id}: {e}")
    
    return success_count

def clear_entity(session, qid, csrf_token):
    """Clear all content from an entity"""
    entity_data = get_entity_data(session, qid)
    if not entity_data:
        return False
    
    # Remove all claims
    if 'claims' in entity_data:
        for property_id, claims in entity_data['claims'].items():
            for claim in claims:
                claim_id = claim['id']
                params = {
                    'action': 'wbremoveclaims',
                    'claim': claim_id,
                    'format': 'json',
                    'token': csrf_token,
                    'bot': 1
                }
                
                try:
                    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
                    time.sleep(0.2)
                except Exception:
                    pass
    
    # Remove labels
    if 'labels' in entity_data:
        for lang in entity_data['labels']:
            params = {
                'action': 'wbsetlabel',
                'id': qid,
                'language': lang,
                'value': '',
                'format': 'json',
                'token': csrf_token,
                'bot': 1
            }
            try:
                response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
                time.sleep(0.2)
            except Exception:
                pass
    
    # Remove descriptions
    if 'descriptions' in entity_data:
        for lang in entity_data['descriptions']:
            params = {
                'action': 'wbsetdescription',
                'id': qid,
                'language': lang,
                'value': '',
                'format': 'json',
                'token': csrf_token,
                'bot': 1
            }
            try:
                response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
                time.sleep(0.2)
            except Exception:
                pass
    
    return True

def create_redirect(session, from_qid, to_qid, csrf_token):
    """Create a redirect from one entity to another"""
    params = {
        'action': 'wbcreateredirect',
        'from': from_qid,
        'to': to_qid,
        'format': 'json',
        'token': csrf_token,
        'bot': 1
    }
    
    try:
        response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
        result = response.json()
        return 'success' in result
    except Exception:
        return False

def merge_duplicate(session, keep_qid, remove_qid, csrf_token):
    """Merge a single duplicate pair"""
    print(f"  Merging {remove_qid} -> {keep_qid}")
    
    # Step 1: Copy claims
    copied = copy_claims(session, remove_qid, keep_qid, csrf_token)
    
    # Step 2: Clear entity
    if not clear_entity(session, remove_qid, csrf_token):
        print(f"    Failed to clear {remove_qid}")
        return False
    
    # Step 3: Create redirect
    if not create_redirect(session, remove_qid, keep_qid, csrf_token):
        print(f"    Failed to create redirect {remove_qid} -> {keep_qid}")
        return False
    
    print(f"    SUCCESS: {copied} claims copied, redirect created")
    return True

def main():
    print("Bulk Duplicate Merger")
    print("Processing duplicate_mappings_report.txt")
    
    # Parse duplicates file
    print("Parsing duplicates file...")
    duplicates = parse_duplicates_file()
    
    total_gedcom_ids = len(duplicates)
    total_removals = sum(len(data['remove']) for data in duplicates.values())
    
    print(f"Found {total_gedcom_ids} GEDCOM IDs with {total_removals} duplicates to merge")
    
    # Create session and login
    session = create_session()
    if not login_to_wiki(session):
        print("Login failed!")
        return
    
    csrf_token = get_csrf_token(session)
    print("Login successful!")
    
    # Process each duplicate group
    processed = 0
    successful = 0
    failed = 0
    
    for gedcom_id, data in duplicates.items():
        keep_qid = data['keep']
        remove_qids = data['remove']
        
        if not keep_qid or not remove_qids:
            continue
        
        processed += 1
        print(f"\n[{processed}/{total_gedcom_ids}] Processing {gedcom_id}: {keep_qid} <- {len(remove_qids)} duplicates")
        
        group_success = 0
        group_failed = 0
        
        for remove_qid in remove_qids:
            if merge_duplicate(session, keep_qid, remove_qid, csrf_token):
                group_success += 1
                successful += 1
            else:
                group_failed += 1
                failed += 1
        
        print(f"  Group result: {group_success} successful, {group_failed} failed")
        
        # Progress update every 10 groups
        if processed % 10 == 0:
            print(f"\n--- Progress: {processed}/{total_gedcom_ids} groups, {successful} successful merges, {failed} failed ---")
    
    print(f"\n=== BULK MERGE COMPLETE ===")
    print(f"Processed: {processed} GEDCOM ID groups")
    print(f"Successful merges: {successful}")
    print(f"Failed merges: {failed}")
    print(f"Success rate: {successful/(successful+failed)*100:.1f}%" if successful+failed > 0 else "No merges attempted")

if __name__ == '__main__':
    main()