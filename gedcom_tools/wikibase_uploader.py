#!/usr/bin/env python3
"""
Upload GEDCOM data to evolutionism.miraheze.org Wikibase.
Creates items for individuals and families with genealogical relationships.
"""

import requests
import json
import sys
import time
import re
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import quote

class WikibaseUploader:
    def __init__(self, api_url: str, username: str, password: str):
        self.api_url = api_url
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.csrf_token = None
        self.logged_in = False
        
        # Track created items
        self.individual_mappings = {}  # @I123@ -> Q456
        self.family_mappings = {}      # @F123@ -> Q456
        self.current_qid = None        # Will be determined from existing items
        
        # Statistics
        self.stats = {
            'individuals_processed': 0,
            'individuals_created': 0,
            'families_processed': 0,
            'families_created': 0,
            'relationships_added': 0,
            'errors': 0
        }
    
    def login(self):
        """Login to the wiki and get CSRF token."""
        print(f"Logging in as {self.username}...")
        
        # Get login token
        login_token_params = {
            'action': 'query',
            'meta': 'tokens',
            'type': 'login',
            'format': 'json'
        }
        
        response = self.session.get(self.api_url, params=login_token_params)
        response.raise_for_status()
        data = response.json()
        login_token = data['query']['tokens']['logintoken']
        
        # Login
        login_params = {
            'action': 'login',
            'lgname': self.username,
            'lgpassword': self.password,
            'lgtoken': login_token,
            'format': 'json'
        }
        
        response = self.session.post(self.api_url, data=login_params)
        response.raise_for_status()
        login_result = response.json()
        
        if login_result['login']['result'] != 'Success':
            raise Exception(f"Login failed: {login_result['login']['result']}")
        
        # Get CSRF token for editing
        csrf_params = {
            'action': 'query',
            'meta': 'tokens',
            'format': 'json'
        }
        
        response = self.session.get(self.api_url, params=csrf_params)
        response.raise_for_status()
        data = response.json()
        self.csrf_token = data['query']['tokens']['csrftoken']
        self.logged_in = True
        
        print("Successfully logged in!")
    
    def get_next_qid(self) -> int:
        """Find the next available Q ID by checking existing items."""
        if self.current_qid is not None:
            self.current_qid += 1
            return self.current_qid
        
        # Start checking from Q1000 to avoid conflicts with existing items
        test_qid = 1000
        while True:
            try:
                params = {
                    'action': 'wbgetentities',
                    'ids': f'Q{test_qid}',
                    'format': 'json'
                }
                response = self.session.get(self.api_url, params=params)
                data = response.json()
                
                if 'entities' in data and f'Q{test_qid}' in data['entities']:
                    # This QID exists, try next
                    test_qid += 1
                else:
                    # This QID is available
                    self.current_qid = test_qid
                    return test_qid
                    
            except Exception as e:
                print(f"Error checking Q{test_qid}: {e}")
                test_qid += 1
                if test_qid > 2000:  # Safety limit
                    raise Exception("Cannot find available QID")
    
    def create_item(self, labels: Dict[str, str], descriptions: Dict[str, str] = None) -> str:
        """Create a new Wikibase item."""
        if not self.logged_in:
            raise Exception("Not logged in")
        
        data = {
            'labels': labels
        }
        
        if descriptions:
            data['descriptions'] = descriptions
        
        params = {
            'action': 'wbeditentity',
            'new': 'item',
            'data': json.dumps(data),
            'token': self.csrf_token,
            'format': 'json'
        }
        
        try:
            response = self.session.post(self.api_url, data=params)
            response.raise_for_status()
            result = response.json()
            
            if 'success' in result and result['success'] == 1:
                qid = result['entity']['id']
                print(f"Created item {qid}: {labels.get('en', 'No label')}")
                return qid
            else:
                raise Exception(f"Failed to create item: {result}")
                
        except Exception as e:
            print(f"Error creating item: {e}")
            self.stats['errors'] += 1
            return None
    
    def add_claim(self, qid: str, property_id: str, target_qid: str):
        """Add a claim (statement) to an item."""
        if not self.logged_in:
            raise Exception("Not logged in")
        
        claim_data = {
            'mainsnak': {
                'snaktype': 'value',
                'property': property_id,
                'datavalue': {
                    'value': {'entity-type': 'item', 'numeric-id': int(target_qid[1:])},
                    'type': 'wikibase-entityid'
                }
            },
            'type': 'statement'
        }
        
        params = {
            'action': 'wbcreateclaim',
            'entity': qid,
            'snaktype': 'value',
            'property': property_id,
            'value': json.dumps({'entity-type': 'item', 'numeric-id': int(target_qid[1:])}),
            'token': self.csrf_token,
            'format': 'json'
        }
        
        try:
            response = self.session.post(self.api_url, data=params)
            response.raise_for_status()
            result = response.json()
            
            if 'success' in result and result['success'] == 1:
                self.stats['relationships_added'] += 1
                return True
            else:
                print(f"Failed to add claim {qid} -> {property_id} -> {target_qid}: {result}")
                return False
                
        except Exception as e:
            print(f"Error adding claim: {e}")
            self.stats['errors'] += 1
            return False
    
    def parse_gedcom_individual(self, lines: List[str], start_idx: int) -> Tuple[Dict, int]:
        """Parse an individual record from GEDCOM lines."""
        individual = {
            'id': None,
            'names': [],
            'birth_date': None,
            'death_date': None,
            'parents_family': None,
            'spouse_families': [],
            'sex': None,
            'notes': [],
            'refns': []
        }
        
        i = start_idx
        if not lines[i].startswith('0 @') or not lines[i].endswith(' INDI'):
            return individual, i
        
        # Get individual ID
        parts = lines[i].split()
        individual['id'] = parts[1]  # @I123@
        i += 1
        
        # Process individual data
        while i < len(lines) and not lines[i].startswith('0 '):
            line = lines[i].strip()
            
            if line.startswith('1 NAME '):
                name = line[7:].strip()
                # Clean up name format
                name = name.replace('/', ' ').strip()
                if name:
                    individual['names'].append(name)
                    
            elif line.startswith('1 SEX '):
                individual['sex'] = line[6:].strip()
                
            elif line.startswith('1 BIRT'):
                # Look for date on next line
                if i + 1 < len(lines) and lines[i + 1].startswith('2 DATE '):
                    individual['birth_date'] = lines[i + 1][7:].strip()
                    
            elif line.startswith('1 DEAT'):
                # Look for date on next line
                if i + 1 < len(lines) and lines[i + 1].startswith('2 DATE '):
                    individual['death_date'] = lines[i + 1][7:].strip()
                    
            elif line.startswith('1 FAMC '):
                individual['parents_family'] = line[7:].strip()
                
            elif line.startswith('1 FAMS '):
                individual['spouse_families'].append(line[7:].strip())
                
            elif line.startswith('1 NOTE '):
                note = line[7:].strip()
                individual['notes'].append(note)
                
            elif line.startswith('1 REFN '):
                refn = line[7:].strip()
                individual['refns'].append(refn)
            
            i += 1
        
        return individual, i
    
    def parse_gedcom_family(self, lines: List[str], start_idx: int) -> Tuple[Dict, int]:
        """Parse a family record from GEDCOM lines."""
        family = {
            'id': None,
            'husband': None,
            'wife': None,
            'children': [],
            'marriage_date': None,
            'notes': []
        }
        
        i = start_idx
        if not lines[i].startswith('0 @') or not lines[i].endswith(' FAM'):
            return family, i
        
        # Get family ID
        parts = lines[i].split()
        family['id'] = parts[1]  # @F123@
        i += 1
        
        # Process family data
        while i < len(lines) and not lines[i].startswith('0 '):
            line = lines[i].strip()
            
            if line.startswith('1 HUSB '):
                family['husband'] = line[7:].strip()
                
            elif line.startswith('1 WIFE '):
                family['wife'] = line[7:].strip()
                
            elif line.startswith('1 CHIL '):
                family['children'].append(line[7:].strip())
                
            elif line.startswith('1 MARR'):
                # Look for date on next line
                if i + 1 < len(lines) and lines[i + 1].startswith('2 DATE '):
                    family['marriage_date'] = lines[i + 1][7:].strip()
                    
            elif line.startswith('1 NOTE '):
                note = line[7:].strip()
                family['notes'].append(note)
            
            i += 1
        
        return family, i
    
    def process_gedcom_file(self, filename: str):
        """Process the entire GEDCOM file and upload to Wikibase."""
        print(f"Processing GEDCOM file: {filename}")
        
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        lines = [line.rstrip('\r\n') for line in lines]
        
        individuals = []
        families = []
        
        # First pass: parse all individuals and families
        print("Parsing GEDCOM records...")
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith('0 @') and line.endswith(' INDI'):
                individual, next_i = self.parse_gedcom_individual(lines, i)
                if individual['id']:
                    individuals.append(individual)
                    self.stats['individuals_processed'] += 1
                i = next_i
                
            elif line.startswith('0 @') and line.endswith(' FAM'):
                family, next_i = self.parse_gedcom_family(lines, i)
                if family['id']:
                    families.append(family)
                    self.stats['families_processed'] += 1
                i = next_i
                
            else:
                i += 1
        
        print(f"Found {len(individuals)} individuals and {len(families)} families")
        
        # Second pass: create Wikibase items for individuals
        print("Creating individual items...")
        for individual in individuals:
            try:
                # Create label from name
                name = individual['names'][0] if individual['names'] else f"Individual {individual['id']}"
                
                # Create description
                description_parts = []
                if individual['birth_date']:
                    description_parts.append(f"b. {individual['birth_date']}")
                if individual['death_date']:
                    description_parts.append(f"d. {individual['death_date']}")
                
                description = ', '.join(description_parts) if description_parts else "Person"
                
                labels = {'en': name}
                descriptions = {'en': description} if description != "Person" else None
                
                qid = self.create_item(labels, descriptions)
                if qid:
                    self.individual_mappings[individual['id']] = qid
                    self.stats['individuals_created'] += 1
                    
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error creating individual {individual['id']}: {e}")
                self.stats['errors'] += 1
        
        # Third pass: create Wikibase items for families
        print("Creating family items...")
        for family in families:
            try:
                # Create label for family
                husband_name = "Unknown"
                wife_name = "Unknown"
                
                if family['husband'] and family['husband'] in self.individual_mappings:
                    # Find husband's name from individuals list
                    for ind in individuals:
                        if ind['id'] == family['husband']:
                            husband_name = ind['names'][0] if ind['names'] else "Unknown"
                            break
                
                if family['wife'] and family['wife'] in self.individual_mappings:
                    # Find wife's name from individuals list
                    for ind in individuals:
                        if ind['id'] == family['wife']:
                            wife_name = ind['names'][0] if ind['names'] else "Unknown"
                            break
                
                family_name = f"Family of {husband_name} and {wife_name}"
                description = f"Family unit"
                if family['marriage_date']:
                    description += f", married {family['marriage_date']}"
                
                labels = {'en': family_name}
                descriptions = {'en': description}
                
                qid = self.create_item(labels, descriptions)
                if qid:
                    self.family_mappings[family['id']] = qid
                    self.stats['families_created'] += 1
                    
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error creating family {family['id']}: {e}")
                self.stats['errors'] += 1
        
        # Fourth pass: add relationships using existing properties P1 (Parents) and P2 (Spouse family)
        print("Adding relationships...")
        
        for individual in individuals:
            if individual['id'] not in self.individual_mappings:
                continue
                
            individual_qid = self.individual_mappings[individual['id']]
            
            # Add parent family relationship (P1: Parents)
            if individual['parents_family'] and individual['parents_family'] in self.family_mappings:
                parent_family_qid = self.family_mappings[individual['parents_family']]
                success = self.add_claim(individual_qid, 'P1', parent_family_qid)
                if success:
                    print(f"Added parent relationship: {individual_qid} -> P1 -> {parent_family_qid}")
                time.sleep(0.2)
            
            # Add spouse family relationships (P2: Spouse family)
            for spouse_family_id in individual['spouse_families']:
                if spouse_family_id in self.family_mappings:
                    spouse_family_qid = self.family_mappings[spouse_family_id]
                    success = self.add_claim(individual_qid, 'P2', spouse_family_qid)
                    if success:
                        print(f"Added spouse relationship: {individual_qid} -> P2 -> {spouse_family_qid}")
                    time.sleep(0.2)
    
    def generate_qid_mapping_file(self, filename: str):
        """Generate a file mapping GEDCOM IDs to Wikibase QIDs."""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# GEDCOM ID to Wikibase QID Mapping\n")
            f.write("# Generated by wikibase_uploader.py\n\n")
            
            f.write("# Individuals\n")
            for gedcom_id, qid in sorted(self.individual_mappings.items()):
                f.write(f"{gedcom_id}\t{qid}\n")
            
            f.write("\n# Families\n")
            for gedcom_id, qid in sorted(self.family_mappings.items()):
                f.write(f"{gedcom_id}\t{qid}\n")
        
        print(f"QID mapping saved to: {filename}")
    
    def print_statistics(self):
        """Print upload statistics."""
        print("\n=== Upload Statistics ===")
        print(f"Individuals processed: {self.stats['individuals_processed']}")
        print(f"Individuals created: {self.stats['individuals_created']}")
        print(f"Families processed: {self.stats['families_processed']}")
        print(f"Families created: {self.stats['families_created']}")
        print(f"Relationships added: {self.stats['relationships_added']}")
        print(f"Errors encountered: {self.stats['errors']}")
        
        if self.stats['individuals_processed'] > 0:
            success_rate = (self.stats['individuals_created'] / self.stats['individuals_processed']) * 100
            print(f"Individual creation success rate: {success_rate:.1f}%")

def main():
    if len(sys.argv) != 4:
        print("Usage: python wikibase_uploader.py <gedcom_file> <username> <password>")
        print("Example: python wikibase_uploader.py master_combined.ged myusername mypassword")
        sys.exit(1)
    
    gedcom_file = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    
    api_url = "https://evolutionism.miraheze.org/w/api.php"
    
    uploader = WikibaseUploader(api_url, username, password)
    
    try:
        uploader.login()
        uploader.process_gedcom_file(gedcom_file)
        uploader.generate_qid_mapping_file("gedcom_to_qid_mapping.txt")
        uploader.print_statistics()
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()