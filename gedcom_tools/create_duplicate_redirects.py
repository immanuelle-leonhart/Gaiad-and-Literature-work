#!/usr/bin/env python3
"""
Create redirects for entities without external identifiers to their matches with identifiers.
Reads from potential_duplicates_quick.csv and creates redirect properties in MongoDB.
"""

import pymongo
import csv
from collections import defaultdict
import sys

def main():
    print("=== CREATING REDIRECTS FOR DUPLICATE ENTITIES ===")
    print()
    
    # Connect to MongoDB
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['gaiad_processing_db']
    collection = db['entities']
    
    # Read CSV and build redirect mapping
    redirect_map = {}  # source_qid -> target_qid
    processed_pairs = set()  # Track unique pairs to avoid duplicates
    
    print("Reading duplicate entities from CSV...")
    with open('potential_duplicates_quick.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            source_qid = row['entity_without_ids']
            target_qid = row['entity_with_ids']
            
            # Create unique pair key to avoid processing same redirect multiple times
            pair_key = (source_qid, target_qid)
            if pair_key in processed_pairs:
                continue
            processed_pairs.add(pair_key)
            
            # Only create redirect if we haven't seen this source before
            if source_qid not in redirect_map:
                redirect_map[source_qid] = target_qid
            elif redirect_map[source_qid] != target_qid:
                print(f"WARNING: {source_qid} has multiple targets: {redirect_map[source_qid]} and {target_qid}")
    
    print(f"Found {len(redirect_map)} unique redirects to create")
    print()
    
    # Verify all source and target entities exist
    print("Verifying entities exist...")
    existing_entities = set()
    for entity in collection.find({}, {'qid': 1}):
        existing_entities.add(entity['qid'])
    
    missing_sources = []
    missing_targets = []
    
    for source_qid, target_qid in redirect_map.items():
        if source_qid not in existing_entities:
            missing_sources.append(source_qid)
        if target_qid not in existing_entities:
            missing_targets.append(target_qid)
    
    if missing_sources:
        print(f"ERROR: {len(missing_sources)} source entities not found in database:")
        for qid in missing_sources[:10]:
            print(f"  {qid}")
        if len(missing_sources) > 10:
            print(f"  ... and {len(missing_sources) - 10} more")
        return False
    
    if missing_targets:
        print(f"ERROR: {len(missing_targets)} target entities not found in database:")
        for qid in missing_targets[:10]:
            print(f"  {qid}")
        if len(missing_targets) > 10:
            print(f"  ... and {len(missing_targets) - 10} more")
        return False
    
    print("All entities exist in database")
    print()
    
    # Check for entities that already have redirects or external identifiers
    print("Checking for conflicts...")
    conflicts = []
    
    for source_qid in redirect_map.keys():
        entity = collection.find_one({'qid': source_qid})
        if entity:
            properties = entity.get('properties', {})
            
            # Check if already a redirect
            if 'redirect' in properties:
                conflicts.append(f"{source_qid} already has redirect to {properties['redirect'][0]['value']}")
                continue
            
            # Check if has external identifiers (shouldn't happen based on our selection criteria)
            external_props = ['P61', 'P62', 'P63', 'P1185', 'P1819', 'P2949', 'P4638', 'P4159', 'P7929', 'P535', 'P6821']
            has_external = any(prop in properties for prop in external_props)
            if has_external:
                found_props = [prop for prop in external_props if prop in properties]
                conflicts.append(f"{source_qid} has external identifiers: {found_props}")
    
    if conflicts:
        print(f"Found {len(conflicts)} conflicts:")
        for conflict in conflicts[:10]:
            print(f"  {conflict}")
        if len(conflicts) > 10:
            print(f"  ... and {len(conflicts) - 10} more")
        print()
        print("Remove conflicting entities from redirect list? (y/n):")
        response = input().lower()
        if response == 'y':
            # Remove conflicting entities
            for conflict in conflicts:
                source_qid = conflict.split()[0]
                if source_qid in redirect_map:
                    del redirect_map[source_qid]
            print(f"Removed {len(conflicts)} conflicting entities. Remaining: {len(redirect_map)} redirects")
        else:
            print("Aborting due to conflicts")
            return False
    
    print(f"Ready to create {len(redirect_map)} redirects")
    print()
    
    # Create redirects
    print("Creating redirects...")
    bulk_ops = []
    
    for source_qid, target_qid in redirect_map.items():
        # Create redirect property
        redirect_claim = {
            'value': target_qid,
            'type': 'wikibase-entityid',
            'claim_id': f"{source_qid}_redirect_{target_qid}"
        }
        
        # Clear all properties except redirect
        bulk_ops.append(
            pymongo.UpdateOne(
                {'qid': source_qid},
                {
                    '$set': {
                        'properties.redirect': [redirect_claim],
                        'labels': {},
                        'descriptions': {},
                        'aliases': {}
                    },
                    '$unset': {
                        # Remove all other properties to make this a clean redirect
                        prop: 1 for prop in [
                            'properties.P55', 'properties.P56', 'properties.P57',
                            'properties.P20', 'properties.P42', 'properties.P47', 'properties.P48',
                            'properties.P5', 'properties.P3', 'properties.P39'
                        ]
                    }
                }
            )
        )
    
    # Execute in batches
    batch_size = 1000
    total_processed = 0
    
    for i in range(0, len(bulk_ops), batch_size):
        batch = bulk_ops[i:i + batch_size]
        result = collection.bulk_write(batch)
        total_processed += result.modified_count
        print(f"  Processed {total_processed}/{len(bulk_ops)} redirects...")
    
    print(f"Successfully created {total_processed} redirects")
    print()
    
    # Verify redirects were created
    print("Verifying redirects...")
    redirect_count = collection.count_documents({'properties.redirect': {'$exists': True}})
    print(f"Total redirect entities in database: {redirect_count:,}")
    
    # Show some samples
    print()
    print("Sample redirects created:")
    samples = list(collection.find({'properties.redirect': {'$exists': True}}).limit(5))
    for sample in samples:
        source_qid = sample['qid']
        target_qid = sample['properties']['redirect'][0]['value']
        print(f"  {source_qid} -> {target_qid}")
    
    client.close()
    print()
    print("SUCCESS: Redirect creation completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)