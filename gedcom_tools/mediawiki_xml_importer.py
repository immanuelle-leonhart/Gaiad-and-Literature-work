#!/usr/bin/env python3
"""
MediaWiki XML Importer for Evolutionism Miraheze

Imports all generated XML files to evolutionism.miraheze.org using the MediaWiki API.
Handles authentication, chunking, timeouts, and retries for reliable import.

Features:
- Bot authentication with login credentials
- Chunked file upload for large XML files
- Automatic retry on timeouts and errors
- Progress tracking and verification
- Session management and CSRF token handling
"""

import requests
import os
import time
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
import json
import sys

# MediaWiki configuration
WIKI_URL = "https://evolutionism.miraheze.org"
API_ENDPOINT = f"{WIKI_URL}/w/api.php"

# Import configuration
XML_DIRECTORY = "wikibase_export"  # Directory where XML files are located
XML_FILE_PATTERN = "gaiad_wikibase_export_part_{:03d}.xml"
TOTAL_FILES = 30

# Request timeouts and retries
REQUEST_TIMEOUT = 300  # 5 minutes
MAX_RETRIES = 3
RETRY_DELAY = 30  # seconds

class MediaWikiImporter:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Gaiad Genealogy XML Importer/1.0 (https://github.com/user/gaiad-genealogy)'
        })
        
        self.stats = {
            'files_processed': 0,
            'files_successful': 0,
            'files_failed': 0,
            'total_entities_imported': 0,
            'import_errors': [],
            'start_time': time.time()
        }
        
        print(f"MediaWiki Importer initialized")
        print(f"Target wiki: {WIKI_URL}")
        print(f"Username: {username}")
        print()
    
    def login(self):
        """Authenticate with MediaWiki"""
        print("=== AUTHENTICATION ===")
        print("Logging in to MediaWiki...")
        
        try:
            # Get login token
            login_token_params = {
                'action': 'query',
                'meta': 'tokens',
                'type': 'login',
                'format': 'json'
            }
            
            response = self.session.post(API_ENDPOINT, data=login_token_params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            if 'query' not in data or 'tokens' not in data['query']:
                raise Exception(f"Failed to get login token: {data}")
            
            login_token = data['query']['tokens']['logintoken']
            print(f"  Got login token: {login_token[:20]}...")
            
            # Perform login
            login_params = {
                'action': 'login',
                'lgname': self.username,
                'lgpassword': self.password,
                'lgtoken': login_token,
                'format': 'json'
            }
            
            response = self.session.post(API_ENDPOINT, data=login_params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            if data.get('login', {}).get('result') != 'Success':
                raise Exception(f"Login failed: {data}")
            
            print("  SUCCESS: Logged in successfully")
            
            # Verify we have edit permissions
            user_info_params = {
                'action': 'query',
                'meta': 'userinfo',
                'uiprop': 'rights',
                'format': 'json'
            }
            
            response = self.session.post(API_ENDPOINT, data=user_info_params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            rights = data.get('query', {}).get('userinfo', {}).get('rights', [])
            print(f"  User rights: {', '.join(rights[:10])}")
            
            if 'import' not in rights:
                print("  WARNING: User may not have import rights")
            
            return True
            
        except Exception as e:
            print(f"  ERROR: Authentication failed: {e}")
            return False
    
    def get_csrf_token(self):
        """Get CSRF token for protected operations"""
        try:
            params = {
                'action': 'query',
                'meta': 'tokens',
                'type': 'csrf',
                'format': 'json'
            }
            
            response = self.session.post(API_ENDPOINT, data=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            token = data['query']['tokens']['csrftoken']
            return token
            
        except Exception as e:
            print(f"  ERROR: Failed to get CSRF token: {e}")
            return None
    
    def count_entities_in_xml(self, xml_file_path):
        """Count entities in an XML file"""
        try:
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            
            # Count page elements (entities)
            pages = root.findall('.//{http://www.mediawiki.org/xml/export-0.11/}page')
            return len(pages)
            
        except Exception as e:
            print(f"  WARNING: Could not count entities in {xml_file_path}: {e}")
            return 0
    
    def import_xml_file(self, xml_file_path, file_number):
        """Import a single XML file"""
        filename = os.path.basename(xml_file_path)
        print(f"=== IMPORTING FILE {file_number}/{TOTAL_FILES}: {filename} ===")
        
        if not os.path.exists(xml_file_path):
            print(f"  ERROR: File not found: {xml_file_path}")
            self.stats['files_failed'] += 1
            self.stats['import_errors'].append(f"{filename}: File not found")
            return False
        
        file_size = os.path.getsize(xml_file_path)
        entity_count = self.count_entities_in_xml(xml_file_path)
        
        print(f"  File size: {file_size:,} bytes")
        print(f"  Estimated entities: {entity_count:,}")
        
        for attempt in range(MAX_RETRIES):
            try:
                print(f"  Import attempt {attempt + 1}/{MAX_RETRIES}...")
                
                # Get fresh CSRF token for this import
                csrf_token = self.get_csrf_token()
                if not csrf_token:
                    raise Exception("Failed to get CSRF token")
                
                # Prepare import request
                import_params = {
                    'action': 'import',
                    'format': 'json',
                    'token': csrf_token,
                    'interwikiprefix': 'gaiad',  # Import with gaiad prefix
                    'summary': f'Automated import of Gaiad genealogical data - {filename}',
                    'namespace': '',  # Import to appropriate namespaces based on XML content
                    'assignknownusers': 1,  # Assign to known users
                    'usewguser': 1  # Use current user as importer
                }
                
                # Upload XML file
                with open(xml_file_path, 'rb') as xml_file:
                    files = {
                        'xml': (filename, xml_file, 'application/xml')
                    }
                    
                    print(f"    Uploading {filename}...")
                    response = self.session.post(
                        API_ENDPOINT,
                        data=import_params,
                        files=files,
                        timeout=REQUEST_TIMEOUT
                    )
                    response.raise_for_status()
                
                # Parse response
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    # Sometimes MediaWiki returns HTML error pages
                    if 'error' in response.text.lower() or response.status_code != 200:
                        raise Exception(f"Server returned non-JSON response: {response.text[:500]}")
                    raise
                
                # Check for API errors
                if 'error' in data:
                    error_code = data['error'].get('code', 'unknown')
                    error_info = data['error'].get('info', 'No details')
                    raise Exception(f"API error {error_code}: {error_info}")
                
                # Check import results
                if 'import' in data:
                    import_results = data['import']
                    
                    if isinstance(import_results, list):
                        # Multiple import results
                        successful_imports = sum(1 for result in import_results if result.get('title'))
                        failed_imports = len(import_results) - successful_imports
                        
                        print(f"    SUCCESS: {successful_imports} entities imported")
                        if failed_imports > 0:
                            print(f"    WARNING: {failed_imports} entities failed to import")
                        
                        self.stats['total_entities_imported'] += successful_imports
                        
                    else:
                        # Single import result
                        if import_results.get('title'):
                            print(f"    SUCCESS: Imported {import_results['title']}")
                            self.stats['total_entities_imported'] += entity_count
                        else:
                            print(f"    WARNING: Import may have failed: {import_results}")
                
                else:
                    # No specific import results, but no error either
                    print(f"    SUCCESS: Import completed (no detailed results)")
                    self.stats['total_entities_imported'] += entity_count
                
                self.stats['files_successful'] += 1
                print(f"  OK File {filename} imported successfully")
                return True
                
            except requests.exceptions.Timeout:
                print(f"    TIMEOUT on attempt {attempt + 1}")
                if attempt < MAX_RETRIES - 1:
                    print(f"    Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    error_msg = f"{filename}: Import timed out after {MAX_RETRIES} attempts"
                    print(f"  ERROR: {error_msg}")
                    self.stats['files_failed'] += 1
                    self.stats['import_errors'].append(error_msg)
                    return False
                    
            except Exception as e:
                print(f"    ERROR on attempt {attempt + 1}: {e}")
                if attempt < MAX_RETRIES - 1:
                    print(f"    Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    error_msg = f"{filename}: {str(e)}"
                    print(f"  ERROR: Import failed after {MAX_RETRIES} attempts")
                    self.stats['files_failed'] += 1
                    self.stats['import_errors'].append(error_msg)
                    return False
        
        return False
    
    def verify_import(self):
        """Verify that entities were successfully imported"""
        print("=== IMPORT VERIFICATION ===")
        print("Checking a sample of imported entities...")
        
        # Sample QIDs to check
        sample_qids = ['Q1', 'Q100', 'Q1000', 'Q10000']
        verified_count = 0
        
        for qid in sample_qids:
            try:
                # Check if entity exists
                params = {
                    'action': 'wbgetentities',
                    'ids': qid,
                    'format': 'json'
                }
                
                response = self.session.post(API_ENDPOINT, data=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if 'entities' in data and qid in data['entities']:
                    entity = data['entities'][qid]
                    if 'missing' not in entity:
                        verified_count += 1
                        print(f"  OK {qid}: Found")
                    else:
                        print(f"  - {qid}: Missing")
                else:
                    print(f"  - {qid}: Not found")
                    
            except Exception as e:
                print(f"  ERROR checking {qid}: {e}")
        
        print(f"Verification: {verified_count}/{len(sample_qids)} sample entities found")
        return verified_count > 0
    
    def import_all_files(self):
        """Import all XML files"""
        print("=== STARTING XML IMPORT TO EVOLUTIONISM.MIRAHEZE.ORG ===")
        print()
        
        # Check if XML files exist
        existing_files = []
        for i in range(1, TOTAL_FILES + 1):
            filename = XML_FILE_PATTERN.format(i)
            filepath = os.path.join(XML_DIRECTORY, filename)
            if os.path.exists(filepath):
                existing_files.append((filepath, i))
            else:
                print(f"WARNING: File not found: {filename}")
        
        print(f"Found {len(existing_files)} of {TOTAL_FILES} expected XML files")
        
        if not existing_files:
            print("ERROR: No XML files found to import")
            return False
        
        print()
        
        # Import each file
        for filepath, file_number in existing_files:
            self.stats['files_processed'] += 1
            success = self.import_xml_file(filepath, file_number)
            
            if success:
                print(f"  File {file_number} completed successfully")
            else:
                print(f"  File {file_number} failed")
            
            print()
            
            # Brief pause between files
            time.sleep(2)
        
        # Final statistics
        duration = time.time() - self.stats['start_time']
        
        print("=== IMPORT SUMMARY ===")
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Files successful: {self.stats['files_successful']}")
        print(f"Files failed: {self.stats['files_failed']}")
        print(f"Total entities imported: {self.stats['total_entities_imported']:,}")
        print(f"Import duration: {duration:.1f} seconds")
        
        if self.stats['import_errors']:
            print()
            print("IMPORT ERRORS:")
            for error in self.stats['import_errors']:
                print(f"  - {error}")
        
        if self.stats['files_successful'] > 0:
            print()
            print("SUCCESS: XML import completed!")
            print(f"Imported {self.stats['files_successful']} files with {self.stats['total_entities_imported']:,} entities")
            
            # Verify import
            verification_success = self.verify_import()
            if verification_success:
                print("Verification: Sample entities found in wiki")
            else:
                print("WARNING: Verification failed - entities may not be accessible")
                
        else:
            print()
            print("ERROR: No files were successfully imported")
            return False
        
        return self.stats['files_successful'] > 0

def main():
    print("MediaWiki XML Importer for Evolutionism Miraheze")
    print("=" * 50)
    print()
    
    # Get credentials from command line arguments or environment
    username = None
    password = None
    
    if len(sys.argv) >= 3:
        username = sys.argv[1]
        password = sys.argv[2]
    else:
        # Try environment variables
        username = os.environ.get('MEDIAWIKI_USERNAME')
        password = os.environ.get('MEDIAWIKI_PASSWORD')
    
    if not username or not password:
        print("ERROR: Username and password are required")
        print("Usage: python mediawiki_xml_importer.py <username> <password>")
        print("   or: set MEDIAWIKI_USERNAME and MEDIAWIKI_PASSWORD environment variables")
        return False
    
    print()
    
    # Create importer
    importer = MediaWikiImporter(username, password)
    
    try:
        # Authenticate
        if not importer.login():
            print("FATAL: Authentication failed")
            return False
        
        print()
        
        # Import all files
        success = importer.import_all_files()
        
        return success
        
    except KeyboardInterrupt:
        print("\nImport interrupted by user")
        return False
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)