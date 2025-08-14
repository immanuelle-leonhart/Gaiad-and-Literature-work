#!/usr/bin/env python3

import csv
import requests
import time
import sys
import codecs
from typing import Dict, List, Optional

# Set the stdout encoding to UTF-8 to handle Unicode characters
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

class NonLatinNamesProcessor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GaiadGenealogyBot/1.0 (https://evolutionism.miraheze.org/wiki/User:ImmanuelleBot)'
        })
        self.api_url = 'https://evolutionism.miraheze.org/w/api.php'
        self.processed_count = 0
        
    def login(self, username: str, password: str) -> bool:
        """Login to the wiki"""
        # Get login token
        login_token_params = {
            'action': 'query',
            'meta': 'tokens',
            'type': 'login',
            'format': 'json'
        }
        
        response = self.session.get(self.api_url, params=login_token_params)
        if response.status_code != 200:
            print(f"Failed to get login token: {response.status_code}")
            return False
            
        data = response.json()
        if 'query' not in data or 'tokens' not in data['query']:
            print("Failed to get login token from response")
            return False
            
        login_token = data['query']['tokens']['logintoken']
        
        # Perform login
        login_params = {
            'action': 'login',
            'lgname': username,
            'lgpassword': password,
            'lgtoken': login_token,
            'format': 'json'
        }
        
        response = self.session.post(self.api_url, data=login_params)
        if response.status_code != 200:
            print(f"Login failed: {response.status_code}")
            return False
            
        result = response.json()
        if result.get('login', {}).get('result') == 'Success':
            print("Successfully logged in")
            return True
        else:
            print(f"Login failed: {result}")
            return False
    
    def get_csrf_token(self) -> Optional[str]:
        """Get CSRF token for editing"""
        params = {
            'action': 'query',
            'meta': 'tokens',
            'format': 'json'
        }
        
        response = self.session.get(self.api_url, params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get('query', {}).get('tokens', {}).get('csrftoken')
        return None
    
    def get_entity_data(self, qid: str) -> Optional[Dict]:
        """Get current entity data"""
        params = {
            'action': 'wbgetentities',
            'ids': qid,
            'format': 'json'
        }
        
        response = self.session.get(self.api_url, params=params)
        if response.status_code == 200:
            data = response.json()
            if 'entities' in data and qid in data['entities']:
                return data['entities'][qid]
        return None
    
    def update_entity_labels_aliases(self, qid: str, current_label: str, translation: str) -> bool:
        """Update entity: move current en label to alias, add translation as en label and alias"""
        csrf_token = self.get_csrf_token()
        if not csrf_token:
            print(f"Failed to get CSRF token for {qid}")
            return False
        
        # Get current entity data
        entity_data = self.get_entity_data(qid)
        if not entity_data:
            print(f"Failed to get entity data for {qid}")
            return False
        
        # Get current aliases
        current_aliases = entity_data.get('aliases', {}).get('en', [])
        alias_values = [alias['value'] for alias in current_aliases]
        
        # Prepare the data to update
        data = {
            'action': 'wbeditentity',
            'id': qid,
            'token': csrf_token,
            'format': 'json',
            'bot': 1,
            'summary': f'Updated non-Latin name: moved "{current_label}" to alias, set "{translation}" as new en label'
        }
        
        # Build the entity data
        entity_update = {
            'labels': {
                'en': {'language': 'en', 'value': translation}
            },
            'aliases': {
                'en': []
            }
        }
        
        # Add current label as alias if not already present
        if current_label not in alias_values:
            entity_update['aliases']['en'].append({'language': 'en', 'value': current_label})
        
        # Add translation as alias if not already present and different from label
        if translation not in alias_values and translation != current_label:
            entity_update['aliases']['en'].append({'language': 'en', 'value': translation})
        
        # Add all existing aliases back
        for alias in current_aliases:
            if alias['value'] not in [current_label, translation]:
                entity_update['aliases']['en'].append(alias)
        
        data['data'] = str(entity_update).replace("'", '"')
        
        # Make the update request
        response = self.session.post(self.api_url, data=data)
        
        if response.status_code == 200:
            result = response.json()
            if 'success' in result:
                print(f"[OK] Updated {qid}: '{current_label}' -> '{translation}'")
                return True
            else:
                print(f"[FAIL] Failed to update {qid}: {result}")
                return False
        else:
            print(f"[ERROR] HTTP error updating {qid}: {response.status_code}")
            return False
    
    def process_csv_file(self, csv_file_path: str):
        """Process the CSV file and update all entities"""
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                # Skip empty first line if it exists
                first_line = file.readline().strip()
                if not first_line:
                    # Skip the empty line
                    pass
                else:
                    # Go back to beginning if first line wasn't empty
                    file.seek(0)
                    
                csv_reader = csv.DictReader(file)
                
                total_rows = sum(1 for _ in csv_reader)
                file.seek(0)
                # Skip empty first line again if it exists
                first_line = file.readline().strip()
                if not first_line:
                    pass
                else:
                    file.seek(0)
                csv_reader = csv.DictReader(file)
                
                print(f"Processing {total_rows} entries from {csv_file_path}")
                
                for row_num, row in enumerate(csv_reader, 1):
                    qid = row['id'].strip()
                    current_label = row['label_en'].strip()
                    translation = row['translation'].strip()
                    
                    print(f"[{row_num}/{total_rows}] Processing {qid}...")
                    
                    success = self.update_entity_labels_aliases(qid, current_label, translation)
                    
                    if success:
                        self.processed_count += 1
                    
                    # Rate limiting
                    time.sleep(0.5)
                
                print(f"\nCompleted! Successfully processed {self.processed_count} out of {total_rows} entries.")
                
        except FileNotFoundError:
            print(f"Error: File {csv_file_path} not found")
        except Exception as e:
            print(f"Error processing CSV file: {e}")

def main():
    if len(sys.argv) != 4:
        print("Usage: python non_latin_names_processor.py <csv_file_path> <username> <password>")
        print("Example: python non_latin_names_processor.py non_latin_names_with_translation_v2.csv ImmanuelleBot password")
        sys.exit(1)
    
    csv_file_path = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    
    processor = NonLatinNamesProcessor()
    
    # Login
    if not processor.login(username, password):
        print("Failed to login. Exiting.")
        sys.exit(1)
    
    # Process the CSV file
    processor.process_csv_file(csv_file_path)

if __name__ == "__main__":
    main()