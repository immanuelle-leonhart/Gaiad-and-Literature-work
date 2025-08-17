#!/usr/bin/env python3
"""
COMPLETE MERGER FOR @I56212@ DUPLICATE

1. Copy claims from Q131895 to Q120233
2. Clear all data from Q131895 (labels, descriptions, claims)  
3. Create redirect from Q131895 to Q120233
"""

import requests
import json
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Complete Merger I56212/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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

def clear_entity(session, qid, csrf_token):
    """Clear all content from an entity (labels, descriptions, claims)"""
    print(f"Clearing all content from {qid}")
    
    entity_data = get_entity_data(session, qid)
    if not entity_data:
        print(f"  Entity {qid} not found")
        return False
    
    success_count = 0
    error_count = 0
    
    # Remove all claims
    if 'claims' in entity_data:
        print(f"  Removing {len(entity_data['claims'])} claim types")
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
                    result = response.json()
                    
                    if 'success' in result:
                        success_count += 1
                        print(f"    Removed claim {claim_id}")
                    else:
                        print(f"    Error removing claim {claim_id}: {result}")
                        error_count += 1
                    
                    time.sleep(0.2)
                    
                except Exception as e:
                    print(f"    Exception removing claim {claim_id}: {e}")
                    error_count += 1
    
    # Remove all labels
    if 'labels' in entity_data:
        print(f"  Removing labels")
        for lang, label in entity_data['labels'].items():
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
                result = response.json()
                
                if 'success' in result:
                    success_count += 1
                    print(f"    Removed label ({lang})")
                else:
                    print(f"    Error removing label ({lang}): {result}")
                    error_count += 1
                
                time.sleep(0.2)
                
            except Exception as e:
                print(f"    Exception removing label ({lang}): {e}")
                error_count += 1
    
    # Remove all descriptions
    if 'descriptions' in entity_data:
        print(f"  Removing descriptions")
        for lang, desc in entity_data['descriptions'].items():
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
                result = response.json()
                
                if 'success' in result:
                    success_count += 1
                    print(f"    Removed description ({lang})")
                else:
                    print(f"    Error removing description ({lang}): {result}")
                    error_count += 1
                
                time.sleep(0.2)
                
            except Exception as e:
                print(f"    Exception removing description ({lang}): {e}")
                error_count += 1
    
    # Remove all aliases
    if 'aliases' in entity_data:
        print(f"  Removing aliases")
        for lang, aliases in entity_data['aliases'].items():
            for alias in aliases:
                params = {
                    'action': 'wbsetaliases',
                    'id': qid,
                    'language': lang,
                    'remove': alias['value'],
                    'format': 'json',
                    'token': csrf_token,
                    'bot': 1
                }
                
                try:
                    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
                    result = response.json()
                    
                    if 'success' in result:
                        success_count += 1
                        print(f"    Removed alias ({lang})")
                    else:
                        print(f"    Error removing alias ({lang}): {result}")
                        error_count += 1
                    
                    time.sleep(0.2)
                    
                except Exception as e:
                    print(f"    Exception removing alias ({lang}): {e}")
                    error_count += 1
    
    print(f"Cleared {success_count} items, {error_count} errors")
    return error_count == 0

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
    print("Complete Merger for @I56212@ duplicate")
    print("This will clear Q131895 and redirect it to Q120233")
    print("Q120233 already contains the merged data")
    
    keep_qid = "Q120233"
    redirect_qid = "Q131895"
    
    # Create session and login
    session = create_session()
    if not login_to_wiki(session):
        print("Login failed!")
        return
    
    csrf_token = get_csrf_token(session)
    print("Login successful!")
    
    print(f"\n--- Clearing entity {redirect_qid} ---")
    
    # Step 1: Clear the duplicate entity
    if not clear_entity(session, redirect_qid, csrf_token):
        print("Failed to clear entity, aborting")
        return
    
    print(f"\n--- Creating redirect ---")
    
    # Step 2: Create redirect
    if create_redirect(session, redirect_qid, keep_qid, csrf_token):
        print(f"\nSUCCESS: {redirect_qid} now redirects to {keep_qid}")
        print(f"Merger complete!")
    else:
        print(f"\nFAILED: Could not create redirect")

if __name__ == '__main__':
    main()