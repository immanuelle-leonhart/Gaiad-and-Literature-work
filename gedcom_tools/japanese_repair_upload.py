#!/usr/bin/env python3
"""
JAPANESE GENEALOGY REPAIR AND UPLOAD PROGRAM

Independent copy of repair_then_upload.py for Japanese genealogy data.
Uses separate mapping file to avoid conflicts during parallel processing.
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
        
        # Required properties for genealogy
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
    
    def load_existing_mappings(self):
        """Load any existing GEDCOM ID to QID mappings."""
        print(f"Loading existing mappings from {self.mapping_file}...")
        
        try:
            with open(self.mapping_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            in_individuals = False
            in_families = False
            in_properties = False
            
            for line in lines:
                line = line.strip()
                if line == "# Individuals":
                    in_individuals = True
                    in_families = False
                    in_properties = False
                    continue
                elif line == "# Families":
                    in_individuals = False
                    in_families = True
                    in_properties = False
                    continue
                elif line == "# Properties":
                    in_individuals = False
                    in_families = False
                    in_properties = True
                    continue
                elif line.startswith('#') or not line:
                    continue
                
                if '\t' in line:
                    gedcom_id, qid = line.split('\t', 1)
                    if in_individuals:
                        self.individual_mappings[gedcom_id] = qid
                        self.existing_items.add(qid)
                    elif in_families:
                        self.family_mappings[gedcom_id] = qid
                        self.existing_items.add(qid)
                    elif in_properties:
                        self.property_mappings[gedcom_id] = qid
            
            print(f"Loaded {len(self.individual_mappings)} individual mappings")
            print(f"Loaded {len(self.family_mappings)} family mappings")
            print(f"Loaded {len(self.property_mappings)} property mappings")
            
        except FileNotFoundError:
            print(f"No existing mappings file found - starting fresh")
    
    def ensure_properties_exist(self):
        """Create any missing properties we need."""
        print("Ensuring required properties exist...")
        
        for prop_name, prop_label in self.needed_properties.items():
            if prop_name in self.property_mappings:
                continue  # Already exists
            
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
            found = False
            
            if 'search' in data:
                for result in data['search']:
                    if result['label'].lower() == prop_label.lower():
                        self.property_mappings[prop_name] = result['id']
                        print(f"Found existing property {result['id']}: {prop_label}")
                        found = True
                        break
            
            if not found:
                print(f"Property {prop_label} not found - would need to create")
                # For now, skip creation to avoid conflicts
            
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
                # Parse record fields
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
    
    def create_individual_item(self, individual_data):
        """Create a new individual item."""
        # Build labels and descriptions
        labels = {'en': {'language': 'en', 'value': 'Japanese Individual'}}
        descriptions = {'en': {'language': 'en', 'value': 'Character from Japanese genealogy'}}
        
        if 'full_name' in individual_data.get('other_fields', {}):
            labels['en']['value'] = individual_data['other_fields']['full_name']
        elif individual_data.get('names'):
            name = individual_data['names'][0].replace('/', ' ').strip()
            if name:
                labels['en']['value'] = name
        
        # Instance of Japanese genealogy character - we'll need a different class
        claims = []
        if 'instance_of' in self.property_mappings:
            # Note: Would need to create Q-item for "Japanese genealogy character"
            claims.append({
                'mainsnak': {
                    'snaktype': 'value',
                    'property': self.property_mappings['instance_of'],
                    'datavalue': {
                        'value': {'entity-type': 'item', 'numeric-id': 279},  # Temporary - reuse Gaiad
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
        
        params = {
            'action': 'wbeditentity',
            'new': 'item',
            'data': json.dumps(item_data),
            'format': 'json',
            'token': self.csrf_token
        }
        
        try:
            response = self.session.post(self.api_url, data=params)
            result = response.json()
            
            if 'entity' in result:
                qid = result['entity']['id']
                print(f"Created Japanese individual {qid}: {labels['en']['value']}")
                return qid
            else:
                print(f"Error creating Japanese individual: {result}")
                return None
                
        except Exception as e:
            print(f"Exception creating Japanese individual: {e}")
            return None
    
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
    
    def run_japanese_upload(self, gedcom_file):
        """Main function for Japanese genealogy upload."""
        print("Starting Japanese genealogy upload...")
        
        # Setup
        if not self.login():
            return False
        
        self.load_existing_mappings()
        self.parse_gedcom_file(gedcom_file)
        self.ensure_properties_exist()
        
        # Create individuals that don't exist yet
        remaining_individuals = []
        for gedcom_id, individual_data in self.individuals_data.items():
            if gedcom_id not in self.individual_mappings:
                remaining_individuals.append((gedcom_id, individual_data))
        
        print(f"Found {len(remaining_individuals)} Japanese individuals to upload")
        
        # Upload in small batches
        batch_size = 10
        for i in range(0, len(remaining_individuals), batch_size):
            batch = remaining_individuals[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1}: items {i+1} to {min(i+batch_size, len(remaining_individuals))}")
            
            for gedcom_id, individual_data in batch:
                qid = self.create_individual_item(individual_data)
                if qid:
                    self.individual_mappings[gedcom_id] = qid
                    self.stats['items_created'] += 1
                    time.sleep(0.2)  # Rate limiting
            
            # Save mappings after each batch
            self.save_mappings()
            print(f"Batch completed. Total created: {self.stats['items_created']}")
            time.sleep(2)  # Pause between batches
        
        print(f"\nJapanese upload completed!")
        print(f"Items created: {self.stats['items_created']}")
        
        return True

def main():
    if len(sys.argv) != 2:
        print("Usage: python japanese_repair_upload.py <japanese_gedcom_file>")
        print("Example: python japanese_repair_upload.py \"C:\\path\\to\\japanese_genealogy.ged\"")
        sys.exit(1)
    
    gedcom_file = sys.argv[1]
    
    uploader = JapaneseRepairUpload("Immanuelle", "1996ToOmega!")
    success = uploader.run_japanese_upload(gedcom_file)
    
    if success:
        print("Japanese upload completed successfully!")
    else:
        print("Japanese upload failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()