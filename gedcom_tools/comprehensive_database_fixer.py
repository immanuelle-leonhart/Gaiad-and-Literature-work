#!/usr/bin/env python3
"""
COMPREHENSIVE DATABASE FIXER

Fixes multiple database issues:
1. Sex (P11) deprecated -> Sex (P55) with proper objects (Q153719/Q153718)
2. Birth/Death dates (P7/P8) -> Date of Birth/Death (P56/P57)
3. Clean Notes page (P15) "REFERENCE_NUMBERS:" entries
4. Extract Wikidata QIDs from GEDCOM REFN (P41) -> Wikidata ID (P44)
5. Extract Geni IDs from GEDCOM REFN (P41) -> Geni profile ID (P43)
6. Import Wikidata labels/descriptions for entities with Wikidata IDs
7. Add Image properties from Wikidata
8. Create correspondence CSV file
9. Add instance of Q153720 for items with no identifiers
"""

import requests
import json
import time
import re
import csv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Wikibase configuration
WIKI_API_URL = "https://evolutionism.miraheze.org/w/api.php"
WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"

# Authentication
USERNAME = "Immanuelle"
PASSWORD = "1996ToOmega!"

class DatabaseFixer:
    def __init__(self):
        self.session = requests.Session()
        self.wikidata_session = requests.Session()
        self.csrf_token = None
        self.correspondence_data = []
        
        # Setup sessions with retry strategy
        self.session.headers.update({
            'User-Agent': 'Comprehensive Database Fixer/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
        })
        retry_strategy = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.wikidata_session.mount("http://", adapter)
        self.wikidata_session.mount("https://", adapter)
        
    def login(self):
        """Login to the wiki"""
        print("Logging in...")
        
        token_params = {'action': 'query', 'meta': 'tokens', 'type': 'login', 'format': 'json'}
        response = self.session.get(WIKI_API_URL, params=token_params, timeout=30)
        if response.status_code != 200:
            print(f"HTTP error: {response.status_code}")
            return False
        token_data = response.json()
        login_token = token_data['query']['tokens']['logintoken']
        
        login_data = {'action': 'login', 'lgname': USERNAME, 'lgpassword': PASSWORD, 'lgtoken': login_token, 'format': 'json'}
        response = self.session.post(WIKI_API_URL, data=login_data)
        result = response.json().get('login', {}).get('result') == 'Success'
        
        if result:
            print("Login successful")
            self.get_csrf_token()
            return True
        else:
            print("Login failed")
            return False
            
    def get_csrf_token(self):
        """Get CSRF token"""
        response = self.session.get(WIKI_API_URL, params={'action': 'query', 'meta': 'tokens', 'format': 'json'})
        self.csrf_token = response.json()['query']['tokens']['csrftoken']
        print("CSRF token obtained")
        
    def get_entity_data(self, qid):
        """Get entity data"""
        try:
            response = self.session.get(WIKI_API_URL, params={
                'action': 'wbgetentities',
                'ids': qid,
                'format': 'json'
            })
            
            data = response.json()
            if 'entities' in data and qid in data['entities']:
                entity = data['entities'][qid]
                if 'missing' not in entity:
                    return entity
            return None
        except Exception as e:
            print(f"Error getting entity {qid}: {e}")
            return None
            
    def remove_claim(self, claim_id):
        """Remove a claim"""
        try:
            data = {
                'action': 'wbremoveclaims',
                'claim': claim_id,
                'token': self.csrf_token,
                'format': 'json',
                'bot': 1
            }
            
            response = self.session.post(WIKI_API_URL, data=data)
            result = response.json()
            
            return 'success' in result
            
        except Exception as e:
            print(f"Error removing claim {claim_id}: {e}")
            return False
            
    def create_claim(self, qid, property_id, value_type, value):
        """Create a new claim"""
        try:
            data = {
                'action': 'wbcreateclaim',
                'entity': qid,
                'property': property_id,
                'snaktype': 'value',
                'token': self.csrf_token,
                'format': 'json',
                'bot': 1
            }
            
            if value_type == 'item':
                data['value'] = json.dumps({'entity-type': 'item', 'id': value})
            elif value_type == 'string':
                data['value'] = json.dumps({'type': 'string', 'value': value})
            elif value_type == 'time':
                data['value'] = json.dumps(value)
            elif value_type == 'url':
                data['value'] = json.dumps({'type': 'string', 'value': value})
                
            response = self.session.post(WIKI_API_URL, data=data)
            result = response.json()
            
            return 'success' in result
            
        except Exception as e:
            print(f"Error creating claim: {e}")
            return False
            
    def fix_sex_property(self, qid, entity):
        """Fix deprecated Sex (P11) to Sex (P55)"""
        if 'P11' not in entity.get('claims', {}):
            return
            
        print(f"  Fixing sex property for {qid}")
        
        for claim in entity['claims']['P11']:
            if 'datavalue' in claim['mainsnak']:
                try:
                    value = claim['mainsnak']['datavalue']['value']
                    
                    # Handle monolingual text format
                    if isinstance(value, dict) and 'text' in value:
                        text_value = value['text'].lower()
                        if text_value in ['f', 'female']:
                            if self.create_claim(qid, 'P55', 'item', 'Q153719'):
                                self.remove_claim(claim['id'])
                                print(f"    Converted '{value['text']}' -> Female (Q153719)")
                        elif text_value in ['m', 'male']:
                            if self.create_claim(qid, 'P55', 'item', 'Q153718'):
                                self.remove_claim(claim['id'])
                                print(f"    Converted '{value['text']}' -> Male (Q153718)")
                    # Handle simple string format
                    elif isinstance(value, str):
                        value_lower = value.lower()
                        if value_lower in ['f', 'female']:
                            if self.create_claim(qid, 'P55', 'item', 'Q153719'):
                                self.remove_claim(claim['id'])
                                print(f"    Converted {value} -> Female (Q153719)")
                        elif value_lower in ['m', 'male']:
                            if self.create_claim(qid, 'P55', 'item', 'Q153718'):
                                self.remove_claim(claim['id'])
                                print(f"    Converted {value} -> Male (Q153718)")
                    # Handle Wikidata QID format
                    elif isinstance(value, dict) and 'id' in value:
                        wikidata_id = value['id']
                        if wikidata_id == 'Q6581072':  # Wikidata Female
                            if self.create_claim(qid, 'P55', 'item', 'Q153719'):
                                self.remove_claim(claim['id'])
                                print(f"    Converted Wikidata Female -> Q153719")
                        elif wikidata_id == 'Q6581097':  # Wikidata Male
                            if self.create_claim(qid, 'P55', 'item', 'Q153718'):
                                self.remove_claim(claim['id'])
                                print(f"    Converted Wikidata Male -> Q153718")
                                
                    time.sleep(0.2)
                    
                except Exception as e:
                    print(f"    Error processing sex claim: {e}")
                    
    def fix_date_properties(self, qid, entity):
        """Fix deprecated date properties P7/P8 -> P56/P57"""
        claims = entity.get('claims', {})
        
        # Birth date P7 -> P56 (only if P56 doesn't exist)
        if 'P7' in claims and 'P56' not in claims:
            print(f"  Fixing birth date for {qid}")
            for claim in claims['P7']:
                if 'datavalue' in claim['mainsnak']:
                    try:
                        date_value = claim['mainsnak']['datavalue']['value']
                        # Handle monolingual text format (e.g., "97 B.C.")
                        if isinstance(date_value, dict) and 'text' in date_value:
                            date_text = date_value['text']
                            time_obj = self.parse_bc_date(date_text)
                            if time_obj and self.create_claim(qid, 'P56', 'time', time_obj):
                                self.remove_claim(claim['id'])
                                print(f"    Moved birth date '{date_text}' to P56")
                        # Handle time format
                        elif isinstance(date_value, dict) and 'time' in date_value:
                            if self.create_claim(qid, 'P56', 'time', date_value):
                                self.remove_claim(claim['id'])
                                print(f"    Moved birth date to P56")
                        time.sleep(0.2)
                    except Exception as e:
                        print(f"    Error processing birth date: {e}")
        elif 'P7' in claims and 'P56' in claims:
            # P56 exists, just remove P7
            print(f"  Removing deprecated P7 (P56 exists) for {qid}")
            for claim in claims['P7']:
                self.remove_claim(claim['id'])
                print(f"    Removed deprecated birth date")
        
        # Death date P8 -> P57 (only if P57 doesn't exist) 
        if 'P8' in claims and 'P57' not in claims:
            print(f"  Fixing death date for {qid}")
            for claim in claims['P8']:
                if 'datavalue' in claim['mainsnak']:
                    try:
                        date_value = claim['mainsnak']['datavalue']['value']
                        # Handle monolingual text format
                        if isinstance(date_value, dict) and 'text' in date_value:
                            date_text = date_value['text']
                            time_obj = self.parse_bc_date(date_text)
                            if time_obj and self.create_claim(qid, 'P57', 'time', time_obj):
                                self.remove_claim(claim['id'])
                                print(f"    Moved death date '{date_text}' to P57")
                        # Handle time format
                        elif isinstance(date_value, dict) and 'time' in date_value:
                            if self.create_claim(qid, 'P57', 'time', date_value):
                                self.remove_claim(claim['id'])
                                print(f"    Moved death date to P57")
                        time.sleep(0.2)
                    except Exception as e:
                        print(f"    Error processing death date: {e}")
        elif 'P8' in claims and 'P57' in claims:
            # P57 exists, just remove P8
            print(f"  Removing deprecated P8 (P57 exists) for {qid}")
            for claim in claims['P8']:
                self.remove_claim(claim['id'])
                print(f"    Removed deprecated death date")
                
    def parse_bc_date(self, date_text):
        """Parse BC date text into Wikibase time format"""
        try:
            import re
            # Handle formats like "97 B.C." or "48 BC"
            bc_match = re.search(r'(\d+)\s*B\.?C\.?', date_text, re.IGNORECASE)
            if bc_match:
                year = int(bc_match.group(1))
                # BC years are negative in Wikibase format
                return {
                    'time': f'-{year:04d}-00-00T00:00:00Z',
                    'timezone': 0,
                    'before': 0,
                    'after': 0,
                    'precision': 9,  # Year precision
                    'calendarmodel': 'http://www.wikidata.org/entity/Q1985786'  # Proleptic Gregorian
                }
            
            # Handle AD dates
            ad_match = re.search(r'(\d+)\s*A\.?D\.?', date_text, re.IGNORECASE)
            if ad_match:
                year = int(ad_match.group(1))
                return {
                    'time': f'+{year:04d}-00-00T00:00:00Z',
                    'timezone': 0,
                    'before': 0,
                    'after': 0,
                    'precision': 9,
                    'calendarmodel': 'http://www.wikidata.org/entity/Q1985786'
                }
                
            # Handle simple year numbers
            year_match = re.search(r'^(\d+)$', date_text.strip())
            if year_match:
                year = int(year_match.group(1))
                return {
                    'time': f'+{year:04d}-00-00T00:00:00Z',
                    'timezone': 0,
                    'before': 0,
                    'after': 0,
                    'precision': 9,
                    'calendarmodel': 'http://www.wikidata.org/entity/Q1985786'
                }
                
        except Exception as e:
            print(f"    Error parsing date '{date_text}': {e}")
            
        return None
                        
    def fix_notes_property(self, qid, entity):
        """Remove Notes page (P15) entries that equal 'REFERENCE_NUMBERS:'"""
        if 'P15' not in entity.get('claims', {}):
            return
            
        for claim in entity['claims']['P15']:
            if 'datavalue' in claim['mainsnak']:
                try:
                    value = claim['mainsnak']['datavalue']['value']
                    if isinstance(value, str) and value.strip() == "REFERENCE_NUMBERS:":
                        if self.remove_claim(claim['id']):
                            print(f"  Removed REFERENCE_NUMBERS note from {qid}")
                        time.sleep(0.2)
                except Exception as e:
                    print(f"    Error processing notes: {e}")
                    
    def extract_identifiers_from_refn(self, qid, entity):
        """Extract Wikidata QIDs and Geni IDs from GEDCOM REFN (P41)"""
        if 'P41' not in entity.get('claims', {}):
            return None, None
            
        print(f"  Processing REFN for {qid}")
        wikidata_qid = None
        geni_id = None
        
        for claim in entity['claims']['P41']:
            if 'datavalue' in claim['mainsnak']:
                try:
                    value = claim['mainsnak']['datavalue']['value']
                    print(f"    Found REFN value: {value} (type: {type(value)})")
                    
                    # Handle string values directly (Q445758)
                    if isinstance(value, str):
                        # Check for Wikidata QID (Q followed by numbers)
                        if re.match(r'^Q\d+$', value):
                            wikidata_qid = value
                            print(f"    Creating P44 claim for {value}")
                            # Create Wikidata ID claim
                            if self.create_claim(qid, 'P44', 'string', value):
                                print(f"    Successfully created P44 claim")
                                # Add described at URL
                                wikidata_url = f"https://wikidata.org/wiki/{value}"
                                print(f"    Adding described at URL: {wikidata_url}")
                                if self.create_claim(qid, 'P45', 'url', wikidata_url):
                                    print(f"    Successfully created P45 claim")
                                # Remove from REFN
                                if self.remove_claim(claim['id']):
                                    print(f"    Successfully removed REFN claim")
                                print(f"    Extracted Wikidata ID: {value}")
                            else:
                                print(f"    Failed to create P44 claim for {value}")
                                
                        # Check for Geni ID (geni: prefix)
                        elif value.startswith('geni:'):
                            geni_number = value[5:]  # Remove 'geni:' prefix
                            geni_id = geni_number
                            # Create Geni profile ID claim
                            if self.create_claim(qid, 'P43', 'string', geni_number):
                                # Add described at URL
                                geni_url = f"https://www.geni.com/profile/index/{geni_number}"
                                self.create_claim(qid, 'P45', 'url', geni_url)
                                # Remove from REFN
                                self.remove_claim(claim['id'])
                                print(f"    Extracted Geni ID: {geni_number}")
                        else:
                            print(f"    Unknown REFN format: {value}")
                            
                    # Handle monolingual text format
                    elif isinstance(value, dict) and 'text' in value:
                        text_value = value['text']
                        # Check for Wikidata QID
                        if re.match(r'^Q\d+$', text_value):
                            wikidata_qid = text_value
                            if self.create_claim(qid, 'P44', 'string', text_value):
                                wikidata_url = f"https://wikidata.org/wiki/{text_value}"
                                self.create_claim(qid, 'P45', 'url', wikidata_url)
                                self.remove_claim(claim['id'])
                                print(f"    Extracted Wikidata ID: {text_value}")
                        # Check for Geni ID
                        elif text_value.startswith('geni:'):
                            geni_number = text_value[5:]
                            geni_id = geni_number
                            if self.create_claim(qid, 'P43', 'string', geni_number):
                                geni_url = f"https://www.geni.com/profile/index/{geni_number}"
                                self.create_claim(qid, 'P45', 'url', geni_url)
                                self.remove_claim(claim['id'])
                                print(f"    Extracted Geni ID: {geni_number}")
                                
                    time.sleep(0.2)
                        
                except Exception as e:
                    print(f"    Error processing REFN: {e}")
                    
        return wikidata_qid, geni_id
        
    def get_wikidata_entity(self, qid):
        """Get entity data from Wikidata"""
        try:
            response = self.wikidata_session.get(WIKIDATA_API_URL, params={
                'action': 'wbgetentities',
                'ids': qid,
                'format': 'json'
            })
            
            data = response.json()
            if 'entities' in data and qid in data['entities']:
                entity = data['entities'][qid]
                if 'missing' not in entity:
                    return entity
            return None
        except Exception as e:
            print(f"Error getting Wikidata entity {qid}: {e}")
            return None
            
    def import_wikidata_labels_descriptions(self, local_qid, wikidata_qid):
        """Import labels and descriptions from Wikidata"""
        print(f"  Importing Wikidata data for {local_qid} from {wikidata_qid}")
        
        wd_entity = self.get_wikidata_entity(wikidata_qid)
        if not wd_entity:
            print(f"    Could not fetch Wikidata entity {wikidata_qid}")
            return
            
        # Move current English label to alias first
        local_entity = self.get_entity_data(local_qid)
        if (local_entity and 'labels' in local_entity and 
            'en' in local_entity['labels']):
            current_label = local_entity['labels']['en']['value']
            # Add as alias (this would need alias API calls)
            print(f"    Current label '{current_label}' should be moved to aliases")
            
        # Import labels from Wikidata
        if 'labels' in wd_entity:
            for lang, label_data in wd_entity['labels'].items():
                try:
                    # Set label
                    data = {
                        'action': 'wbsetlabel',
                        'id': local_qid,
                        'language': lang,
                        'value': label_data['value'],
                        'token': self.csrf_token,
                        'format': 'json',
                        'bot': 1
                    }
                    
                    response = self.session.post(WIKI_API_URL, data=data)
                    if 'success' in response.json():
                        print(f"    Set {lang} label: {label_data['value']}")
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"    Error setting {lang} label: {e}")
                    
        # Clear and import descriptions
        if 'descriptions' in wd_entity:
            for lang, desc_data in wd_entity['descriptions'].items():
                try:
                    # Set description
                    data = {
                        'action': 'wbsetdescription',
                        'id': local_qid,
                        'language': lang,
                        'value': desc_data['value'],
                        'token': self.csrf_token,
                        'format': 'json',
                        'bot': 1
                    }
                    
                    response = self.session.post(WIKI_API_URL, data=data)
                    if 'success' in response.json():
                        print(f"    Set {lang} description: {desc_data['value']}")
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"    Error setting {lang} description: {e}")
                    
        # Import image if available
        if ('claims' in wd_entity and 'P18' in wd_entity['claims'] and
            len(wd_entity['claims']['P18']) > 0):
            try:
                image_claim = wd_entity['claims']['P18'][0]
                if 'datavalue' in image_claim['mainsnak']:
                    image_filename = image_claim['mainsnak']['datavalue']['value']
                    if self.create_claim(local_qid, 'P58', 'string', image_filename):
                        print(f"    Added image: {image_filename}")
            except Exception as e:
                print(f"    Error adding image: {e}")
                
    def add_no_identifiers_instance(self, qid):
        """Add instance of Q153720 for items with no identifiers"""
        if self.create_claim(qid, 'P39', 'item', 'Q153720'):
            print(f"  Added 'Item with no identifiers' instance to {qid}")
            
    def process_entity(self, qid):
        """Process a single entity"""
        entity = self.get_entity_data(qid)
        if not entity:
            return
            
        print(f"Processing {qid}")
        
        # Fix sex property
        self.fix_sex_property(qid, entity)
        
        # Fix date properties
        self.fix_date_properties(qid, entity)
        
        # Fix notes property
        self.fix_notes_property(qid, entity)
        
        # Extract identifiers from REFN
        wikidata_qid, geni_id = self.extract_identifiers_from_refn(qid, entity)
        
        # Import Wikidata data if available
        if wikidata_qid:
            self.import_wikidata_labels_descriptions(qid, wikidata_qid)
            
        # Get current English label for CSV
        en_label = ''
        if entity and 'labels' in entity and 'en' in entity['labels']:
            en_label = entity['labels']['en']['value']
        
        # Add to correspondence data
        self.correspondence_data.append({
            'local_qid': qid,
            'wikidata_qid': wikidata_qid or '',
            'geni_id': geni_id or '',
            'en_label': en_label
        })
        
        # Add no identifiers instance if needed
        if not wikidata_qid and not geni_id:
            self.add_no_identifiers_instance(qid)
            
        time.sleep(0.5)  # Rate limiting
        
    def save_correspondence_csv(self):
        """Save correspondence data to CSV"""
        filename = 'qid_correspondence.csv'
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['evolutionism_qid', 'wikidata_qid', 'geni_id', 'en_label']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in self.correspondence_data:
                writer.writerow({
                    'evolutionism_qid': row['local_qid'],
                    'wikidata_qid': row['wikidata_qid'],
                    'geni_id': row['geni_id'],
                    'en_label': row['en_label']
                })
                
        print(f"Saved correspondence data to {filename}")
        
    def run_comprehensive_fix(self, start_qid=1, end_qid=50000):
        """Run comprehensive fix on range of QIDs"""
        if not self.login():
            print("Login failed!")
            return
            
        print(f"Starting comprehensive database fix from Q{start_qid} to Q{end_qid}")
        
        processed = 0
        for i in range(start_qid, end_qid + 1):
            qid = f"Q{i}"
            self.process_entity(qid)
            processed += 1
            
            if processed % 100 == 0:
                print(f"Processed {processed} entities...")
                
        self.save_correspondence_csv()
        print(f"Comprehensive fix complete! Processed {processed} entities.")

def main():
    import sys
    
    fixer = DatabaseFixer()
    
    if len(sys.argv) > 1:
        start_qid = int(sys.argv[1])
        end_qid = int(sys.argv[2]) if len(sys.argv) > 2 else start_qid + 1000
    else:
        start_qid = 1
        end_qid = 50000
        
    fixer.run_comprehensive_fix(start_qid, end_qid)

if __name__ == "__main__":
    main()