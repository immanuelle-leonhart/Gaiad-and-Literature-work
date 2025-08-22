#!/usr/bin/env python3
"""
Remove duplicate property claims from entities in the MongoDB database.
This script deduplicates properties where the same value appears multiple times
for the same property on the same entity.
"""

import pymongo
from collections import defaultdict
import sys

def deduplicate_claims(claims):
    """
    Remove duplicate claims from a list of property claims.
    Returns (unique_claims, duplicates_removed_count)
    """
    seen_keys = set()
    unique_claims = []
    duplicates_removed = 0
    
    for claim in claims:
        # Create a key based on the claim value and type
        value = claim.get('value')
        claim_type = claim.get('type', '')
        
        # Handle different value types to create unique keys
        if isinstance(value, dict):
            if 'id' in value:
                key = (value['id'], claim_type)
            elif 'text' in value:
                key = (value['text'], value.get('language', ''), claim_type)
            else:
                key = (str(value), claim_type)
        else:
            key = (str(value), claim_type)
        
        if key in seen_keys:
            duplicates_removed += 1
        else:
            seen_keys.add(key)
            unique_claims.append(claim)
    
    return unique_claims, duplicates_removed

def main():
    print("=== REMOVING DUPLICATE PROPERTIES ===")
    print()
    
    # Connect to MongoDB
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['gaiad_processing_db']
    collection = db['entities']
    
    # Statistics tracking
    total_entities = 0
    entities_with_duplicates = 0
    total_claims_before = 0
    total_claims_after = 0
    total_duplicates_removed = 0
    property_stats = defaultdict(lambda: {'before': 0, 'after': 0, 'removed': 0})
    
    # Process entities in batches
    batch_size = 1000
    bulk_operations = []
    
    print("Processing entities to remove duplicate properties...")
    
    for entity in collection.find():
        total_entities += 1
        if total_entities % 5000 == 0:
            print(f"  Processed {total_entities:,} entities...")
        
        # Skip redirect entities
        if 'redirect' in entity.get('properties', {}):
            continue
        
        qid = entity['qid']
        properties = entity.get('properties', {})
        entity_modified = False
        new_properties = {}
        
        for prop_id, claims in properties.items():
            if prop_id == 'redirect':
                new_properties[prop_id] = claims
                continue
            
            original_count = len(claims)
            total_claims_before += original_count
            property_stats[prop_id]['before'] += original_count
            
            # Deduplicate claims for this property
            unique_claims, duplicates_removed = deduplicate_claims(claims)
            
            final_count = len(unique_claims)
            total_claims_after += final_count
            property_stats[prop_id]['after'] += final_count
            property_stats[prop_id]['removed'] += duplicates_removed
            
            if duplicates_removed > 0:
                entity_modified = True
                total_duplicates_removed += duplicates_removed
            
            new_properties[prop_id] = unique_claims
        
        if entity_modified:
            entities_with_duplicates += 1
            
            # Add to bulk operations
            bulk_operations.append(
                pymongo.UpdateOne(
                    {'qid': qid},
                    {'$set': {'properties': new_properties}}
                )
            )
        
        # Execute batch when it reaches the limit
        if len(bulk_operations) >= batch_size:
            if bulk_operations:
                collection.bulk_write(bulk_operations)
                bulk_operations = []
    
    # Execute remaining operations
    if bulk_operations:
        collection.bulk_write(bulk_operations)
    
    print(f"  Processed {total_entities:,} entities total")
    print()
    
    # Display results
    print("=== DEDUPLICATION RESULTS ===")
    print(f"Total entities processed: {total_entities:,}")
    print(f"Entities with duplicates removed: {entities_with_duplicates:,}")
    print(f"Total claims before: {total_claims_before:,}")
    print(f"Total claims after: {total_claims_after:,}")
    print(f"Total duplicates removed: {total_duplicates_removed:,}")
    print(f"Space reduction: {total_duplicates_removed/total_claims_before*100:.2f}%")
    print()
    
    # Property-specific statistics
    print("Properties with duplicates removed:")
    for prop_id in sorted(property_stats.keys()):
        stats = property_stats[prop_id]
        if stats['removed'] > 0:
            reduction_pct = stats['removed'] / stats['before'] * 100
            print(f"  {prop_id}: {stats['before']:,} -> {stats['after']:,} ({stats['removed']:,} removed, {reduction_pct:.1f}%)")
    
    print()
    
    # Verification
    print("Verifying deduplication...")
    verification_sample = 0
    remaining_duplicates = 0
    
    for entity in collection.find().limit(1000):
        if 'redirect' in entity.get('properties', {}):
            continue
            
        verification_sample += 1
        properties = entity.get('properties', {})
        
        for prop_id, claims in properties.items():
            if prop_id == 'redirect':
                continue
                
            # Check if any duplicates remain
            seen_keys = set()
            for claim in claims:
                value = claim.get('value')
                claim_type = claim.get('type', '')
                
                if isinstance(value, dict):
                    if 'id' in value:
                        key = (value['id'], claim_type)
                    elif 'text' in value:
                        key = (value['text'], value.get('language', ''), claim_type)
                    else:
                        key = (str(value), claim_type)
                else:
                    key = (str(value), claim_type)
                
                if key in seen_keys:
                    remaining_duplicates += 1
                    break
                seen_keys.add(key)
    
    print(f"Verification sample: {verification_sample:,} entities")
    print(f"Remaining duplicates found: {remaining_duplicates}")
    
    if remaining_duplicates == 0:
        print("SUCCESS: All duplicates successfully removed!")
    else:
        print(f"WARNING: {remaining_duplicates} duplicates still found")
    
    client.close()
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)