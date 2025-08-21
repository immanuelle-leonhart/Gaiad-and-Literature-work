#!/usr/bin/env python3
"""
Wikibase Entity Uploader

Uploads entities from XML files to evolutionism.miraheze.org using the Wikibase API.
Instead of using XML import, this parses the XML and creates entities using the
wbcreateclaim and wbeditentity APIs, which is more reliable for Wikibase.

This approach:
- Parses the XML to extract entity data
- Creates entities one by one using Wikibase APIs
- Handles redirects properly
- Provides better error handling and progress tracking
"""

import requests
import os
import time
import xml.etree.ElementTree as ET
import json
import sys
from urllib.parse import urljoin

# MediaWiki configuration
WIKI_URL = "https://evolutionism.miraheze.org"
API_ENDPOINT = f"{WIKI_URL}/w/api.php"

# Upload configuration  
XML_DIRECTORY = "wikibase_export"
XML_FILE_PATTERN = "gaiad_wikibase_export_part_{:03d}.xml"
TOTAL_FILES = 30

# Request settings
REQUEST_TIMEOUT = 60
MAX_RETRIES = 3
RETRY_DELAY = 10

class WikibaseEntityUploader:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Gaiad Genealogy Entity Uploader/1.0'
        })
        
        self.stats = {
            'files_processed': 0,
            'entities_processed': 0,
            'entities_created': 0,
            'entities_updated': 0,
            'redirects_created': 0,
            'errors': 0,
            'start_time': time.time()
        }
        
        print(f"Wikibase Entity Uploader initialized")
        print(f"Target wiki: {WIKI_URL}")
        print(f"Username: {username}")
    
    def login(self):
        """Authenticate with MediaWiki"""
        print("\n=== AUTHENTICATION ===")
        
        try:
            # Get login token
            response = self.session.post(API_ENDPOINT, data={
                'action': 'query',
                'meta': 'tokens', 
                'type': 'login',
                'format': 'json'
            }, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            login_token = response.json()['query']['tokens']['logintoken']
            
            # Login
            response = self.session.post(API_ENDPOINT, data={
                'action': 'login',
                'lgname': self.username,
                'lgpassword': self.password,
                'lgtoken': login_token,
                'format': 'json'
            }, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            result = response.json()
            if result['login']['result'] != 'Success':
                raise Exception(f"Login failed: {result}")
            
            print("SUCCESS: Logged in successfully")
            return True
            
        except Exception as e:
            print(f"ERROR: Authentication failed: {e}")
            return False
    
    def get_csrf_token(self):
        """Get CSRF token"""
        try:
            response = self.session.post(API_ENDPOINT, data={
                'action': 'query',
                'meta': 'tokens',
                'type': 'csrf', 
                'format': 'json'
            }, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            return response.json()['query']['tokens']['csrftoken']
        except:
            return None
    
    def parse_xml_file(self, xml_file_path):
        """Parse XML file and extract entities"""
        try:
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            
            entities = []
            namespace_uri = "http://www.mediawiki.org/xml/export-0.11/"
            
            for page in root.findall(f'.//{{{namespace_uri}}}page'):
                title_elem = page.find(f'{{{namespace_uri}}}title')
                if title_elem is None:
                    continue
                    
                title = title_elem.text
                if not title or not title.startswith('Item:'):
                    continue
                
                qid = title.replace('Item:', '')
                if not qid.startswith('Q'):
                    continue
                
                # Check if it's a redirect
                redirect_elem = page.find(f'{{{namespace_uri}}}redirect')
                if redirect_elem is not None:
                    redirect_target = redirect_elem.get('title', '').replace('Item:', '')
                    entities.append({
                        'qid': qid,
                        'type': 'redirect',
                        'target': redirect_target
                    })
                    continue
                
                # Get revision content
                revision = page.find(f'.//{{{namespace_uri}}}revision')
                if revision is None:
                    continue
                    
                text_elem = revision.find(f'{{{namespace_uri}}}text')
                if text_elem is None or not text_elem.text:
                    continue
                
                try:
                    entity_data = json.loads(text_elem.text)
                    entities.append({
                        'qid': qid,
                        'type': 'entity',
                        'data': entity_data
                    })
                except json.JSONDecodeError:
                    print(f"  WARNING: Could not parse JSON for {qid}")
                    continue
            
            return entities
            
        except Exception as e:
            print(f"  ERROR: Failed to parse {xml_file_path}: {e}")
            return []
    
    def entity_exists(self, qid):
        """Check if entity already exists"""
        try:
            response = self.session.post(API_ENDPOINT, data={
                'action': 'wbgetentities',
                'ids': qid,
                'format': 'json'
            }, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            return qid in data.get('entities', {}) and 'missing' not in data['entities'].get(qid, {})
            
        except:
            return False
    
    def create_redirect(self, qid, target_qid):
        """Create a redirect entity"""
        try:
            csrf_token = self.get_csrf_token()
            if not csrf_token:
                return False
            
            response = self.session.post(API_ENDPOINT, data={
                'action': 'wbcreateredirect',
                'from': qid,
                'to': target_qid,
                'token': csrf_token,
                'format': 'json'
            }, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            result = response.json()
            if 'success' in result:
                return True
            else:
                print(f"    Redirect creation failed for {qid} -> {target_qid}: {result}")
                return False
                
        except Exception as e:
            print(f"    ERROR creating redirect {qid} -> {target_qid}: {e}")
            return False
    
    def create_entity(self, qid, entity_data):
        """Create or update an entity"""
        try:
            csrf_token = self.get_csrf_token()
            if not csrf_token:
                return False
            
            # Check if entity exists
            if self.entity_exists(qid):
                print(f"    Entity {qid} already exists, updating...")
                action = 'wbeditentity'
                params = {
                    'action': action,
                    'id': qid,
                    'data': json.dumps(entity_data),
                    'token': csrf_token,
                    'format': 'json'
                }
            else:
                print(f"    Creating new entity {qid}...")
                action = 'wbeditentity'
                params = {
                    'action': action,
                    'new': 'item',
                    'data': json.dumps(entity_data),
                    'token': csrf_token,
                    'format': 'json'
                }
            
            response = self.session.post(API_ENDPOINT, data=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            result = response.json()
            if 'entity' in result:
                created_qid = result['entity']['id']
                print(f"    SUCCESS: Entity created/updated as {created_qid}")
                return True
            else:
                print(f"    ERROR: Entity creation failed for {qid}: {result}")
                return False
                
        except Exception as e:
            print(f"    ERROR creating entity {qid}: {e}")
            return False
    
    def process_entities(self, entities, file_number):
        """Process a list of entities from one file"""
        print(f"  Processing {len(entities)} entities...")
        
        file_created = 0
        file_redirects = 0
        file_errors = 0
        
        for i, entity in enumerate(entities):
            if i % 100 == 0 and i > 0:
                print(f"    Processed {i}/{len(entities)} entities...")
            
            qid = entity['qid']
            entity_type = entity['type']
            
            try:
                if entity_type == 'redirect':
                    target_qid = entity['target']
                    success = self.create_redirect(qid, target_qid)
                    if success:
                        file_redirects += 1
                        self.stats['redirects_created'] += 1
                    else:
                        file_errors += 1
                        self.stats['errors'] += 1
                        
                elif entity_type == 'entity':
                    entity_data = entity['data']
                    success = self.create_entity(qid, entity_data)
                    if success:
                        file_created += 1
                        self.stats['entities_created'] += 1
                    else:
                        file_errors += 1
                        self.stats['errors'] += 1
                
                self.stats['entities_processed'] += 1
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                print(f"    ERROR processing {qid}: {e}")
                file_errors += 1
                self.stats['errors'] += 1
        
        print(f"  File {file_number} results: {file_created} created, {file_redirects} redirects, {file_errors} errors")
        return file_errors == 0
    
    def upload_all_files(self):
        """Upload all XML files"""
        print("\n=== STARTING ENTITY UPLOAD ===")
        
        # Find existing files
        existing_files = []
        for i in range(1, TOTAL_FILES + 1):
            filename = XML_FILE_PATTERN.format(i)
            filepath = os.path.join(XML_DIRECTORY, filename)
            if os.path.exists(filepath):
                existing_files.append((filepath, i))
        
        print(f"Found {len(existing_files)} XML files to process")
        
        if not existing_files:
            print("ERROR: No XML files found")
            return False
        
        # Process each file
        for filepath, file_number in existing_files:
            self.stats['files_processed'] += 1
            print(f"\n=== PROCESSING FILE {file_number}/{TOTAL_FILES} ===")
            print(f"File: {os.path.basename(filepath)}")
            
            # Parse XML
            entities = self.parse_xml_file(filepath)
            if not entities:
                print("  No entities found in file")
                continue
            
            print(f"  Found {len(entities)} entities in XML")
            
            # Process entities
            success = self.process_entities(entities, file_number)
            
            if success:
                print(f"  File {file_number} completed successfully")
            else:
                print(f"  File {file_number} completed with errors")
        
        # Final stats
        duration = time.time() - self.stats['start_time']
        print(f"\n=== UPLOAD SUMMARY ===")
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Entities processed: {self.stats['entities_processed']:,}")
        print(f"Entities created/updated: {self.stats['entities_created']:,}")
        print(f"Redirects created: {self.stats['redirects_created']:,}")
        print(f"Errors: {self.stats['errors']:,}")
        print(f"Duration: {duration:.1f} seconds")
        print(f"Rate: {self.stats['entities_processed'] / duration:.1f} entities/second")
        
        return self.stats['errors'] < self.stats['entities_processed'] * 0.1  # Less than 10% error rate

def main():
    if len(sys.argv) < 3:
        print("Usage: python wikibase_entity_uploader.py <username> <password>")
        return False
    
    username = sys.argv[1]
    password = sys.argv[2]
    
    uploader = WikibaseEntityUploader(username, password)
    
    if not uploader.login():
        return False
    
    success = uploader.upload_all_files()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)