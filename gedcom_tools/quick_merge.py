#!/usr/bin/env python3
"""
QUICK MERGE TOOL

Usage: python quick_merge.py Q12345 Q67890
Merges Q67890 into Q12345 (always merges to the lowest QID)
"""

import sys
import requests
import json
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Quick Merge Tool/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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
        return True
    
    success_count = 0
    error_count = 0
    
    for property_id, claims in source_entity['claims'].items():
        for claim in claims:
            # Extract the claim value
            if 'datavalue' not in claim['mainsnak']:
                continue
                
            datavalue = claim['mainsnak']['datavalue']
            value = datavalue['value']
            
            # Create the claim on target entity
            params = {
                'action': 'wbcreateclaim',
                'entity': target_qid,
                'property': property_id,
                'snaktype': 'value',
                'value': json.dumps(value),
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
                    print(f"  Error copying {property_id}: {result}")
                    
            except Exception as e:
                error_count += 1
                print(f"  Exception copying {property_id}: {e}")
            
            time.sleep(0.1)
    
    print(f"  Copied {success_count} claims, {error_count} errors")
    return True

def clear_entity(session, qid, csrf_token):
    """Clear all content from entity (labels, descriptions, aliases, claims)"""
    print(f"  Clearing entity {qid}...")
    
    # Get entity data
    entity = get_entity_data(session, qid)
    if not entity:
        return True
    
    # Remove all claims
    if 'claims' in entity:
        for property_id, claims in entity['claims'].items():
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
                    session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
                    time.sleep(0.1)
    
    # Clear labels
    if 'labels' in entity:
        for lang in entity['labels']:
            params = {
                'action': 'wbsetlabel',
                'id': qid,
                'language': lang,
                'value': '',
                'format': 'json',
                'token': csrf_token,
                'bot': 1
            }
            session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
    
    # Clear descriptions  
    if 'descriptions' in entity:
        for lang in entity['descriptions']:
            params = {
                'action': 'wbsetdescription',
                'id': qid,
                'language': lang,
                'value': '',
                'format': 'json',
                'token': csrf_token,
                'bot': 1
            }
            session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
    
    # Clear aliases
    if 'aliases' in entity:
        for lang in entity['aliases']:
            params = {
                'action': 'wbsetaliases',
                'id': qid,
                'language': lang,
                'set': '',
                'format': 'json',
                'token': csrf_token,
                'bot': 1
            }
            session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
    
    return True

def create_redirect(session, source_qid, target_qid, csrf_token):
    """Create redirect from source to target"""
    print(f"  Creating redirect {source_qid} → {target_qid}...")
    
    params = {
        'action': 'wbmergeitems',
        'fromid': source_qid,
        'toid': target_qid,
        'format': 'json',
        'token': csrf_token,
        'bot': 1
    }
    
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params, timeout=60)
    result = response.json()
    
    if 'success' in result:
        print(f"  Successfully created redirect")
        return True
    else:
        print(f"  Failed to create redirect: {result}")
        return False

def merge_entities(qid1, qid2):
    """Merge two entities (always merges to lowest QID)"""
    # Determine merge direction (always merge to lowest QID)
    qnum1 = int(qid1[1:])
    qnum2 = int(qid2[1:])
    
    if qnum1 < qnum2:
        target_qid = qid1
        source_qid = qid2
    else:
        target_qid = qid2
        source_qid = qid1
    
    print(f"Merging {source_qid} → {target_qid}")
    
    # Create session and login
    session = create_session()
    if not login_to_wiki(session):
        print("Failed to login!")
        return False
    
    csrf_token = get_csrf_token(session)
    
    # Copy claims from source to target
    print(f"Copying claims from {source_qid} to {target_qid}...")
    copy_claims(session, source_qid, target_qid, csrf_token)
    
    # Clear source entity
    clear_entity(session, source_qid, csrf_token)
    
    # Create redirect
    if not create_redirect(session, source_qid, target_qid, csrf_token):
        print(f"Redirect failed, entity {source_qid} cleared but not redirected")
    
    print(f"Merge complete: {source_qid} → {target_qid}")
    return True

def main():
    if len(sys.argv) != 3:
        print("Usage: python quick_merge.py Q12345 Q67890")
        print("Merges the higher QID into the lower QID")
        return
    
    qid1 = sys.argv[1].upper()
    qid2 = sys.argv[2].upper()
    
    if not (qid1.startswith('Q') and qid2.startswith('Q')):
        print("Error: Both arguments must be QIDs (e.g., Q12345)")
        return
    
    merge_entities(qid1, qid2)

if __name__ == '__main__':
    main()