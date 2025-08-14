#!/usr/bin/env python3
"""
MISSING INDIVIDUALS CREATOR - COMPLETE VERSION

Creates wikibase items for all individuals found in the GEDCOM but missing from QID mapping.
Uses the same property structure and data extraction as the complete_master_uploader.py
to ensure consistency and completeness.

Properties used:
- P41: GEDCOM REFN
- P12: Given name
- P13: Surname  
- P14: Full name
- P15: Birth date
- P16: Death date
- P11: Sex
- P3: Instance of (Q279 for Gaiad character)
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
        'User-Agent': 'Missing Individuals Creator Bot/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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

def load_missing_individuals():
    """Load the list of missing individual IDs"""
    missing_individuals = []
    try:
        with open('missing_individuals_report.txt', 'r', encoding='utf-8') as f:
            reading_ids = False
            for line in f:
                line = line.strip()
                if line == "MISSING INDIVIDUAL IDs:":
                    reading_ids = True
                    continue
                if reading_ids and line.startswith('@I') and line.endswith('@'):
                    missing_individuals.append(line)
        print(f"Loaded {len(missing_individuals)} missing individual IDs")
    except FileNotFoundError:
        print("missing_individuals_report.txt not found. Run missing_individuals_checker.py first.")
        return []
    return missing_individuals

def extract_individual_data_from_gedcom(individual_id):
    """Extract all data for a specific individual from the GEDCOM using same format as master uploader"""
    individual_data = {
        'gedcom_id': individual_id,
        'other_fields': {},
        'dates': {},
        'refns': [],
        'notes': []
    }
    
    with open('new_gedcoms/source gedcoms/master_combined.ged', 'r', encoding='utf-8') as f:
        reading_individual = False
        current_note = []
        in_birth_date = False
        in_death_date = False
        
        for line in f:
            line = line.strip()
            
            # Start of our target individual
            if line == f"0 {individual_id} INDI":
                reading_individual = True
                continue
            
            # End of any individual record
            elif line.startswith('0 @') and reading_individual:
                # Save any accumulated note
                if current_note:
                    individual_data['notes'].append('\n'.join(current_note))
                break
            
            elif reading_individual:
                # Name processing (same as master uploader)
                if line.startswith('1 NAME '):
                    name = line[7:].strip()  # Remove "1 NAME "
                    if '/' in name:
                        parts = name.split('/')
                        individual_data['other_fields']['given_name'] = parts[0].strip()
                        if len(parts) > 1:
                            individual_data['other_fields']['surname'] = parts[1].strip()
                    individual_data['other_fields']['full_name'] = name.replace('/', ' ').strip()
                
                elif line.startswith('2 GIVN '):
                    individual_data['other_fields']['given_name'] = line[7:]
                elif line.startswith('2 SURN '):
                    individual_data['other_fields']['surname'] = line[7:]
                elif line.startswith('2 NSFX '):
                    individual_data['other_fields']['suffix'] = line[7:]
                
                # Sex
                elif line.startswith('1 SEX '):
                    individual_data['other_fields']['sex'] = line[6:].strip()
                
                # Date processing (same as master uploader)
                elif line.startswith('1 BIRT'):
                    in_birth_date = True
                    in_death_date = False
                elif line.startswith('1 DEAT'):
                    in_birth_date = False  
                    in_death_date = True
                elif line.startswith('2 DATE '):
                    date_value = line[7:].strip()
                    if in_birth_date:
                        individual_data['dates']['birth_date'] = date_value
                    elif in_death_date:
                        individual_data['dates']['death_date'] = date_value
                
                # Notes (same as master uploader)
                elif line.startswith('1 NOTE '):
                    if current_note:
                        individual_data['notes'].append('\n'.join(current_note))
                        current_note = []
                    current_note.append(line[7:])
                elif line.startswith('2 CONT '):
                    current_note.append(line[7:])
                elif line.startswith('2 CONC '):
                    if current_note:
                        current_note[-1] += line[7:]
                
                # REFN (same as master uploader)
                elif line.startswith('1 REFN '):
                    individual_data['refns'].append(line[7:])
                
                # Reset date context for other level 1 entries
                elif line.startswith('1 ') and not line.startswith('1 NOTE') and not line.startswith('1 REFN'):
                    in_birth_date = False
                    in_death_date = False
        
        # Save final note if exists
        if current_note:
            individual_data['notes'].append('\n'.join(current_note))
    
    return individual_data

def create_wikibase_item(session, csrf_token, individual_data):
    """Create a wikibase item for an individual using same format as master uploader"""
    
    # Build labels and descriptions
    labels = {}
    descriptions = {}
    
    # Create English label from name components (same as master uploader)
    name_parts = []
    if 'given_name' in individual_data['other_fields']:
        name_parts.append(individual_data['other_fields']['given_name'])
    if 'surname' in individual_data['other_fields']:
        name_parts.append(individual_data['other_fields']['surname'])
    if 'suffix' in individual_data['other_fields']:
        name_parts.append(individual_data['other_fields']['suffix'])
    
    # Fall back to full_name if no components
    if not name_parts and 'full_name' in individual_data['other_fields']:
        name_parts.append(individual_data['other_fields']['full_name'])
    
    if name_parts:
        labels['en'] = {'language': 'en', 'value': ' '.join(name_parts)}
        descriptions['en'] = {'language': 'en', 'value': 'Gaiad character'}
    else:
        labels['en'] = {'language': 'en', 'value': f'Person {individual_data["gedcom_id"]}'}
        descriptions['en'] = {'language': 'en', 'value': 'Gaiad character'}
    
    # Create the item with instance of Gaiad character (Q279)
    claims = {
        'P39': [{  # instance of
            'mainsnak': {
                'snaktype': 'value',
                'property': 'P39',
                'datavalue': {
                    'value': {'entity-type': 'item', 'numeric-id': 279},  # Q279 = Gaiad character
                    'type': 'wikibase-entityid'
                }
            },
            'type': 'statement',
            'rank': 'normal'
        }]
    }
    
    item_data = {
        'labels': labels,
        'descriptions': descriptions,
        'claims': claims
    }
    
    params = {
        'action': 'wbeditentity',
        'new': 'item',
        'data': json.dumps(item_data),
        'format': 'json',
        'token': csrf_token,
        'bot': 1
    }
    
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
    result = response.json()
    
    if 'entity' in result:
        return result['entity']['id']
    else:
        print(f"Error creating item for {individual_data['gedcom_id']}: {result}")
        return None

def remove_all_claims_from_item(session, qid, csrf_token):
    """Remove all existing claims from an item (except instance of)"""
    try:
        # Get all claims for the item
        response = session.get('https://evolutionism.miraheze.org/w/api.php', params={
            'action': 'wbgetentities',
            'ids': qid,
            'format': 'json'
        })
        
        data = response.json()
        if 'entities' not in data or qid not in data['entities']:
            return False
            
        claims = data['entities'][qid].get('claims', {})
        removed_count = 0
        
        for property_id, claim_list in claims.items():
            # Keep instance of (P39) but remove everything else
            if property_id == 'P39':
                continue
                
            for claim in claim_list:
                claim_id = claim.get('id')
                if claim_id:
                    params = {
                        'action': 'wbremoveclaims',
                        'claim': claim_id,
                        'format': 'json',
                        'token': csrf_token,
                        'bot': 1
                    }
                    
                    remove_response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
                    if remove_response.json().get('success') == 1:
                        removed_count += 1
                    time.sleep(0.1)
        
        print(f"    Removed {removed_count} existing claims from {qid}")
        return True
        
    except Exception as e:
        print(f"    Error removing claims from {qid}: {e}")
        return False

def add_all_properties_to_item(session, qid, individual_data, csrf_token):
    """Add all properties to the item using correct property IDs"""
    
    # ACTUAL property mappings from your wikibase
    properties = {
        'gedcom_refn': 'P41',    # GEDCOM REFN
        'given_name': 'P3',      # Given name  
        'surname': 'P4',         # Surname
        'full_name': 'P5',       # Full name
        'birth_date': 'P7',      # Birth date
        'death_date': 'P8',      # Death date
        'sex': 'P11',            # Sex
        'notes': 'P15'           # Notes page
    }
    
    success_count = 0
    
    # Add all REFNs
    if individual_data.get('refns'):
        for refn in individual_data['refns']:
            if add_statement_to_item(session, qid, properties['gedcom_refn'], refn, 'string', csrf_token):
                success_count += 1
    
    # Add name properties
    for field in ['full_name', 'given_name', 'surname']:
        if field in individual_data.get('other_fields', {}) and field in properties:
            if add_statement_to_item(session, qid, properties[field], 
                                   individual_data['other_fields'][field], 'monolingualtext', csrf_token):
                success_count += 1
    
    # Add date properties
    for field in ['birth_date', 'death_date']:
        if field in individual_data.get('dates', {}) and field in properties:
            if add_statement_to_item(session, qid, properties[field],
                                   individual_data['dates'][field], 'monolingualtext', csrf_token):
                success_count += 1
    
    # Add sex
    if 'sex' in individual_data.get('other_fields', {}):
        if add_statement_to_item(session, qid, properties['sex'],
                               individual_data['other_fields']['sex'], 'monolingualtext', csrf_token):
            success_count += 1
    
    return success_count

def add_statement_to_item(session, qid, property_id, value, value_type, csrf_token):
    """Add a statement to a wikibase item"""
    try:
        if value_type == 'monolingualtext':
            value_data = json.dumps({
                'text': str(value),
                'language': 'en'
            })
        elif value_type == 'string':
            value_data = json.dumps(str(value))
        else:
            return False
        
        params = {
            'action': 'wbcreateclaim',
            'entity': qid,
            'property': property_id,
            'snaktype': 'value',
            'value': value_data,
            'format': 'json',
            'token': csrf_token,
            'bot': 1
        }
        
        response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
        result = response.json()
        
        return 'claim' in result
    except Exception as e:
        print(f"Error adding statement {property_id}={value}: {e}")
        return False

def update_mapping_file(individual_id, qid):
    """Add the new mapping to gedcom_to_qid_mapping.txt"""
    with open('gedcom_to_qid_mapping.txt', 'a', encoding='utf-8') as f:
        f.write(f"{individual_id}\t{qid}\n")

def load_existing_mappings():
    """Load existing GEDCOM to QID mappings"""
    mappings = {}
    try:
        with open('gedcom_to_qid_mapping.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '\t' in line:
                    gedcom_id, qid = line.split('\t', 1)
                    if gedcom_id.startswith('@I') and gedcom_id.endswith('@'):
                        mappings[gedcom_id] = qid
        print(f"Loaded {len(mappings)} existing mappings")
    except FileNotFoundError:
        print("No existing mappings found")
    return mappings

def main():
    print("Starting missing individuals creator - repairs broken items and creates new ones...")
    
    # Create session and login
    session = create_session()
    if not login_to_wiki(session):
        print("Failed to login. Exiting.")
        return
    
    csrf_token = get_csrf_token(session)
    
    # Load missing individuals and existing mappings
    missing_individuals = load_missing_individuals()
    existing_mappings = load_existing_mappings()
    
    if not missing_individuals:
        print("No missing individuals to process.")
        return
    
    print(f"Processing {len(missing_individuals)} missing individuals...")
    
    success_count = 0
    repaired_count = 0
    created_count = 0
    error_count = 0
    
    for i, individual_id in enumerate(missing_individuals, 1):
        try:
            print(f"[{i}/{len(missing_individuals)}] Processing {individual_id}...")
            
            # Extract data from GEDCOM
            individual_data = extract_individual_data_from_gedcom(individual_id)
            
            # Check if this individual already has a QID (was created by broken script)
            if individual_id in existing_mappings:
                qid = existing_mappings[individual_id]
                print(f"  REPAIRING existing item {qid}...")
                
                # First remove all existing properties (except instance of)
                if remove_all_claims_from_item(session, qid, csrf_token):
                    time.sleep(0.5)
                    
                    # Then add all properties with correct IDs
                    properties_added = add_all_properties_to_item(session, qid, individual_data, csrf_token)
                    print(f"  REPAIRED: Added {properties_added} properties to {qid}")
                    repaired_count += 1
                else:
                    print(f"  ERROR: Failed to remove existing properties from {qid}")
                    error_count += 1
                
            else:
                # Create new wikibase item
                qid = create_wikibase_item(session, csrf_token, individual_data)
                if not qid:
                    error_count += 1
                    continue
                
                time.sleep(0.5)
                
                # Add all properties to new item
                properties_added = add_all_properties_to_item(session, qid, individual_data, csrf_token)
                
                # Update mapping file
                update_mapping_file(individual_id, qid)
                
                print(f"  CREATED: New item {qid} with {properties_added} properties")
                created_count += 1
            
            success_count += 1
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"  ERROR processing {individual_id}: {e}")
            error_count += 1
            time.sleep(2)  # Longer pause on error
    
    print(f"\nMissing individuals processing complete!")
    print(f"Total processed: {success_count}")
    print(f"Items repaired: {repaired_count}")
    print(f"Items created: {created_count}")
    print(f"Errors: {error_count}")

if __name__ == '__main__':
    main()