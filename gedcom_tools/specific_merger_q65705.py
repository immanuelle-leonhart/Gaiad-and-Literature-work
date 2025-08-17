#!/usr/bin/env python3
"""
SPECIFIC MERGER: Q105603 → Q65705

Merges Q105603 into Q65705 (lowest QID)
Based on existing individual_merger.py logic
"""

import requests
import json
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Specific Merger Q65705/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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
    
    response = session.get('https://evolutionism.miraheze.org/w/api.php', params=params, timeout=30)
    data = response.json()
    
    if 'entities' in data and qid in data['entities']:
        entity = data['entities'][qid]
        if 'missing' not in entity:
            return entity
    return None

def copy_claims(session, from_qid, to_qid, csrf_token):
    """Copy all claims from one entity to another"""
    print(f"  Copying claims from {from_qid} to {to_qid}")
    
    from_entity = get_entity_data(session, from_qid)
    if not from_entity or 'claims' not in from_entity:
        print(f"  No claims to copy from {from_qid}")
        return True
    
    for property_id, claims in from_entity['claims'].items():
        for claim in claims:
            try:
                # Create new claim on target entity
                claim_data = {
                    'action': 'wbcreateclaim',
                    'entity': to_qid,
                    'property': property_id,
                    'snaktype': claim['mainsnak']['snaktype'],
                    'token': csrf_token,
                    'format': 'json',
                    'bot': 1
                }
                
                if claim['mainsnak']['snaktype'] == 'value':
                    claim_data['value'] = json.dumps(claim['mainsnak']['datavalue']['value'])
                
                response = session.post('https://evolutionism.miraheze.org/w/api.php', data=claim_data, timeout=30)
                result = response.json()
                
                if 'success' not in result:
                    print(f"    Warning: Failed to copy claim {property_id}: {result}")
                else:
                    print(f"    OK Copied {property_id}")
                    
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"    Error copying claim {property_id}: {e}")
                continue
    
    return True

def find_backlinks(session, qid):
    """Find all entities that reference this QID"""
    print(f"  Finding backlinks to {qid}")
    backlinks = []
    
    # Use Special:WhatLinksHere API approach
    params = {
        'action': 'query',
        'list': 'backlinks',
        'bltitle': f'Item:{qid}',
        'blnamespace': 120,  # Item namespace
        'bllimit': 500,
        'format': 'json'
    }
    
    try:
        response = session.get('https://evolutionism.miraheze.org/w/api.php', params=params, timeout=30)
        data = response.json()
        
        if 'query' in data and 'backlinks' in data['query']:
            for link in data['query']['backlinks']:
                title = link['title']
                if title.startswith('Item:Q'):
                    backlink_qid = title.replace('Item:', '')
                    backlinks.append(backlink_qid)
                    
        print(f"  Found {len(backlinks)} backlinks")
        return backlinks
        
    except Exception as e:
        print(f"  Error finding backlinks: {e}")
        return []

def update_references(session, old_qid, new_qid, csrf_token):
    """Update all references from old_qid to new_qid"""
    print(f"  Updating references from {old_qid} to {new_qid}")
    
    backlinks = find_backlinks(session, old_qid)
    
    for backlink_qid in backlinks:
        try:
            entity = get_entity_data(session, backlink_qid)
            if not entity or 'claims' not in entity:
                continue
                
            updated = False
            for property_id, claims in entity['claims'].items():
                for claim in claims:
                    if (claim['mainsnak']['snaktype'] == 'value' and 
                        'datavalue' in claim['mainsnak'] and
                        claim['mainsnak']['datavalue'].get('value', {}).get('id') == old_qid):
                        
                        # Update this claim to point to new_qid
                        update_data = {
                            'action': 'wbsetclaimvalue',
                            'claim': claim['id'],
                            'snaktype': 'value',
                            'value': json.dumps({'entity-type': 'item', 'id': new_qid}),
                            'token': csrf_token,
                            'format': 'json',
                            'bot': 1
                        }
                        
                        response = session.post('https://evolutionism.miraheze.org/w/api.php', data=update_data, timeout=30)
                        result = response.json()
                        
                        if 'success' in result:
                            print(f"    OK Updated reference in {backlink_qid}")
                            updated = True
                        else:
                            print(f"    Warning: Failed to update reference in {backlink_qid}: {result}")
                            
                        time.sleep(0.5)
                        
            if not updated:
                print(f"    No references found in {backlink_qid}")
                
        except Exception as e:
            print(f"    Error updating references in {backlink_qid}: {e}")
            continue
    
    return True

def clear_entity(session, qid, csrf_token):
    """Clear all content from an entity"""
    print(f"  Clearing entity {qid}")
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
    
    # Remove aliases
    if 'aliases' in entity_data:
        for lang in entity_data['aliases']:
            params = {
                'action': 'wbsetaliases',
                'id': qid,
                'language': lang,
                'set': '',  # Empty string removes all aliases
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

def create_redirect(session, old_qid, new_qid, csrf_token):
    """Create redirect from old entity to new entity"""
    print(f"  Creating redirect from {old_qid} to {new_qid}")
    
    try:
        redirect_data = {
            'action': 'wbcreateredirect',
            'from': old_qid,
            'to': new_qid,
            'token': csrf_token,
            'format': 'json',
            'bot': 1
        }
        
        response = session.post('https://evolutionism.miraheze.org/w/api.php', data=redirect_data, timeout=30)
        result = response.json()
        
        if 'success' in result:
            print(f"  OK Created redirect from {old_qid} to {new_qid}")
            return True
        else:
            print(f"  Failed to create redirect: {result}")
            return False
            
    except Exception as e:
        print(f"  Error creating redirect: {e}")
        return False

def merge_entities(session, keep_qid, redirect_qid, csrf_token):
    """Merge two entities: copy claims, update backlinks, clear entity, create redirect"""
    print(f"Merging {redirect_qid} into {keep_qid}")
    
    # Step 1: Copy all claims
    if not copy_claims(session, redirect_qid, keep_qid, csrf_token):
        print(f"  Failed to copy claims, aborting merge")
        return False
    
    # Step 2: Update all references
    if not update_references(session, redirect_qid, keep_qid, csrf_token):
        print(f"  Warning: Some references may not have been updated")
    
    # Step 3: Clear the entity before creating redirect
    if not clear_entity(session, redirect_qid, csrf_token):
        print(f"  Failed to clear entity {redirect_qid}")
        return False
    
    # Step 4: Create redirect
    if not create_redirect(session, redirect_qid, keep_qid, csrf_token):
        print(f"  Failed to create redirect")
        return False
    
    print(f"OK Successfully merged {redirect_qid} into {keep_qid}")
    return True

def main():
    print("Specific Merger: Q105603 -> Q65705")
    print("This will merge Q105603 into Q65705")
    
    session = create_session()
    
    if not login_to_wiki(session):
        print("Failed to login")
        return
    
    print("OK Login successful")
    csrf_token = get_csrf_token(session)
    print("OK Got CSRF token")
    
    # Merge Q105603 into Q65705
    merge_success = merge_entities(session, 'Q65705', 'Q105603', csrf_token)
    if merge_success:
        print("OK Successfully merged Q105603 into Q65705")
        print("\nSUCCESS Merge completed successfully!")
        print("Q105603 -> Q65705 (claims copied)")
        print("Q65705 (kept as primary)")
    else:
        print("ERROR Failed to merge Q105603 into Q65705")

if __name__ == '__main__':
    main()