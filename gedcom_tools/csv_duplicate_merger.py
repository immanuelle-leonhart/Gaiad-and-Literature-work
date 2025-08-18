#!/usr/bin/env python3
"""
CSV DUPLICATE MERGER

Processes qid_correspondence.csv to find and merge duplicate entities 
that share the same external identifiers (Geni IDs, UUIDs, Wikidata QIDs).
Based on the duplicate checker analysis.
"""

import requests
import json
import time
import csv
from collections import defaultdict
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'CSV Duplicate Merger/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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

def find_csv_duplicates():
    """Find duplicate groups from CSV based on shared external IDs"""
    print("Analyzing qid_correspondence.csv for duplicates...")
    
    # Track by external identifiers
    wikidata_groups = defaultdict(list)
    geni_groups = defaultdict(list) 
    uuid_groups = defaultdict(list)
    
    try:
        with open('qid_correspondence.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                evolutionism_qid = row.get('evolutionism_qid', '').strip()
                wikidata_qid = row.get('wikidata_qid', '').strip()
                geni_id = row.get('geni_id', '').strip()
                uuid = row.get('uuid', '').strip()
                en_label = row.get('en_label', '').strip()
                
                if not evolutionism_qid:
                    continue
                
                # Group by Wikidata QID
                if wikidata_qid:
                    wikidata_groups[wikidata_qid].append((evolutionism_qid, en_label))
                
                # Group by Geni ID (skip Private entries - they're expected duplicates)
                if geni_id and 'Private' not in en_label:
                    geni_groups[geni_id].append((evolutionism_qid, en_label))
                
                # Group by UUID
                if uuid:
                    uuid_groups[uuid].append((evolutionism_qid, en_label))
    
    except FileNotFoundError:
        print("ERROR: qid_correspondence.csv not found!")
        return []
    
    # Find groups with duplicates and create merge pairs
    merge_pairs = []
    
    # Process each type of duplicate
    for group_type, groups in [('wikidata', wikidata_groups), ('geni', geni_groups), ('uuid', uuid_groups)]:
        for identifier, entities in groups.items():
            if len(entities) > 1:
                # Sort by QID number to find target (lowest QID)
                qid_data = [(qid, int(qid[1:]), label) for qid, label in entities]
                qid_data.sort(key=lambda x: x[1])
                
                target_qid = qid_data[0][0]
                target_label = qid_data[0][2]
                
                # Create merge pairs for all others -> target
                for qid, _, label in qid_data[1:]:
                    merge_pairs.append({
                        'type': group_type,
                        'identifier': identifier,
                        'target': target_qid,
                        'target_label': target_label,
                        'source': qid,
                        'source_label': label
                    })
    
    return merge_pairs

def get_entity_data(session, qid):
    """Get entity data"""
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

def copy_claims(session, source_qid, target_qid, csrf_token):
    """Copy all claims from source to target entity"""
    source_entity = get_entity_data(session, source_qid)
    if not source_entity or 'claims' not in source_entity:
        return 0
    
    success_count = 0
    
    for property_id, claims in source_entity['claims'].items():
        for claim in claims:
            if 'datavalue' not in claim['mainsnak']:
                continue
                
            datavalue = claim['mainsnak']['datavalue']
            
            # Handle different value types
            if datavalue['type'] == 'wikibase-entityid':
                value = datavalue['value']['id']
            elif datavalue['type'] == 'string':
                value = datavalue['value']
            elif datavalue['type'] == 'time':
                value = json.dumps(datavalue['value'])
            elif datavalue['type'] == 'monolingualtext':
                value = json.dumps(datavalue['value'])
            else:
                value = json.dumps(datavalue['value'])
            
            params = {
                'action': 'wbcreateclaim',
                'entity': target_qid,
                'property': property_id,
                'snaktype': 'value',
                'value': value,
                'format': 'json',
                'token': csrf_token,
                'bot': 1
            }
            
            try:
                response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params, timeout=30)
                result = response.json()
                
                if 'success' in result:
                    success_count += 1
                    
            except Exception as e:
                pass  # Continue with other claims
            
            time.sleep(0.1)
    
    return success_count

