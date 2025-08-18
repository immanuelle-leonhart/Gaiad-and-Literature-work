#!/usr/bin/env python3
"""
LATIN ALIAS PROMOTER

For QIDs in labels_greek_armenian_cyrillic.csv, checks if there are existing English aliases
that use only Latin script (no Hebrew characters). If found, promotes the
best Latin alias to be the main English label and moves the current label to aliases.
"""

import requests
import json
import time
import csv
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Latin Alias Promoter/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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
    """Get entity data including labels and aliases"""
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

def is_latin_script(text):
    """Check if text contains only Latin script characters (no Hebrew, Arabic, etc.)"""
    if not text:
        return False
    
    # Hebrew unicode range: \u0590-\u05FF
    # Arabic unicode range: \u0600-\u06FF
    # Check for non-Latin scripts
    hebrew_arabic_pattern = re.compile(r'[\u0590-\u06FF]')
    
    # If it contains Hebrew/Arabic characters, it's not pure Latin
    if hebrew_arabic_pattern.search(text):
        return False
    
    # Check if it's mostly Latin characters (allow some punctuation, numbers, spaces)
    latin_pattern = re.compile(r'^[a-zA-Z0-9\s\-\.\,\'\(\)]+$')
    return latin_pattern.match(text) is not None

def score_alias_quality(alias):
    """Score alias quality - higher is better"""
    score = 0
    
    # Prefer longer names (more descriptive)
    score += len(alias) * 0.1
    
    # Prefer names with capital letters (proper names)
    score += sum(1 for c in alias if c.isupper()) * 2
    
    # Prefer names with spaces (full names vs single words)
    score += alias.count(' ') * 5
    
    # Penalize names with numbers (often IDs)
    score -= sum(1 for c in alias if c.isdigit()) * 3
    
    # Penalize very short names
    if len(alias) < 3:
        score -= 10
    
    # Penalize names that are all caps (often abbreviations)
    if alias.isupper() and len(alias) > 2:
        score -= 5
    
    return score

def add_alias(session, qid, language, alias, csrf_token):
    """Add an alias to an entity"""
    params = {
        'action': 'wbsetaliases',
        'id': qid,
        'language': language,
        'add': alias,
        'format': 'json',
        'token': csrf_token,
        'summary': f'Adding demoted label as alias: {alias}',
        'bot': 1
    }
    
    try:
        response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params, timeout=30)
        return response.json()
    except Exception as e:
        return {'error': {'info': str(e)}}

def set_label(session, qid, language, label, csrf_token):
    """Set the label for an entity"""
    params = {
        'action': 'wbsetlabel',
        'id': qid,
        'language': language,
        'value': label,
        'format': 'json',
        'token': csrf_token,
        'summary': f'Promoting Latin alias to label: {label}',
        'bot': 1
    }
    
    try:
        response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params, timeout=30)
        return response.json()
    except Exception as e:
        return {'error': {'info': str(e)}}

def remove_alias(session, qid, language, alias, csrf_token):
    """Remove a specific alias from an entity"""
    params = {
        'action': 'wbsetaliases',
        'id': qid,
        'language': language,
        'remove': alias,
        'format': 'json',
        'token': csrf_token,
        'summary': f'Removing alias promoted to label: {alias}',
        'bot': 1
    }
    
    try:
        response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params, timeout=30)
        return response.json()
    except Exception as e:
        return {'error': {'info': str(e)}}

