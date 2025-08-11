#!/usr/bin/env python3
"""
Japanese GEDCOM Repair Script
Repairs existing individuals on Evolutionism wiki with missing data from Japanese GEDCOM file.
Only updates existing individuals found in mapping file - does not create new ones.
"""

import sys
import re
import time
import requests
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json

def create_session():
    """Create a robust session with retries"""
    session = requests.Session()
    
    # Set user agent to comply with policy
    session.headers.update({
        'User-Agent': 'Japanese GEDCOM Repair Bot/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
    })
    
    retry_strategy = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

def login_to_wiki(session):
    """Login to the wiki"""
    print("Logging into Evolutionism wiki...")
    
    # Get login token
    token_params = {
        'action': 'query',
        'meta': 'tokens',
        'type': 'login',
        'format': 'json'
    }
    
    try:
        response = session.get('https://evolutionism.miraheze.org/w/api.php', params=token_params, timeout=30)
        print(f"Token response status: {response.status_code}")
        print(f"Token response text: {response.text[:200]}...")
        
        if response.status_code != 200:
            print(f"Failed to get token, status: {response.status_code}")
            return False
            
        token_data = response.json()
        login_token = token_data['query']['tokens']['logintoken']
    except Exception as e:
        print(f"Error getting login token: {e}")
        return False
    
    # Login
    login_data = {
        'action': 'login',
        'lgname': 'Immanuelle',
        'lgpassword': '1996ToOmega!',
        'lgtoken': login_token,
        'format': 'json'
    }
    
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=login_data)
    login_result = response.json()
    
    if login_result.get('login', {}).get('result') == 'Success':
        print("Successfully logged in!")
        return True
    else:
        print(f"Login failed: {login_result}")
        return False

def get_csrf_token(session):
    """Get CSRF token for editing"""
    params = {
        'action': 'query',
        'meta': 'tokens',
        'format': 'json'
    }
    
    response = session.get('https://evolutionism.miraheze.org/w/api.php', params=params)
    data = response.json()
    return data['query']['tokens']['csrftoken']

