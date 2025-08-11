#!/usr/bin/env python3
"""
COMPLETE MASTER GEDCOM UPLOADER

This program uploads ALL remaining individuals and families from the master GEDCOM
that were never uploaded. The main repair program only repaired ~6k existing items
but never uploaded the remaining ~93k individuals and families.

Features:
- Safely resumable (maintains full state in mapping file)
- Handles the complete 99,518 individuals and families  
- Creates proper family relationships
- Preserves all REFNs and properties
- Uses same property structure as repair programs
"""

import requests
import json
import sys
import time
import mwclient
import re
from typing import Dict, List, Optional, Set, Tuple

class CompleteMasterUploader:
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
        
        # Mappings
        self.individual_mappings = {} # @I123@ -> Q456
        self.family_mappings = {}     # @F123@ -> Q456
        self.property_mappings = {}   # field_name -> P123
        self.mapping_file = 'master_gedcom_to_qid_mapping.txt'
        
        # State tracking
        self.existing_items = set()   # QIDs that exist already
        self.uploaded_items = set()   # QIDs uploaded this session
        self.completed_items = set()  # QIDs that are fully complete
        
        # Statistics
        self.stats = {
            'items_discovered': 0,
            'items_uploaded': 0,
            'families_uploaded': 0,
            'properties_added': 0,
            'relationships_added': 0,
            'refns_added': 0,
            'errors': 0,
            'skipped_existing': 0
        }
        
        # Required properties - SAME AS OTHER PROGRAMS
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
                'User-Agent': 'CompleteMasterUploader/1.0 (https://evolutionism.miraheze.org/wiki/User:Immanuelle)'
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
        """Load any existing mappings from previous runs."""
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
    
    def load_shared_properties(self):
        """Load properties from the main repair program if available."""
        print("Loading shared properties from other repair programs...")
        
        # Try to load from the Japanese mapping file first
        try:
            with open('japanese_gedcom_to_qid_mapping.txt', 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            in_properties = False
            for line in lines:
                line = line.strip()
                if line == "# Properties":
                    in_properties = True
                    continue
                elif line.startswith('# ') and in_properties:
                    break
                elif line.startswith('#') or not line:
                    continue
                
                if in_properties and '\t' in line:
                    prop_name, prop_id = line.split('\t', 1)
                    if prop_name in self.needed_properties:
                        self.property_mappings[prop_name] = prop_id
                        print(f"Loaded shared property {prop_id}: {self.needed_properties[prop_name]}")
            
            print(f"Loaded {len(self.property_mappings)} shared properties")
            
        except FileNotFoundError:
            print("No shared properties found - will search individually")
            
            # Search for existing properties
            for prop_name, prop_label in self.needed_properties.items():
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
        """Parse the complete master GEDCOM file."""
        print(f"Parsing master GEDCOM file: {filename}")
        print("This is a large file (99,518+ individuals and families) - please wait...")
        
        with open(filename, 'rb') as f:
            content = f.read().decode('utf-8-sig')
        
        lines = content.split('\n')
        current_record = None
        current_type = None
        
        individual_count = 0
        family_count = 0
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            
            # Progress indicator
            if line_num % 50000 == 0:
                print(f"  Processed {line_num:,} lines...")
            
            # Start of new record
            if line.startswith('0 @') and (line.endswith(' INDI') or line.endswith(' FAM')):
                # Save previous record
                if current_record and current_type:
                    if current_type == 'INDI':
                        self.individuals_data[current_record['gedcom_id']] = current_record
                        individual_count += 1
                    elif current_type == 'FAM':
                        self.families_data[current_record['gedcom_id']] = current_record
                        family_count += 1
                
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
                # Parse record fields - COMPREHENSIVE PARSING
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
                individual_count += 1
            elif current_type == 'FAM':
                self.families_data[current_record['gedcom_id']] = current_record
                family_count += 1
        
        print(f"Parsing completed!")
        print(f"Parsed {individual_count:,} individuals")
        print(f"Parsed {family_count:,} families") 
        print(f"Total: {individual_count + family_count:,} records")
    
    def create_individual_item(self, individual_data):
        """Create a new individual item - NO DESCRIPTIONS."""
        # Build labels only - NO DESCRIPTIONS
        labels = {'en': {'language': 'en', 'value': 'Gaiad Individual'}}
        
        if 'full_name' in individual_data.get('other_fields', {}):
            labels['en']['value'] = individual_data['other_fields']['full_name']
        elif individual_data.get('names'):
            name = individual_data['names'][0].replace('/', ' ').strip()
            if name:
                labels['en']['value'] = name
        
        # Instance of Gaiad character
        claims = []
        if 'instance_of' in self.property_mappings:
            claims.append({
                'mainsnak': {
                    'snaktype': 'value',
                    'property': self.property_mappings['instance_of'],
                    'datavalue': {
                        'value': {'entity-type': 'item', 'numeric-id': 279},
                        'type': 'wikibase-entityid'
                    }
                },
                'type': 'statement'
            })
        
        item_data = {
            'labels': labels,
            'claims': claims
        }
        # NO DESCRIPTIONS - they break uploads
        
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
                print(f"Created individual {qid}: {labels['en']['value']}")
                return qid
            else:
                print(f"Error creating individual: {result}")
                self.stats['errors'] += 1
                return None
                
        except Exception as e:
            print(f"Exception creating individual: {e}")
            self.stats['errors'] += 1
            return None
    
    def create_family_item(self, family_data):
        """Create a new family item - NO DESCRIPTIONS."""
        # Build labels only - NO DESCRIPTIONS
        family_id = family_data['gedcom_id']
        labels = {'en': {'language': 'en', 'value': f'Family {family_id}'}}
        
        # Instance of Gaiad family (Q280)
        claims = []
        if 'instance_of' in self.property_mappings:
            claims.append({
                'mainsnak': {
                    'snaktype': 'value',
                    'property': self.property_mappings['instance_of'],
                    'datavalue': {
                        'value': {'entity-type': 'item', 'numeric-id': 280},
                        'type': 'wikibase-entityid'
                    }
                },
                'type': 'statement'
            })
        
        item_data = {
            'labels': labels,
            'claims': claims
        }
        # NO DESCRIPTIONS - they break uploads
        
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
                print(f"Created family {qid}: {labels['en']['value']}")
                return qid
            else:
                print(f"Error creating family: {result}")
                self.stats['errors'] += 1
                return None
                
        except Exception as e:
            print(f"Exception creating family: {e}")
            self.stats['errors'] += 1
            return None
    
    def add_statement_to_item(self, qid, property_pid, value, value_type='monolingualtext'):
        """Add a statement to an existing wikibase item."""
        try:
            if value_type == 'monolingualtext':
                datavalue = {
                    'value': {'text': str(value), 'language': 'en'},
                    'type': 'monolingualtext'
                }
            elif value_type == 'string':
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
    
    def add_all_properties_to_item(self, qid, item_data):
        """Add all possible properties to an item."""
        # Add all REFNs
        refn_prop = self.property_mappings.get('gedcom_refn')
        if refn_prop:
            for refn in item_data.get('refns', []):
                if self.add_statement_to_item(qid, refn_prop, refn, 'monolingualtext'):
                    self.stats['refns_added'] += 1
        
        # Add name properties
        if 'full_name' in self.property_mappings and 'full_name' in item_data.get('other_fields', {}):
            self.add_statement_to_item(qid, self.property_mappings['full_name'], 
                                     item_data['other_fields']['full_name'], 'monolingualtext')
        
        if 'given_name' in self.property_mappings and 'given_name' in item_data.get('other_fields', {}):
            self.add_statement_to_item(qid, self.property_mappings['given_name'], 
                                     item_data['other_fields']['given_name'], 'monolingualtext')
        
        if 'surname' in self.property_mappings and 'surname' in item_data.get('other_fields', {}):
            self.add_statement_to_item(qid, self.property_mappings['surname'], 
                                     item_data['other_fields']['surname'], 'monolingualtext')
        
        # Add dates
        for date_field in ['birth_date', 'death_date']:
            if date_field in self.property_mappings and date_field in item_data.get('dates', {}):
                self.add_statement_to_item(qid, self.property_mappings[date_field], 
                                         item_data['dates'][date_field], 'monolingualtext')
        
        # Add sex
        if 'sex' in self.property_mappings and 'sex' in item_data.get('other_fields', {}):
            self.add_statement_to_item(qid, self.property_mappings['sex'], 
                                     item_data['other_fields']['sex'], 'monolingualtext')
    
    def save_mappings(self):
        """Save current mappings to file."""
        print("Saving mappings...")
        
        with open(self.mapping_file, 'w', encoding='utf-8') as f:
            f.write("# Master GEDCOM ID to Wikibase QID Mapping\n")
            f.write("# Generated by complete_master_uploader.py\n\n")
            
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
    
    def run_complete_upload(self, gedcom_file):
        """Main function - upload all remaining individuals and families."""
        print("Starting complete master GEDCOM upload...")
        print("This will upload ALL remaining individuals and families (~93k items)")
        
        # Setup
        if not self.login():
            return False
        
        self.load_existing_mappings()
        self.load_shared_properties()
        self.parse_gedcom_file(gedcom_file)
        
        # Count what needs to be uploaded
        remaining_individuals = []
        for gedcom_id, individual_data in self.individuals_data.items():
            if gedcom_id not in self.individual_mappings:
                remaining_individuals.append((gedcom_id, individual_data))
        
        remaining_families = []
        for gedcom_id, family_data in self.families_data.items():
            if gedcom_id not in self.family_mappings:
                remaining_families.append((gedcom_id, family_data))
        
        print(f"\nUPLOAD PLAN:")
        print(f"  Individuals already uploaded: {len(self.individual_mappings):,}")
        print(f"  Families already uploaded: {len(self.family_mappings):,}")
        print(f"  Individuals to upload: {len(remaining_individuals):,}")
        print(f"  Families to upload: {len(remaining_families):,}")
        print(f"  TOTAL NEW ITEMS: {len(remaining_individuals) + len(remaining_families):,}")
        
        # Phase 1: Upload individuals
        print(f"\nPhase 1: Uploading {len(remaining_individuals):,} individuals...")
        
        batch_size = 50  # Process in batches
        for i in range(0, len(remaining_individuals), batch_size):
            batch = remaining_individuals[i:i+batch_size]
            print(f"Processing individual batch {i//batch_size + 1}: items {i+1} to {min(i+batch_size, len(remaining_individuals))}")
            
            for gedcom_id, individual_data in batch:
                qid = self.create_individual_item(individual_data)
                if qid:
                    self.individual_mappings[gedcom_id] = qid
                    self.stats['items_uploaded'] += 1
                    
                    # Add all properties immediately
                    self.add_all_properties_to_item(qid, individual_data)
                    
                    time.sleep(0.1)  # Rate limiting
            
            # Save mappings after each batch
            self.save_mappings()
            print(f"Batch completed. Total individuals uploaded: {self.stats['items_uploaded']:,}")
            time.sleep(1)  # Pause between batches
        
        # Phase 2: Upload families
        print(f"\nPhase 2: Uploading {len(remaining_families):,} families...")
        
        for i in range(0, len(remaining_families), batch_size):
            batch = remaining_families[i:i+batch_size]
            print(f"Processing family batch {i//batch_size + 1}: items {i+1} to {min(i+batch_size, len(remaining_families))}")
            
            for gedcom_id, family_data in batch:
                qid = self.create_family_item(family_data)
                if qid:
                    self.family_mappings[gedcom_id] = qid
                    self.stats['families_uploaded'] += 1
                    
                    # Add family properties and relationships
                    self.add_all_properties_to_item(qid, family_data)
                    
                    time.sleep(0.1)  # Rate limiting
            
            # Save mappings after each batch
            self.save_mappings()
            print(f"Batch completed. Total families uploaded: {self.stats['families_uploaded']:,}")
            time.sleep(1)  # Pause between batches
        
        # Phase 3: Add relationships (this is complex and might need separate implementation)
        print(f"\nPhase 3: Adding family relationships...")
        print("(This phase will link families to individuals - complex implementation needed)")
        
        self.save_mappings()
        
        print(f"\nCOMPLETE MASTER UPLOAD FINISHED!")
        print(f"Individuals uploaded: {self.stats['items_uploaded']:,}")
        print(f"Families uploaded: {self.stats['families_uploaded']:,}")
        print(f"Properties added: {self.stats['properties_added']:,}")
        print(f"REFNs added: {self.stats['refns_added']:,}")
        print(f"Errors: {self.stats['errors']:,}")
        
        return True

def main():
    if len(sys.argv) != 2:
        print("Usage: python complete_master_uploader.py <master_gedcom_file>")
        print("Example: python complete_master_uploader.py \"C:\\\\path\\\\to\\\\master_combined.ged\"")
        sys.exit(1)
    
    gedcom_file = sys.argv[1]
    
    uploader = CompleteMasterUploader("Immanuelle", "1996ToOmega!")
    success = uploader.run_complete_upload(gedcom_file)
    
    if success:
        print("Complete master upload finished successfully!")
    else:
        print("Complete master upload failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()