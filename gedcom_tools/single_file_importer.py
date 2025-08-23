#!/usr/bin/env python3
"""
Single File XML Importer

Imports a single XML file to evolutionism.miraheze.org
Usage: python single_file_importer.py <xml_file> <username> <password>
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

# Request timeouts and retries
REQUEST_TIMEOUT = 300  # 5 minutes
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

class SingleFileImporter:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Gaiad Genealogy Single File Importer/1.0'
        })
        
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
                'lgname': self.username,
                'lgpassword': self.password,
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
    
    def import_xml_file(self, xml_file_path):
        """Import a single XML file"""
        print(f"=== IMPORTING XML FILE ===")
        print(f"File: {xml_file_path}")
        
        if not os.path.exists(xml_file_path):
            print(f"ERROR: File not found: {xml_file_path}")
            return False
        
        file_size = os.path.getsize(xml_file_path) / (1024 * 1024)  # MB
        print(f"File size: {file_size:.1f} MB")
        
        try:
            # Read XML file
            with open(xml_file_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            print("XML file loaded successfully")
            
            # Import via Special:Import
            import_url = f"{WIKI_URL}/wiki/Special:Import"
            print(f"Importing via: {import_url}")
            
            # Get edit token for import
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
            print(f"Got CSRF token: {csrf_token[:20]}...")
            
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
            
            print("Starting import...")
            start_time = time.time()
            
            # Submit import
            import_response = self.session.post(
                API_ENDPOINT,
                data=import_params,
                files=files,
                timeout=REQUEST_TIMEOUT
            )
            
            duration = time.time() - start_time
            print(f"Import request completed in {duration:.1f} seconds")
            
            import_response.raise_for_status()
            result_data = import_response.json()
            
            print(f"Import response: {result_data}")
            
            if 'import' in result_data:
                import_info = result_data['import']
                print(f"Import successful!")
                if isinstance(import_info, list):
                    print(f"Imported {len(import_info)} items")
                return True
            else:
                print(f"Import failed: {result_data}")
                return False
                
        except Exception as e:
            print(f"ERROR: Import failed: {e}")
            return False

def main():
    if len(sys.argv) != 4:
        print("Single File XML Importer")
        print("Usage: python single_file_importer.py <xml_file> <username> <password>")
        sys.exit(1)
    
    xml_file = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    
    importer = SingleFileImporter(username, password)
    
    # Login
    if not importer.login():
        print("FATAL: Authentication failed")
        sys.exit(1)
    
    # Import file
    success = importer.import_xml_file(xml_file)
    
    if success:
        print("SUCCESS: Import completed")
        sys.exit(0)
    else:
        print("FAILED: Import failed")
        sys.exit(1)

if __name__ == "__main__":
    main()