def load_mapping_file():
    """Load the Japanese GEDCOM to QID mapping"""
    mapping = {}
    properties = {}
    
    try:
        with open('japanese_gedcom_to_qid_mapping.txt', 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Extract properties section
            lines = content.split('\n')
            in_properties = False
            in_individuals = False
            
            for line in lines:
                line = line.strip()
                if line == '# Properties':
                    in_properties = True
                    continue
                elif line == '# Individuals':
                    in_properties = False
                    in_individuals = True
                    continue
                elif line.startswith('#') or not line:
                    continue
                
                if in_properties and '\t' in line:
                    prop, pid = line.split('\t', 1)
                    properties[prop] = pid
                elif in_individuals and '\t' in line:
                    gedcom_id, qid = line.split('\t', 1)
                    mapping[gedcom_id] = qid
    
    except FileNotFoundError:
        print("Error: japanese_gedcom_to_qid_mapping.txt not found!")
        return {}, {}
    
    print(f"Loaded {len(mapping)} individual mappings and {len(properties)} properties")
    return mapping, properties

def parse_gedcom_individual(lines):
    """Parse a single individual from GEDCOM lines"""
    individual = {'id': '', 'data': {}}
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
            
        parts = line.split(' ', 2)
        if len(parts) < 2:
            i += 1
            continue
            
        level = int(parts[0])
        tag = parts[1]
        value = parts[2] if len(parts) > 2 else ''
        
        if level == 0 and tag.startswith('@I') and tag.endswith('@'):
            individual['id'] = tag
        elif level == 1:
            if tag == 'NAME':
                individual['data']['full_name'] = value
                # Split into given and surname if possible
                name_parts = value.split('/')
                if len(name_parts) >= 2:
                    individual['data']['given_name'] = name_parts[0].strip()
                    individual['data']['surname'] = name_parts[1].strip()
                else:
                    individual['data']['given_name'] = value
            elif tag == 'SEX':
                individual['data']['sex'] = 'Q6581097' if value == 'M' else 'Q6581072'  # male/female
            elif tag == 'BIRT':
                # Look ahead for date
                if i + 1 < len(lines) and '2 DATE' in lines[i + 1]:
                    date_line = lines[i + 1].strip()
                    date_value = date_line.split('DATE', 1)[1].strip()
                    individual['data']['birth_date'] = date_value
                    i += 1  # Skip the date line
            elif tag == 'DEAT':
                # Look ahead for date
                if i + 1 < len(lines) and '2 DATE' in lines[i + 1]:
                    date_line = lines[i + 1].strip()
                    date_value = date_line.split('DATE', 1)[1].strip()
                    individual['data']['death_date'] = date_value
                    i += 1  # Skip the date line
            elif tag == 'REFN':
                # Look ahead for type
                if i + 1 < len(lines) and '2 TYPE WIKIDATA' in lines[i + 1]:
                    individual['data']['gedcom_refn'] = value
                    i += 1  # Skip the type line
        
        i += 1
    
    return individual

def parse_japanese_gedcom():
    """Parse the Japanese GEDCOM file"""
    individuals = {}
    
    try:
        with open('new_gedcoms/source gedcoms/japan_genealogy_sample.ged', 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("Error: japan_genealogy_sample.ged not found!")
        return {}
    
    lines = content.split('\n')
    current_individual = []
    
    for line in lines:
        if line.startswith('0 @I') and line.endswith('@ INDI'):
            # Process previous individual if exists
            if current_individual:
                individual = parse_gedcom_individual(current_individual)
                if individual['id']:
                    individuals[individual['id']] = individual['data']
            
            # Start new individual
            current_individual = [line]
        elif current_individual:
            if line.startswith('0 ') and not line.endswith('@ INDI'):
                # This is the end of the current individual
                individual = parse_gedcom_individual(current_individual)
                if individual['id']:
                    individuals[individual['id']] = individual['data']
                current_individual = []
            else:
                # Continue with current individual
                current_individual.append(line)
    
    # Process final individual if exists
    if current_individual:
        individual = parse_gedcom_individual(current_individual)
        if individual['id']:
            individuals[individual['id']] = individual['data']
    
    print(f"Parsed {len(individuals)} individuals from Japanese GEDCOM")
    return individuals

def add_statement_to_item(session, qid, property_pid, value, value_type, csrf_token):
    """Add a statement to an existing wikibase item using the working format."""
    try:
        if value_type == 'string':
            datavalue = {
                'value': str(value),
                'type': 'string'
            }
        elif value_type == 'monolingualtext':
            datavalue = {
                'value': {
                    'text': str(value),
                    'language': 'en'
                },
                'type': 'monolingualtext'
            }
        elif value_type == 'item':
            # Extract numeric ID from QID
            if isinstance(value, str) and value.startswith('Q'):
                numeric_id = int(value[1:])
            else:
                numeric_id = int(value)
            
            datavalue = {
                'value': {'entity-type': 'item', 'numeric-id': numeric_id},
                'type': 'wikibase-entityid'
            }
        else:
            # Default to monolingualtext since most properties seem to expect it
            datavalue = {
                'value': {
                    'text': str(value),
                    'language': 'en'
                },
                'type': 'monolingualtext'
            }
        
        statement_data = {
            'claims': [
                {
                    'mainsnak': {
                        'snaktype': 'value',
                        'property': property_pid,
                        'datavalue': datavalue
                    },
                    'type': 'statement'
                }
            ]
        }
        
        params = {
            'action': 'wbeditentity',
            'id': qid,
            'data': json.dumps(statement_data),
            'format': 'json',
            'token': csrf_token,
            'summary': 'Adding data from Japanese GEDCOM file'
        }
        
        response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params, timeout=30)
        result = response.json()
        
        if 'entity' in result:
            return True
        else:
            print(f"    Error adding statement: {result}")
            return False
    
    except Exception as e:
        print(f"    Exception adding statement: {e}")
        return False

def update_individual(session, qid, updates, properties, csrf_token):
    """Update an individual on the wiki with new data"""
    if not updates:
        return True
        
    print(f"Updating {qid} with {len(updates)} properties...")
    
    # Process each property individually
    success = True
    for prop_name, value in updates.items():
        if prop_name in properties:
            pid = properties[prop_name]
            print(f"  Adding {prop_name} ({pid}): {value}")
            
            # Determine value type based on property
            if prop_name == 'sex':
                value_type = 'item'
            elif prop_name == 'gedcom_refn':
                value_type = 'string'  # This one works as string
            else:
                # Most name and date properties expect monolingualtext
                value_type = 'monolingualtext'
            
            if add_statement_to_item(session, qid, pid, value, value_type, csrf_token):
                print(f"    Successfully added {prop_name}")
            else:
                success = False
                
            # Rate limiting between properties
            time.sleep(0.5)
    
    return success

def main(dry_run=False):
    """Main repair function"""
    print("Starting Japanese GEDCOM repair process...")
    
    # Load mapping and parse GEDCOM
    mapping, properties = load_mapping_file()
    if not mapping or not properties:
        print("Failed to load mapping file. Exiting.")
        return
    
    individuals = parse_japanese_gedcom()
    if not individuals:
        print("Failed to parse GEDCOM file. Exiting.")
        return
    
    if dry_run:
        print("\n=== DRY RUN - Showing first 10 individuals that would be updated ===")
        count = 0
        for gedcom_id, data in individuals.items():
            if gedcom_id in mapping:
                qid = mapping[gedcom_id]
                updates = {k: v for k, v in data.items() if v and v.strip()}
                if updates:
                    print(f"\n{gedcom_id} -> {qid}")
                    for prop, value in updates.items():
                        print(f"  {prop}: {value}")
                    count += 1
                    if count >= 10:
                        break
        print(f"\nTotal individuals in GEDCOM: {len(individuals)}")
        print(f"Total individuals in mapping: {len(mapping)}")
        matched = sum(1 for gid in individuals if gid in mapping)
        print(f"Individuals that would be updated: {matched}")
        return
    
    # Create session and login
    session = create_session()
    if not login_to_wiki(session):
        print("Failed to login. Exiting.")
        return
    
    csrf_token = get_csrf_token(session)
    
    # Process each individual in the GEDCOM
    success_count = 0
    error_count = 0
    
    for gedcom_id, data in individuals.items():
        if gedcom_id in mapping:
            qid = mapping[gedcom_id]
            print(f"\nProcessing {gedcom_id} -> {qid}")
            
            # Filter out empty values
            updates = {k: v for k, v in data.items() if v and v.strip()}
            
            if updates:
                if update_individual(session, qid, updates, properties, csrf_token):
                    success_count += 1
                else:
                    error_count += 1
                
                # Rate limiting
                time.sleep(1)
            else:
                print(f"No updates needed for {qid}")
        else:
            print(f"Skipping {gedcom_id} - not in mapping file")
    
    print(f"\nRepair complete!")
    print(f"Successfully updated: {success_count}")
    print(f"Errors: {error_count}")

if __name__ == '__main__':
    # Run dry run first
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--dry-run':
        main(dry_run=True)
    else:
        main()