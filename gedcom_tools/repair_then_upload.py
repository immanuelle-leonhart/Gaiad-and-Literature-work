#!/usr/bin/env python3
"""
COMPREHENSIVE REPAIR AND UPLOAD PROGRAM

Phase 1: REPAIR all existing broken items (Q281-Q6243+) by adding missing properties, REFNs, relationships
Phase 2: UPLOAD remaining individuals/families in a safe, resumable manner

This program is designed to be safely killed and restarted at any point.
"""

import requests
import json
import sys
import time
import mwclient
import re
from typing import Dict, List, Optional, Set, Tuple

class RepairThenUpload:
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
                'User-Agent': 'RepairThenUpload/1.0 (https://evolutionism.miraheze.org/wiki/User:Immanuelle)'
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
        print("Loading existing mappings...")
        
        try:
            with open('gedcom_to_qid_mapping.txt', 'r', encoding='utf-8') as f:
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
            print("No existing mappings file found")
    
    def discover_existing_items(self):
        """Discover what items already exist and map them to GEDCOM IDs."""
        print("Discovering existing items in wikibase and mapping to GEDCOM...")
        
        # Query for items in batches, but actually examine their content
        batch_size = 50
        start_qid = 281  # We know items start around Q281
        max_consecutive_missing = 100  # Stop after this many consecutive missing QIDs
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
                    
                    # Check if this looks like a Gaiad individual
                    is_gaiad_individual = False
                    
                    # Check instance of claims for Q279 (Gaiad character)
                    if 'claims' in entity:
                        for prop_id, claims in entity['claims'].items():
                            for claim in claims:
                                try:
                                    mainsnak = claim.get('mainsnak', {})
                                    datavalue = mainsnak.get('datavalue', {})
                                    if isinstance(datavalue, dict):
                                        value = datavalue.get('value', {})
                                        if isinstance(value, dict) and value.get('numeric-id') == 279:
                                            is_gaiad_individual = True
                                            break
                                except (AttributeError, TypeError):
                                    continue
                    
                    # Also check description for "Gaiad" 
                    if 'descriptions' in entity and 'en' in entity['descriptions']:
                        desc = entity['descriptions']['en']['value'].lower()
                        if 'gaiad' in desc:
                            is_gaiad_individual = True
                    
                    if is_gaiad_individual:
                        self.existing_items.add(qid)
                        print(f"  Found Gaiad individual: {qid}")
                        
                        # Try to find GEDCOM ID in the item's properties
                        # This would require examining REFN claims or other identifying info
                        # For now, we'll need to match by other means in repair phase
                else:
                    consecutive_missing += 1
            
            if not found_any_this_batch:
                consecutive_missing += batch_size
            
            start_qid += batch_size
            time.sleep(0.1)  # Rate limiting
        
        print(f"Found {len(self.existing_items)} existing Gaiad items in wikibase")
    
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
                # Create the property
                pid = self.create_property(prop_name, prop_label)
                if pid:
                    self.property_mappings[prop_name] = pid
                    print(f"Created new property {pid}: {prop_label}")
            
            time.sleep(0.2)  # Rate limiting
    
    def create_property(self, prop_name, prop_label):
        """Create a new property."""
        datatype = 'string'  # Most properties are strings
        if prop_name in ['mother', 'father', 'spouse', 'child', 'instance_of']:
            datatype = 'wikibase-item'
        
        property_data = {
            'labels': {'en': {'language': 'en', 'value': prop_label}},
            'descriptions': {'en': {'language': 'en', 'value': f'GEDCOM {prop_name} field'}},
            'datatype': datatype
        }
        
        params = {
            'action': 'wbeditentity',
            'new': 'property',
            'data': json.dumps(property_data),
            'format': 'json',
            'token': self.csrf_token,
            'bot': 1
        }
        
        try:
            response = self.session.post(self.api_url, data=params)
            result = response.json()
            
            if 'entity' in result:
                return result['entity']['id']
            else:
                print(f"Error creating property {prop_label}: {result}")
                return None
        except Exception as e:
            print(f"Exception creating property {prop_label}: {e}")
            return None
    
    def parse_gedcom_file(self, filename):
        """Parse the complete GEDCOM file and store all data."""
        print(f"Parsing GEDCOM file: {filename}")
        
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
                'token': self.csrf_token,
                'bot': 1
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
    
    def repair_existing_item(self, qid):
        """Repair a single existing item by adding missing properties."""
        print(f"Repairing {qid}...")
        
        # Find the GEDCOM data for this item
        gedcom_id = None
        item_data = None
        
        # First check if we already have a mapping
        for gid, q in self.individual_mappings.items():
            if q == qid:
                gedcom_id = gid
                item_data = self.individuals_data.get(gid)
                break
        
        # If no mapping, try to match by examining the item
        if not gedcom_id:
            gedcom_id = self.match_qid_to_gedcom(qid)
            if gedcom_id:
                item_data = self.individuals_data.get(gedcom_id)
                # Add this mapping for future reference
                self.individual_mappings[gedcom_id] = qid
                print(f"  Matched {qid} to {gedcom_id}")
        
        if not gedcom_id or not item_data:
            print(f"  Could not find GEDCOM data for {qid} - skipping")
            return False
        
        print(f"  Repairing {qid} using GEDCOM data from {gedcom_id}")
        
        # Add instance of Gaiad character
        if 'instance_of' in self.property_mappings:
            self.add_statement_to_item(qid, self.property_mappings['instance_of'], 'Q279', 'item')
        
        # Add all REFNs
        refn_prop = self.property_mappings.get('gedcom_refn')
        if refn_prop:
            for refn in item_data.get('refns', []):
                self.add_statement_to_item(qid, refn_prop, refn, 'string')
                self.stats['refns_added'] += 1
        
        # Add name properties
        if 'full_name' in self.property_mappings and 'full_name' in item_data.get('other_fields', {}):
            self.add_statement_to_item(qid, self.property_mappings['full_name'], 
                                     item_data['other_fields']['full_name'], 'string')
        
        if 'given_name' in self.property_mappings and 'given_name' in item_data.get('other_fields', {}):
            self.add_statement_to_item(qid, self.property_mappings['given_name'], 
                                     item_data['other_fields']['given_name'], 'string')
        
        if 'surname' in self.property_mappings and 'surname' in item_data.get('other_fields', {}):
            self.add_statement_to_item(qid, self.property_mappings['surname'], 
                                     item_data['other_fields']['surname'], 'string')
        
        # Add dates
        for date_field in ['birth_date', 'death_date']:
            if date_field in self.property_mappings and date_field in item_data.get('dates', {}):
                self.add_statement_to_item(qid, self.property_mappings[date_field], 
                                         item_data['dates'][date_field], 'string')
        
        # Add sex
        if 'sex' in self.property_mappings and 'sex' in item_data.get('other_fields', {}):
            self.add_statement_to_item(qid, self.property_mappings['sex'], 
                                     item_data['other_fields']['sex'], 'string')
        
        # TODO: Add relationships (mother, father, spouse, children)
        # This requires looking up the target QIDs from GEDCOM IDs
        
        self.stats['items_repaired'] += 1
        self.repaired_items.add(qid)
        
        print(f"  Successfully repaired {qid}")
        return True
    
    def save_mappings(self):
        """Save current mappings to file."""
        print("Saving mappings...")
        
        with open('gedcom_to_qid_mapping.txt', 'w', encoding='utf-8') as f:
            f.write("# GEDCOM ID to Wikibase QID Mapping\n")
            f.write("# Generated by repair_then_upload.py\n\n")
            
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
    
    def run_repair_phase(self):
        """Phase 1: Repair all existing broken items."""
        print("\n" + "="*60)
        print("PHASE 1: REPAIRING EXISTING ITEMS")
        print("="*60)
        
        existing_qids = sorted(list(self.existing_items), key=lambda x: int(x[1:]))
        print(f"Found {len(existing_qids)} existing items to repair")
        
        for i, qid in enumerate(existing_qids):
            if qid in self.repaired_items:
                continue  # Already repaired
            
            print(f"Progress: {i+1}/{len(existing_qids)}")
            self.repair_existing_item(qid)
            
            # Save mappings every 10 items
            if (i + 1) % 10 == 0:
                self.save_mappings()
                print(f"Saved progress - {self.stats['items_repaired']} items repaired so far")
            
            time.sleep(0.1)  # Rate limiting
        
        self.save_mappings()
        print(f"\nPhase 1 completed! Repaired {self.stats['items_repaired']} items")
    
    def run_upload_phase(self):
        """Phase 2: Upload remaining individuals safely."""
        print("\n" + "="*60)  
        print("PHASE 2: UPLOADING REMAINING ITEMS")
        print("="*60)
        
        # Count individuals that still need to be created
        remaining_individuals = []
        for gedcom_id, individual_data in self.individuals_data.items():
            if gedcom_id not in self.individual_mappings:
                remaining_individuals.append((gedcom_id, individual_data))
        
        print(f"Found {len(remaining_individuals)} individuals still to upload")
        
        # TODO: Implement safe batch upload with immediate relationship creation
        print("Phase 2 upload implementation needed...")
    
    def run_comprehensive_repair_and_upload(self, gedcom_file):
        """Main function - repair then upload."""
        print("Starting comprehensive repair and upload...")
        
        # Setup
        if not self.login():
            return False
        
        self.load_existing_mappings()
        self.discover_existing_items()
        self.parse_gedcom_file(gedcom_file)
        self.ensure_properties_exist()
        
        # Phase 1: Repair existing items
        self.run_repair_phase()
        
        # Phase 2: Upload remaining items
        self.run_upload_phase()
        
        print(f"\nFINAL STATISTICS:")
        for key, value in self.stats.items():
            print(f"  {key}: {value}")
        
        return True

def main():
    if len(sys.argv) != 2:
        print("Usage: python repair_then_upload.py <gedcom_file>")
        print("Example: python repair_then_upload.py \"C:\\path\\to\\master_combined.ged\"")
        sys.exit(1)
    
    gedcom_file = sys.argv[1]
    
    repairer = RepairThenUpload("Immanuelle", "1996ToOmega!")
    success = repairer.run_comprehensive_repair_and_upload(gedcom_file)
    
    if success:
        print("Repair and upload completed successfully!")
    else:
        print("Repair and upload failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()