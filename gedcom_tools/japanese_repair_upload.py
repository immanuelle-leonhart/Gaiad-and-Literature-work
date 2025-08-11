#!/usr/bin/env python3
"""
JAPANESE GENEALOGY REPAIR PROGRAM

Repairs existing Japanese genealogy items (30k people uploaded).
Focuses on adding missing properties, REFNs, and data to existing items.
Uses separate mapping file to avoid conflicts with other uploads.
NO DESCRIPTIONS - they break the program.
"""

import requests
import json
import sys
import time
import mwclient
import re
from typing import Dict, List, Optional, Set, Tuple

class JapaneseRepairUpload:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        
        # Authentication
        self.site = None
        self.session = None
        self.csrf_token = None
        self.api_url = "https://evolutionism.miraheze.org/w/api.php"
        
        # Data storage
        self.individuals_data = {}    # @I123@ -> full parsed data
        self.families_data = {}       # @F123@ -> full parsed data
        
        # Mappings - use separate files for Japanese data
        self.individual_mappings = {} # @I123@ -> Q456
        self.family_mappings = {}     # @F123@ -> Q456
        self.property_mappings = {}   # field_name -> P123
        self.mapping_file = 'japanese_gedcom_to_qid_mapping.txt'
        
        # State tracking
        self.existing_items = set()   # QIDs that exist in wikibase
        self.repaired_items = set()   # QIDs that have been fully repaired
        self.created_items = set()    # QIDs that have been created this session
        
        # Statistics
        self.stats = {
            'items_repaired': 0,
            'properties_added': 0,
            'refns_added': 0,
            'relationships_added': 0,
            'items_created': 0,
            'families_created': 0,
            'errors': 0
        }
        
        # Required properties for genealogy - SAME AS MAIN PROGRAM
        self.needed_properties = {
            'gedcom_refn': 'GEDCOM REFN',
            'given_name': 'Given name', 
            'surname': 'Surname',
            'full_name': 'Full name',
            'birth_date': 'Birth date',
            'death_date': 'Death date',
            'sex': 'Sex',
            'mother': 'Mother',
            'father': 'Father',
            'spouse': 'Spouse',
            'child': 'Child',
            'instance_of': 'Instance of'
        }
    
    def login(self):
        """Login and setup authenticated session."""
        print(f"Logging in as {self.username}...")
        
        try:
            self.site = mwclient.Site("evolutionism.miraheze.org", path="/w/")
            self.session = requests.Session()
            
            self.session.headers.update({
                'User-Agent': 'JapaneseRepairUpload/1.0 (https://evolutionism.miraheze.org/wiki/User:Immanuelle)'
            })
            
            self.site.login(self.username, self.password)
            
            # Copy cookies from mwclient to requests session
            for cookie in self.site.connection.cookies:
                self.session.cookies.set(cookie.name, cookie.value, domain=cookie.domain)
            
            # Get CSRF token
            response = self.session.get(self.api_url, params={
                'action': 'query',
                'meta': 'tokens',
                'format': 'json'
            })
            
            data = response.json()
            if 'query' in data and 'tokens' in data['query']:
                self.csrf_token = data['query']['tokens']['csrftoken']
                print(f"Login successful! CSRF token: {self.csrf_token[:10]}...")
                return True
            else:
                print(f"Error getting CSRF token: {data}")
                return False
                
        except Exception as e:
            print(f"Login failed: {e}")
            return False
    
    def discover_japanese_items(self):
        """Discover existing Japanese items in wikibase."""
        print("Discovering existing Japanese genealogy items...")
        
        # Query for items in large batches to find Japanese genealogy items
        batch_size = 100
        start_qid = 2500  # Start from where Japanese items likely begin
        max_consecutive_missing = 200  # Larger gap for Japanese items
        consecutive_missing = 0
        
        while consecutive_missing < max_consecutive_missing:
            qids_to_check = [f"Q{i}" for i in range(start_qid, start_qid + batch_size)]
            qids_param = '|'.join(qids_to_check)
            
            response = self.session.get(self.api_url, params={
                'action': 'wbgetentities',
                'ids': qids_param,
                'props': 'labels|descriptions|claims',
                'format': 'json'
            })
            
            data = response.json()
            if 'entities' not in data:
                break
            
            found_any_this_batch = False
            
            for qid in qids_to_check:
                if qid in data['entities'] and 'missing' not in data['entities'][qid]:
                    found_any_this_batch = True
                    consecutive_missing = 0
                    
                    entity = data['entities'][qid]
                    
                    # Check if this looks like a Japanese genealogy individual
                    is_japanese_individual = False
                    
                    # Check labels for Japanese characteristics
                    if 'labels' in entity and 'en' in entity['labels']:
                        label = entity['labels']['en']['value'].lower()
                        if 'japanese' in label or any(char in label for char in ['japanese', 'japan']):
                            is_japanese_individual = True
                    
                    # Check description for Japanese characteristics
                    if 'descriptions' in entity and 'en' in entity['descriptions']:
                        desc = entity['descriptions']['en']['value'].lower()
                        if 'japanese' in desc or 'japan' in desc:
                            is_japanese_individual = True
                    
                    # Check instance of claims - might be instance of Q279 but Japanese
                    if 'claims' in entity:
                        for prop_id, claims in entity['claims'].items():
                            for claim in claims:
                                try:
                                    mainsnak = claim.get('mainsnak', {})
                                    datavalue = mainsnak.get('datavalue', {})
                                    if isinstance(datavalue, dict):
                                        value = datavalue.get('value', {})
                                        if isinstance(value, dict) and value.get('numeric-id') == 279:
                                            # This is a genealogy character - check if Japanese by QID range
                                            qid_num = int(qid[1:])
                                            if qid_num > 2500:  # Japanese items likely in higher QID range
                                                is_japanese_individual = True
                                                break
                                except (AttributeError, TypeError):
                                    continue
                    
                    if is_japanese_individual:
                        self.existing_items.add(qid)
                        print(f"  Found Japanese individual: {qid}")
                else:
                    consecutive_missing += 1
            
            if not found_any_this_batch:
                consecutive_missing += batch_size
            
            start_qid += batch_size
            time.sleep(0.1)  # Rate limiting
        
        print(f"Found {len(self.existing_items)} existing Japanese items in wikibase")
    
    def ensure_properties_exist(self):
        """Load existing properties from the main genealogy upload."""
        print("Loading shared properties from main genealogy upload...")
        
        # Load properties from main mapping file
        try:
            with open('gedcom_to_qid_mapping.txt', 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            in_properties = False
            for line in lines:
                line = line.strip()
                if line == "# Properties":
                    in_properties = True
                    continue
                elif line.startswith('# ') or not line:
                    if in_properties and line.startswith('# ') and line != "# Properties":
                        break
                    continue
                
                if in_properties and '\t' in line:
                    prop_name, prop_id = line.split('\t', 1)
                    if prop_name in self.needed_properties:
                        self.property_mappings[prop_name] = prop_id
                        print(f"Loaded property {prop_id}: {self.needed_properties[prop_name]}")
            
            print(f"Loaded {len(self.property_mappings)} shared properties")
            
        except FileNotFoundError:
            print("Could not find main mapping file - will search for properties individually")
            
            for prop_name, prop_label in self.needed_properties.items():
                # Search for existing property
                response = self.session.get(self.api_url, params={
                    'action': 'wbsearchentities',
                    'search': prop_label,
                    'language': 'en',
                    'type': 'property',
                    'limit': 5,
                    'format': 'json'
                })
                
                data = response.json()
                if 'search' in data:
                    for result in data['search']:
                        if result['label'].lower() == prop_label.lower():
                            self.property_mappings[prop_name] = result['id']
                            print(f"Found existing property {result['id']}: {prop_label}")
                            break
                
                time.sleep(0.2)  # Rate limiting
    
    def parse_gedcom_file(self, filename):
        """Parse the complete GEDCOM file and store all data."""
        print(f"Parsing Japanese GEDCOM file: {filename}")
        
        with open(filename, 'rb') as f:
            content = f.read().decode('utf-8-sig')
        
        lines = content.split('\n')
        current_record = None
        current_type = None
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            
            # Start of new record
            if line.startswith('0 @') and (line.endswith(' INDI') or line.endswith(' FAM')):
                # Save previous record
                if current_record and current_type:
                    if current_type == 'INDI':
                        self.individuals_data[current_record['gedcom_id']] = current_record
                    elif current_type == 'FAM':
                        self.families_data[current_record['gedcom_id']] = current_record
                
                # Start new record
                parts = line.split()
                gedcom_id = parts[1]  # @I123@ or @F123@
                current_type = parts[2]  # INDI or FAM
                
                current_record = {
                    'gedcom_id': gedcom_id,
                    'type': current_type,
                    'names': [],
                    'refns': [],
                    'dates': {},
                    'relationships': {},
                    'other_fields': {},
                    'notes': []
                }
                
            elif current_record:
                # Parse record fields - SAME AS MAIN PROGRAM
                if line.startswith('1 NAME '):
                    name = line[7:].strip()
                    current_record['names'].append(name)
                    # Parse name parts
                    if '/' in name:
                        parts = name.split('/')
                        current_record['other_fields']['given_name'] = parts[0].strip()
                        if len(parts) > 1:
                            current_record['other_fields']['surname'] = parts[1].strip()
                    current_record['other_fields']['full_name'] = name.replace('/', ' ').strip()
                    
                elif line.startswith('1 SEX '):
                    current_record['other_fields']['sex'] = line[6:].strip()
                    
                elif line.startswith('1 BIRT'):
                    current_record['current_event'] = 'birth'
                elif line.startswith('1 DEAT'):
                    current_record['current_event'] = 'death'
                elif line.startswith('2 DATE '):
                    event = current_record.get('current_event', 'unknown')
                    current_record['dates'][f'{event}_date'] = line[7:].strip()
                    
                elif line.startswith('1 REFN '):
                    current_record['refns'].append(line[7:].strip())
                    
                elif line.startswith('1 FAMS '):
                    spouse_fam = line[7:].strip()
                    if 'spouse_families' not in current_record['relationships']:
                        current_record['relationships']['spouse_families'] = []
                    current_record['relationships']['spouse_families'].append(spouse_fam)
                    
                elif line.startswith('1 FAMC '):
                    parent_fam = line[7:].strip()
                    current_record['relationships']['parent_family'] = parent_fam
                    
                elif line.startswith('1 HUSB '):
                    current_record['relationships']['husband'] = line[7:].strip()
                elif line.startswith('1 WIFE '):
                    current_record['relationships']['wife'] = line[7:].strip()
                elif line.startswith('1 CHIL '):
                    if 'children' not in current_record['relationships']:
                        current_record['relationships']['children'] = []
                    current_record['relationships']['children'].append(line[7:].strip())
                    
                elif line.startswith('1 NOTE'):
                    note = line[7:].strip() if len(line) > 7 else ""
                    current_record['notes'].append(note)
        
        # Save the last record
        if current_record and current_type:
            if current_type == 'INDI':
                self.individuals_data[current_record['gedcom_id']] = current_record
            elif current_type == 'FAM':
                self.families_data[current_record['gedcom_id']] = current_record
        
        print(f"Parsed {len(self.individuals_data)} individuals and {len(self.families_data)} families")
    
    def match_qid_to_gedcom(self, qid):
        """Try to match a QID to a GEDCOM individual by examining the item's label."""
        response = self.session.get(self.api_url, params={
            'action': 'wbgetentities',
            'ids': qid,
            'props': 'labels|descriptions',
            'format': 'json'
        })
        
        data = response.json()
        if 'entities' not in data or qid not in data['entities']:
            return None
        
        entity = data['entities'][qid]
        
        # Get the label
        label = None
        if 'labels' in entity and 'en' in entity['labels']:
            label = entity['labels']['en']['value']
        
        if not label:
            return None
        
        # Try to find matching GEDCOM individual by name
        for gedcom_id, individual_data in self.individuals_data.items():
            if individual_data.get('other_fields', {}).get('full_name') == label:
                return gedcom_id
            
            # Also try exact name matches
            for name in individual_data.get('names', []):
                clean_name = name.replace('/', ' ').strip()
                if clean_name == label:
                    return gedcom_id
        
        print(f"  Could not match {qid} ('{label}') to any GEDCOM individual")
        return None
    
    def add_statement_to_item(self, qid, property_pid, value, value_type='string'):
        """Add a statement to an existing wikibase item."""
        try:
            if value_type == 'string':
                datavalue = {
                    'value': str(value),
                    'type': 'string'
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
                'token': self.csrf_token
            }
            
            response = self.session.post(self.api_url, data=params)
            result = response.json()
            
            if 'entity' in result:
                self.stats['properties_added'] += 1
                return True
            else:
                print(f"Error adding statement to {qid}: {result}")
                self.stats['errors'] += 1
                return False
                
        except Exception as e:
            print(f"Exception adding statement to {qid}: {e}")
            self.stats['errors'] += 1
            return False
    
    def repair_existing_item(self, qid):
        """Repair a single existing item by adding missing properties."""
        print(f"Repairing Japanese individual {qid}...")
        
        # Find the GEDCOM data for this item
        gedcom_id = self.match_qid_to_gedcom(qid)
        if not gedcom_id:
            print(f"  Could not find GEDCOM data for {qid} - skipping")
            return False
        
        individual_data = self.individuals_data.get(gedcom_id)
        if not individual_data:
            print(f"  No individual data for {gedcom_id} - skipping")
            return False
        
        # Add this mapping for future reference
        self.individual_mappings[gedcom_id] = qid
        print(f"  Matched {qid} to {gedcom_id}")
        
        # Add instance of Japanese genealogy character - use same Q279 for now
        if 'instance_of' in self.property_mappings:
            self.add_statement_to_item(qid, self.property_mappings['instance_of'], 'Q279', 'item')
        
        # Add all REFNs
        refn_prop = self.property_mappings.get('gedcom_refn')
        if refn_prop:
            for refn in individual_data.get('refns', []):
                self.add_statement_to_item(qid, refn_prop, refn, 'string')
                self.stats['refns_added'] += 1
        
        # Add name properties - SAME AS MAIN PROGRAM
        if 'full_name' in self.property_mappings and 'full_name' in individual_data.get('other_fields', {}):
            self.add_statement_to_item(qid, self.property_mappings['full_name'], 
                                     individual_data['other_fields']['full_name'], 'string')
        
        if 'given_name' in self.property_mappings and 'given_name' in individual_data.get('other_fields', {}):
            self.add_statement_to_item(qid, self.property_mappings['given_name'], 
                                     individual_data['other_fields']['given_name'], 'string')
        
        if 'surname' in self.property_mappings and 'surname' in individual_data.get('other_fields', {}):
            self.add_statement_to_item(qid, self.property_mappings['surname'], 
                                     individual_data['other_fields']['surname'], 'string')
        
        # Add dates
        for date_field in ['birth_date', 'death_date']:
            if date_field in self.property_mappings and date_field in individual_data.get('dates', {}):
                self.add_statement_to_item(qid, self.property_mappings[date_field], 
                                         individual_data['dates'][date_field], 'string')
        
        # Add sex
        if 'sex' in self.property_mappings and 'sex' in individual_data.get('other_fields', {}):
            self.add_statement_to_item(qid, self.property_mappings['sex'], 
                                     individual_data['other_fields']['sex'], 'string')
        
        self.stats['items_repaired'] += 1
        self.repaired_items.add(qid)
        print(f"  Successfully repaired {qid}")
        return True
    
    def save_mappings(self):
        """Save current mappings to Japanese-specific file."""
        print("Saving Japanese genealogy mappings...")
        
        with open(self.mapping_file, 'w', encoding='utf-8') as f:
            f.write("# Japanese GEDCOM ID to Wikibase QID Mapping\n")
            f.write("# Generated by japanese_repair_upload.py\n\n")
            
            # Properties
            f.write("# Properties\n")
            for prop_name, prop_id in sorted(self.property_mappings.items()):
                f.write(f"{prop_name}\t{prop_id}\n")
            f.write("\n")
            
            # Individuals  
            f.write("# Individuals\n")
            for gedcom_id, qid in sorted(self.individual_mappings.items()):
                f.write(f"{gedcom_id}\t{qid}\n")
            f.write("\n")
            
            # Families
            f.write("# Families\n")
            for gedcom_id, qid in sorted(self.family_mappings.items()):
                f.write(f"{gedcom_id}\t{qid}\n")
    
    def run_japanese_repair(self, gedcom_file):
        """Main function for Japanese genealogy repair."""
        print("Starting Japanese genealogy repair (30k existing items)...")
        
        # Setup
        if not self.login():
            return False
        
        self.parse_gedcom_file(gedcom_file)
        self.ensure_properties_exist()
        self.discover_japanese_items()
        
        # Phase 1: Repair existing items
        print(f"Phase 1: Repairing {len(self.existing_items)} existing Japanese items...")
        
        existing_qids = sorted(list(self.existing_items), key=lambda x: int(x[1:]))
        
        for i, qid in enumerate(existing_qids):
            if qid in self.repaired_items:
                continue  # Already repaired
            
            print(f"Progress: {i+1}/{len(existing_qids)}")
            self.repair_existing_item(qid)
            
            # Save mappings every 50 items
            if (i + 1) % 50 == 0:
                self.save_mappings()
                print(f"Saved progress - {self.stats['items_repaired']} items repaired so far")
            
            time.sleep(0.1)  # Rate limiting
        
        self.save_mappings()
        print(f"\nJapanese genealogy repair completed!")
        print(f"Items repaired: {self.stats['items_repaired']}")
        print(f"Properties added: {self.stats['properties_added']}")
        print(f"REFNs added: {self.stats['refns_added']}")
        print(f"Errors: {self.stats['errors']}")
        
        return True

def main():
    if len(sys.argv) != 2:
        print("Usage: python japanese_repair_upload.py <japanese_gedcom_file>")
        print("Example: python japanese_repair_upload.py \"C:\\path\\to\\japan_genealogy_sample.ged\"")
        sys.exit(1)
    
    gedcom_file = sys.argv[1]
    
    repairer = JapaneseRepairUpload("Immanuelle", "1996ToOmega!")
    success = repairer.run_japanese_repair(gedcom_file)
    
    if success:
        print("Japanese repair completed successfully!")
    else:
        print("Japanese repair failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()