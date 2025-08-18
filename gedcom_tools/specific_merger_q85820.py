#!/usr/bin/env python3
"""
SPECIFIC MERGER: Q97505 → Q85820

Merges Q97505 into Q85820 (lowest QID)
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
        'User-Agent': 'Specific Merger Q85820/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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

def copy_claims(session, source_qid, target_qid, csrf_token):
    """Copy all claims from source entity to target entity"""
    print(f"Getting claims from {source_qid}...")
    source_entity = get_entity_data(session, source_qid)
    
    if not source_entity:
        print(f"Could not get data for {source_qid}")
        return False
    
    if 'claims' not in source_entity:
        print(f"No claims found in {source_qid}")
        return True
    
    success_count = 0
    error_count = 0
    
    print(f"Copying claims from {source_qid} to {target_qid}...")
    
    for property_id, claims in source_entity['claims'].items():
        print(f"  Copying {len(claims)} claims for property {property_id}")
        
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
                else:
                    error_count += 1
                    if 'error' in result:
                        print(f"    Error: {result['error']}")
                    
            except Exception as e:
                error_count += 1
                print(f"    Exception: {e}")
            
            time.sleep(0.2)
    
    print(f"Copied {success_count} claims successfully, {error_count} errors")
    return True

def clear_entity_content(session, qid, csrf_token):
    """Clear all content from an entity before redirect"""
    print(f"Clearing content from {qid}...")
    
    entity_data = get_entity_data(session, qid)
    if not entity_data:
        return True
    
    # Remove all claims
    if 'claims' in entity_data:
        print(f"  Removing {len(entity_data['claims'])} properties...")
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
    
    # Remove labels
    if 'labels' in entity_data:
        print(f"  Removing labels...")
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
                session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
            except:
                pass
    
    # Remove descriptions
    if 'descriptions' in entity_data:
        print(f"  Removing descriptions...")
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
                session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
            except:
                pass
    
    # Remove aliases
    if 'aliases' in entity_data:
        print(f"  Removing aliases...")
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
                session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
            except:
                pass
    
    print(f"  Content cleared from {qid}")
    return True

def create_redirect(session, from_qid, to_qid, csrf_token):
    """Create a redirect from one entity to another"""
    print(f"Creating redirect {from_qid} -> {to_qid}...")
    
    params = {
        'action': 'wbmergeitems',
        'fromid': from_qid,
        'toid': to_qid,
        'format': 'json',
        'token': csrf_token,
        'bot': 1
    }
    
    try:
        response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params, timeout=60)
        result = response.json()
        
        if 'success' in result:
            print(f"Successfully created redirect from {from_qid} to {to_qid}")
            return True
        else:
            print(f"Failed to create redirect: {result}")
            return False
            
    except Exception as e:
        print(f"Exception creating redirect: {e}")
        return False

def main():
    print("=== SPECIFIC MERGER: Q97505 -> Q85820 ===")
    print("This will merge Q97505 into Q85820")
    
    # Create session and login
    session = create_session()
    
    print("Logging in...")
    if not login_to_wiki(session):
        print("Failed to login. Exiting.")
        return False
    
    csrf_token = get_csrf_token(session)
    print("Login successful!")
    
    source_qid = "Q97505"
    target_qid = "Q85820"
    
    try:
        # Step 1: Copy all claims from source to target
        if not copy_claims(session, source_qid, target_qid, csrf_token):
            print("Failed to copy claims")
            return False
        
        # Step 2: Clear the source entity
        clear_entity_content(session, source_qid, csrf_token)
        
        # Step 3: Create redirect
        if not create_redirect(session, source_qid, target_qid, csrf_token):
            print(f"Warning: Could not create redirect. {source_qid} has been cleared but not redirected.")
        
        print(f"\n=== MERGE COMPLETE ===")
        print(f"Successfully merged {source_qid} -> {target_qid}")
        return True
        
    except Exception as e:
        print(f"Error during merge: {e}")
        return False

if __name__ == '__main__':
    main()