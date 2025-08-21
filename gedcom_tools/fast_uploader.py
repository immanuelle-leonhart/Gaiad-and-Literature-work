#!/usr/bin/env python3
"""
Fast Wikibase Uploader

This is a streamlined version that starts uploading immediately without 
counting all entities first. Based on the working production uploader.
"""

import pymongo
import requests
import json
import time
import sys

# Configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
WIKI_URL = "https://evolutionism.miraheze.org"
API_ENDPOINT = f"{WIKI_URL}/w/api.php"

class FastWikibaseUploader:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Gaiad Genealogy Fast Uploader/1.0'
        })
        
        # MongoDB connection
        self.mongo_client = pymongo.MongoClient(MONGO_URI)
        self.db = self.mongo_client[DATABASE_NAME]
        self.collection = self.db['entities']
        
        self.stats = {
            'entities_processed': 0,
            'entities_created': 0,
            'entities_skipped': 0,
            'entities_failed': 0,
            'redirects_skipped': 0,
            'start_time': time.time()
        }
        
        print("Fast Wikibase Uploader initialized")
        
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
    
    def create_working_wikibase_data(self, entity):
        """Create the EXACT format that works (tested successfully)"""
        qid = entity['qid']
        wikibase_data = {}
        
        # Labels - WORKING monolingualtext format
        labels = entity.get('labels', {})
        if labels:
            wikibase_data['labels'] = {}
            for lang, text in labels.items():
                if isinstance(text, str) and text.strip():
                    wikibase_data['labels'][lang] = {
                        'language': lang,
                        'value': text.strip()
                    }
        
        # Descriptions - same working format
        descriptions = entity.get('descriptions', {})
        if descriptions:
            wikibase_data['descriptions'] = {}
            for lang, text in descriptions.items():
                if isinstance(text, str) and text.strip():
                    wikibase_data['descriptions'][lang] = {
                        'language': lang,
                        'value': text.strip()
                    }
        
        # Claims - exact working format from test
        properties = entity.get('properties', {})
        if properties:
            wikibase_data['claims'] = {}
            
            for prop_id, claims in properties.items():
                if prop_id == 'redirect':
                    continue
                
                wikibase_claims = []
                for claim in claims:
                    claim_value = claim.get('value')
                    claim_type = claim.get('type', 'string')
                    
                    if not claim_value:
                        continue
                    
                    # Create exact claim structure that works
                    wikibase_claim = {
                        'mainsnak': {
                            'snaktype': 'value',
                            'property': prop_id
                        },
                        'type': 'statement', 
                        'rank': 'normal'
                    }
                    
                    # Handle different property types with working formats
                    if claim_type == 'external-id':
                        # External IDs (P61, P62, P63) 
                        wikibase_claim['mainsnak']['datavalue'] = {
                            'value': str(claim_value),
                            'type': 'string'
                        }
                        wikibase_claim['mainsnak']['datatype'] = 'external-id'
                        
                    elif claim_type == 'monolingualtext':
                        # Monolingualtext properties
                        if isinstance(claim_value, dict) and 'text' in claim_value and 'language' in claim_value:
                            wikibase_claim['mainsnak']['datavalue'] = {
                                'value': claim_value,
                                'type': 'monolingualtext'
                            }
                            wikibase_claim['mainsnak']['datatype'] = 'monolingualtext'
                        else:
                            continue
                        
                    elif claim_type in ['wikibase-item', 'wikibase-entityid']:
                        # Entity references (P20, P42, P47, P48)
                        if isinstance(claim_value, dict) and 'id' in claim_value:
                            wikibase_claim['mainsnak']['datavalue'] = {
                                'value': claim_value,
                                'type': 'wikibase-entityid'
                            }
                            wikibase_claim['mainsnak']['datatype'] = 'wikibase-item'
                        elif isinstance(claim_value, str) and claim_value.startswith('Q'):
                            try:
                                numeric_id = int(claim_value[1:])
                                wikibase_claim['mainsnak']['datavalue'] = {
                                    'value': {
                                        'entity-type': 'item',
                                        'numeric-id': numeric_id,
                                        'id': claim_value
                                    },
                                    'type': 'wikibase-entityid'
                                }
                                wikibase_claim['mainsnak']['datatype'] = 'wikibase-item'
                            except (ValueError, IndexError):
                                continue
                        else:
                            continue
                    
                    elif claim_type == 'time':
                        # Date properties (P56, P57)
                        if isinstance(claim_value, dict):
                            wikibase_claim['mainsnak']['datavalue'] = {
                                'value': claim_value,
                                'type': 'time'
                            }
                        else:
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
                        wikibase_claim['mainsnak']['datatype'] = 'time'
                    
                    else:
                        # String properties (default)
                        wikibase_claim['mainsnak']['datavalue'] = {
                            'value': str(claim_value),
                            'type': 'string'
                        }
                        wikibase_claim['mainsnak']['datatype'] = 'string'
                    
                    wikibase_claims.append(wikibase_claim)
                
                if wikibase_claims:
                    wikibase_data['claims'][prop_id] = wikibase_claims
        
        return wikibase_data
    
    def create_entity(self, entity):
        """Create entity using working format"""
        qid = entity['qid']
        
        # Skip redirects - we'll handle them later
        if 'redirect' in entity.get('properties', {}):
            self.stats['redirects_skipped'] += 1
            return True
        
        try:
            # Check if already exists
            if self.entity_exists(qid):
                self.stats['entities_skipped'] += 1
                return True
            
            # Create working data
            wikibase_data = self.create_working_wikibase_data(entity)
            
            # Get CSRF token
            csrf_token = self.get_csrf_token()
            
            # Create entity
            response = self.session.post(API_ENDPOINT, data={
                'action': 'wbeditentity',
                'new': 'item',
                'data': json.dumps(wikibase_data),
                'token': csrf_token,
                'format': 'json'
            })
            
            result = response.json()
            
            if 'entity' in result:
                created_qid = result['entity']['id']
                self.stats['entities_created'] += 1
                return True
            else:
                error_info = result.get('error', {})
                print(f"  ERROR creating {qid}: {error_info.get('info', 'Unknown error')}")
                self.stats['entities_failed'] += 1
                return False
        
        except Exception as e:
            print(f"  ERROR creating {qid}: {e}")
            self.stats['entities_failed'] += 1
            return False
    
    def upload_batch(self, entities, batch_num):
        """Upload a batch of entities"""
        print(f"\n=== BATCH {batch_num} ===")
        print(f"Processing {len(entities)} entities...")
        
        batch_created = 0
        batch_failed = 0
        
        for i, entity in enumerate(entities):
            if i % 10 == 0 and i > 0:
                print(f"  Progress: {i}/{len(entities)} entities...")
            
            success = self.create_entity(entity)
            if success:
                batch_created += 1
            else:
                batch_failed += 1
            
            self.stats['entities_processed'] += 1
            
            # Rate limiting - small delay
            time.sleep(0.2)
        
        print(f"Batch results: {batch_created} created, {batch_failed} failed")
        return batch_failed == 0
    
    def upload_entities(self, batch_size=25, max_batches=None):
        """Upload entities in batches, starting immediately"""
        print("\n=== STARTING FAST UPLOAD ===")
        print("Starting upload without full count...")
        
        current_batch = []
        batch_num = 1
        
        print(f"Batch size: {batch_size}")
        if max_batches:
            print(f"Max batches: {max_batches}")
        print()
        
        for entity in self.collection.find():
            # Skip redirects for now
            if 'redirect' not in entity.get('properties', {}):
                current_batch.append(entity)
                
                # Process batch when full
                if len(current_batch) >= batch_size:
                    self.upload_batch(current_batch, batch_num)
                    current_batch = []
                    batch_num += 1
                    
                    # Show progress
                    duration = time.time() - self.stats['start_time']
                    if duration > 0:
                        rate = self.stats['entities_processed'] / duration
                        print(f"Progress: {self.stats['entities_processed']} processed, {self.stats['entities_created']} created, {self.stats['entities_failed']} failed")
                        print(f"Rate: {rate:.2f} entities/second\n")
                    
                    # Optional: limit for testing
                    if max_batches and batch_num > max_batches:
                        print(f"Reached max batches limit: {max_batches}")
                        break
        
        # Upload remaining entities
        if current_batch:
            self.upload_batch(current_batch, batch_num)
        
        # Final statistics
        duration = time.time() - self.stats['start_time']
        print(f"\n=== UPLOAD SESSION COMPLETE ===")
        print(f"Duration: {duration/60:.1f} minutes")
        print(f"Entities processed: {self.stats['entities_processed']:,}")
        print(f"Entities created: {self.stats['entities_created']:,}")
        print(f"Entities skipped (existing): {self.stats['entities_skipped']:,}")
        print(f"Entities failed: {self.stats['entities_failed']:,}")
        print(f"Redirects skipped: {self.stats['redirects_skipped']:,}")
        
        if self.stats['entities_processed'] > 0:
            print(f"Success rate: {self.stats['entities_created']/(self.stats['entities_processed'] - self.stats['redirects_skipped'])*100:.1f}%")
        
        if duration > 0:
            print(f"Upload rate: {self.stats['entities_processed']/duration:.2f} entities/second")
        
        self.mongo_client.close()
        
        return self.stats['entities_failed'] < self.stats['entities_created'] * 0.1

def main():
    if len(sys.argv) < 3:
        print("Usage: python fast_uploader.py <username> <password> [batch_size] [max_batches]")
        print("Example: python fast_uploader.py Immanuelle 'password' 25 10")
        return False
    
    username = sys.argv[1]
    password = sys.argv[2]
    batch_size = int(sys.argv[3]) if len(sys.argv) > 3 else 25
    max_batches = int(sys.argv[4]) if len(sys.argv) > 4 else None
    
    uploader = FastWikibaseUploader(username, password)
    
    if not uploader.login():
        return False
    
    success = uploader.upload_entities(batch_size, max_batches)
    
    if success:
        print("\nSUCCESS: Upload completed successfully!")
    else:
        print("\nWARNING: Upload completed with some failures")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)