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
    def __init__(self, wiki_api_url=None, username=None, password=None):
        self.wiki_api_url = wiki_api_url or "https://evolutionism.miraheze.org/w/api.php"
        self.username = username or USERNAME
        self.password = password or PASSWORD
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
        response = self.session.get(self.wiki_api_url, params=token_params, timeout=30)
        if response.status_code != 200:
            print(f"HTTP error: {response.status_code}")
            return False
        token_data = response.json()
        login_token = token_data['query']['tokens']['logintoken']
        
        login_data = {'action': 'login', 'lgname': USERNAME, 'lgpassword': PASSWORD, 'lgtoken': login_token, 'format': 'json'}
        response = self.session.post(self.wiki_api_url, data=login_data)
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
        response = self.session.get(self.wiki_api_url, params={'action': 'query', 'meta': 'tokens', 'format': 'json'})
        self.csrf_token = response.json()['query']['tokens']['csrftoken']
        print("CSRF token obtained")
        
    def get_entity_data(self, qid):
        """Get entity data"""
        try:
            response = self.session.get(self.wiki_api_url, params={
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
            
            response = self.session.post(self.wiki_api_url, data=data)
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
                data['value'] = json.dumps(value)
            elif value_type == 'time':
                data['value'] = json.dumps(value)
            elif value_type == 'url':
                data['value'] = json.dumps(value)
                
            response = self.session.post(self.wiki_api_url, data=data)
            result = response.json()
            
            if 'success' not in result:
                print(f"    Create claim failed: {result}")
            
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
                if self.remove_claim(claim['id']):
                    print(f"    Removed deprecated death date")
                time.sleep(0.2)
                
    def parse_bc_date(self, date_text):
        """Parse various date text formats into Wikibase time format"""
        try:
            import re
            
            # Month name mappings
            months = {
                'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
                'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12,
                'JANUARY': 1, 'FEBRUARY': 2, 'MARCH': 3, 'APRIL': 4,
                'JUNE': 6, 'JULY': 7, 'AUGUST': 8, 'SEPTEMBER': 9,
                'OCTOBER': 10, 'NOVEMBER': 11, 'DECEMBER': 12
            }
            
            # Handle "15 JUN 1301" format
            day_month_year = re.search(r'(\d{1,2})\s+([A-Z]{3,9})\s+(\d{3,4})', date_text, re.IGNORECASE)
            if day_month_year:
                day = int(day_month_year.group(1))
                month_name = day_month_year.group(2).upper()
                year = int(day_month_year.group(3))
                
                if month_name in months:
                    month = months[month_name]
                    return {
                        'time': f'+{year:04d}-{month:02d}-{day:02d}T00:00:00Z',
                        'timezone': 0,
                        'before': 0,
                        'after': 0,
                        'precision': 11,  # Day precision
                        'calendarmodel': 'http://www.wikidata.org/entity/Q1985786'
                    }
            
            # Handle "JUN 1301" format (month year)
            month_year = re.search(r'([A-Z]{3,9})\s+(\d{3,4})', date_text, re.IGNORECASE)
            if month_year:
                month_name = month_year.group(1).upper()
                year = int(month_year.group(2))
                
                if month_name in months:
                    month = months[month_name]
                    return {
                        'time': f'+{year:04d}-{month:02d}-00T00:00:00Z',
                        'timezone': 0,
                        'before': 0,
                        'after': 0,
                        'precision': 10,  # Month precision
                        'calendarmodel': 'http://www.wikidata.org/entity/Q1985786'
                    }
            
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
        """Extract Wikidata QIDs, Geni IDs, and UUID REFNs from GEDCOM REFN (P41)"""
        if 'P41' not in entity.get('claims', {}):
            return None, None, []
            
        print(f"  Processing REFN for {qid}")
        wikidata_qids = []
        geni_ids = []
        uuid_refns = []
        
        for claim in entity['claims']['P41']:
            if 'datavalue' in claim['mainsnak']:
                try:
                    value = claim['mainsnak']['datavalue']['value']
                    print(f"    Found REFN value: {value} (type: {type(value)})")
                    
                    # Handle string values directly (Q445758)
                    if isinstance(value, str):
                        # Check for Wikidata QID (Q followed by numbers)
                        if re.match(r'^Q\d+$', value):
                            wikidata_qids.append(value)
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
                            geni_ids.append(geni_number)
                            # Create Geni profile ID claim
                            if self.create_claim(qid, 'P43', 'string', geni_number):
                                # Add described at URL
                                geni_url = f"https://www.geni.com/profile/index/{geni_number}"
                                self.create_claim(qid, 'P45', 'url', geni_url)
                                # Remove from REFN
                                self.remove_claim(claim['id'])
                                print(f"    Extracted Geni ID: {geni_number}")
                        
                        # Check for UUID-like strings (hex digits, likely UUIDs)
                        elif re.match(r'^[A-F0-9]{32,40}$', value, re.IGNORECASE):
                            uuid_refns.append(value)
                            # Create UUID REFN claim (P60)
                            if self.create_claim(qid, 'P60', 'string', value):
                                # Remove from REFN
                                self.remove_claim(claim['id'])
                                print(f"    Extracted UUID REFN: {value}")
                        else:
                            print(f"    Unknown REFN format: {value}")
                            
                    # Handle monolingual text format
                    elif isinstance(value, dict) and 'text' in value:
                        text_value = value['text']
                        # Check for Wikidata QID
                        if re.match(r'^Q\d+$', text_value):
                            wikidata_qids.append(text_value)
                            if self.create_claim(qid, 'P44', 'string', text_value):
                                wikidata_url = f"https://wikidata.org/wiki/{text_value}"
                                self.create_claim(qid, 'P45', 'url', wikidata_url)
                                self.remove_claim(claim['id'])
                                print(f"    Extracted Wikidata ID: {text_value}")
                        # Check for Geni ID
                        elif text_value.startswith('geni:'):
                            geni_number = text_value[5:]
                            geni_ids.append(geni_number)
                            if self.create_claim(qid, 'P43', 'string', geni_number):
                                geni_url = f"https://www.geni.com/profile/index/{geni_number}"
                                self.create_claim(qid, 'P45', 'url', geni_url)
                                self.remove_claim(claim['id'])
                                print(f"    Extracted Geni ID: {geni_number}")
                        # Check for UUID-like strings
                        elif re.match(r'^[A-F0-9]{32,40}$', text_value, re.IGNORECASE):
                            uuid_refns.append(text_value)
                            if self.create_claim(qid, 'P60', 'string', text_value):
                                self.remove_claim(claim['id'])
                                print(f"    Extracted UUID REFN: {text_value}")
                                
                    time.sleep(0.2)
                        
                except Exception as e:
                    print(f"    Error processing REFN: {e}")
                    
        # Return first/primary IDs for compatibility, but all are processed
        primary_wikidata = wikidata_qids[0] if wikidata_qids else None  
        primary_geni = geni_ids[0] if geni_ids else None
        return primary_wikidata, primary_geni, uuid_refns
        
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
        """Import labels and descriptions from Wikidata - OPTIMIZED VERSION"""
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
            try:
                print(f"    Current label '{current_label}' should be moved to aliases")
            except UnicodeEncodeError:
                print(f"    Current label with non-ASCII characters should be moved to aliases")
            
        # OPTIMIZED LABEL IMPORT - Priority: en > mul > all languages
        if 'labels' in wd_entity:
            labels_to_import = {}
            
            # Priority 1: English label
            if 'en' in wd_entity['labels']:
                labels_to_import['en'] = wd_entity['labels']['en']
                print(f"    Found English label: {wd_entity['labels']['en']['value']}")
            
            # Priority 2: If no English, use 'mul' (multilingual) as English
            elif 'mul' in wd_entity['labels']:
                labels_to_import['en'] = {
                    'language': 'en',
                    'value': wd_entity['labels']['mul']['value']
                }
                print(f"    Using mul label as English: {wd_entity['labels']['mul']['value']}")
            
            # Priority 3: If neither English nor mul exists, import all languages
            else:
                print(f"    No English or mul label found, importing all languages")
                labels_to_import = wd_entity['labels']
            
            # Import the selected labels
            for lang, label_data in labels_to_import.items():
                try:
                    data = {
                        'action': 'wbsetlabel',
                        'id': local_qid,
                        'language': lang,
                        'value': label_data['value'],
                        'token': self.csrf_token,
                        'format': 'json',
                        'bot': 1
                    }
                    
                    response = self.session.post(self.wiki_api_url, data=data)
                    if 'success' in response.json():
                        print(f"    Set {lang} label: {label_data['value']}")
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"    Error setting {lang} label: {e}")
                    
        # OPTIMIZED DESCRIPTION IMPORT - Only English description
        if 'descriptions' in wd_entity:
            if 'en' in wd_entity['descriptions']:
                try:
                    desc_data = wd_entity['descriptions']['en']
                    data = {
                        'action': 'wbsetdescription',
                        'id': local_qid,
                        'language': 'en',
                        'value': desc_data['value'],
                        'token': self.csrf_token,
                        'format': 'json',
                        'bot': 1
                    }
                    
                    response = self.session.post(self.wiki_api_url, data=data)
                    if 'success' in response.json():
                        print(f"    Set en description: {desc_data['value']}")
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"    Error setting en description: {e}")
            else:
                print(f"    No English description available")
                    
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
                
        # Import Geni IDs if available (P2600)
        geni_ids_from_wd = []
        if ('claims' in wd_entity and 'P2600' in wd_entity['claims']):
            print(f"    Found Geni IDs in Wikidata")
            for geni_claim in wd_entity['claims']['P2600']:
                try:
                    if 'datavalue' in geni_claim['mainsnak']:
                        geni_id = geni_claim['mainsnak']['datavalue']['value']
                        geni_ids_from_wd.append(geni_id)
                        
                        # Create Geni profile ID claim
                        if self.create_claim(local_qid, 'P43', 'string', geni_id):
                            # Add described at URL
                            geni_url = f"https://www.geni.com/profile/index/{geni_id}"
                            self.create_claim(local_qid, 'P45', 'url', geni_url)
                            print(f"    Added Geni ID from Wikidata: {geni_id}")
                except Exception as e:
                    print(f"    Error adding Geni ID: {e}")
                    
        return geni_ids_from_wd
                
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
        new_wikidata_qid, new_geni_id, uuid_refns = self.extract_identifiers_from_refn(qid, entity)
        
        # Check for existing Wikidata IDs (P44), Geni IDs (P43), and UUID REFNs (P60)
        existing_wikidata_qids = []
        existing_geni_ids = []
        existing_uuid_refns = []
        
        claims = entity.get('claims', {})
        if 'P44' in claims:
            for claim in claims['P44']:
                if 'datavalue' in claim['mainsnak']:
                    existing_wikidata_qids.append(claim['mainsnak']['datavalue']['value'])
                    
        if 'P43' in claims:
            for claim in claims['P43']:
                if 'datavalue' in claim['mainsnak']:
                    existing_geni_ids.append(claim['mainsnak']['datavalue']['value'])
                    
        if 'P60' in claims:
            for claim in claims['P60']:
                if 'datavalue' in claim['mainsnak']:
                    existing_uuid_refns.append(claim['mainsnak']['datavalue']['value'])
        
        # Use primary Wikidata QID for import (new or existing)
        primary_wikidata_qid = new_wikidata_qid or (existing_wikidata_qids[0] if existing_wikidata_qids else None)
        
        # Import Wikidata data if available
        geni_ids_from_wd = []
        if primary_wikidata_qid and new_wikidata_qid:  # Only import if newly found
            geni_ids_from_wd = self.import_wikidata_labels_descriptions(qid, primary_wikidata_qid)
            
        # Get current English label and aliases for CSV
        en_labels = []
        
        # Add main English label
        if entity and 'labels' in entity and 'en' in entity['labels']:
            en_labels.append(entity['labels']['en']['value'])
            
        # Add English aliases
        if entity and 'aliases' in entity and 'en' in entity['aliases']:
            for alias in entity['aliases']['en']:
                alias_value = alias['value']
                if alias_value not in en_labels:  # Avoid duplicates
                    en_labels.append(alias_value)
        
        # Join multiple labels with semicolons
        combined_en_labels = ';'.join(en_labels) if en_labels else ''
        
        # Combine all Geni IDs (new + existing + from Wikidata)
        all_geni_ids = []
        if new_geni_id:
            all_geni_ids.append(new_geni_id)
        all_geni_ids.extend(existing_geni_ids)
        all_geni_ids.extend(geni_ids_from_wd)
        
        # Remove duplicates while preserving order
        unique_geni_ids = []
        for gid in all_geni_ids:
            if gid not in unique_geni_ids:
                unique_geni_ids.append(gid)
        
        # Combine all Wikidata QIDs
        all_wikidata_qids = []
        if new_wikidata_qid:
            all_wikidata_qids.append(new_wikidata_qid)
        all_wikidata_qids.extend(existing_wikidata_qids)
        
        # Remove duplicates
        unique_wikidata_qids = []
        for wid in all_wikidata_qids:
            if wid not in unique_wikidata_qids:
                unique_wikidata_qids.append(wid)
                
        # Combine all UUID REFNs (new + existing)
        all_uuid_refns = []
        all_uuid_refns.extend(uuid_refns)
        all_uuid_refns.extend(existing_uuid_refns)
        
        # Remove duplicates
        unique_uuid_refns = []
        for uid in all_uuid_refns:
            if uid not in unique_uuid_refns:
                unique_uuid_refns.append(uid)
        
        # Join multiple IDs with semicolons
        combined_geni_ids = ';'.join(unique_geni_ids) if unique_geni_ids else ''
        combined_wikidata_qids = ';'.join(unique_wikidata_qids) if unique_wikidata_qids else ''
        combined_uuid_refns = ';'.join(unique_uuid_refns) if unique_uuid_refns else ''
        
        # Add to correspondence data (ALWAYS add, regardless of identifiers)
        self.correspondence_data.append({
            'local_qid': qid,
            'wikidata_qid': combined_wikidata_qids,
            'geni_id': combined_geni_ids,
            'en_label': combined_en_labels,
            'uuid': combined_uuid_refns
        })
        
        # Add no identifiers instance if needed
        if not combined_wikidata_qids and not combined_geni_ids and not combined_uuid_refns:
            self.add_no_identifiers_instance(qid)
            
        time.sleep(0.5)  # Rate limiting
        
    def save_correspondence_csv(self):
        """Save correspondence data to CSV"""
        import os
        filename = 'qid_correspondence.csv'
        
        # Check if file exists to determine if we need headers
        file_exists = os.path.exists(filename)
        
        # Read existing data to avoid duplicates
        existing_qids = set()
        if file_exists:
            try:
                with open(filename, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        existing_qids.add(row['evolutionism_qid'])
            except Exception as e:
                print(f"Warning: Could not read existing CSV: {e}")
        
        # Open in append mode if file exists, write mode if new
        mode = 'a' if file_exists else 'w'
        with open(filename, mode, newline='', encoding='utf-8') as csvfile:
            fieldnames = ['evolutionism_qid', 'wikidata_qid', 'geni_id', 'en_label', 'uuid']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header only for new files
            if not file_exists:
                writer.writeheader()
                
            # Write new data, updating existing entries
            for row in self.correspondence_data:
                qid = row['local_qid']
                if qid in existing_qids:
                    # For existing QIDs, we need to update the entire file
                    # This is more complex, so for now just append new ones
                    print(f"  Skipping {qid} (already exists in CSV)")
                else:
                    writer.writerow({
                        'evolutionism_qid': row['local_qid'],
                        'wikidata_qid': row['wikidata_qid'],
                        'geni_id': row['geni_id'],
                        'en_label': row['en_label'],
                        'uuid': row['uuid']
                    })
                    print(f"  Added {qid} to CSV")
                
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
                # Save CSV every 100 entities
                self.save_correspondence_csv()
                # Clear correspondence data to save memory
                self.correspondence_data = []
                
        # Final save
        self.save_correspondence_csv()
        print(f"Comprehensive fix complete! Processed {processed} entities.")

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
            wiki_api_url = f"{wiki_url}/api.php"
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