def clear_entity_content(session, qid, csrf_token):
    """Clear all content from an entity before redirect"""
    entity_data = get_entity_data(session, qid)
    if not entity_data:
        return True
    
    # Remove all claims
    if 'claims' in entity_data:
        for property_id, claims in entity_data['claims'].items():
            for claim in claims:
                claim_id = claim.get('id')
                if claim_id:
                    params = {
                        'action': 'wbremoveclaims',
                        'claim': claim_id,
                        'format': 'json',
                        'token': csrf_token,
                        'bot': 1
                    }
                    try:
                        session.post('https://evolutionism.miraheze.org/w/api.php', data=params, timeout=30)
                        time.sleep(0.1)
                    except:
                        pass
    
    # Clear labels, descriptions, aliases
    for data_type in ['labels', 'descriptions', 'aliases']:
        if data_type in entity_data:
            for lang in entity_data[data_type]:
                if data_type == 'aliases':
                    params = {
                        'action': 'wbsetaliases',
                        'id': qid,
                        'language': lang,
                        'set': '',
                        'format': 'json',
                        'token': csrf_token,
                        'bot': 1
                    }
                elif data_type == 'labels':
                    params = {
                        'action': 'wbsetlabel',
                        'id': qid,
                        'language': lang,
                        'value': '',
                        'format': 'json',
                        'token': csrf_token,
                        'bot': 1
                    }
                else:  # descriptions
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
                    session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
                except:
                    pass
    
    return True

def create_redirect(session, source_qid, target_qid, csrf_token):
    """Create redirect from source to target"""
    params = {
        'action': 'wbmergeitems',
        'fromid': source_qid,
        'toid': target_qid,
        'format': 'json',
        'token': csrf_token,
        'bot': 1
    }
    
    try:
        response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params, timeout=60)
        result = response.json()
        return 'success' in result
    except Exception as e:
        return False

def perform_merge(session, merge_pair, csrf_token):
    """Perform a single merge operation"""
    source_qid = merge_pair['source']
    target_qid = merge_pair['target']
    merge_type = merge_pair['type']
    identifier = merge_pair['identifier']
    
    try:
        source_label = merge_pair['source_label']
        target_label = merge_pair['target_label']
        print(f"  {merge_type.upper()} {identifier}: {source_qid} '{source_label}' -> {target_qid} '{target_label}'")
    except UnicodeEncodeError:
        print(f"  {merge_type.upper()} {identifier}: {source_qid} -> {target_qid} [Unicode labels]")
    
    try:
        # Step 1: Copy claims from source to target
        copied_claims = copy_claims(session, source_qid, target_qid, csrf_token)
        
        # Step 2: Clear source entity
        clear_entity_content(session, source_qid, csrf_token)
        
        # Step 3: Create redirect
        if create_redirect(session, source_qid, target_qid, csrf_token):
            print(f"    SUCCESS: {copied_claims} claims copied, redirect created")
            return True
        else:
            print(f"    WARNING: Claims copied but redirect failed")
            return False
            
    except Exception as e:
        print(f"    ERROR: {e}")
        return False

def main():
    print("=" * 60)
    print("CSV DUPLICATE MERGER")
    print("=" * 60)
    
    # Find duplicate pairs from CSV
    merge_pairs = find_csv_duplicates()
    print(f"Found {len(merge_pairs)} duplicate pairs to merge")
    
    if not merge_pairs:
        print("No duplicates found to merge!")
        return
    
    # Show summary by type
    by_type = {}
    for pair in merge_pairs:
        by_type[pair['type']] = by_type.get(pair['type'], 0) + 1
    
    for merge_type, count in by_type.items():
        print(f"  {merge_type.capitalize()} duplicates: {count}")
    
    print("\nStarting merges...")
    
    # Create session and login
    session = create_session()
    if not login_to_wiki(session):
        print("Failed to login. Exiting.")
        return
    
    csrf_token = get_csrf_token(session)
    print("Login successful!")
    
    successful_merges = 0
    failed_merges = 0
    
    for i, merge_pair in enumerate(merge_pairs):
        print(f"\n[{i+1}/{len(merge_pairs)}] Processing merge...")
        
        if perform_merge(session, merge_pair, csrf_token):
            successful_merges += 1
        else:
            failed_merges += 1
        
        time.sleep(1)  # Rate limiting
        
        # Progress update every 10 merges
        if (i + 1) % 10 == 0:
            print(f"\n--- Progress: {i+1}/{len(merge_pairs)} processed, {successful_merges} successful, {failed_merges} failed ---")
    
    print(f"\n" + "=" * 60)
    print("CSV DUPLICATE MERGE COMPLETE")
    print(f"Total merges attempted: {len(merge_pairs)}")
    print(f"Successful merges: {successful_merges}")
    print(f"Failed merges: {failed_merges}")
    print(f"Success rate: {successful_merges/(successful_merges+failed_merges)*100:.1f}%" if successful_merges+failed_merges > 0 else "0%")
    print("=" * 60)

if __name__ == '__main__':
    main()