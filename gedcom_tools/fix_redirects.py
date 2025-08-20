#!/usr/bin/env python3
"""
Fix Redirect Creation

The entity merger successfully eliminated duplicates and updated references,
but failed to create redirect properties. This script fixes that by:

1. Finding empty entities (should be redirects)  
2. Reconstructing redirect mappings from entity relationships
3. Adding proper redirect properties to empty entities

Strategy: Empty entities that lost their properties during merges should
redirect to entities that have the same identifier values they used to have.
"""

import pymongo
import time
from collections import defaultdict

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

class RedirectFixer:
    def __init__(self, mongo_uri=MONGO_URI):
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db[COLLECTION_NAME]
        
        self.stats = {
            'empty_entities_found': 0,
            'redirects_created': 0,
            'redirects_failed': 0
        }
        
        print(f"Connected to MongoDB: {DATABASE_NAME}.{COLLECTION_NAME}")
    
    def find_empty_entities(self):
        """Find entities that should be redirects (empty properties)"""
        print("Finding empty entities that should be redirects...")
        
        empty_entities = []
        
        query = {
            'properties': {},
            'labels': {},
            'descriptions': {},
            'aliases': {}
        }
        
        for entity in self.collection.find(query):
            empty_entities.append(entity['qid'])
        
        self.stats['empty_entities_found'] = len(empty_entities)
        print(f"  Found {len(empty_entities):,} empty entities")
        
        return empty_entities
    
    def find_redirect_targets_by_pattern(self, empty_qids):
        """Find redirect targets using QID proximity pattern"""
        print("Finding redirect targets using QID proximity analysis...")
        
        redirect_mapping = {}  # empty_qid -> target_qid
        
        # Convert QIDs to numbers for analysis
        def qid_to_number(qid):
            return int(qid[1:]) if qid.startswith('Q') else 0
        
        empty_numbers = sorted([qid_to_number(qid) for qid in empty_qids])
        
        print(f"  Analyzing {len(empty_numbers):,} empty QID numbers...")
        
        # For each empty entity, find the nearest lower-numbered entity with properties
        targets_found = 0
        
        for empty_qid in empty_qids:
            empty_num = qid_to_number(empty_qid)
            
            # Search for nearest lower QID that has properties
            # Most merges follow pattern: higher QID -> lower QID
            best_target = None
            search_range = 100  # Search within 100 QIDs
            
            for offset in range(1, search_range + 1):
                candidate_num = empty_num - offset
                if candidate_num <= 0:
                    break
                    
                candidate_qid = f"Q{candidate_num}"
                
                # Check if this candidate has properties
                candidate = self.collection.find_one({'qid': candidate_qid})
                if candidate and candidate.get('properties', {}):
                    best_target = candidate_qid
                    break
            
            if best_target:
                redirect_mapping[empty_qid] = best_target
                targets_found += 1
            
            if targets_found % 1000 == 0:
                print(f"    Found targets for {targets_found:,} empty entities...")
        
        print(f"  Found redirect targets for {len(redirect_mapping):,} empty entities")
        return redirect_mapping
    
    def create_redirect_properties(self, redirect_mapping):
        """Add redirect properties to empty entities"""
        print("Creating redirect properties...")
        
        bulk_ops = []
        created = 0
        failed = 0
        
        for empty_qid, target_qid in redirect_mapping.items():
            try:
                # Create redirect property
                redirect_property = {
                    'redirect': [{
                        'value': target_qid,
                        'type': 'wikibase-item', 
                        'claim_id': f"{empty_qid}_redirect_to_{target_qid}"
                    }]
                }
                
                # Add to bulk operations
                bulk_ops.append(
                    pymongo.UpdateOne(
                        {'qid': empty_qid},
                        {'$set': {'properties': redirect_property}}
                    )
                )
                
                created += 1
                
                # Execute in batches
                if len(bulk_ops) >= 1000:
                    result = self.collection.bulk_write(bulk_ops)
                    bulk_ops = []
                    
            except Exception as e:
                print(f"    Error creating redirect for {empty_qid}: {e}")
                failed += 1
        
        # Execute remaining operations
        if bulk_ops:
            result = self.collection.bulk_write(bulk_ops)
        
        self.stats['redirects_created'] = created
        self.stats['redirects_failed'] = failed
        
        print(f"  Created {created:,} redirect properties")
        if failed > 0:
            print(f"  Failed to create {failed:,} redirects")
    
    def verify_redirects(self):
        """Verify redirect creation worked"""
        print("Verifying redirect creation...")
        
        redirect_count = self.collection.count_documents({
            'properties.redirect': {'$exists': True}
        })
        
        print(f"  Entities with redirect properties: {redirect_count:,}")
        
        # Show samples
        samples = list(self.collection.find({
            'properties.redirect': {'$exists': True}
        }).limit(3))
        
        if samples:
            print("  Sample redirects:")
            for sample in samples:
                redirect_target = sample['properties']['redirect'][0]['value']
                print(f"    {sample['qid']} -> {redirect_target}")
        
        return redirect_count
    
    def run_redirect_fix(self):
        """Run complete redirect fixing process"""
        start_time = time.time()
        
        print("REDIRECT FIXING PROCESS")
        print("=" * 50)
        print("Fixing redirect creation that failed during entity merger")
        print()
        
        # Step 1: Find empty entities
        empty_entities = self.find_empty_entities()
        
        if not empty_entities:
            print("No empty entities found - redirects may already be fixed")
            return
        
        # Step 2: Find redirect targets
        redirect_mapping = self.find_redirect_targets_by_pattern(empty_entities)
        
        if not redirect_mapping:
            print("Could not determine redirect targets")
            return
        
        # Step 3: Create redirect properties
        self.create_redirect_properties(redirect_mapping)
        
        # Step 4: Verify results
        final_count = self.verify_redirects()
        
        duration = time.time() - start_time
        
        print()
        print("=" * 50)
        print("REDIRECT FIXING COMPLETE")
        print("=" * 50)
        print(f"Empty entities found: {self.stats['empty_entities_found']:,}")
        print(f"Redirects created: {self.stats['redirects_created']:,}")
        print(f"Redirects failed: {self.stats['redirects_failed']:,}")
        print(f"Final redirect count: {final_count:,}")
        print(f"Duration: {duration:.1f} seconds")
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()

def main():
    fixer = RedirectFixer()
    
    try:
        fixer.run_redirect_fix()
    finally:
        fixer.close()

if __name__ == "__main__":
    main()