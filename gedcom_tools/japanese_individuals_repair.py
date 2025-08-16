#!/usr/bin/env python3
"""
JAPANESE INDIVIDUALS REPAIR SCRIPT

This script processes Japanese GEDCOM individuals that may be missing QIDs and repairs their data:
1. Adds Sex (P11) property as monolingual text
2. Takes REFN and adds it as Wikidata ID (P44)
3. Adds QID as "Described at url" (P45) with https://wikidata.org/wiki/QID
4. Fetches labels and descriptions from Wikidata
5. Copies English label to alias before replacing it with Wikidata data

Uses correct property IDs and wbcreateclaim API pattern from working scripts.
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
        'User-Agent': 'Japanese Individuals Repair/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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

def load_japanese_mappings():
    """Load Japanese GEDCOM to QID mappings"""
    mappings = {}
    try:
        with open('japanese_gedcom_to_qid_mapping.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '\t' in line and line.startswith('@I'):
                    parts = line.split('\t')
                    if len(parts) == 2:
                        gedcom_id, qid = parts
                        mappings[gedcom_id] = qid
        print(f"Loaded {len(mappings)} Japanese GEDCOM mappings")
        return mappings
    except FileNotFoundError:
        print("Error: japanese_gedcom_to_qid_mapping.txt not found")
        return {}

def parse_japanese_gedcom():
    """Parse Japanese GEDCOM individuals"""
    individuals = {}
    try:
        with open('new_gedcoms/source gedcoms/japan_genealogy_sample.ged', 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        current_record = []
        record_type = None
        
        for line in lines:
            if line.startswith('0 @I') and line.endswith('@ INDI'):
                # Process previous individual
                if current_record and record_type == 'INDI':
                    individual = parse_individual_record(current_record)
                    if individual and individual['id']:
                        individuals[individual['id']] = individual
                
                current_record = [line]
                record_type = 'INDI'
            elif current_record and record_type == 'INDI':
                if line.startswith('0 ') and not line.endswith('@ INDI'):
                    # End of current individual
                    individual = parse_individual_record(current_record)
                    if individual and individual['id']:
                        individuals[individual['id']] = individual
                    current_record = []
                    record_type = None
                else:
                    current_record.append(line)
        
        # Handle last individual
        if current_record and record_type == 'INDI':
            individual = parse_individual_record(current_record)
            if individual and individual['id']:
                individuals[individual['id']] = individual
                
    except FileNotFoundError:
        print("Error: japan_genealogy_sample.ged not found")
        return {}
    except Exception as e:
        print(f"Error parsing Japanese GEDCOM: {e}")
        return {}
    
    print(f"Parsed {len(individuals)} Japanese individuals from GEDCOM")
    return individuals

def parse_individual_record(lines):
    """Parse a single individual record"""
    individual = {
        'id': '',
        'sex': '',
        'refn': '',
        'names': [],
        'birth_date': '',
        'death_date': ''
    }
    
    for line in lines:
        line = line.strip()
        if line.startswith('0 @I') and line.endswith('@ INDI'):
            parts = line.split(' ', 2)
            if len(parts) >= 2:
                individual['id'] = parts[1]
        elif line.startswith('1 SEX '):
            individual['sex'] = line[6:].strip()
        elif line.startswith('1 REFN '):
            individual['refn'] = line[7:].strip()
        elif line.startswith('1 NAME '):
            individual['names'].append(line[7:].strip())
        elif line.startswith('1 BIRT'):
            # Look for date in next lines
            pass
        elif line.startswith('2 DATE ') and 'BIRT' in str(lines):
            individual['birth_date'] = line[7:].strip()
        elif line.startswith('1 DEAT'):
            pass
        elif line.startswith('2 DATE ') and 'DEAT' in str(lines):
            individual['death_date'] = line[7:].strip()
    
    return individual

def get_entity_data(session, qid):
    """Get current entity data from Wikibase"""
    params = {
        'action': 'wbgetentities',
        'ids': qid,
        'format': 'json'
    }
    
    response = session.get('https://evolutionism.miraheze.org/w/api.php', params=params)
    if response.status_code == 200:
        data = response.json()
        if 'entities' in data and qid in data['entities']:
            return data['entities'][qid]
    return None

def get_wikidata_info(wikidata_qid):
    """Fetch labels and descriptions from Wikidata"""
    try:
        wikidata_url = f"https://www.wikidata.org/w/api.php"
        params = {
            'action': 'wbgetentities',
            'ids': wikidata_qid,
            'format': 'json',
            'props': 'labels|descriptions'
        }
        
        response = requests.get(wikidata_url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'entities' in data and wikidata_qid in data['entities']:
                entity = data['entities'][wikidata_qid]
                return {
                    'labels': entity.get('labels', {}),
                    'descriptions': entity.get('descriptions', {})
                }
    except Exception as e:
        print(f"    Warning: Could not fetch Wikidata info for {wikidata_qid}: {e}")
    return None

def add_property_claim(session, qid, property_id, value, value_type='string', csrf_token=None):
    """Add a property claim using wbcreateclaim"""
    if not csrf_token:
        csrf_token = get_csrf_token(session)
    
    if value_type == 'string':
        claim_value = json.dumps(value)
    elif value_type == 'monolingualtext':
        claim_value = json.dumps({'text': value, 'language': 'en'})
    elif value_type == 'url':
        claim_value = json.dumps(value)
    else:
        claim_value = json.dumps(value)
    
    params = {
        'action': 'wbcreateclaim',
        'entity': qid,
        'property': property_id,
        'snaktype': 'value',
        'value': claim_value,
        'format': 'json',
        'token': csrf_token,
        'bot': 1
    }
    
    try:
        response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
        result = response.json()
        if 'claim' in result:
            return True, result
        else:
            return False, result
    except Exception as e:
        return False, {'error': str(e)}

def update_entity_labels_descriptions(session, qid, wikidata_info, csrf_token=None):
    """Update entity: add all labels and descriptions from Wikidata in all languages"""
    if not csrf_token:
        csrf_token = get_csrf_token(session)
    
    # Get current entity data
    entity_data = get_entity_data(session, qid)
    if not entity_data:
        return False, "Could not get entity data"
    
    # Prepare update data with all languages
    entity_update = {
        'labels': {},
        'descriptions': {},
        'aliases': {}
    }
    
    # Add all labels from Wikidata
    if 'labels' in wikidata_info:
        for lang_code, label_data in wikidata_info['labels'].items():
            if 'value' in label_data:
                entity_update['labels'][lang_code] = {
                    'language': lang_code,
                    'value': label_data['value']
                }
                
                # For English, move current label to alias if different
                if lang_code == 'en':
                    current_aliases = entity_data.get('aliases', {}).get('en', [])
                    current_label = entity_data.get('labels', {}).get('en', {}).get('value', '')
                    alias_values = [alias['value'] for alias in current_aliases]
                    
                    entity_update['aliases']['en'] = []
                    
                    # Add current label as alias if it exists and is different
                    if current_label and current_label not in alias_values and current_label != label_data['value']:
                        entity_update['aliases']['en'].append({'language': 'en', 'value': current_label})
                    
                    # Add all existing aliases back
                    for alias in current_aliases:
                        if alias['value'] not in [label_data['value'], current_label]:
                            entity_update['aliases']['en'].append(alias)
    
    # Add all descriptions from Wikidata
    if 'descriptions' in wikidata_info:
        for lang_code, desc_data in wikidata_info['descriptions'].items():
            if 'value' in desc_data:
                entity_update['descriptions'][lang_code] = {
                    'language': lang_code,
                    'value': desc_data['value']
                }
    
    params = {
        'action': 'wbeditentity',
        'id': qid,
        'token': csrf_token,
        'format': 'json',
        'bot': 1,
        'data': json.dumps(entity_update)
    }
    
    try:
        response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
        result = response.json()
        if 'success' in result:
            return True, result
        else:
            return False, result
    except Exception as e:
        return False, {'error': str(e)}

def repair_japanese_individual(session, individual, qid, csrf_token):
    """Repair a single Japanese individual"""
    print(f"  Processing {individual['id']} -> {qid}")
    success_count = 0
    error_count = 0
    
    # 1. Add Sex (P11) if available
    if individual['sex']:
        sex_map = {'M': 'male', 'F': 'female'}
        sex_value = sex_map.get(individual['sex'], individual['sex'].lower())
        success, result = add_property_claim(session, qid, 'P11', sex_value, 'monolingualtext', csrf_token)
        if success:
            success_count += 1
            print(f"    SUCCESS: Added sex: {sex_value}")
        else:
            error_count += 1
            error_msg = str(result).encode('utf-8', 'ignore').decode('utf-8')
            print(f"    ERROR: Failed to add sex: {error_msg}")
        time.sleep(0.5)
    
    # 2. Add Wikidata ID (P44) from REFN if it looks like a Wikidata QID
    if individual['refn'] and re.match(r'^Q\d+$', individual['refn']):
        success, result = add_property_claim(session, qid, 'P44', individual['refn'], 'string', csrf_token)
        if success:
            success_count += 1
            print(f"    SUCCESS: Added Wikidata ID: {individual['refn']}")
            
            # 3. Add "Described at url" (P45)
            wikidata_url = f"https://wikidata.org/wiki/{individual['refn']}"
            success2, result2 = add_property_claim(session, qid, 'P45', wikidata_url, 'url', csrf_token)
            if success2:
                success_count += 1
                print(f"    SUCCESS: Added described at URL: {wikidata_url}")
            else:
                error_count += 1
                error_msg = str(result2).encode('utf-8', 'ignore').decode('utf-8')
                print(f"    ERROR: Failed to add described at URL: {error_msg}")
            time.sleep(0.5)
            
            # 4. Fetch Wikidata labels and descriptions
            wikidata_info = get_wikidata_info(individual['refn'])
            if wikidata_info:
                # Update all labels and descriptions in all languages
                success3, result3 = update_entity_labels_descriptions(session, qid, wikidata_info, csrf_token)
                if success3:
                    success_count += 1
                    label_count = len(wikidata_info.get('labels', {}))
                    desc_count = len(wikidata_info.get('descriptions', {}))
                    print(f"    SUCCESS: Added {label_count} labels and {desc_count} descriptions from Wikidata")
                else:
                    error_count += 1
                    try:
                        error_msg = str(result3).encode('utf-8', 'ignore').decode('utf-8')
                        print(f"    ERROR: Failed to update labels/descriptions: {error_msg}")
                    except UnicodeEncodeError:
                        print("    ERROR: Failed to update labels/descriptions: [Unicode error in response]")
                time.sleep(0.5)
                
        else:
            error_count += 1
            try:
                error_msg = str(result).encode('utf-8', 'ignore').decode('utf-8')
                print(f"    ERROR: Failed to add Wikidata ID: {error_msg}")
            except UnicodeEncodeError:
                print("    ERROR: Failed to add Wikidata ID: [Unicode error in response]")
        time.sleep(0.5)
    
    return success_count, error_count

def main():
    print("Starting Japanese Individuals Repair...")
    print("Property mappings:")
    print("  P11: Sex (monolingualtext)")
    print("  P44: Wikidata ID") 
    print("  P45: Described at url")
    
    # Create session and login
    session = create_session()
    if not login_to_wiki(session):
        print("Login failed!")
        return
    
    csrf_token = get_csrf_token(session)
    print("Login successful!")
    
    # Load data
    japanese_mappings = load_japanese_mappings()
    if not japanese_mappings:
        print("No Japanese mappings found!")
        return
    
    japanese_individuals = parse_japanese_gedcom()
    if not japanese_individuals:
        print("No Japanese individuals found!")
        return
    
    total_success = 0
    total_errors = 0
    processed_count = 0
    
    # Process each individual that has a QID mapping
    for gedcom_id, qid in japanese_mappings.items():
        if gedcom_id in japanese_individuals:
            individual = japanese_individuals[gedcom_id]
            processed_count += 1
            
            print(f"\n[{processed_count}] Processing {gedcom_id} -> {qid}")
            success, errors = repair_japanese_individual(session, individual, qid, csrf_token)
            total_success += success
            total_errors += errors
            
            # Rate limiting
            time.sleep(1)
    
    print(f"\nJapanese Individuals Repair complete!")
    print(f"Processed {processed_count} individuals")
    print(f"Successful operations: {total_success}")
    print(f"Errors: {total_errors}")

if __name__ == '__main__':
    main()