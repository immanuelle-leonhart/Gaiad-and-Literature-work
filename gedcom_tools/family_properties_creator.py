#!/usr/bin/env python3
"""
FAMILY PROPERTIES CREATOR

Creates the required family relationship properties in Evolutionism Wikibase:
- P22: Father 
- P25: Mother
- P26: Spouse 
- P40: Child

These properties are needed for family relationship scripts to work.
"""

import requests
import json
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Family Properties Creator/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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

def create_property(session, label, description, datatype, csrf_token):
    """Create a new property in the Wikibase"""
    
    property_data = {
        'labels': {'en': {'language': 'en', 'value': label}},
        'descriptions': {'en': {'language': 'en', 'value': description}},
        'datatype': datatype
    }
    
    params = {
        'action': 'wbeditentity',
        'new': 'property',
        'data': json.dumps(property_data),
        'format': 'json',
        'token': csrf_token,
        'bot': 1
    }
    
    try:
        response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
        result = response.json()
        
        if 'entity' in result:
            property_id = result['entity']['id']
            print(f"Created property {property_id}: {label}")
            return property_id
        else:
            print(f"Error creating property '{label}': {result}")
            return None
            
    except Exception as e:
        print(f"Exception creating property '{label}': {e}")
        return None

def check_property_exists(session, label):
    """Check if a property with this label already exists"""
    params = {
        'action': 'wbsearchentities',
        'search': label,
        'language': 'en', 
        'type': 'property',
        'limit': 10,
        'format': 'json'
    }
    
    response = session.get('https://evolutionism.miraheze.org/w/api.php', params=params)
    data = response.json()
    
    if 'search' in data:
        for result in data['search']:
            if result['label'].lower() == label.lower():
                print(f"Property '{label}' already exists as {result['id']}")
                return result['id']
    
    return None

def main():
    print("Creating family relationship properties for Evolutionism Wikibase...")
    
    # Family relationship properties to create
    properties = [
        {
            'label': 'Father',
            'description': 'Male parent of the subject',
            'datatype': 'wikibase-item'
        },
        {
            'label': 'Mother', 
            'description': 'Female parent of the subject',
            'datatype': 'wikibase-item'
        },
        {
            'label': 'Spouse',
            'description': 'Person married to the subject',
            'datatype': 'wikibase-item'
        },
        {
            'label': 'Child',
            'description': 'Child of the subject',
            'datatype': 'wikibase-item'
        }
    ]
    
    session = create_session()
    if not login_to_wiki(session):
        print("Failed to login. Exiting.")
        return
    
    csrf_token = get_csrf_token(session)
    
    created_properties = {}
    
    for prop in properties:
        label = prop['label']
        description = prop['description'] 
        datatype = prop['datatype']
        
        # Check if property already exists
        existing_id = check_property_exists(session, label)
        if existing_id:
            created_properties[label.lower()] = existing_id
            continue
            
        # Create new property
        property_id = create_property(session, label, description, datatype, csrf_token)
        if property_id:
            created_properties[label.lower()] = property_id
            time.sleep(1)  # Rate limiting
    
    print(f"\nFamily relationship properties:")
    print("=" * 40)
    for name, prop_id in created_properties.items():
        print(f"{name.title()}: {prop_id}")
    
    # Save mapping to file
    with open('family_properties_mapping.txt', 'w', encoding='utf-8') as f:
        f.write("# Family Relationship Properties Mapping\n")
        f.write("# Generated by family_properties_creator.py\n\n")
        for name, prop_id in created_properties.items():
            f.write(f"{name}\t{prop_id}\n")
    
    print(f"\nProperties mapping saved to family_properties_mapping.txt")
    print("Family relationship properties creation complete!")

if __name__ == '__main__':
    main()