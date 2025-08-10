#!/usr/bin/env python3
"""
Upload GEDCOM data to evolutionism.miraheze.org Wikibase.
Creates items for individuals and families with monolingual text properties for all GEDCOM fields.
Creates separate wiki pages for notes and links to them via property.
Uses mwclient for authentication like the working shinto wiki bot.
"""

import requests
import json
import sys
import time
import re
import mwclient
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import quote

class GedcomWikibaseUploader:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        
        # Use mwclient for authentication like the working bot
        self.site = mwclient.Site("evolutionism.miraheze.org", path="/w/")
        self.session = requests.Session()
        
        # Set proper User-Agent header (required by Miraheze)
        self.session.headers.update({
            'User-Agent': 'GedcomWikibaseUploader/1.0 (https://evolutionism.miraheze.org/wiki/User:Immanuelle; genealogy-bot@example.com)'
        })
        
        self.api_url = "https://evolutionism.miraheze.org/w/api.php"
        self.csrf_token = None
        self.logged_in = False
        
        # Track created items and properties
        self.individual_mappings = {}  # @I123@ -> Q456
        self.family_mappings = {}      # @F123@ -> Q456
        self.property_mappings = {}    # field_name -> P123
        self.current_qid = None        # Will be determined from existing items
        self.current_pid = None        # Will be determined from existing properties
        
        # Statistics
        self.stats = {
            'individuals_processed': 0,
            'individuals_created': 0,
            'families_processed': 0,
            'families_created': 0,
            'properties_created': 0,
            'statements_added': 0,
            'notes_pages_created': 0,
            'errors': 0
        }
        
        # Standard properties we'll create for genealogical data
        self.needed_properties = {
            'given_name': 'Given name',
            'surname': 'Surname', 
            'full_name': 'Full name',
            'alternate_name': 'Alternate name',
            'birth_date': 'Birth date',
            'death_date': 'Death date',
            'burial_date': 'Burial date',
            'marriage_date': 'Marriage date',
            'sex': 'Sex',
            'occupation': 'Occupation',
            'residence': 'Residence',
            'source': 'Source',
            'notes_page': 'Notes page',
            'parent_family': 'Parent family',
            'spouse_family': 'Spouse family',
            'husband': 'Husband',
            'wife': 'Wife',
            'child': 'Child',
            'mother': 'Mother',
            'father': 'Father'
        }
        
        # Instance relationships
        self.gaiad_character_qid = "Q279"  # Gaiad character
        self.gaiad_family_qid = "Q280"     # Gaiad family
    
    def login(self):
        """Login using mwclient like the working bot."""
        print(f"Logging in as {self.username}...")
        
        try:
            self.site.login(self.username, self.password)
            print("Successfully logged in with mwclient!")
            
            # Now get CSRF token for API operations using the authenticated session
            # Copy cookies from mwclient to requests session
            for cookie in self.site.connection.cookies:
                self.session.cookies.set(cookie.name, cookie.value, domain=cookie.domain)
            
            # Get CSRF token
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
            
            print("Got CSRF token for API operations!")
            
        except Exception as e:
            raise Exception(f"Login failed: {e}")
    
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
                    entity = data['entities'][f'Q{test_qid}']
                    if not entity.get('missing', False):
                        # This QID exists, try next
                        test_qid += 1
                        continue
                
                # This QID is available
                self.current_qid = test_qid
                return test_qid
                    
            except Exception as e:
                print(f"Error checking Q{test_qid}: {e}")
                test_qid += 1
                if test_qid > 2000:  # Safety limit
                    raise Exception("Cannot find available QID")
    
    def get_next_pid(self) -> int:
        """Find the next available P ID by checking existing properties."""
        if self.current_pid is not None:
            self.current_pid += 1
            return self.current_pid
        
        # Start checking from P10 to avoid conflicts with existing properties
        test_pid = 10
        while True:
            try:
                params = {
                    'action': 'wbgetentities',
                    'ids': f'P{test_pid}',
                    'format': 'json'
                }
                response = self.session.get(self.api_url, params=params)
                data = response.json()
                
                if 'entities' in data and f'P{test_pid}' in data['entities']:
                    entity = data['entities'][f'P{test_pid}']
                    if not entity.get('missing', False):
                        # This PID exists, try next
                        test_pid += 1
                        continue
                
                # This PID is available
                self.current_pid = test_pid
                return test_pid
                    
            except Exception as e:
                print(f"Error checking P{test_pid}: {e}")
                test_pid += 1
                if test_pid > 200:  # Safety limit
                    raise Exception("Cannot find available PID")
    
    def create_property(self, label: str, datatype: str = 'monolingualtext') -> str:
        """Create a new Wikibase property."""
        if not self.logged_in:
            raise Exception("Not logged in")
        
        data = {
            'labels': {'en': {'language': 'en', 'value': label}},
            'datatype': datatype
        }
        
        params = {
            'action': 'wbeditentity',
            'new': 'property',
            'data': json.dumps(data),
            'token': self.csrf_token,
            'format': 'json'
        }
        
        try:
            response = self.session.post(self.api_url, data=params)
            response.raise_for_status()
            result = response.json()
            
            if 'success' in result and result['success'] == 1:
                pid = result['entity']['id']
                print(f"Created property {pid}: {label} ({datatype})")
                self.stats['properties_created'] += 1
                return pid
            else:
                raise Exception(f"Failed to create property: {result}")
                
        except Exception as e:
            print(f"Error creating property '{label}': {e}")
            self.stats['errors'] += 1
            return None
    
    def create_item(self, labels: Dict[str, str], descriptions: Dict[str, str] = None) -> str:
        """Create a new Wikibase item."""
        if not self.logged_in:
            raise Exception("Not logged in")
        
        # Format labels correctly for wikibase API
        formatted_labels = {}
        for lang, label in labels.items():
            formatted_labels[lang] = {'language': lang, 'value': label}
        
        data = {
            'labels': formatted_labels
        }
        
        if descriptions:
            formatted_descriptions = {}
            for lang, desc in descriptions.items():
                formatted_descriptions[lang] = {'language': lang, 'value': desc}
            data['descriptions'] = formatted_descriptions
        
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
    
    def add_monolingual_claim(self, qid: str, property_id: str, text: str, language: str = 'en'):
        """Add a monolingual text claim to an item."""
        if not self.logged_in:
            raise Exception("Not logged in")
        
        value_data = {
            'text': text,
            'language': language
        }
        
        params = {
            'action': 'wbcreateclaim',
            'entity': qid,
            'snaktype': 'value',
            'property': property_id,
            'value': json.dumps(value_data),
            'token': self.csrf_token,
            'format': 'json'
        }
        
        try:
            response = self.session.post(self.api_url, data=params)
            response.raise_for_status()
            result = response.json()
            
            if 'success' in result and result['success'] == 1:
                self.stats['statements_added'] += 1
                return True
            else:
                print(f"Failed to add claim {qid} -> {property_id} -> '{text}': {result}")
                return False
                
        except Exception as e:
            print(f"Error adding monolingual claim: {e}")
            self.stats['errors'] += 1
            return False
    
    def add_string_claim(self, qid: str, property_id: str, text: str):
        """Add a string claim to an item."""
        if not self.logged_in:
            raise Exception("Not logged in")
        
        params = {
            'action': 'wbcreateclaim',
            'entity': qid,
            'snaktype': 'value',
            'property': property_id,
            'value': json.dumps(text),  # Simple string value
            'token': self.csrf_token,
            'format': 'json'
        }
        
        try:
            response = self.session.post(self.api_url, data=params)
            response.raise_for_status()
            result = response.json()
            
            if 'success' in result and result['success'] == 1:
                self.stats['statements_added'] += 1
                return True
            else:
                print(f"Failed to add string claim {qid} -> {property_id} -> '{text}': {result}")
                return False
                
        except Exception as e:
            print(f"Error adding string claim: {e}")
            self.stats['errors'] += 1
            return False
    
    def add_item_claim(self, qid: str, property_id: str, target_qid: str):
        """Add an item claim (link to another item) to an item."""
        if not self.logged_in:
            raise Exception("Not logged in")
        
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
                self.stats['statements_added'] += 1
                return True
            else:
                print(f"Failed to add item claim {qid} -> {property_id} -> {target_qid}: {result}")
                return False
                
        except Exception as e:
            print(f"Error adding item claim: {e}")
            self.stats['errors'] += 1
            return False
    
    def create_notes_page(self, qid: str, gedcom_id: str, notes_content: str) -> str:
        """Create a notes page in the Notes namespace using the QID."""
        if not notes_content.strip():
            return None
            
        # Use QID for page title, not GEDCOM ID
        page_title = f"Notes:{qid}"
        
        # Create the page content with proper links
        page_content = f"== Notes for [[Item:{qid}|{qid}]] ==\n\n{notes_content}\n\n[[Category:GEDCOM Notes]]\n[[Category:Gaiad Character Notes]]"
        
        try:
            page = self.site.pages[page_title]
            page.save(page_content, summary=f'Created notes page for {qid}')
            self.stats['notes_pages_created'] += 1
            # Return the full URL to the notes page
            return f"https://evolutionism.miraheze.org/wiki/{page_title}"
                
        except Exception as e:
            print(f"Error creating notes page: {e}")
            self.stats['errors'] += 1
            return None
    
    def setup_properties(self):
        """Create or find all needed properties for genealogical data."""
        print("Setting up properties...")
        
        # First try to find existing properties
        self.find_existing_properties()
        
        for prop_key, prop_label in self.needed_properties.items():
            if prop_key in self.property_mappings:
                print(f"Using existing property for {prop_key}: {self.property_mappings[prop_key]}")
                continue
                
            if prop_key in ['parent_family', 'spouse_family', 'husband', 'wife', 'child', 'mother', 'father']:
                # These should link to other items
                datatype = 'wikibase-item'
            elif prop_key == 'notes_page':
                # This should be a URL/string
                datatype = 'string'
            else:
                # Everything else is monolingual text
                datatype = 'monolingualtext'
            
            pid = self.create_property(prop_label, datatype)
            if pid:
                self.property_mappings[prop_key] = pid
                time.sleep(0.3)  # Rate limiting
    
    def find_existing_properties(self):
        """Find existing properties that match our needed properties."""
        # Hard-code the known property mappings from the previous run
        known_mappings = {
            'given_name': 'P3',
            'surname': 'P4', 
            'full_name': 'P5',
            'alternate_name': 'P6',
            'birth_date': 'P7',
            'death_date': 'P8',
            'burial_date': 'P9',
            'marriage_date': 'P10',
            'sex': 'P11',
            'occupation': 'P12',
            'residence': 'P13',
            'source': 'P14',
            'notes_page': 'P15',
            'parent_family': 'P16',
            'spouse_family': 'P2',  # This was already existing
            'husband': 'P18',
            'wife': 'P19',
            'child': 'P20',
            'mother': 'P21',
            'father': 'P22',
            'instance_of': 'P39'  # Instance of
        }
        
        # Verify these properties actually exist
        for prop_key, pid in known_mappings.items():
            try:
                params = {
                    'action': 'wbgetentities',
                    'ids': pid,
                    'format': 'json'
                }
                response = self.session.get(self.api_url, params=params)
                data = response.json()
                
                if 'entities' in data and pid in data['entities']:
                    entity = data['entities'][pid]
                    if not entity.get('missing', False):
                        self.property_mappings[prop_key] = pid
                        print(f"Found existing property {pid} for {prop_key}")
                        
            except Exception as e:
                print(f"Error checking property {pid}: {e}")
                continue
    
    def parse_name(self, name_string: str) -> Tuple[str, str, str]:
        """Parse a GEDCOM name into components."""
        # Basic parsing of "Given /Surname/" format
        if '/' in name_string:
            parts = name_string.split('/')
            given = parts[0].strip()
            surname = parts[1].strip() if len(parts) > 1 else ''
            full = f"{given} {surname}".strip()
        else:
            given = name_string.strip()
            surname = ''
            full = given
        
        return given, surname, full
    
    def parse_gedcom_individual(self, lines: List[str], start_idx: int) -> Tuple[Dict, int]:
        """Parse an individual record from GEDCOM lines."""
        individual = {
            'id': None,
            'names': [],
            'birth_date': None,
            'death_date': None,
            'burial_date': None,
            'parents_family': None,
            'spouse_families': [],
            'sex': None,
            'occupation': [],
            'residence': [],
            'sources': [],
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
                    
            elif line.startswith('1 BURI'):
                # Look for date on next line
                if i + 1 < len(lines) and lines[i + 1].startswith('2 DATE '):
                    individual['burial_date'] = lines[i + 1][7:].strip()
                    
            elif line.startswith('1 OCCU '):
                individual['occupation'].append(line[7:].strip())
                
            elif line.startswith('1 RESI '):
                individual['residence'].append(line[7:].strip())
                
            elif line.startswith('1 FAMC '):
                individual['parents_family'] = line[7:].strip()
                
            elif line.startswith('1 FAMS '):
                individual['spouse_families'].append(line[7:].strip())
                
            elif line.startswith('1 SOUR '):
                individual['sources'].append(line[7:].strip())
                
            elif line.startswith('1 NOTE '):
                note = line[7:].strip()
                # Collect continuation lines
                j = i + 1
                while j < len(lines) and (lines[j].startswith('2 CONT ') or lines[j].startswith('2 CONC ')):
                    if lines[j].startswith('2 CONT '):
                        note += '\n' + lines[j][7:]
                    else:  # CONC
                        note += lines[j][7:]
                    j += 1
                individual['notes'].append(note)
                i = j - 1  # Adjust index since we processed extra lines
                
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
            'notes': [],
            'sources': []
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
                    
            elif line.startswith('1 SOUR '):
                family['sources'].append(line[7:].strip())
                
            elif line.startswith('1 NOTE '):
                note = line[7:].strip()
                # Collect continuation lines
                j = i + 1
                while j < len(lines) and (lines[j].startswith('2 CONT ') or lines[j].startswith('2 CONC ')):
                    if lines[j].startswith('2 CONT '):
                        note += '\n' + lines[j][7:]
                    else:  # CONC
                        note += lines[j][7:]
                    j += 1
                family['notes'].append(note)
                i = j - 1  # Adjust index since we processed extra lines
            
            i += 1
        
        return family, i
    
    def process_individual(self, individual: Dict) -> Optional[str]:
        """Process a single individual and create wikibase item."""
        if not individual['id'] or not individual['names']:
            return None
        
        # Parse primary name for label
        primary_name = individual['names'][0]
        given, surname, full = self.parse_name(primary_name)
        
        # Create item with parsed name as label
        label = full if full else individual['id']
        
        # Create description
        description_parts = []
        if individual['birth_date']:
            description_parts.append(f"b. {individual['birth_date']}")
        if individual['death_date']:
            description_parts.append(f"d. {individual['death_date']}")
        description = ', '.join(description_parts) if description_parts else "Person"
        
        labels = {'en': label}
        descriptions = {'en': description} if description != "Person" else None
        
        qid = self.create_item(labels, descriptions)
        if not qid:
            return None
        
        self.individual_mappings[individual['id']] = qid
        self.stats['individuals_created'] += 1
        
        # Add instance of relationship: P39 -> Q279 (Gaiad character)
        if 'instance_of' in self.property_mappings:
            self.add_item_claim(qid, self.property_mappings['instance_of'], self.gaiad_character_qid)
        
        # Add all the monolingual text properties
        if given and 'given_name' in self.property_mappings:
            self.add_monolingual_claim(qid, self.property_mappings['given_name'], given)
        
        if surname and 'surname' in self.property_mappings:
            self.add_monolingual_claim(qid, self.property_mappings['surname'], surname)
        
        if full and 'full_name' in self.property_mappings:
            self.add_monolingual_claim(qid, self.property_mappings['full_name'], full)
        
        # Add alternate names
        for name in individual['names'][1:]:  # Skip primary name
            if 'alternate_name' in self.property_mappings:
                self.add_monolingual_claim(qid, self.property_mappings['alternate_name'], name)
        
        # Add dates
        if individual['birth_date'] and 'birth_date' in self.property_mappings:
            self.add_monolingual_claim(qid, self.property_mappings['birth_date'], individual['birth_date'])
        
        if individual['death_date'] and 'death_date' in self.property_mappings:
            self.add_monolingual_claim(qid, self.property_mappings['death_date'], individual['death_date'])
        
        if individual['burial_date'] and 'burial_date' in self.property_mappings:
            self.add_monolingual_claim(qid, self.property_mappings['burial_date'], individual['burial_date'])
        
        # Add other fields
        if individual['sex'] and 'sex' in self.property_mappings:
            self.add_monolingual_claim(qid, self.property_mappings['sex'], individual['sex'])
        
        for occupation in individual['occupation']:
            if 'occupation' in self.property_mappings:
                self.add_monolingual_claim(qid, self.property_mappings['occupation'], occupation)
        
        for residence in individual['residence']:
            if 'residence' in self.property_mappings:
                self.add_monolingual_claim(qid, self.property_mappings['residence'], residence)
        
        for source in individual['sources']:
            if 'source' in self.property_mappings:
                self.add_monolingual_claim(qid, self.property_mappings['source'], source)
        
        # Handle notes - create separate pages
        if individual['notes']:
            all_notes = '\n\n'.join(individual['notes'])
            notes_page = self.create_notes_page(qid, individual['id'], all_notes)
            if notes_page and 'notes_page' in self.property_mappings:
                # notes_page is a string property, not monolingual text
                self.add_string_claim(qid, self.property_mappings['notes_page'], notes_page)
        
        # Note: Family relationships will be added after families are processed
        
        # Rate limiting
        time.sleep(0.1)
        
        return qid
    
    def process_family(self, family: Dict) -> Optional[str]:
        """Process a single family and create wikibase item."""
        if not family['id']:
            return None
        
        # Create label for family
        husband_name = "Unknown"
        wife_name = "Unknown"
        
        if family['husband'] and family['husband'] in self.individual_mappings:
            # Find husband's name from the processed individuals
            husband_name = "Husband"  # Could be improved to get actual name
        
        if family['wife'] and family['wife'] in self.individual_mappings:
            # Find wife's name from the processed individuals  
            wife_name = "Wife"  # Could be improved to get actual name
        
        # Create unique family name using GEDCOM ID
        clean_id = family['id'].replace('@', '').replace('F', 'Family ')
        family_name = f"{clean_id}: {husband_name} & {wife_name}"
        description = f"Family unit ({clean_id})"
        if family['marriage_date']:
            description += f", married {family['marriage_date']}"
        
        labels = {'en': family_name}
        descriptions = {'en': description}
        
        qid = self.create_item(labels, descriptions)
        if not qid:
            return None
        
        self.family_mappings[family['id']] = qid
        self.stats['families_created'] += 1
        
        # Add instance of relationship: P39 -> Q280 (Gaiad family)
        if 'instance_of' in self.property_mappings:
            self.add_item_claim(qid, self.property_mappings['instance_of'], self.gaiad_family_qid)
        
        # Add family relationships
        if family['husband'] and family['husband'] in self.individual_mappings and 'husband' in self.property_mappings:
            husband_qid = self.individual_mappings[family['husband']]
            self.add_item_claim(qid, self.property_mappings['husband'], husband_qid)
            
        if family['wife'] and family['wife'] in self.individual_mappings and 'wife' in self.property_mappings:
            wife_qid = self.individual_mappings[family['wife']]
            self.add_item_claim(qid, self.property_mappings['wife'], wife_qid)
        
        # Add children
        for child_id in family['children']:
            if child_id in self.individual_mappings and 'child' in self.property_mappings:
                child_qid = self.individual_mappings[child_id]
                self.add_item_claim(qid, self.property_mappings['child'], child_qid)
        
        # Add marriage date
        if family['marriage_date'] and 'marriage_date' in self.property_mappings:
            self.add_monolingual_claim(qid, self.property_mappings['marriage_date'], family['marriage_date'])
        
        # Add sources
        for source in family['sources']:
            if 'source' in self.property_mappings:
                self.add_monolingual_claim(qid, self.property_mappings['source'], source)
        
        # Handle notes - create separate pages
        if family['notes']:
            all_notes = '\n\n'.join(family['notes'])
            notes_page = self.create_notes_page(qid, family['id'], all_notes)
            if notes_page and 'notes_page' in self.property_mappings:
                self.add_string_claim(qid, self.property_mappings['notes_page'], notes_page)
        
        # Rate limiting
        time.sleep(0.1)
        
        return qid
    
    def process_gedcom_file(self, filename: str):
        """Process the entire GEDCOM file and upload to Wikibase."""
        print(f"Processing GEDCOM file: {filename}")
        
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        lines = [line.rstrip('\r\n') for line in lines]
        
        # First: Setup all needed properties
        self.setup_properties()
        
        individuals = []
        families = []
        
        # Parse all individuals and families
        print("Parsing individuals and families...")
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
        
        # Process individuals in batches to avoid overwhelming the server
        batch_size = 50
        for batch_start in range(0, len(individuals), batch_size):
            batch_end = min(batch_start + batch_size, len(individuals))
            batch = individuals[batch_start:batch_end]
            
            print(f"Processing individuals {batch_start+1} to {batch_end}...")
            
            for individual in batch:
                try:
                    self.process_individual(individual)
                except Exception as e:
                    print(f"Error processing individual {individual['id']}: {e}")
                    self.stats['errors'] += 1
            
            # Longer pause between batches
            if batch_end < len(individuals):
                print(f"Completed batch. Pausing before next batch...")
                time.sleep(2)
        
        # Process families in batches (after individuals are created)
        print("\nProcessing families...")
        for batch_start in range(0, len(families), batch_size):
            batch_end = min(batch_start + batch_size, len(families))
            batch = families[batch_start:batch_end]
            
            print(f"Processing families {batch_start+1} to {batch_end}...")
            
            for family in batch:
                try:
                    self.process_family(family)
                except Exception as e:
                    print(f"Error processing family {family['id']}: {e}")
                    self.stats['errors'] += 1
            
            # Longer pause between batches
            if batch_end < len(families):
                print(f"Completed family batch. Pausing before next batch...")
                time.sleep(2)
        
        # Third pass: Add relationships from individuals back to families
        print("\nAdding individual-to-family relationships...")
        
        for individual in individuals:
            if individual['id'] not in self.individual_mappings:
                continue
                
            individual_qid = self.individual_mappings[individual['id']]
            
            # Add parent family relationship
            if individual['parents_family'] and individual['parents_family'] in self.family_mappings and 'parent_family' in self.property_mappings:
                parent_family_qid = self.family_mappings[individual['parents_family']]
                self.add_item_claim(individual_qid, self.property_mappings['parent_family'], parent_family_qid)
            
            # Add spouse family relationships  
            for spouse_family_id in individual['spouse_families']:
                if spouse_family_id in self.family_mappings and 'spouse_family' in self.property_mappings:
                    spouse_family_qid = self.family_mappings[spouse_family_id]
                    self.add_item_claim(individual_qid, self.property_mappings['spouse_family'], spouse_family_qid)
        
        # Also add direct parent relationships (mother/father) from families
        for family in families:
            if family['id'] not in self.family_mappings:
                continue
                
            # Add mother/father relationships to children
            if family['husband'] and family['husband'] in self.individual_mappings and 'father' in self.property_mappings:
                father_qid = self.individual_mappings[family['husband']]
                for child_id in family['children']:
                    if child_id in self.individual_mappings:
                        child_qid = self.individual_mappings[child_id]
                        self.add_item_claim(child_qid, self.property_mappings['father'], father_qid)
            
            if family['wife'] and family['wife'] in self.individual_mappings and 'mother' in self.property_mappings:
                mother_qid = self.individual_mappings[family['wife']]
                for child_id in family['children']:
                    if child_id in self.individual_mappings:
                        child_qid = self.individual_mappings[child_id]
                        self.add_item_claim(child_qid, self.property_mappings['mother'], mother_qid)
        
        print("Relationship processing complete!")
    
    def generate_qid_mapping_file(self, filename: str):
        """Generate a file mapping GEDCOM IDs to Wikibase QIDs."""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# GEDCOM ID to Wikibase QID Mapping\n")
            f.write("# Generated by gedcom_wikibase_uploader.py\n\n")
            
            f.write("# Properties\n")
            for field_name, pid in sorted(self.property_mappings.items()):
                f.write(f"{field_name}\t{pid}\n")
            
            f.write("\n# Individuals\n")
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
        print(f"Properties created: {self.stats['properties_created']}")
        print(f"Statements added: {self.stats['statements_added']}")
        print(f"Notes pages created: {self.stats['notes_pages_created']}")
        print(f"Errors encountered: {self.stats['errors']}")
        
        if self.stats['individuals_processed'] > 0:
            success_rate = (self.stats['individuals_created'] / self.stats['individuals_processed']) * 100
            print(f"Individual creation success rate: {success_rate:.1f}%")

def main():
    if len(sys.argv) != 3:
        print("Usage: python gedcom_wikibase_uploader.py <gedcom_file> <password>")
        print("Example: python gedcom_wikibase_uploader.py master_combined.ged mypassword")
        sys.exit(1)
    
    gedcom_file = sys.argv[1]
    password = sys.argv[2]
    
    # Get credentials
    username = "Immanuelle"
    
    uploader = GedcomWikibaseUploader(username, password)
    
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