#!/usr/bin/env python3
"""
Resume GEDCOM upload from where it left off.
Much simpler and more robust than the original uploader.
"""

import requests
import json
import sys
import time
import mwclient
from typing import Dict, List, Optional

def login():
    """Login and get session."""
    site = mwclient.Site("evolutionism.miraheze.org", path="/w/")
    session = requests.Session()
    
    session.headers.update({
        'User-Agent': 'ResumeUploader/1.0 (https://evolutionism.miraheze.org/wiki/User:Immanuelle)'
    })
    
    site.login("Immanuelle", "1996ToOmega!")
    
    # Copy cookies
    for cookie in site.connection.cookies:
        session.cookies.set(cookie.name, cookie.value, domain=cookie.domain)
    
    # Get CSRF token
    response = session.get("https://evolutionism.miraheze.org/w/api.php", params={
        'action': 'query',
        'meta': 'tokens',
        'format': 'json'
    })
    
    data = response.json()
    csrf_token = data['query']['tokens']['csrftoken']
    
    return session, csrf_token

def get_last_qid(session):
    """Find the highest QID to continue from."""
    response = session.get("https://evolutionism.miraheze.org/w/api.php", params={
        'action': 'wbsearchentities',
        'search': 'Q',
        'language': 'en',
        'type': 'item',
        'limit': 50,
        'format': 'json'
    })
    
    data = response.json()
    if 'search' not in data:
        return 280  # Start from Q281
    
    max_qid = 280
    for item in data['search']:
        qid_num = int(item['id'][1:])  # Remove Q prefix
        if qid_num > max_qid:
            max_qid = qid_num
    
    return max_qid

def create_individual_item(session, csrf_token, individual_data):
    """Create a single individual item."""
    
    # Build labels and descriptions
    labels = {}
    descriptions = {}
    claims = []
    
    # Use full name as label if available
    if 'full_name' in individual_data:
        labels['en'] = {'language': 'en', 'value': individual_data['full_name']}
    elif 'given_name' in individual_data and 'surname' in individual_data:
        labels['en'] = {'language': 'en', 'value': f"{individual_data['given_name']} {individual_data['surname']}"}
    elif 'given_name' in individual_data:
        labels['en'] = {'language': 'en', 'value': individual_data['given_name']}
    elif 'surname' in individual_data:
        labels['en'] = {'language': 'en', 'value': individual_data['surname']}
    else:
        labels['en'] = {'language': 'en', 'value': f"Individual {individual_data['gedcom_id']}"}
    
    descriptions['en'] = {'language': 'en', 'value': 'Character from the Gaiad mythology'}
    
    # Instance of Gaiad character (P39 -> Q279)
    claims.append({
        'mainsnak': {
            'snaktype': 'value',
            'property': 'P39',
            'datavalue': {
                'value': {'entity-type': 'item', 'numeric-id': 279},
                'type': 'wikibase-entityid'
            }
        },
        'type': 'statement'
    })
    
    item_data = {
        'labels': labels,
        'descriptions': descriptions,
        'claims': claims
    }
    
    # Create the item
    params = {
        'action': 'wbeditentity',
        'new': 'item',
        'data': json.dumps(item_data),
        'format': 'json',
        'token': csrf_token
    }
    
    response = session.post("https://evolutionism.miraheze.org/w/api.php", data=params)
    result = response.json()
    
    if 'entity' in result:
        return result['entity']['id']
    else:
        print(f"Error creating item: {result}")
        return None

def parse_individuals_from_file(filename, start_index=0, count=50):
    """Parse a batch of individuals from GEDCOM file."""
    individuals = []
    
    with open(filename, 'rb') as f:
        content = f.read().decode('utf-8-sig')
    
    lines = content.split('\n')
    current_individual = None
    individual_count = 0
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('0 @') and line.endswith(' INDI'):
            # Save previous individual if we have one and are in our target range
            if current_individual and individual_count >= start_index and individual_count < start_index + count:
                individuals.append(current_individual)
            
            # Start new individual
            if current_individual:
                individual_count += 1
            
            # Stop if we've collected enough
            if len(individuals) >= count:
                break
            
            gedcom_id = line.split()[1]  # @I123@
            current_individual = {
                'gedcom_id': gedcom_id,
                'refns': []
            }
            
        elif current_individual and line.startswith('1 NAME '):
            name = line[7:].strip()
            parts = name.split('/')
            if len(parts) >= 2:
                current_individual['given_name'] = parts[0].strip()
                current_individual['surname'] = parts[1].strip()
            current_individual['full_name'] = name.replace('/', ' ').strip()
            
        elif current_individual and line.startswith('1 REFN '):
            refn = line[7:].strip()
            current_individual['refns'].append(refn)
    
    # Don't forget the last individual
    if current_individual and individual_count >= start_index and individual_count < start_index + count:
        individuals.append(current_individual)
    
    return individuals, individual_count + 1

def main():
    print("Resuming GEDCOM upload...")
    
    # Login
    session, csrf_token = login()
    print("Logged in successfully")
    
    # Find where to continue from
    last_qid = get_last_qid(session)
    print(f"Last QID found: Q{last_qid}")
    
    # Calculate how many individuals we've already processed
    # We started from Q281, so subtract 280 to get the count
    start_index = last_qid - 280
    print(f"Continuing from individual #{start_index}")
    
    batch_size = 50
    total_created = 0
    
    while True:
        # Get next batch of individuals
        individuals, total_individuals = parse_individuals_from_file(
            "C:\\Users\\Immanuelle\\Documents\\Github\\Gaiad-Genealogy\\new_gedcoms\\source gedcoms\\master_combined.ged",
            start_index,
            batch_size
        )
        
        if not individuals:
            print("No more individuals to process")
            break
        
        print(f"Processing batch: individuals {start_index+1} to {start_index+len(individuals)}")
        
        for individual in individuals:
            qid = create_individual_item(session, csrf_token, individual)
            if qid:
                print(f"Created {qid}: {individual.get('full_name', individual['gedcom_id'])}")
                total_created += 1
                
                # Update mapping file
                with open('gedcom_to_qid_mapping.txt', 'a', encoding='utf-8') as f:
                    f.write(f"{individual['gedcom_id']}\t{qid}\n")
                
            else:
                print(f"Failed to create individual: {individual['gedcom_id']}")
            
            # Rate limiting
            time.sleep(0.1)
        
        start_index += len(individuals)
        
        print(f"Batch completed. Total created this session: {total_created}")
        print("Pausing before next batch...")
        time.sleep(5)

if __name__ == "__main__":
    main()