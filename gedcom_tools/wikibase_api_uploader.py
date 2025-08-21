#!/usr/bin/env python3
"""
Wikibase API-Compatible Uploader

Creates entities using the CORRECT Wikibase API format that addresses all the errors:
- Labels: proper monolingual text format
- Entity references: correct wikibase-item structure  
- External IDs: proper external-id format
- Properties: correct claim structure
"""

import requests
import pymongo
import time
import json
import sys

# Configuration
WIKI_URL = "https://evolutionism.miraheze.org"
API_ENDPOINT = f"{WIKI_URL}/w/api.php"
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"

class WikibaseAPIUploader:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Gaiad Genealogy API Uploader/1.0'
        })
        
        # MongoDB connection
        self.mongo_client = pymongo.MongoClient(MONGO_URI)
        self.db = self.mongo_client[DATABASE_NAME]
        self.collection = self.db['entities']
        
        self.stats = {
            'entities_processed': 0,
            'entities_created': 0,
            'entities_updated': 0,
            'errors': 0,
            'start_time': time.time()
        }
    
    def login(self):
        """Login to MediaWiki"""
        print("=== AUTHENTICATION ===")
        try:
            # Get login token
            response = self.session.post(API_ENDPOINT, data={
                'action': 'query',
                'meta': 'tokens',
                'type': 'login',
                'format': 'json'
            })
            response.raise_for_status()
            login_token = response.json()['query']['tokens']['logintoken']
            
            # Login
            response = self.session.post(API_ENDPOINT, data={
                'action': 'login',
                'lgname': self.username,
                'lgpassword': self.password,
                'lgtoken': login_token,
                'format': 'json'
            })
            response.raise_for_status()
            
            result = response.json()
            if result['login']['result'] != 'Success':
                raise Exception(f"Login failed: {result}")
            
            print("SUCCESS: Logged in")
            return True
        except Exception as e:
            print(f"ERROR: {e}")
            return False
    
    def get_csrf_token(self):
        """Get CSRF token"""
        response = self.session.post(API_ENDPOINT, data={
            'action': 'query',
            'meta': 'tokens',
            'type': 'csrf',
            'format': 'json'
        })
        return response.json()['query']['tokens']['csrftoken']
    
    def create_proper_wikibase_data(self, entity):
        """Create proper Wikibase API JSON structure"""
        qid = entity['qid']
        wikibase_data = {}
        
        # Labels - CORRECT monolingual format
        labels = entity.get('labels', {})
        if labels:
            wikibase_data['labels'] = {}
            for lang, text in labels.items():
                if isinstance(text, str) and text.strip():
                    wikibase_data['labels'][lang] = {
                        'language': lang,
                        'value': text.strip()
                    }
        
        # Descriptions - same format as labels
        descriptions = entity.get('descriptions', {})
        if descriptions:
            wikibase_data['descriptions'] = {}
            for lang, text in descriptions.items():
                if isinstance(text, str) and text.strip():
                    wikibase_data['descriptions'][lang] = {
                        'language': lang,
                        'value': text.strip()
                    }
        
        # Claims/Properties - CORRECT claim format
        properties = entity.get('properties', {})
        if properties:
            wikibase_data['claims'] = {}
            
            for prop_id, claims in properties.items():
                if prop_id == 'redirect':
                    continue  # Skip redirects
                
                wikibase_claims = []
                for claim in claims:
                    claim_value = claim.get('value')
                    claim_type = claim.get('type', 'string')
                    
                    if not claim_value:
                        continue
                    
                    # Create proper claim structure
                    wikibase_claim = {
                        'mainsnak': {
                            'snaktype': 'value',
                            'property': prop_id
                        },
                        'type': 'statement',
                        'rank': 'normal'
                    }
                    
                    # Handle different property types with CORRECT formats
                    if claim_type == 'external-id':
                        # External IDs (P61, P62, P63)
                        wikibase_claim['mainsnak']['datavalue'] = {
                            'value': str(claim_value),
                            'type': 'string'
                        }
                        
                    elif claim_type == 'wikibase-item':
                        # Entity references (P20, P42, P47, P48)
                        if isinstance(claim_value, str) and claim_value.startswith('Q'):
                            numeric_id = int(claim_value[1:]) if claim_value[1:].isdigit() else 1
                            wikibase_claim['mainsnak']['datavalue'] = {
                                'value': {
                                    'entity-type': 'item',
                                    'numeric-id': numeric_id,
                                    'id': claim_value
                                },
                                'type': 'wikibase-entityid'
                            }
                        else:
                            continue  # Skip invalid entity references
                    
                    elif claim_type == 'time':
                        # Date properties (P56, P57)
                        if isinstance(claim_value, dict):
                            wikibase_claim['mainsnak']['datavalue'] = {
                                'value': claim_value,
                                'type': 'time'
                            }
                        else:
                            # Convert string dates to time format
                            wikibase_claim['mainsnak']['datavalue'] = {
                                'value': {
                                    'time': str(claim_value),
                                    'timezone': 0,
                                    'before': 0,
                                    'after': 0,
                                    'precision': 11,
                                    'calendarmodel': 'http://www.wikidata.org/entity/Q1985727'
                                },
                                'type': 'time'
                            }
                    
                    else:
                        # String properties (default)
                        wikibase_claim['mainsnak']['datavalue'] = {
                            'value': str(claim_value),
                            'type': 'string'
                        }
                    
                    wikibase_claims.append(wikibase_claim)
                
                if wikibase_claims:
                    wikibase_data['claims'][prop_id] = wikibase_claims
        
        return wikibase_data
    
    def entity_exists(self, qid):
        """Check if entity exists"""
        try:
            response = self.session.post(API_ENDPOINT, data={
                'action': 'wbgetentities',
                'ids': qid,
                'format': 'json'
            })
            data = response.json()
            return qid in data.get('entities', {}) and 'missing' not in data['entities'].get(qid, {})
        except:
            return False
    
    def create_or_update_entity(self, entity):
        """Create or update a single entity"""
        qid = entity['qid']
        
        # Skip redirects
        if 'redirect' in entity.get('properties', {}):
            return True  # Skip redirects for now
        
        try:
            # Create proper Wikibase data
            wikibase_data = self.create_proper_wikibase_data(entity)
            
            # Get CSRF token
            csrf_token = self.get_csrf_token()
            
            # Check if exists
            exists = self.entity_exists(qid)
            
            if exists:
                print(f"  Updating {qid}...")
                params = {
                    'action': 'wbeditentity',
                    'id': qid,
                    'data': json.dumps(wikibase_data),
                    'token': csrf_token,
                    'format': 'json'
                }
            else:
                print(f"  Creating {qid}...")
                params = {
                    'action': 'wbeditentity',
                    'new': 'item',
                    'data': json.dumps(wikibase_data),
                    'token': csrf_token,
                    'format': 'json'
                }
            
            response = self.session.post(API_ENDPOINT, data=params)
            result = response.json()
            
            if 'entity' in result:
                if exists:
                    self.stats['entities_updated'] += 1
                else:
                    self.stats['entities_created'] += 1
                return True
            else:
                error_info = result.get('error', {})
                print(f"    ERROR: {error_info.get('info', 'Unknown error')}")
                self.stats['errors'] += 1
                return False
        
        except Exception as e:
            print(f"    ERROR: {e}")
            self.stats['errors'] += 1
            return False
    
    def test_single_entity(self):
        """Test with a single entity to verify format"""
        print("\n=== TESTING SINGLE ENTITY ===")
        
        # Find an entity with various properties
        test_entity = None
        for entity in self.collection.find().limit(100):
            properties = entity.get('properties', {})
            if 'P61' in properties or 'P20' in properties:  # Has external ID or entity reference
                test_entity = entity
                break
        
        if not test_entity:
            print("No suitable test entity found")
            return False
        
        print(f"Testing with entity {test_entity['qid']}")
        
        # Show the data we'll send
        wikibase_data = self.create_proper_wikibase_data(test_entity)
        print("Wikibase data structure:")
        print(json.dumps(wikibase_data, indent=2)[:1000] + "..." if len(str(wikibase_data)) > 1000 else json.dumps(wikibase_data, indent=2))
        
        # Try to create/update
        success = self.create_or_update_entity(test_entity)
        
        if success:
            print("SUCCESS: Test entity created/updated successfully!")
            print("Format is correct - ready for bulk upload")
        else:
            print("FAILED: Test entity had errors - format needs more fixes")
        
        return success
    
    def upload_sample_entities(self, count=10):
        """Upload a small sample to test"""
        print(f"\n=== UPLOADING {count} SAMPLE ENTITIES ===")
        
        sample_entities = list(self.collection.find().limit(count))
        successful = 0
        
        for i, entity in enumerate(sample_entities, 1):
            print(f"{i}/{count}: {entity['qid']}")
            if self.create_or_update_entity(entity):
                successful += 1
            
            # Rate limiting
            time.sleep(0.5)
        
        print(f"Results: {successful}/{count} successful")
        return successful == count

def main():
    if len(sys.argv) < 3:
        print("Usage: python wikibase_api_uploader.py <username> <password> [test|sample]")
        return False
    
    username = sys.argv[1]
    password = sys.argv[2]
    mode = sys.argv[3] if len(sys.argv) > 3 else 'test'
    
    uploader = WikibaseAPIUploader(username, password)
    
    if not uploader.login():
        return False
    
    if mode == 'test':
        # Test single entity
        success = uploader.test_single_entity()
    elif mode == 'sample':
        # Upload small sample
        success = uploader.upload_sample_entities(10)
    else:
        print("Invalid mode. Use 'test' or 'sample'")
        return False
    
    uploader.mongo_client.close()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)