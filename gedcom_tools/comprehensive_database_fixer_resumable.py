#!/usr/bin/env python3
"""
COMPREHENSIVE DATABASE FIXER - RESUMABLE VERSION

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

RESUMABLE: Automatically skips entities already processed in CSV file
UNICODE SAFE: Handles Unicode characters properly for Windows
"""

import requests
import json
import time
import re
import csv
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Wikibase configuration
WIKI_API_URL = "https://evolutionism.miraheze.org/w/api.php"
WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"

# Authentication
USERNAME = "Immanuelle"
PASSWORD = "1996ToOmega!"

def safe_print(text):
    """Safely print text, handling Unicode encoding issues on Windows"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Replace problematic characters with safe equivalents
        safe_text = text.encode('ascii', 'replace').decode('ascii')
        print(safe_text)

class DatabaseFixer:
    def __init__(self, wiki_api_url=None, username=None, password=None):
        self.wiki_api_url = wiki_api_url or "https://evolutionism.miraheze.org/w/api.php"
        self.username = username or USERNAME
        self.password = password or PASSWORD
        self.session = requests.Session()
        self.wikidata_session = requests.Session()
        self.csrf_token = None
        self.correspondence_data = []
        self.processed_entities = set()  # Track already processed entities
        
        # Load existing CSV to check for already processed entities
        self.load_existing_csv()
        
        # Setup sessions with retry strategy
        self.session.headers.update({
            'User-Agent': 'Comprehensive Database Fixer/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
        })
        retry_strategy = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Setup Wikidata session
        self.wikidata_session.headers.update({
            'User-Agent': 'Comprehensive Database Fixer/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
        })
        self.wikidata_session.mount("http://", adapter)
        self.wikidata_session.mount("https://", adapter)
        
    def load_existing_csv(self):
        """Load existing CSV file to determine which entities have already been processed"""
        csv_file = "qid_correspondence.csv"
        if os.path.exists(csv_file):
            try:
                with open(csv_file, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if row and row[0].startswith('Q'):
                            self.processed_entities.add(row[0])
                safe_print(f"Loaded {len(self.processed_entities)} already processed entities from CSV")
            except Exception as e:
                safe_print(f"Error loading existing CSV: {e}")
        else:
            safe_print("No existing CSV found, starting fresh")

    def login(self):
        """Login to Wikibase"""
        safe_print("Logging in...")
        
        # Get login token
        params = {
            'action': 'query',
            'meta': 'tokens',
            'type': 'login',
            'format': 'json'
        }
        
        response = self.session.get(self.wiki_api_url, params=params)
        data = response.json()
        
        if 'error' in data:
            safe_print(f"Error getting login token: {data['error']}")
            return False
            
        login_token = data['query']['tokens']['logintoken']
        
        # Login
        login_data = {
            'action': 'login',
            'lgname': self.username,
            'lgpassword': self.password,
            'lgtoken': login_token,
            'format': 'json'
        }
        
        response = self.session.post(self.wiki_api_url, data=login_data)
        data = response.json()
        
        if data['login']['result'] == 'Success':
            safe_print("Login successful")
            self.get_csrf_token()
            return True
        else:
            safe_print(f"Login failed: {data['login']['result']}")
            return False
    
    def get_csrf_token(self):
        """Get CSRF token for editing"""
        params = {
            'action': 'query',
            'meta': 'tokens',
            'format': 'json'
        }
        
        response = self.session.get(self.wiki_api_url, params=params)
        data = response.json()
        
        if 'query' in data and 'tokens' in data['query']:
            self.csrf_token = data['query']['tokens']['csrftoken']
            safe_print("CSRF token obtained")
        else:
            safe_print("Failed to get CSRF token")
    
    def get_entity(self, qid):
        """Get entity data from Wikibase"""
        params = {
            'action': 'wbgetentities',
            'ids': qid,
            'format': 'json'
        }
        
        try:
            response = self.session.get(self.wiki_api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'entities' in data and qid in data['entities']:
                return data['entities'][qid]
            return None
        except Exception as e:
            safe_print(f"Error getting entity {qid}: {e}")
            return None

    def get_wikidata_entity(self, qid):
        """Get entity data from Wikidata"""
        params = {
            'action': 'wbgetentities',
            'ids': qid,
            'format': 'json'
        }
        
        try:
            response = self.wikidata_session.get(WIKIDATA_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'entities' in data and qid in data['entities'] and 'missing' not in data['entities'][qid]:
                return data['entities'][qid]
            return None
        except Exception as e:
            safe_print(f"Error getting Wikidata entity {qid}: {e}")
            return None

    def create_claim(self, qid, property_id, value, datatype='string'):
        """Create a claim on an entity"""
        claim_data = {
            'action': 'wbcreateclaim',
            'entity': qid,
            'property': property_id,
            'snaktype': 'value',
            'format': 'json',
            'token': self.csrf_token,
            'bot': 1
        }
        
        if datatype == 'wikibase-item':
            claim_data['value'] = json.dumps({'entity-type': 'item', 'numeric-id': int(value[1:])})
        elif datatype == 'time':
            claim_data['value'] = json.dumps(value)
        else:
            claim_data['value'] = json.dumps(value)
        
        try:
            response = self.session.post(self.wiki_api_url, data=claim_data)
            response.raise_for_status()
            data = response.json()
            
            if 'success' in data and data['success'] == 1:
                return True
            else:
                safe_print(f"    Error creating claim: {data}")
                return False
        except Exception as e:
            safe_print(f"    Exception creating claim: {e}")
            return False

    def remove_claim(self, claim_id):
        """Remove a claim"""
        remove_data = {
            'action': 'wbremoveclaims',
            'claim': claim_id,
            'format': 'json',
            'token': self.csrf_token,
            'bot': 1
        }
        
        try:
            response = self.session.post(self.wiki_api_url, data=remove_data)
            response.raise_for_status()
            data = response.json()
            
            if 'success' in data and data['success'] == 1:
                return True
            else:
                safe_print(f"    Error removing claim: {data}")
                return False
        except Exception as e:
            safe_print(f"    Exception removing claim: {e}")
            return False

    def set_label(self, qid, language, label):
        """Set label for entity"""
        label_data = {
            'action': 'wbsetlabel',
            'id': qid,
            'language': language,
            'value': label,
            'format': 'json',
            'token': self.csrf_token,
            'bot': 1
        }
        
        try:
            response = self.session.post(self.wiki_api_url, data=label_data)
            response.raise_for_status()
            data = response.json()
            
            if 'success' in data and data['success'] == 1:
                return True
            else:
                safe_print(f"    Error setting label: {data}")
                return False
        except Exception as e:
            safe_print(f"    Exception setting label: {e}")
            return False

    def set_description(self, qid, language, description):
        """Set description for entity"""
        desc_data = {
            'action': 'wbsetdescription',
            'id': qid,
            'language': language,
            'value': description,
            'format': 'json',
            'token': self.csrf_token,
            'bot': 1
        }
        
        try:
            response = self.session.post(self.wiki_api_url, data=desc_data)
            response.raise_for_status()
            data = response.json()
            
            if 'success' in data and data['success'] == 1:
                return True
            else:
                safe_print(f"    Error setting description: {data}")
                return False
        except Exception as e:
            safe_print(f"    Exception setting description: {e}")
            return False

    def add_alias(self, qid, language, alias):
        """Add alias for entity"""
        alias_data = {
            'action': 'wbsetaliases',
            'id': qid,
            'language': language,
            'add': alias,
            'format': 'json',
            'token': self.csrf_token,
            'bot': 1
        }
        
        try:
            response = self.session.post(self.wiki_api_url, data=alias_data)
            response.raise_for_status()
            data = response.json()
            
            if 'success' in data and data['success'] == 1:
                return True
            else:
                safe_print(f"    Error adding alias: {data}")
                return False
        except Exception as e:
            safe_print(f"    Exception adding alias: {e}")
            return False

    def format_date_value(self, date_str):
        """Format date string into Wikibase time format"""
        # Handle various date formats from GEDCOM
        date_str = date_str.strip()
        
        # Handle circa dates
        if date_str.lower().startswith('abt') or date_str.lower().startswith('c.') or date_str.lower().startswith('circa'):
            # Remove circa indicators
            date_str = re.sub(r'^(abt|c\.|circa)\s*', '', date_str, flags=re.IGNORECASE)
        
        # Handle year only (e.g., "1534")
        if re.match(r'^\d{4}$', date_str):
            return {
                'time': f'+{date_str}-00-00T00:00:00Z',
                'timezone': 0,
                'before': 0,
                'after': 0,
                'precision': 9,  # year precision
                'calendarmodel': 'http://www.wikidata.org/entity/Q1985727'
            }
        
        # Handle full dates (e.g., "12 JAN 1534")
        date_match = re.match(r'^(\d{1,2})\s+([A-Z]{3})\s+(\d{4})$', date_str)
        if date_match:
            day, month_abbr, year = date_match.groups()
            month_map = {
                'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
                'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
                'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
            }
            month = month_map.get(month_abbr, '00')
            day = day.zfill(2)
            
            return {
                'time': f'+{year}-{month}-{day}T00:00:00Z',
                'timezone': 0,
                'before': 0,
                'after': 0,
                'precision': 11,  # day precision
                'calendarmodel': 'http://www.wikidata.org/entity/Q1985727'
            }
        
        # Handle month/year (e.g., "JAN 1534")
        month_year_match = re.match(r'^([A-Z]{3})\s+(\d{4})$', date_str)
        if month_year_match:
            month_abbr, year = month_year_match.groups()
            month_map = {
                'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
                'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
                'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
            }
            month = month_map.get(month_abbr, '00')
            
            return {
                'time': f'+{year}-{month}-00T00:00:00Z',
                'timezone': 0,
                'before': 0,
                'after': 0,
                'precision': 10,  # month precision
                'calendarmodel': 'http://www.wikidata.org/entity/Q1985727'
            }
        
        return None

    def import_wikidata_labels_descriptions(self, qid, wd_qid):
        """Import labels and descriptions from Wikidata"""
        wd_entity = self.get_wikidata_entity(wd_qid)
        if not wd_entity:
            return []
        
        current_entity = self.get_entity(qid)
        if not current_entity:
            return []
        
        # Get current label to potentially move to aliases
        current_label = None
        if 'labels' in current_entity and 'en' in current_entity['labels']:
            current_label = current_entity['labels']['en']['value']
        
        geni_ids = []
        
        # Priority system for label import
        labels_to_import = {}
        
        # Priority 1: English label
        if 'en' in wd_entity['labels']:
            labels_to_import['en'] = wd_entity['labels']['en']
            safe_print(f"    Found English label: {wd_entity['labels']['en']['value']}")
        
        # Priority 2: If no English, use 'mul' (multilingual) as English
        elif 'mul' in wd_entity['labels']:
            labels_to_import['en'] = {
                'language': 'en',
                'value': wd_entity['labels']['mul']['value']
            }
            safe_print(f"    Using multilingual label as English: {wd_entity['labels']['mul']['value']}")
        
        # Priority 3: Use any other available label as English
        elif wd_entity['labels']:
            # Get first available label
            first_lang = list(wd_entity['labels'].keys())[0]
            labels_to_import['en'] = {
                'language': 'en',
                'value': wd_entity['labels'][first_lang]['value']
            }
            safe_print(f"    Using {first_lang} label as English: {wd_entity['labels'][first_lang]['value']}")
        
        # Import labels
        for lang, label_data in labels_to_import.items():
            if current_label and current_label != label_data['value']:
                safe_print(f"    Current label '{current_label}' should be moved to aliases")
                # Move current label to aliases first
                self.add_alias(qid, 'en', current_label)
            
            self.set_label(qid, lang, label_data['value'])
            safe_print(f"    Set {lang} label: {label_data['value']}")
        
        # Import description (English priority)
        if 'descriptions' in wd_entity:
            if 'en' in wd_entity['descriptions']:
                self.set_description(qid, 'en', wd_entity['descriptions']['en']['value'])
                safe_print(f"    Set en description: {wd_entity['descriptions']['en']['value']}")
            else:
                safe_print("    No English description available")
        
        # Import image if available
        if 'claims' in wd_entity and 'P18' in wd_entity['claims']:
            try:
                image_claim = wd_entity['claims']['P18'][0]
                if 'mainsnak' in image_claim and 'datavalue' in image_claim['mainsnak']:
                    image_filename = image_claim['mainsnak']['datavalue']['value']
                    # Create image claim (P58 is our image property)
                    if self.create_claim(qid, 'P58', image_filename, 'string'):
                        safe_print(f"    Added image: {image_filename}")
                    else:
                        safe_print(f"    Failed to add image: {image_filename}")
            except Exception as e:
                safe_print(f"    Error adding image: {e}")
        
        # Extract Geni IDs from Wikidata
        if 'claims' in wd_entity and 'P2600' in wd_entity['claims']:
            for claim in wd_entity['claims']['P2600']:
                if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
                    geni_id = claim['mainsnak']['datavalue']['value']
                    geni_ids.append(geni_id)
        
        return geni_ids

    def process_entity(self, qid):
        """Process a single entity for comprehensive fixes"""
        # Skip if already processed
        if qid in self.processed_entities:
            safe_print(f"  Skipping {qid} (already exists in CSV)")
            return
            
        safe_print(f"Processing {qid}")
        
        entity = self.get_entity(qid)
        if not entity or 'missing' in entity:
            safe_print(f"  Entity {qid} not found")
            return
        
        # Initialize tracking variables
        wikidata_qid = None
        geni_profile_id = None
        
        # Process claims
        if 'claims' in entity:
            # 1. Fix sex property (P11 -> P55 with proper values)
            if 'P11' in entity['claims']:
                safe_print(f"  Fixing sex property for {qid}")
                for claim in entity['claims']['P11']:
                    if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
                        sex_value = claim['mainsnak']['datavalue']['value']
                        if isinstance(sex_value, str):
                            if sex_value.lower() == 'male':
                                if self.create_claim(qid, 'P55', 'Q153718', 'wikibase-item'):
                                    safe_print(f"    Converted 'male' -> Male (Q153718)")
                                    self.remove_claim(claim['id'])
                            elif sex_value.lower() == 'female':
                                if self.create_claim(qid, 'P55', 'Q153719', 'wikibase-item'):
                                    safe_print(f"    Converted 'female' -> Female (Q153719)")
                                    self.remove_claim(claim['id'])
            
            # 2. Fix birth date property (P7 -> P56)
            if 'P7' in entity['claims']:
                safe_print(f"  Fixing birth date for {qid}")
                for claim in entity['claims']['P7']:
                    if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
                        date_value = claim['mainsnak']['datavalue']['value']
                        if isinstance(date_value, str):
                            formatted_date = self.format_date_value(date_value)
                            if formatted_date and self.create_claim(qid, 'P56', formatted_date, 'time'):
                                safe_print(f"    Moved birth date '{date_value}' to P56")
                                self.remove_claim(claim['id'])
            
            # 3. Fix death date property (P8 -> P57)
            if 'P8' in entity['claims']:
                safe_print(f"  Fixing death date for {qid}")
                for claim in entity['claims']['P8']:
                    if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
                        date_value = claim['mainsnak']['datavalue']['value']
                        if isinstance(date_value, str):
                            formatted_date = self.format_date_value(date_value)
                            if formatted_date and self.create_claim(qid, 'P57', formatted_date, 'time'):
                                safe_print(f"    Moved death date '{date_value}' to P57")
                                self.remove_claim(claim['id'])
            
            # 4. Process REFN claims to extract Wikidata and Geni IDs
            if 'P41' in entity['claims']:
                safe_print(f"  Processing REFN for {qid}")
                for claim in entity['claims']['P41']:
                    if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
                        refn_value = claim['mainsnak']['datavalue']['value']
                        safe_print(f"    Found REFN value: {refn_value} (type: {type(refn_value)})")
                        
                        # Check if it's a Wikidata QID
                        if isinstance(refn_value, str) and refn_value.startswith('Q') and refn_value[1:].isdigit():
                            # Create P44 claim for Wikidata ID
                            if self.create_claim(qid, 'P44', refn_value, 'string'):
                                safe_print(f"    Creating P44 claim for {refn_value}")
                                safe_print(f"    Successfully created P44 claim")
                                
                                # Create P45 claim for described at URL
                                wikidata_url = f"https://wikidata.org/wiki/{refn_value}"
                                if self.create_claim(qid, 'P45', wikidata_url, 'string'):
                                    safe_print(f"    Adding described at URL: {wikidata_url}")
                                    safe_print(f"    Successfully created P45 claim")
                                
                                # Remove original REFN claim
                                if self.remove_claim(claim['id']):
                                    safe_print(f"    Successfully removed REFN claim")
                                
                                wikidata_qid = refn_value
                                safe_print(f"    Extracted Wikidata ID: {refn_value}")
                        
                        # Check if it's a Geni profile ID (numeric)
                        elif isinstance(refn_value, str) and refn_value.isdigit():
                            # Create P43 claim for Geni profile ID
                            if self.create_claim(qid, 'P43', refn_value, 'string'):
                                safe_print(f"    Created P43 claim for Geni ID: {refn_value}")
                                
                                # Create P45 claim for described at URL
                                geni_url = f"https://www.geni.com/people/{refn_value}"
                                if self.create_claim(qid, 'P45', geni_url, 'string'):
                                    safe_print(f"    Added Geni URL: {geni_url}")
                                
                                # Remove original REFN claim
                                if self.remove_claim(claim['id']):
                                    safe_print(f"    Successfully removed REFN claim")
                                
                                geni_profile_id = refn_value
                                safe_print(f"    Extracted Geni ID: {refn_value}")
        
        # 5. Import Wikidata data if we have a Wikidata QID
        geni_ids_from_wd = []
        if wikidata_qid:
            safe_print(f"  Importing Wikidata data for {qid} from {wikidata_qid}")
            geni_ids_from_wd = self.import_wikidata_labels_descriptions(qid, wikidata_qid)
        
        # 6. Check if entity has no identifier properties and add instance claim
        has_identifiers = False
        if 'claims' in entity:
            # Check for key identifier properties
            identifier_properties = ['P44', 'P43', 'P41']  # Wikidata ID, Geni ID, REFN
            for prop in identifier_properties:
                if prop in entity['claims'] and entity['claims'][prop]:
                    has_identifiers = True
                    break
        
        if not has_identifiers:
            # Add instance of "Item with no identifiers" (Q153720)
            if self.create_claim(qid, 'P3', 'Q153720', 'wikibase-item'):
                safe_print(f"  Added 'Item with no identifiers' instance to {qid}")
        
        # 7. Add to correspondence data
        # Get current label
        current_label = ""
        if 'labels' in entity and 'en' in entity['labels']:
            current_label = entity['labels']['en']['value']
        
        # Combine all Geni IDs
        all_geni_ids = []
        if geni_profile_id:
            all_geni_ids.append(geni_profile_id)
        all_geni_ids.extend(geni_ids_from_wd)
        
        # Add row to correspondence data
        self.correspondence_data.append([
            qid,
            wikidata_qid or '',
            ';'.join(all_geni_ids) if all_geni_ids else '',
            current_label,
            ''  # Extra field for notes
        ])
        
        # Mark as processed
        self.processed_entities.add(qid)
        
        # Small delay to avoid overwhelming the server
        time.sleep(0.1)

    def save_correspondence_csv(self, filename="qid_correspondence.csv"):
        """Save correspondence data to CSV file (append mode for resumability)"""
        if not self.correspondence_data:
            return
            
        file_exists = os.path.exists(filename)
        
        with open(filename, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # Write header only if file doesn't exist
            if not file_exists:
                writer.writerow(['Local_QID', 'Wikidata_QID', 'Geni_IDs', 'Label', 'Notes'])
            
            # Write data
            writer.writerows(self.correspondence_data)
                
        safe_print(f"Saved correspondence data to {filename}")
        
    def run_comprehensive_fix(self, start_qid=1, end_qid=50000):
        """Run comprehensive fix on range of QIDs"""
        if not self.login():
            safe_print("Login failed!")
            return
            
        safe_print(f"Starting comprehensive database fix from Q{start_qid} to Q{end_qid}")
        
        # Determine actual starting point based on already processed entities
        actual_start = start_qid
        for i in range(start_qid, end_qid + 1):
            if f"Q{i}" not in self.processed_entities:
                actual_start = i
                break
        else:
            safe_print("All entities in range already processed!")
            return
            
        if actual_start > start_qid:
            safe_print(f"Resuming from Q{actual_start} (skipped {actual_start - start_qid} already processed)")
        
        processed = 0
        for i in range(actual_start, end_qid + 1):
            qid = f"Q{i}"
            self.process_entity(qid)
            processed += 1
            
            if processed % 100 == 0:
                safe_print(f"Processed {processed} new entities...")
                # Save CSV every 100 entities
                self.save_correspondence_csv()
                # Clear correspondence data to save memory
                self.correspondence_data = []
                
        # Final save
        self.save_correspondence_csv()
        safe_print(f"Comprehensive fix complete! Processed {processed} new entities.")

def main():
    import sys
    
    # Parse command line arguments: start_qid end_qid username password wiki_url
    if len(sys.argv) > 1:
        start_qid = int(sys.argv[1])
        end_qid = int(sys.argv[2]) if len(sys.argv) > 2 else start_qid + 1000
        username = sys.argv[3] if len(sys.argv) > 3 else None
        password = sys.argv[4] if len(sys.argv) > 4 else None
        wiki_url = sys.argv[5] if len(sys.argv) > 5 else None
        if wiki_url:
            wiki_api_url = f"{wiki_url}/w/api.php"
        else:
            wiki_api_url = None
    else:
        start_qid = 1
        end_qid = 50000
        username = None
        password = None
        wiki_api_url = None
        
    fixer = DatabaseFixer(wiki_api_url=wiki_api_url, username=username, password=password)
    fixer.run_comprehensive_fix(start_qid, end_qid)

if __name__ == "__main__":
    main()