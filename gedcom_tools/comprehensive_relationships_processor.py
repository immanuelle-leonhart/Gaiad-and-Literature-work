#!/usr/bin/env python3

import re
import requests
import time
import sys
import json
from typing import Dict, Set, List

class ComprehensiveRelationshipsProcessor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GaiadGenealogyBot/1.0 (https://evolutionism.miraheze.org/wiki/User:Immanuelle)'
        })
        self.api_url = 'https://evolutionism.miraheze.org/w/api.php'
        self.qid_mapping = {}
        self.all_family_ids = set()
        self.processed_count = 0
        
    def login(self, username: str, password: str) -> bool:
        """Login to the wiki"""
        # Get login token
        response = self.session.get(self.api_url, params={
            'action': 'query', 'meta': 'tokens', 'type': 'login', 'format': 'json'
        })
        
        if response.status_code != 200:
            print(f"Failed to get login token: {response.status_code}")
            return False
            
        login_token = response.json()['query']['tokens']['logintoken']
        
        # Perform login
        login_data = {
            'action': 'login',
            'lgname': username, 
            'lgpassword': password,
            'lgtoken': login_token,
            'format': 'json'
        }
        
        response = self.session.post(self.api_url, data=login_data)
        return response.json().get('login', {}).get('result') == 'Success'
    
    def get_csrf_token(self) -> str:
        """Get CSRF token for editing"""
        response = self.session.get(self.api_url, params={
            'action': 'query', 'meta': 'tokens', 'format': 'json'
        })
        return response.json()['query']['tokens']['csrftoken']
    
    def load_qid_mapping(self) -> int:
        """Load QID mapping from file"""
        try:
            with open('gedcom_to_qid_mapping.txt', 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    if line and not line.startswith('#') and '\t' in line:
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            gedcom_id = parts[0].strip()
                            qid = parts[1].strip()
                            if gedcom_id and qid:
                                self.qid_mapping[gedcom_id] = qid
                    
                    if line_num % 10000 == 0:
                        print(f"  Loaded {line_num} ID mappings...")
                        
            print(f"Loaded {len(self.qid_mapping)} GEDCOM ID to QID mappings")
            return len(self.qid_mapping)
        except FileNotFoundError:
            print("Error: gedcom_to_qid_mapping.txt not found")
            return 0
    
    def collect_all_family_ids_from_gedcom(self, gedcom_file: str):
        """Collect ALL family IDs by scanning every individual and every family record"""
        print("Collecting all family IDs from GEDCOM file...")
        
        try:
            with open(gedcom_file, 'r', encoding='utf-8', errors='ignore') as file:
                current_record = None
                current_id = None
                line_count = 0
                
                for line in file:
                    line_count += 1
                    if line_count % 100000 == 0:
                        print(f"  Processed {line_count} lines, found {len(self.all_family_ids)} families so far...")
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Start of new record
                    if line.startswith('0 '):
                        parts = line.split(' ', 2)
                        if len(parts) >= 3:
                            current_id = parts[1]
                            current_record = parts[2]
                    
                    # Look for family references in individual records
                    elif current_record == 'INDI' and (line.startswith('1 FAMS ') or line.startswith('1 FAMC ')):
                        # Extract family ID
                        parts = line.split(' ', 2)
                        if len(parts) >= 3:
                            family_id = parts[2].strip()
                            # Remove @ symbols if present
                            family_id = family_id.strip('@')
                            self.all_family_ids.add(family_id)
                    
                    # Look for individual references in family records
                    elif current_record == 'FAM' and (line.startswith('1 HUSB ') or line.startswith('1 WIFE ') or line.startswith('1 CHIL ')):
                        # This is a family record with people in it, add the family ID
                        if current_id:
                            family_id = current_id.strip('@')
                            self.all_family_ids.add(family_id)
                    
                    # Also collect family IDs directly from family records
                    elif current_record == 'FAM' and current_id:
                        # Any family record should be included
                        family_id = current_id.strip('@')
                        self.all_family_ids.add(family_id)
                        
        except FileNotFoundError:
            print(f"Error: GEDCOM file {gedcom_file} not found")
            return
        except Exception as e:
            print(f"Error reading GEDCOM file: {e}")
            return
        
        print(f"Collected {len(self.all_family_ids)} unique family IDs from GEDCOM file")
    
    def load_gedcom_families(self, gedcom_file: str) -> Dict:
        """Load family data from GEDCOM for the collected family IDs"""
        print("Loading family data from GEDCOM...")
        families = {}
        current_family = None
        current_id = None
        line_count = 0
        
        try:
            with open(gedcom_file, 'r', encoding='utf-8', errors='ignore') as file:
                for line in file:
                    line_count += 1
                    if line_count % 100000 == 0:
                        print(f"  Processed {line_count} lines, loaded {len(families)} families...")
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    if line.startswith('0 ') and ' FAM' in line:
                        # Save previous family
                        if current_family and current_id:
                            family_id = current_id.strip('@')
                            if family_id in self.all_family_ids:
                                families[family_id] = current_family
                        
                        # Start new family
                        parts = line.split(' ', 2)
                        current_id = parts[1] if len(parts) > 1 else None
                        current_family = {'id': current_id, 'husband': None, 'wife': None, 'children': []}
                    
                    elif current_family and line.startswith('1 HUSB '):
                        parts = line.split(' ', 2)
                        if len(parts) >= 3:
                            current_family['husband'] = parts[2].strip()
                    
                    elif current_family and line.startswith('1 WIFE '):
                        parts = line.split(' ', 2)
                        if len(parts) >= 3:
                            current_family['wife'] = parts[2].strip()
                    
                    elif current_family and line.startswith('1 CHIL '):
                        parts = line.split(' ', 2)
                        if len(parts) >= 3:
                            current_family['children'].append(parts[2].strip())
                
                # Save last family
                if current_family and current_id:
                    family_id = current_id.strip('@')
                    if family_id in self.all_family_ids:
                        families[family_id] = current_family
        
        except Exception as e:
            print(f"Error loading families: {e}")
            return {}
        
        print(f"Loaded {len(families)} families from GEDCOM")
        return families
    
    def create_relationship_claim(self, from_qid: str, to_qid: str, relationship_property: str) -> bool:
        """Create a relationship claim between two individuals"""
        csrf_token = self.get_csrf_token()
        
        claim_data = {
            'action': 'wbcreateclaim',
            'entity': from_qid,
            'property': relationship_property,
            'snaktype': 'value',
            'value': json.dumps({'entity-type': 'item', 'id': to_qid}),
            'token': csrf_token,
            'format': 'json',
            'bot': 1
        }
        
        response = self.session.post(self.api_url, data=claim_data)
        
        if response.status_code == 200:
            result = response.json()
            if 'claim' in result:
                return True
            else:
                print(f"    WARNING: No 'claim' in result for {from_qid} -> {to_qid} ({relationship_property}): {result}")
                return False
        else:
            print(f"    ERROR: HTTP {response.status_code} creating {from_qid} -> {to_qid} ({relationship_property})")
            return False
    
    def process_family_relationships(self, families: Dict):
        """Process relationships for all families"""
        print(f"Processing relationships for {len(families)} families...")
        
        total_families = len(families)
        relationships_added = 0
        
        for i, (family_id, family) in enumerate(families.items(), 1):
            if i % 100 == 0:
                print(f"[{i}/{total_families}] Processing family {family_id}... ({relationships_added} relationships added so far)")
            
            husband_gedcom = family.get('husband')
            wife_gedcom = family.get('wife')
            children_gedcom = family.get('children', [])
            
            # Get QIDs for family members
            husband_qid = self.qid_mapping.get(husband_gedcom) if husband_gedcom else None
            wife_qid = self.qid_mapping.get(wife_gedcom) if wife_gedcom else None
            children_qids = [self.qid_mapping.get(child) for child in children_gedcom if self.qid_mapping.get(child)]
            
            # Debug for first few families
            if i <= 5:
                print(f"  DEBUG Family {family_id}: husband={husband_gedcom} ({husband_qid}), wife={wife_gedcom} ({wife_qid}), children={len(children_qids)}")
                if not (husband_qid or wife_qid or children_qids):
                    print(f"    No QIDs found for any family members!")
            
            # Create spouse relationships
            if husband_qid and wife_qid:
                if self.create_relationship_claim(husband_qid, wife_qid, 'P26'):  # spouse
                    relationships_added += 1
                if self.create_relationship_claim(wife_qid, husband_qid, 'P26'):  # spouse
                    relationships_added += 1
                time.sleep(0.1)  # Rate limiting
            
            # Create parent-child relationships
            for child_qid in children_qids:
                if husband_qid:
                    if self.create_relationship_claim(child_qid, husband_qid, 'P22'):  # father
                        relationships_added += 1
                    if self.create_relationship_claim(husband_qid, child_qid, 'P40'):  # child
                        relationships_added += 1
                    time.sleep(0.1)
                
                if wife_qid:
                    if self.create_relationship_claim(child_qid, wife_qid, 'P25'):  # mother
                        relationships_added += 1
                    if self.create_relationship_claim(wife_qid, child_qid, 'P40'):  # child
                        relationships_added += 1
                    time.sleep(0.1)
            
            # Create sibling relationships
            for i, child1_qid in enumerate(children_qids):
                for child2_qid in children_qids[i+1:]:
                    if self.create_relationship_claim(child1_qid, child2_qid, 'P3373'):  # sibling
                        relationships_added += 1
                    if self.create_relationship_claim(child2_qid, child1_qid, 'P3373'):  # sibling
                        relationships_added += 1
                    time.sleep(0.1)
        
        print(f"Completed! Added {relationships_added} relationships total.")
        return relationships_added

def main():
    if len(sys.argv) != 4:
        print("Usage: python comprehensive_relationships_processor.py <gedcom_file> <username> <password>")
        print("Example: python comprehensive_relationships_processor.py master_combined.ged Immanuelle password")
        sys.exit(1)
    
    gedcom_file = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    
    processor = ComprehensiveRelationshipsProcessor()
    
    # Login
    print("Logging in...")
    if not processor.login(username, password):
        print("Failed to login. Exiting.")
        sys.exit(1)
    print("Successfully logged in")
    
    # Load QID mapping
    print("Loading QID mappings...")
    if processor.load_qid_mapping() == 0:
        print("Failed to load QID mappings. Exiting.")
        sys.exit(1)
    
    # Step 1: Collect ALL family IDs from the GEDCOM file
    processor.collect_all_family_ids_from_gedcom(gedcom_file)
    
    if not processor.all_family_ids:
        print("No family IDs found. Exiting.")
        sys.exit(1)
    
    # Step 2: Load family data for collected family IDs
    families = processor.load_gedcom_families(gedcom_file)
    
    if not families:
        print("No families loaded. Exiting.")
        sys.exit(1)
    
    # Step 3: Process relationships for all families
    processor.process_family_relationships(families)

if __name__ == "__main__":
    main()