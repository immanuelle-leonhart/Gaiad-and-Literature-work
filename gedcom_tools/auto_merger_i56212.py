#!/usr/bin/env python3
"""
AUTO MERGER FOR @I56212@ DUPLICATE

Automatically merge Q131895 into Q120233 and create redirect
"""

import requests
import json
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Auto Merger I56212/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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

def copy_claims(session, from_qid, to_qid, csrf_token):
    """Copy all claims from one entity to another"""
    print(f"Copying claims from {from_qid} to {to_qid}")
    
    source_data = get_entity_data(session, from_qid)
    if not source_data or 'claims' not in source_data:
        print(f"  No claims found in {from_qid}")
        return True
    
    success_count = 0
    error_count = 0
    
    for property_id, claims in source_data['claims'].items():
        print(f"  Processing property {property_id}")
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
                        print(f"    SUCCESS: Added {property_id}")
                    elif 'error' in result and 'already has' in str(result.get('error', '')):
                        print(f"    SKIP: {property_id} already exists")
                    else:
                        print(f"    ERROR: {property_id} - {result}")
                        error_count += 1
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"    EXCEPTION: {property_id} - {e}")
                    error_count += 1
    
    print(f"Copied {success_count} claims, {error_count} errors")
    return error_count == 0

def find_backlinks(session, target_qid):
    """Find all entities that reference the target QID"""
    print(f"Finding backlinks to {target_qid}")
    
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
        
        print(f"Found {len(backlinks)} backlinks")
        return backlinks
        
    except Exception as e:
        print(f"Error finding backlinks: {e}")
        return []

def update_references(session, old_qid, new_qid, csrf_token):
    """Update all references from old_qid to new_qid"""
    print(f"Updating references from {old_qid} to {new_qid}")
    
    # Find all entities that reference old_qid
    backlinks = find_backlinks(session, old_qid)
    
    if not backlinks:
        print("  No backlinks found")
        return True
    
    updated_count = 0
    error_count = 0
    
    for referring_qid in backlinks:
        print(f"  Updating references in {referring_qid}")
        
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
                        
                        print(f"    Found reference in {property_id}")
                        
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
    
    print(f"Updated {updated_count} references, {error_count} errors")
    return True

def create_redirect(session, from_qid, to_qid, csrf_token):
    """Create a redirect from one entity to another"""
    print(f"Creating redirect from {from_qid} to {to_qid}")
    
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
            print(f"  Successfully created redirect")
            return True
        else:
            print(f"  Error creating redirect: {result}")
            return False
    except Exception as e:
        print(f"  Exception creating redirect: {e}")
        return False

def main():
    print("Auto Merger for @I56212@ duplicate")
    print("KEEP: Q120233 (Geoffroy Grenonat)")
    print("REMOVE: Q131895 (Geoffroy Grenonat) -> will be redirected")
    
    keep_qid = "Q120233"
    redirect_qid = "Q131895"
    
    # Create session and login
    session = create_session()
    if not login_to_wiki(session):
        print("Login failed!")
        return
    
    csrf_token = get_csrf_token(session)
    print("Login successful!")
    
    print(f"\n--- Starting automatic merge process ---")
    
    # Step 1: Copy claims
    if not copy_claims(session, redirect_qid, keep_qid, csrf_token):
        print("Failed to copy claims, aborting")
        return
    
    # Step 2: Update references
    update_references(session, redirect_qid, keep_qid, csrf_token)
    
    # Step 3: Create redirect
    if create_redirect(session, redirect_qid, keep_qid, csrf_token):
        print(f"\nSUCCESS: Merged {redirect_qid} into {keep_qid} with redirect")
        print(f"Q131895 now redirects to Q120233")
        print(f"All backlinks have been updated")
    else:
        print(f"\nFAILED: Could not create redirect")

if __name__ == '__main__':
    main()