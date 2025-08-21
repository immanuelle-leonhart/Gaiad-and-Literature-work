#!/usr/bin/env python3
"""
Import Wikidata QIDs from CSV

Reads a CSV file with:
- Column 1: Local QID (e.g., Q12345)
- Column 2: Wikidata QID (e.g., Q67890)

For each row where column 2 has a Wikidata QID, adds it as a P61 property
to the corresponding entity in MongoDB.
"""

import pymongo
import csv
import time

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

# CSV file path
CSV_FILE = "analysis/geni_ids_with_wikidata.csv"

def import_wikidata_qids_from_csv(csv_file_path):
    """Import Wikidata QIDs from CSV and add as P61 properties"""
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    print(f"=== IMPORTING WIKIDATA QIDs FROM CSV ===")
    print(f"CSV file: {csv_file_path}")
    print()
    
    # Read CSV file
    wikidata_mappings = []
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            
            # Skip header row if present
            first_row = next(reader, None)
            if first_row and first_row[0].lower() == 'qid':
                print("Skipping header row")
            else:
                # Process first row if it's data
                if first_row and len(first_row) >= 2 and first_row[1].strip():
                    local_qid = first_row[0].strip()
                    wikidata_qid = first_row[1].strip()
                    if local_qid.startswith('Q') and wikidata_qid.startswith('Q'):
                        wikidata_mappings.append((local_qid, wikidata_qid))
            
            # Process remaining rows
            for row in reader:
                if len(row) >= 2 and row[1].strip():  # Has Wikidata QID
                    local_qid = row[0].strip()
                    wikidata_qid = row[1].strip()
                    
                    # Validate QID formats
                    if local_qid.startswith('Q') and wikidata_qid.startswith('Q'):
                        wikidata_mappings.append((local_qid, wikidata_qid))
                    else:
                        print(f"Skipping invalid row: {local_qid} -> {wikidata_qid}")
    
    except FileNotFoundError:
        print(f"ERROR: CSV file not found: {csv_file_path}")
        client.close()
        return
    except Exception as e:
        print(f"ERROR reading CSV file: {e}")
        client.close()
        return
    
    print(f"Found {len(wikidata_mappings):,} Wikidata mappings in CSV")
    
    if not wikidata_mappings:
        print("No valid Wikidata mappings found")
        client.close()
        return
    
    print()
    print("Sample mappings:")
    for i, (local_qid, wikidata_qid) in enumerate(wikidata_mappings[:5]):
        print(f"  {local_qid} -> {wikidata_qid}")
    if len(wikidata_mappings) > 5:
        print(f"  ... and {len(wikidata_mappings) - 5} more")
    
    print()
    print("Processing entities...")
    
    # Process each mapping
    bulk_ops = []
    entities_found = 0
    entities_updated = 0
    entities_already_have_p61 = 0
    entities_not_found = 0
    
    for local_qid, wikidata_qid in wikidata_mappings:
        # Find the entity
        entity = collection.find_one({'qid': local_qid})
        
        if not entity:
            entities_not_found += 1
            if entities_not_found <= 10:  # Show first 10 missing
                print(f"  WARNING: Entity {local_qid} not found in database")
            continue
        
        entities_found += 1
        properties = entity.get('properties', {})
        
        # Check if entity already has P61
        if 'P61' in properties:
            entities_already_have_p61 += 1
            continue
        
        # Create new P61 claim
        new_p61_claim = {
            'value': wikidata_qid,
            'type': 'external-id',
            'claim_id': f"{local_qid}_P61_{wikidata_qid}"
        }
        
        # Add P61 property
        bulk_ops.append(
            pymongo.UpdateOne(
                {'qid': local_qid},
                {'$set': {'properties.P61': [new_p61_claim]}}
            )
        )
        entities_updated += 1
        
        # Execute in batches
        if len(bulk_ops) >= 1000:
            collection.bulk_write(bulk_ops)
            bulk_ops = []
            print(f"  Updated {entities_updated:,} entities...")
    
    # Execute remaining operations
    if bulk_ops:
        collection.bulk_write(bulk_ops)
    
    print()
    print("=== IMPORT RESULTS ===")
    print(f"CSV mappings processed: {len(wikidata_mappings):,}")
    print(f"Entities found in database: {entities_found:,}")
    print(f"Entities not found: {entities_not_found:,}")
    print(f"Entities already had P61: {entities_already_have_p61:,}")
    print(f"Entities updated with new P61: {entities_updated:,}")
    
    # Verify the updates
    print()
    print("Verifying P61 additions...")
    
    verification_count = 0
    for local_qid, wikidata_qid in wikidata_mappings[:10]:  # Check first 10
        entity = collection.find_one({'qid': local_qid})
        if entity and 'P61' in entity.get('properties', {}):
            p61_claims = entity['properties']['P61']
            for claim in p61_claims:
                if claim.get('value') == wikidata_qid:
                    verification_count += 1
                    break
    
    print(f"Verified {verification_count}/10 sample updates")
    
    if entities_updated > 0:
        print()
        print("SUCCESS: Wikidata QIDs imported from CSV!")
        print(f"Added P61 properties to {entities_updated:,} entities")
        print("These entities now have enhanced Wikidata linking")
    else:
        print()
        print("INFO: No updates needed - entities already have P61 or were not found")
    
    client.close()
    
    return {
        'csv_mappings': len(wikidata_mappings),
        'entities_found': entities_found,
        'entities_updated': entities_updated,
        'entities_already_had_p61': entities_already_have_p61,
        'entities_not_found': entities_not_found
    }

if __name__ == "__main__":
    import sys
    
    # Allow custom CSV file path as argument
    csv_file = CSV_FILE
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    
    start_time = time.time()
    results = import_wikidata_qids_from_csv(csv_file)
    duration = time.time() - start_time
    print(f"\nCompleted in {duration:.1f} seconds")