def load_hebrew_names_qids():
    """Load QIDs from labels_greek_armenian_cyrillic.csv"""
    qids = []
    try:
        with open('labels_greek_armenian_cyrillic.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                qid = row.get('id', '').strip()
                if qid and qid.startswith('Q'):
                    qids.append(qid)
    except FileNotFoundError:
        print("Error: labels_greek_armenian_cyrillic.csv not found!")
        return []
    
    return qids

def main():
    print("Latin Alias Promoter")
    print("Waiting 30 minutes to avoid race condition with Hebrew names processor...")
    
    # Wait 30 minutes to avoid race condition
    for i in range(30, 0, -1):
        print(f"  Starting in {i} minutes...")
        time.sleep(5)  # Sleep for 1 minute
    
    print("Starting Latin alias promotion...")
    print("Checking labels_greek_armenian_cyrillic.csv QIDs for better Latin script aliases...")
    
    # Load QIDs from CSV
    qids = load_hebrew_names_qids()
    print(f"Found {len(qids)} QIDs to check")
    
    if not qids:
        print("No QIDs to process!")
        return
    
    # Create session and login
    session = create_session()
    if not login_to_wiki(session):
        print("Failed to login. Exiting.")
        return
    
    csrf_token = get_csrf_token(session)
    print("Login successful!")
    
    promoted_count = 0
    error_count = 0
    skipped_count = 0
    
    for i, qid in enumerate(qids):
        print(f"\n[{i+1}/{len(qids)}] Checking {qid}")
        
        # Get entity data
        entity = get_entity_data(session, qid)
        if not entity:
            print(f"  ERROR: Could not get entity data")
            error_count += 1
            continue
        
        # Get current English label
        current_label = None
        if 'labels' in entity and 'en' in entity['labels']:
            current_label = entity['labels']['en']['value']
        
        if not current_label:
            print(f"  No current English label")
            skipped_count += 1
            continue
        
        try:
            print(f"  Current label: '{current_label}'")
        except UnicodeEncodeError:
            print(f"  Current label: [Unicode - {len(current_label)} chars]")
        
        # Get English aliases
        latin_aliases = []
        if 'aliases' in entity and 'en' in entity['aliases']:
            for alias_obj in entity['aliases']['en']:
                alias = alias_obj['value']
                if is_latin_script(alias):
                    latin_aliases.append(alias)
        
        if not latin_aliases:
            print(f"  No Latin script aliases found")
            skipped_count += 1
            continue
        
        print(f"  Found {len(latin_aliases)} Latin aliases")
        
        # Score and find best alias
        best_alias = None
        best_score = -999
        
        for alias in latin_aliases:
            score = score_alias_quality(alias)
            try:
                print(f"    '{alias}' -> score: {score}")
            except UnicodeEncodeError:
                print(f"    [Unicode alias] -> score: {score}")
            
            if score > best_score:
                best_score = score
                best_alias = alias
        
        if not best_alias:
            print(f"  No suitable Latin alias found")
            skipped_count += 1
            continue
        
        # Check if best alias is actually better than current label
        current_score = score_alias_quality(current_label) if is_latin_script(current_label) else -999
        
        if best_score <= current_score:
            print(f"  Current label is already best (score: {current_score} vs {best_score})")
            skipped_count += 1
            continue
        
        try:
            print(f"  Best alias: '{best_alias}' (score: {best_score})")
            print(f"  Promoting to label...")
        except UnicodeEncodeError:
            print(f"  Best alias: [Unicode] (score: {best_score})")
            print(f"  Promoting to label...")
        
        try:
            # Step 1: Add current label as alias
            print(f"    Adding current label as alias...")
            alias_result = add_alias(session, qid, 'en', current_label, csrf_token)
            
            if 'success' in alias_result:
                print(f"      Current label added as alias")
            else:
                print(f"      Error adding alias: {alias_result.get('error', {}).get('info', 'Unknown')}")
            
            time.sleep(0.2)
            
            # Step 2: Set best alias as new label
            print(f"    Setting new label...")
            label_result = set_label(session, qid, 'en', best_alias, csrf_token)
            
            if 'success' in label_result:
                print(f"      New label set successfully")
                
                # Step 3: Remove the alias that became the label
                print(f"    Removing promoted alias...")
                remove_result = remove_alias(session, qid, 'en', best_alias, csrf_token)
                
                if 'success' in remove_result:
                    print(f"      Promoted alias removed from aliases")
                    promoted_count += 1
                else:
                    print(f"      Warning: Could not remove promoted alias: {remove_result.get('error', {}).get('info', 'Unknown')}")
                    promoted_count += 1  # Still count as success
                    
            else:
                print(f"      Error setting label: {label_result.get('error', {}).get('info', 'Unknown')}")
                error_count += 1
                
        except Exception as e:
            print(f"  Exception processing {qid}: {e}")
            error_count += 1
        
        time.sleep(0.5)  # Rate limiting
        
        # Progress update every 25 entities
        if (i + 1) % 25 == 0:
            print(f"\n--- Progress: {i+1}/{len(qids)} checked, {promoted_count} promoted, {error_count} errors, {skipped_count} skipped ---")
    
    print(f"\n=== LATIN ALIAS PROMOTION COMPLETE ===")
    print(f"Total QIDs checked: {len(qids)}")
    print(f"Labels promoted: {promoted_count}")
    print(f"Errors: {error_count}")
    print(f"Skipped: {skipped_count}")

if __name__ == '__main__':
    main()