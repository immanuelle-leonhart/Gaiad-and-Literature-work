#!/usr/bin/env python3
"""
Create wiki pages and P46 links for substantial notes only.
Works similar to the aliases uploader - reads from substantial_notes_analysis.csv
and creates targeted notes pages for meaningful content only.
"""

import requests
import json
import time
import csv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Substantial Notes Creator/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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

def create_notes_wiki_page(session, qid, notes_content, csrf_token):
    """Create a wiki page for the substantial notes."""
    page_title = f"Notes:{qid}"
    
    # Create the wiki page content with better formatting
    wiki_content = f"""== Substantial Notes for [[Item:{qid}|{qid}]] ==

{notes_content}

[[Category:Substantial GEDCOM Notes]]
[[Category:GEDCOM Notes Pages]]"""
    
    # Edit the page (creates if doesn't exist, overwrites if it does)
    params = {
        'action': 'edit',
        'title': page_title,
        'text': wiki_content,
        'summary': f'Creating substantial notes page for {qid}',
        'token': csrf_token,
        'format': 'json',
        'bot': 1
    }
    
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
    result = response.json()
    
    return 'edit' in result and result['edit'].get('result') == 'Success'

def remove_old_notes_property(session, qid, csrf_token):
    """Remove old P15 notes property if it exists."""
    # Get current claims
    params = {
        'action': 'wbgetentities',
        'ids': qid,
        'format': 'json'
    }
    response = session.get('https://evolutionism.miraheze.org/w/api.php', params=params)
    data = response.json()
    
    if 'entities' not in data or qid not in data['entities']:
        return True
    
    entity = data['entities'][qid]
    if 'claims' not in entity or 'P15' not in entity['claims']:
        return True
    
    # Remove all P15 claims
    for claim in entity['claims']['P15']:
        if 'id' in claim:
            claim_id = claim['id']
            remove_params = {
                'action': 'wbremoveclaims',
                'claim': claim_id,
                'token': csrf_token,
                'format': 'json',
                'summary': 'Removing old P15 notes property for substantial notes upgrade',
                'bot': 1
            }
            session.post('https://evolutionism.miraheze.org/w/api.php', data=remove_params)
            time.sleep(0.2)
    
    return True

def add_notes_page_property(session, qid, notes_url, csrf_token):
    """Add P46 property linking to the notes page."""
    params = {
        'action': 'wbcreateclaim',
        'entity': qid,
        'property': 'P46',
        'snaktype': 'value',
        'value': json.dumps(notes_url),
        'format': 'json',
        'token': csrf_token,
        'summary': 'Adding substantial notes page URL (P46)',
        'bot': 1
    }
    
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
    return response.json()

def load_substantial_notes():
    """Load the substantial notes from CSV file."""
    notes_data = []
    try:
        # Increase CSV field size limit for large notes
        csv.field_size_limit(1000000)  # 1MB limit
        with open('substantial_notes_analysis.csv', 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['qid']:  # Only process entries that have QIDs
                    notes_data.append({
                        'gedcom_id': row['gedcom_id'],
                        'qid': row['qid'],
                        'line_count': int(row['line_count']),
                        'char_count': int(row['char_count']),
                        'full_note': row['full_note']
                    })
    except FileNotFoundError:
        print("Error: substantial_notes_analysis.csv not found. Please run long_notes_analyzer.py first.")
        return []
    
    return notes_data

def main():
    print("Starting substantial notes creator...")
    
    # Load substantial notes data
    notes_data = load_substantial_notes()
    if not notes_data:
        return
    
    print(f"Loaded {len(notes_data)} substantial notes entries with QIDs")
    
    session = create_session()
    if not login_to_wiki(session):
        print("Failed to login. Exiting.")
        return
    
    csrf_token = get_csrf_token(session)
    
    success_count = 0
    error_count = 0
    
    for i, note_data in enumerate(notes_data, 1):
        qid = note_data['qid']
        gedcom_id = note_data['gedcom_id']
        notes_content = note_data['full_note']
        line_count = note_data['line_count']
        
        print(f"\n[{i}/{len(notes_data)}] Processing {gedcom_id} -> {qid} ({line_count} lines)")
        
        try:
            # Step 1: Remove old P15 notes property
            print(f"  Removing old P15 property")
            remove_old_notes_property(session, qid, csrf_token)
            time.sleep(0.5)
            
            # Step 2: Create the substantial notes wiki page
            print(f"  Creating substantial notes wiki page")
            if create_notes_wiki_page(session, qid, notes_content, csrf_token):
                print(f"    ✓ Wiki page created successfully")
                time.sleep(0.5)
                
                # Step 3: Add P46 property linking to the notes page
                notes_url = f"https://evolutionism.miraheze.org/wiki/Notes:{qid}"
                print(f"  Adding P46 property: {notes_url}")
                result = add_notes_page_property(session, qid, notes_url, csrf_token)
                
                if 'success' in result:
                    print(f"    ✓ P46 property added successfully")
                    success_count += 1
                else:
                    print(f"    ✗ Error adding P46: {result}")
                    error_count += 1
            else:
                print(f"    ✗ Failed to create wiki page")
                error_count += 1
                
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"  ✗ Exception: {e}")
            error_count += 1
            continue
        
        # Progress update every 50 items
        if i % 50 == 0:
            print(f"\n--- Progress Update ---")
            print(f"Processed: {i}/{len(notes_data)}")
            print(f"Success: {success_count}")
            print(f"Errors: {error_count}")
            print(f"Success rate: {success_count/(success_count+error_count)*100:.1f}%")
    
    print("\n=== FINAL RESULTS ===")
    print(f"Total processed: {len(notes_data)}")
    print(f"Success: {success_count}")
    print(f"Errors: {error_count}")
    if success_count + error_count > 0:
        print(f"Success rate: {success_count/(success_count+error_count)*100:.1f}%")

if __name__ == '__main__':
    main()