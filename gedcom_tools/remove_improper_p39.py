#!/usr/bin/env python3
"""
Remove Improper P39 Properties

Removes all P39 properties with values:
- Q31342 (Referenceless item)
- Q153720 (Item with no identifiers)

These were improperly added to many pages and need to be cleaned up.
"""

import pymongo
import time

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

# Values to remove
IMPROPER_VALUES = {'Q31342', 'Q153720'}  # Referenceless item, Item with no identifiers

def remove_improper_p39_properties():
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    print("=== REMOVING IMPROPER P39 PROPERTIES ===")
    print()
    print("Target values to remove:")
    print("  Q31342 (Referenceless item)")
    print("  Q153720 (Item with no identifiers)")
    print()
    
    # Step 1: Find all entities with P39 properties
    print("Finding entities with P39 properties...")
    
    entities_with_p39 = list(collection.find({'properties.P39': {'$exists': True}}))
    print(f"Found {len(entities_with_p39):,} entities with P39 properties")
    
    if not entities_with_p39:
        print("No entities found with P39 properties")
        client.close()
        return
    
    # Step 2: Analyze and clean P39 properties
    print()
    print("Analyzing P39 properties for improper values...")
    
    bulk_ops = []
    entities_to_update = 0
    claims_to_remove = 0
    entities_to_clear_p39 = 0
    
    for entity in entities_with_p39:
        qid = entity['qid']
        p39_claims = entity['properties']['P39']
        
        # Filter out improper claims
        valid_claims = []
        removed_claims = 0
        
        for claim in p39_claims:
            value = claim.get('value', '')
            
            # Check if this is an improper value
            if isinstance(value, str) and value in IMPROPER_VALUES:
                removed_claims += 1
                claims_to_remove += 1
            elif isinstance(value, dict) and value.get('id') in IMPROPER_VALUES:
                removed_claims += 1
                claims_to_remove += 1
            else:
                # Keep this claim
                valid_claims.append(claim)
        
        # If we removed any claims, update the entity
        if removed_claims > 0:
            entities_to_update += 1
            
            if valid_claims:
                # Update P39 with remaining valid claims
                bulk_ops.append(
                    pymongo.UpdateOne(
                        {'qid': qid},
                        {'$set': {'properties.P39': valid_claims}}
                    )
                )
            else:
                # Remove P39 property entirely (no valid claims left)
                bulk_ops.append(
                    pymongo.UpdateOne(
                        {'qid': qid},
                        {'$unset': {'properties.P39': ''}}
                    )
                )
                entities_to_clear_p39 += 1
            
            # Execute in batches
            if len(bulk_ops) >= 1000:
                collection.bulk_write(bulk_ops)
                bulk_ops = []
                print(f"  Processed {entities_to_update:,} entities...")
    
    # Execute remaining operations
    if bulk_ops:
        collection.bulk_write(bulk_ops)
    
    print()
    print("=== CLEANUP RESULTS ===")
    print(f"Entities examined: {len(entities_with_p39):,}")
    print(f"Entities updated: {entities_to_update:,}")
    print(f"Improper P39 claims removed: {claims_to_remove:,}")
    print(f"Entities with P39 completely removed: {entities_to_clear_p39:,}")
    print(f"Entities with P39 partially cleaned: {entities_to_update - entities_to_clear_p39:,}")
    
    # Step 3: Verify cleanup
    print()
    print("Verifying cleanup...")
    
    remaining_improper = 0
    
    for entity in collection.find({'properties.P39': {'$exists': True}}):
        p39_claims = entity.get('properties', {}).get('P39', [])
        
        for claim in p39_claims:
            value = claim.get('value', '')
            
            if isinstance(value, str) and value in IMPROPER_VALUES:
                remaining_improper += 1
            elif isinstance(value, dict) and value.get('id') in IMPROPER_VALUES:
                remaining_improper += 1
    
    print(f"Remaining improper P39 values: {remaining_improper:,}")
    
    if remaining_improper == 0:
        print()
        print("SUCCESS: All improper P39 properties removed!")
        print("Database cleanup completed successfully.")
    else:
        print(f"WARNING: {remaining_improper:,} improper values still remain")
    
    client.close()
    
    return {
        'entities_examined': len(entities_with_p39),
        'entities_updated': entities_to_update,
        'claims_removed': claims_to_remove,
        'entities_cleared': entities_to_clear_p39,
        'remaining_improper': remaining_improper
    }

if __name__ == "__main__":
    start_time = time.time()
    results = remove_improper_p39_properties()
    duration = time.time() - start_time
    print(f"\nCompleted in {duration:.1f} seconds")