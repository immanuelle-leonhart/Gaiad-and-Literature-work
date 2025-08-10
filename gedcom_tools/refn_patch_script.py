#!/usr/bin/env python3
"""
Patch script to add missing REFN values to existing wikibase items.
Reads GEDCOM file to extract REFNs and adds them as properties to wikibase items.
"""

import requests
import json
import sys
import time
import re
import mwclient
from typing import Dict, List, Optional, Set, Tuple

class REFNPatcher:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        
        # Use mwclient for authentication
        self.site = mwclient.Site("evolutionism.miraheze.org", path="/w/")
        self.session = requests.Session()
        
        # Set proper User-Agent header
        self.session.headers.update({
            'User-Agent': 'REFNPatcher/1.0 (https://evolutionism.miraheze.org/wiki/User:Immanuelle; genealogy-patch@example.com)'
        })
        
        self.api_url = "https://evolutionism.miraheze.org/w/api.php"
        self.csrf_token = None
        
        # Load existing mappings
        self.individual_mappings = {}  # @I123@ -> Q456
        self.family_mappings = {}      # @F123@ -> Q456
        
        # Statistics
        self.stats = {
            'refns_added': 0,
            'items_patched': 0,
            'errors': 0
        }
        
        # REFN property - we'll need to create this
        self.refn_property_pid = None
    
    def login(self):
        """Login using mwclient."""
        print(f"Logging in as {self.username}...")
        
        try:
            self.site.login(self.username, self.password)
            print("Successfully logged in!")
            
            # Copy cookies to requests session
            for cookie in self.site.connection.cookies:
                self.session.cookies.set(cookie.name, cookie.value, domain=cookie.domain)
            
            # Get CSRF token
            csrf_params = {
                'action': 'query',
                'meta': 'tokens',
                'format': 'json'
            }
            
            response = self.session.get(self.api_url, params=csrf_params)
            data = response.json()
            
            if 'query' in data and 'tokens' in data['query']:
                self.csrf_token = data['query']['tokens']['csrftoken']
                print(f"Got CSRF token: {self.csrf_token[:10]}...")
                return True
            else:
                print(f"Error getting CSRF token: {data}")
                return False
                
        except Exception as e:
            print(f"Login failed: {e}")
            return False
    
    def load_mappings(self):
        """Load existing GEDCOM ID to QID mappings."""
        try:
            with open('gedcom_to_qid_mapping.txt', 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            print("Loading existing mappings...")
            in_individuals = False
            in_families = False
            
            for line in lines:
                line = line.strip()
                if line == "# Individuals":
                    in_individuals = True
                    in_families = False
                    continue
                elif line == "# Families":
                    in_individuals = False
                    in_families = True
                    continue
                elif line.startswith('#') or not line:
                    continue
                
                parts = line.split('\t')
                if len(parts) == 2:
                    gedcom_id, qid = parts
                    if in_individuals:
                        self.individual_mappings[gedcom_id] = qid
                    elif in_families:
                        self.family_mappings[gedcom_id] = qid
            
            print(f"Loaded {len(self.individual_mappings)} individual mappings")
            print(f"Loaded {len(self.family_mappings)} family mappings")
            return True
            
        except FileNotFoundError:
            print("Error: gedcom_to_qid_mapping.txt not found!")
            return False
        except Exception as e:
            print(f"Error loading mappings: {e}")
            return False
    
    def create_refn_property(self):
        """Create the REFN property if it doesn't exist."""
        print("Creating REFN property...")
        
        # Check if REFN property already exists
        search_params = {
            'action': 'wbsearchentities',
            'search': 'GEDCOM REFN',
            'language': 'en',
            'type': 'property',
            'limit': 10,
            'format': 'json'
        }
        
        response = self.session.get(self.api_url, params=search_params)
        data = response.json()
        
        if 'search' in data:
            for result in data['search']:
                if 'gedcom refn' in result['label'].lower():
                    self.refn_property_pid = result['id']
                    print(f"Found existing REFN property: {self.refn_property_pid}")
                    return True
        
        # Create new REFN property
        property_data = {
            'labels': {'en': {'language': 'en', 'value': 'GEDCOM REFN'}},
            'descriptions': {'en': {'language': 'en', 'value': 'External reference number or identifier (GEDCOM REFN field)'}},
            'datatype': 'string'
        }
        
        create_params = {
            'action': 'wbeditentity',
            'new': 'property',
            'data': json.dumps(property_data),
            'format': 'json',
            'token': self.csrf_token
        }
        
        try:
            response = self.session.post(self.api_url, data=create_params)
            result = response.json()
            
            if 'entity' in result:
                self.refn_property_pid = result['entity']['id']
                print(f"Created REFN property: {self.refn_property_pid}")
                return True
            else:
                print(f"Error creating REFN property: {result}")
                return False
                
        except Exception as e:
            print(f"Exception creating REFN property: {e}")
            return False
    
    def add_refn_to_item(self, qid: str, refn_value: str):
        """Add a REFN statement to a wikibase item."""
        try:
            # Create the statement data
            statement_data = {
                'claims': [
                    {
                        'mainsnak': {
                            'snaktype': 'value',
                            'property': self.refn_property_pid,
                            'datavalue': {
                                'value': refn_value,
                                'type': 'string'
                            }
                        },
                        'type': 'statement'
                    }
                ]
            }
            
            edit_params = {
                'action': 'wbeditentity',
                'id': qid,
                'data': json.dumps(statement_data),
                'format': 'json',
                'token': self.csrf_token
            }
            
            response = self.session.post(self.api_url, data=edit_params)
            result = response.json()
            
            if 'entity' in result:
                self.stats['refns_added'] += 1
                return True
            else:
                print(f"Error adding REFN to {qid}: {result}")
                self.stats['errors'] += 1
                return False
                
        except Exception as e:
            print(f"Exception adding REFN to {qid}: {e}")
            self.stats['errors'] += 1
            return False
    
    def parse_gedcom_refns(self, gedcom_file: str):
        """Parse GEDCOM file to extract REFNs for each individual/family."""
        refn_data = {}  # gedcom_id -> [refn1, refn2, ...]
        
        print(f"Parsing {gedcom_file} for REFNs...")
        
        try:
            with open(gedcom_file, 'rb') as f:
                content = f.read().decode('utf-8-sig')
            
            lines = content.split('\n')
            current_id = None
            current_refns = []
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('0 @') and (line.endswith(' INDI') or line.endswith(' FAM')):
                    # Save previous item's REFNs
                    if current_id and current_refns:
                        refn_data[current_id] = current_refns[:]
                    
                    # Start new item
                    current_id = line.split()[1]  # Extract @I123@ or @F123@
                    current_refns = []
                
                elif line.startswith('1 REFN ') and current_id:
                    refn_value = line[7:].strip()
                    if refn_value:
                        current_refns.append(refn_value)
            
            # Don't forget the last item
            if current_id and current_refns:
                refn_data[current_id] = current_refns[:]
            
            print(f"Found REFNs for {len(refn_data)} items")
            return refn_data
            
        except Exception as e:
            print(f"Error parsing GEDCOM file: {e}")
            return {}
    
    def patch_refns(self, gedcom_file: str):
        """Main patching function."""
        if not self.login():
            return False
        
        if not self.load_mappings():
            return False
        
        if not self.create_refn_property():
            return False
        
        # Parse REFNs from GEDCOM
        refn_data = self.parse_gedcom_refns(gedcom_file)
        if not refn_data:
            print("No REFNs found to patch!")
            return False
        
        # Patch each item with its REFNs
        total_items = len(refn_data)
        processed = 0
        
        for gedcom_id, refns in refn_data.items():
            processed += 1
            print(f"Processing {processed}/{total_items}: {gedcom_id}")
            
            # Find the corresponding QID
            qid = None
            if gedcom_id.startswith('@I'):
                qid = self.individual_mappings.get(gedcom_id)
            elif gedcom_id.startswith('@F'):
                qid = self.family_mappings.get(gedcom_id)
            
            if not qid:
                print(f"  No QID mapping found for {gedcom_id}")
                continue
            
            # Add each REFN as a statement
            for refn in refns:
                print(f"  Adding REFN '{refn}' to {qid}")
                if self.add_refn_to_item(qid, refn):
                    print(f"    SUCCESS: Added REFN '{refn}'")
                else:
                    print(f"    ERROR: Failed to add REFN '{refn}'")
            
            self.stats['items_patched'] += 1
            
            # Rate limiting
            time.sleep(0.1)
            
            if processed % 100 == 0:
                print(f"Progress: {processed}/{total_items} items processed")
                print(f"Stats: {self.stats['refns_added']} REFNs added, {self.stats['errors']} errors")
        
        print(f"\nPatching completed!")
        print(f"Items patched: {self.stats['items_patched']}")
        print(f"REFNs added: {self.stats['refns_added']}")
        print(f"Errors: {self.stats['errors']}")
        
        return True

def main():
    if len(sys.argv) != 2:
        print("Usage: python refn_patch_script.py <gedcom_file>")
        sys.exit(1)
    
    gedcom_file = sys.argv[1]
    
    patcher = REFNPatcher("Immanuelle", "1996ToOmega!")
    patcher.patch_refns(gedcom_file)

if __name__ == "__main__":
    main()