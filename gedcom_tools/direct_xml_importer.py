#!/usr/bin/env python3
"""
Direct XML File Importer

Imports all 120-part XML files directly without subprocess calls.
This avoids the timeout issues we encountered with subprocess management.
"""

import os
import glob
import time
import requests
import json
from pathlib import Path

# Configuration
EXPORTS_DIR = "exports_with_labels"
USERNAME = "Immanuelle"
PASSWORD = "1996ToOmega!"
WIKI_URL = "https://evolutionism.miraheze.org"
API_ENDPOINT = f"{WIKI_URL}/w/api.php"

# Request timeouts and retries
REQUEST_TIMEOUT = 300  # 5 minutes
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

class DirectXMLImporter:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Gaiad Genealogy Direct XML Importer/1.0'
        })
        
        self.stats = {
            'files_processed': 0,
            'files_successful': 0,
            'files_failed': 0,
            'total_entities_imported': 0,
            'start_time': time.time(),
            'failed_files': []
        }
        
        print(f"Direct XML Importer initialized")
        print(f"Target wiki: {WIKI_URL}")
        print(f"Username: {USERNAME}")
        print()
    
    def login(self):
        """Authenticate with MediaWiki"""
        print("=== AUTHENTICATION ===")
        print("Logging in to MediaWiki...")
        
        try:
            # Get login token
            token_params = {
                'action': 'query',
                'meta': 'tokens',
                'type': 'login',
                'format': 'json'
            }
            
            response = self.session.post(API_ENDPOINT, data=token_params, timeout=30)
            response.raise_for_status()
            token_data = response.json()
            
            if 'query' not in token_data or 'tokens' not in token_data['query']:
                raise Exception("Failed to get login token")
            
            login_token = token_data['query']['tokens']['logintoken']
            print(f"  Got login token: {login_token[:20]}...")
            
            # Login with credentials
            login_params = {
                'action': 'login',
                'lgname': USERNAME,
                'lgpassword': PASSWORD,
                'lgtoken': login_token,
                'format': 'json'
            }
            
            login_response = self.session.post(API_ENDPOINT, data=login_params, timeout=30)
            login_response.raise_for_status()
            login_data = login_response.json()
            
            if 'login' not in login_data:
                raise Exception("Invalid login response")
            
            login_result = login_data['login']['result']
            
            if login_result == 'Success':
                print("  SUCCESS: Authentication successful")
                return True
            else:
                print(f"  ERROR: Authentication failed: {login_data}")
                return False
                
        except Exception as e:
            print(f"  ERROR: Authentication failed: {e}")
            return False
    
    def find_xml_files(self):
        """Find all 120-part XML files"""
        pattern = os.path.join(EXPORTS_DIR, "gaiad_wikibase_export_with_labels_120part_*.xml")
        files = glob.glob(pattern)
        
        # Sort by part number
        def extract_part_number(filename):
            basename = os.path.basename(filename)
            # Extract number from filename like "gaiad_wikibase_export_with_labels_120part_001.xml"
            parts = basename.split('_')
            for part in parts:
                if part.endswith('.xml'):
                    return int(part.replace('.xml', ''))
            return 0
        
        files.sort(key=extract_part_number)
        return files
    
    def import_xml_file(self, xml_file_path, part_number, total_parts):
        """Import a single XML file directly"""
        filename = os.path.basename(xml_file_path)
        print(f"=== IMPORTING PART {part_number}/{total_parts}: {filename} ===")
        
        if not os.path.exists(xml_file_path):
            print(f"  ERROR: File not found: {xml_file_path}")
            return False
        
        file_size = os.path.getsize(xml_file_path) / (1024 * 1024)  # MB
        print(f"  File size: {file_size:.1f} MB")
        
        for attempt in range(MAX_RETRIES):
            try:
                print(f"  Import attempt {attempt + 1}/{MAX_RETRIES}...")
                
                # Read XML file
                with open(xml_file_path, 'r', encoding='utf-8') as f:
                    xml_content = f.read()
                
                print(f"    XML file loaded ({len(xml_content)} characters)")
                
                # Get CSRF token for import
                token_params = {
                    'action': 'query',
                    'meta': 'tokens',
                    'type': 'csrf',
                    'format': 'json'
                }
                
                token_response = self.session.post(API_ENDPOINT, data=token_params, timeout=30)
                token_response.raise_for_status()
                token_data = token_response.json()
                
                if 'query' not in token_data or 'tokens' not in token_data['query']:
                    raise Exception("Failed to get CSRF token")
                    
                csrf_token = token_data['query']['tokens']['csrftoken']
                print(f"    Got CSRF token: {csrf_token[:20]}...")
                
                # Prepare import data
                import_params = {
                    'action': 'import',
                    'token': csrf_token,
                    'format': 'json',
                    'interwikiprefix': 'gaiad',  # Use gaiad as the interwiki prefix
                    'fullhistory': '1',
                    'templates': '1'
                }
                
                # Prepare file data
                files = {
                    'xml': ('import.xml', xml_content, 'application/xml')
                }
                
                print("    Starting import...")
                start_time = time.time()
                
                # Submit import
                import_response = self.session.post(
                    API_ENDPOINT,
                    data=import_params,
                    files=files,
                    timeout=REQUEST_TIMEOUT
                )
                
                duration = time.time() - start_time
                print(f"    Import completed in {duration:.1f} seconds")
                
                import_response.raise_for_status()
                result_data = import_response.json()
                
                # Parse results
                if 'import' in result_data:
                    import_info = result_data['import']
                    if isinstance(import_info, list):
                        entities_imported = len(import_info)
                        print(f"    SUCCESS: Imported {entities_imported} entities")
                        self.stats['total_entities_imported'] += entities_imported
                    else:
                        print(f"    SUCCESS: Import completed")
                        # Estimate entities based on file size (roughly 1 entity per 1KB)
                        estimated_entities = int(file_size * 1000 / 1000)  # rough estimate
                        self.stats['total_entities_imported'] += estimated_entities
                    
                    return True
                else:
                    print(f"    WARNING: Unexpected response: {result_data}")
                    return False
                    
            except requests.exceptions.Timeout:
                print(f"    TIMEOUT on attempt {attempt + 1}")
                if attempt < MAX_RETRIES - 1:
                    print(f"    Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    print(f"  ERROR: Import timed out after {MAX_RETRIES} attempts")
                    return False
                    
            except Exception as e:
                print(f"    ERROR on attempt {attempt + 1}: {e}")
                if attempt < MAX_RETRIES - 1:
                    print(f"    Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    print(f"  ERROR: Import failed after {MAX_RETRIES} attempts")
                    return False
        
        return False
    
    def import_all_files(self):
        """Import all XML files"""
        print("=== STARTING DIRECT XML IMPORT ===")
        print()
        
        # Find all XML files
        xml_files = self.find_xml_files()
        
        if not xml_files:
            print("ERROR: No 120-part XML files found!")
            print(f"Looking in: {EXPORTS_DIR}")
            print("Expected pattern: gaiad_wikibase_export_with_labels_120part_*.xml")
            return False
        
        total_files = len(xml_files)
        print(f"Found {total_files} XML files to import")
        print()
        
        # Show first few files
        print("Files to import:")
        for i, xml_file in enumerate(xml_files[:10]):
            print(f"  {i+1:3d}. {os.path.basename(xml_file)}")
        if total_files > 10:
            print(f"  ... and {total_files - 10} more files")
        print()
        
        # Import each file
        for i, xml_file in enumerate(xml_files, 1):
            print(f"\n{'='*60}")
            
            success = self.import_xml_file(xml_file, i, total_files)
            
            if success:
                self.stats['files_successful'] += 1
                print(f"OK Part {i} completed successfully")
            else:
                self.stats['files_failed'] += 1
                self.stats['failed_files'].append(os.path.basename(xml_file))
                print(f"FAILED Part {i} failed")
            
            self.stats['files_processed'] += 1
            
            # Show progress
            progress = (i / total_files) * 100
            elapsed = time.time() - self.stats['start_time']
            estimated_remaining = (elapsed / i) * (total_files - i) if i > 0 else 0
            
            print(f"Progress: {progress:.1f}% ({i}/{total_files})")
            print(f"Elapsed: {elapsed/60:.1f}min, Est. remaining: {estimated_remaining/60:.1f}min")
            print(f"Success: {self.stats['files_successful']}, Failed: {self.stats['files_failed']}")
            
            # Brief pause between imports
            if i < total_files:
                print("Waiting 2 seconds before next import...")
                time.sleep(2)
        
        # Final summary
        total_time = time.time() - self.stats['start_time']
        print(f"\n{'='*60}")
        print("=== IMPORT SUMMARY ===")
        print(f"Total files: {total_files}")
        print(f"Successful imports: {self.stats['files_successful']}")
        print(f"Failed imports: {self.stats['files_failed']}")
        print(f"Total entities imported: {self.stats['total_entities_imported']:,}")
        print(f"Total time: {total_time/60:.1f} minutes")
        
        if self.stats['failed_files']:
            print(f"\nFailed files:")
            for failed_file in self.stats['failed_files'][:10]:  # Show first 10
                print(f"  - {failed_file}")
            if len(self.stats['failed_files']) > 10:
                print(f"  ... and {len(self.stats['failed_files']) - 10} more")
        
        if self.stats['files_successful'] > 0:
            success_rate = (self.stats['files_successful'] / total_files) * 100
            print(f"\nSuccess rate: {success_rate:.1f}%")
            avg_time = total_time / self.stats['files_successful']
            print(f"Average time per file: {avg_time:.1f} seconds")
        
        if self.stats['files_failed'] == 0:
            print("\nSUCCESS: All files imported successfully!")
        elif self.stats['files_successful'] > self.stats['files_failed']:
            print(f"\nMOSTLY SUCCESSFUL: {self.stats['files_successful']} imports completed")
        else:
            print(f"\nMANY ISSUES: {self.stats['files_failed']} failures")
            print("May need to try even smaller chunks")
        
        return self.stats['files_successful'] > 0

def main():
    print("Direct XML File Importer for Evolutionism Miraheze")
    print("=" * 50)
    print()
    
    # Create importer
    importer = DirectXMLImporter()
    
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
    print("\nImport process completed.")
    if success:
        print("Check the summary above for results.")
    else:
        print("Import failed - check error messages above.")