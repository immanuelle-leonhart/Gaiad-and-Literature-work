#!/usr/bin/env python3
"""
Fix Bad References to Redirects

The entity merger mostly worked, but some references still point to
redirect entities instead of their targets. This script finds and fixes
all such bad references.
"""

import pymongo
import time

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

def fix_bad_references():
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    print("=== FIXING BAD REFERENCES TO REDIRECTS ===")
    print()
    
    # Step 1: Load all redirect mappings
    print("Loading redirect mappings...")
    redirect_mappings = {}
    
    for entity in collection.find():
        properties = entity.get('properties', {})
        if 'redirect' in properties:
            redirect_qid = entity['qid']
            target_qid = properties['redirect'][0]['value']
            redirect_mappings[redirect_qid] = target_qid
    
    print(f"Loaded {len(redirect_mappings):,} redirect mappings")
    
    # Step 2: Find and fix bad references
    print()
    print("Finding and fixing bad references...")
    
    bulk_ops = []
    references_fixed = 0
    entities_updated = 0
    total_checked = 0
    
    for entity in collection.find():
        total_checked += 1
        if total_checked % 10000 == 0:
            print(f"  Checked {total_checked:,} entities...")
        
        # Skip redirect entities themselves
        if 'redirect' in entity.get('properties', {}):
            continue
        
        entity_has_bad_refs = False
        updates = {}
        
        # Check all property references
        properties = entity.get('properties', {})
        for prop_id, claims in properties.items():
            updated_claims = []
            claims_updated = False
            
            for claim in claims:
                updated_claim = claim.copy()
                value = claim.get('value')
                
                # Check different value types for bad references
                if isinstance(value, str) and value in redirect_mappings:
                    # Bad reference - update to target
                    updated_claim['value'] = redirect_mappings[value]
                    claims_updated = True
                    references_fixed += 1
                elif isinstance(value, dict) and value.get('id') in redirect_mappings:
                    # Bad reference in complex value - update to target
                    updated_claim['value'] = value.copy()
                    updated_claim['value']['id'] = redirect_mappings[value['id']]
                    claims_updated = True
                    references_fixed += 1
                
                updated_claims.append(updated_claim)
            
            if claims_updated:
                updates[f'properties.{prop_id}'] = updated_claims
                entity_has_bad_refs = True
        
        # Add to bulk operations if entity needs updates
        if entity_has_bad_refs:
            bulk_ops.append(
                pymongo.UpdateOne(
                    {'qid': entity['qid']},
                    {'$set': updates}
                )
            )
            entities_updated += 1
            
            # Execute batch when full
            if len(bulk_ops) >= 1000:
                collection.bulk_write(bulk_ops)
                bulk_ops = []
    
    # Execute final batch
    if bulk_ops:
        collection.bulk_write(bulk_ops)
    
    print(f"  Checked {total_checked:,} entities")
    print()
    print("=== RESULTS ===")
    print(f"References fixed: {references_fixed:,}")
    print(f"Entities updated: {entities_updated:,}")
    
    # Verify fix worked
    print()
    print("Verifying fix worked...")
    
    remaining_bad_refs = 0
    for entity in collection.find():
        if 'redirect' in entity.get('properties', {}):
            continue
            
        properties = entity.get('properties', {})
        for prop_id, claims in properties.items():
            for claim in claims:
                value = claim.get('value')
                
                referenced_qid = None
                if isinstance(value, str) and value.startswith('Q'):
                    referenced_qid = value
                elif isinstance(value, dict) and value.get('id', '').startswith('Q'):
                    referenced_qid = value['id']
                
                if referenced_qid and referenced_qid in redirect_mappings:
                    remaining_bad_refs += 1
    
    print(f"Remaining bad references: {remaining_bad_refs:,}")
    
    if remaining_bad_refs == 0:
        print()
        print("SUCCESS: All references now point to targets!")
        print("Entity merger is now 100% complete!")
    else:
        print(f"WARNING: {remaining_bad_refs:,} bad references still exist")
    
    client.close()

if __name__ == "__main__":
    start_time = time.time()
    fix_bad_references()
    duration = time.time() - start_time
    print(f"\nCompleted in {duration:.1f} seconds")