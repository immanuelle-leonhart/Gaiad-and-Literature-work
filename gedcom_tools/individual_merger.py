#!/usr/bin/env python3
"""
INDIVIDUAL MERGER SCRIPT

This script merges duplicate individuals in the Wikibase by:
1. Finding individuals with identical names or strong similarity indicators
2. Merging their claims/properties into a single entity
3. Updating all references to point to the kept entity
4. Deleting the duplicate entity

WARNING: This is a destructive operation that should be used carefully!
"""

import requests
import json
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from difflib import SequenceMatcher

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Individual Merger/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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

def get_entity_label(session, qid):
    """Get the English label for an entity"""
    entity_data = get_entity_data(session, qid)
    if entity_data and 'labels' in entity_data and 'en' in entity_data['labels']:
        return entity_data['labels']['en']['value']
    return None

def similarity(a, b):
    """Calculate similarity between two strings"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def find_potential_duplicates(session, start_qid=1, end_qid=1000):
    """Find potential duplicate individuals based on name similarity"""
    print(f"Scanning Q{start_qid} to Q{end_qid} for potential duplicates...")
    
    entities = {}
    duplicates = []
    
    for i in range(start_qid, end_qid + 1):
        qid = f"Q{i}"
        label = get_entity_label(session, qid)
        
        if label:
            # Check for exact matches
            for existing_qid, existing_label in entities.items():
                if label == existing_label:
                    duplicates.append((existing_qid, qid, 1.0, "exact_match"))
                elif similarity(label, existing_label) > 0.9:  # Very high similarity
                    duplicates.append((existing_qid, qid, similarity(label, existing_label), "high_similarity"))
            
            entities[qid] = label
        
        if i % 100 == 0:
            print(f"  Processed Q{i}")
        
        time.sleep(0.1)  # Rate limiting
    
    return duplicates

def copy_claims(session, from_qid, to_qid, csrf_token):
    """Copy all claims from one entity to another"""
    print(f"  Copying claims from {from_qid} to {to_qid}")
    
    source_data = get_entity_data(session, from_qid)
    if not source_data or 'claims' not in source_data:
        return True
    
    success_count = 0
    error_count = 0
    
    for property_id, claims in source_data['claims'].items():
        for claim in claims:
            # Extract the claim value
            if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
                datavalue = claim['mainsnak']['datavalue']
                
                # Create the claim on target entity
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
                        pass  # Claim already exists, skip
                    else:
                        print(f"    Error copying {property_id}: {result}")
                        error_count += 1
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"    Exception copying {property_id}: {e}")
                    error_count += 1
    
    print(f"    Copied {success_count} claims, {error_count} errors")
    return error_count == 0

def find_backlinks(session, target_qid):
    """Find all entities that reference the target QID"""
    print(f"  Finding backlinks to {target_qid}")
    
    backlinks = []
    
    # Use Special:WhatLinksHere equivalent API
    params = {
        'action': 'query',
        'list': 'backlinks',
        'bltitle': f'Item:{target_qid}',
        'blnamespace': 120,  # Item namespace
        'bllimit': 'max',
        'format': 'json'
    }
    
    try:
        response = session.get('https://evolutionism.miraheze.org/w/api.php', params=params)
        result = response.json()
        
        if 'query' in result and 'backlinks' in result['query']:
            for link in result['query']['backlinks']:
                # Extract QID from title (e.g., "Item:Q123" -> "Q123")
                if link['title'].startswith('Item:'):
                    qid = link['title'][5:]  # Remove "Item:" prefix
                    backlinks.append(qid)
        
        print(f"    Found {len(backlinks)} backlinks")
        return backlinks
        
    except Exception as e:
        print(f"    Error finding backlinks: {e}")
        return []

def update_references(session, old_qid, new_qid, csrf_token):
    """Update all references from old_qid to new_qid across the entire database"""
    print(f"  Updating references from {old_qid} to {new_qid}")
    
    # Find all entities that reference old_qid
    backlinks = find_backlinks(session, old_qid)
    
    updated_count = 0
    error_count = 0
    
    for referring_qid in backlinks:
        print(f"    Updating references in {referring_qid}")
        
        # Get the entity data
        entity_data = get_entity_data(session, referring_qid)
        if not entity_data or 'claims' not in entity_data:
            continue
        
        # Look through all claims for references to old_qid
        for property_id, claims in entity_data['claims'].items():
            for claim in claims:
                if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
                    datavalue = claim['mainsnak']['datavalue']
                    
                    # Check if this claim references the old QID
                    if (datavalue.get('type') == 'wikibase-entityid' and 
                        datavalue.get('value', {}).get('id') == old_qid):
                        
                        # Remove the old claim
                        claim_id = claim['id']
                        remove_params = {
                            'action': 'wbremoveclaims',
                            'claim': claim_id,
                            'format': 'json',
                            'token': csrf_token,
                            'bot': 1
                        }
                        
                        try:
                            response = session.post('https://evolutionism.miraheze.org/w/api.php', data=remove_params)
                            remove_result = response.json()
                            
                            if 'success' in remove_result:
                                # Add the new claim with updated reference
                                add_params = {
                                    'action': 'wbcreateclaim',
                                    'entity': referring_qid,
                                    'property': property_id,
                                    'snaktype': 'value',
                                    'value': json.dumps({'entity-type': 'item', 'numeric-id': int(new_qid[1:])}),
                                    'format': 'json',
                                    'token': csrf_token,
                                    'bot': 1
                                }
                                
                                response = session.post('https://evolutionism.miraheze.org/w/api.php', data=add_params)
                                add_result = response.json()
                                
                                if 'success' in add_result:
                                    updated_count += 1
                                    print(f"      Updated {property_id} reference")
                                else:
                                    print(f"      Error adding new reference: {add_result}")
                                    error_count += 1
                            else:
                                print(f"      Error removing old reference: {remove_result}")
                                error_count += 1
                            
                            time.sleep(0.5)  # Rate limiting
                            
                        except Exception as e:
                            print(f"      Exception updating reference: {e}")
                            error_count += 1
    
    print(f"    Updated {updated_count} references, {error_count} errors")
    return error_count == 0

def create_redirect(session, from_qid, to_qid, csrf_token):
    """Create a redirect from one entity to another"""
    print(f"  Creating redirect from {from_qid} to {to_qid}")
    
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
        
        if 'success' in result:
            return True
        else:
            print(f"    Error creating redirect from {from_qid} to {to_qid}: {result}")
            return False
    except Exception as e:
        print(f"    Exception creating redirect from {from_qid} to {to_qid}: {e}")
        return False

def merge_entities(session, keep_qid, redirect_qid, csrf_token):
    """Merge two entities: copy claims from redirect_qid to keep_qid, update all backlinks, then create redirect"""
    print(f"Merging {redirect_qid} into {keep_qid}")
    
    # Step 1: Copy all claims from redirect_qid to keep_qid
    if not copy_claims(session, redirect_qid, keep_qid, csrf_token):
        print(f"  Failed to copy claims, aborting merge")
        return False
    
    # Step 2: Update all references from redirect_qid to keep_qid
    if not update_references(session, redirect_qid, keep_qid, csrf_token):
        print(f"  Failed to update some references, but continuing...")
        # Continue anyway - some references may have been updated
    
    # Step 3: Create a redirect from redirect_qid to keep_qid
    if not create_redirect(session, redirect_qid, keep_qid, csrf_token):
        print(f"  Failed to create redirect from {redirect_qid} to {keep_qid}")
        return False
    
    print(f"  Successfully merged {redirect_qid} into {keep_qid} with redirect")
    return True

def main():
    print("Individual Merger Script")
    print("WARNING: This script will permanently merge entities with redirects!")
    print("This will:")
    print("  1. Copy claims from duplicate to target entity")
    print("  2. Update all backlinks to point to target entity") 
    print("  3. Create redirect from duplicate to target entity")
    print("Make sure you have backups before proceeding.")
    
    # Get range from user
    start_qid = int(input("Enter start QID number (e.g., 1): "))
    end_qid = int(input("Enter end QID number (e.g., 1000): "))
    
    # Create session and login
    session = create_session()
    if not login_to_wiki(session):
        print("Login failed!")
        return
    
    csrf_token = get_csrf_token(session)
    print("Login successful!")
    
    # Find duplicates
    duplicates = find_potential_duplicates(session, start_qid, end_qid)
    
    if not duplicates:
        print("No duplicates found!")
        return
    
    print(f"\nFound {len(duplicates)} potential duplicates:")
    for i, (qid1, qid2, score, reason) in enumerate(duplicates):
        label1 = get_entity_label(session, qid1)
        label2 = get_entity_label(session, qid2)
        print(f"{i+1}. {qid1} ({label1}) <-> {qid2} ({label2}) - {score:.3f} ({reason})")
    
    # Process each duplicate
    for i, (qid1, qid2, score, reason) in enumerate(duplicates):
        label1 = get_entity_label(session, qid1)
        label2 = get_entity_label(session, qid2)
        
        print(f"\n--- Duplicate {i+1}/{len(duplicates)} ---")
        print(f"{qid1}: {label1}")
        print(f"{qid2}: {label2}")
        print(f"Similarity: {score:.3f} ({reason})")
        
        choice = input("Merge? (y/n/q): ").lower()
        
        if choice == 'q':
            break
        elif choice == 'y':
            # Ask which to keep
            keep_choice = input(f"Keep which? (1 for {qid1}, 2 for {qid2}): ")
            
            if keep_choice == '1':
                keep_qid, redirect_qid = qid1, qid2
            elif keep_choice == '2':
                keep_qid, redirect_qid = qid2, qid1
            else:
                print("Invalid choice, skipping")
                continue
            
            # Perform merge
            if merge_entities(session, keep_qid, redirect_qid, csrf_token):
                print(f"Successfully merged {redirect_qid} into {keep_qid} with redirect")
            else:
                print(f"Failed to merge {redirect_qid} into {keep_qid}")
        else:
            print("Skipped")
    
    print("\nMerging complete!")

if __name__ == '__main__':
    main()