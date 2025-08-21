#!/usr/bin/env python3
"""
Export Wikidata QIDs

Creates a simple CSV export with:
- Column 1: Local QID
- Column 2: Wikidata QID (from P61 property)

For all entities that have P61 (Wikidata ID) properties.
"""

import pymongo
import csv
import os

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

# Output configuration
OUTPUT_DIR = "analysis"
OUTPUT_FILE = "all_wikidata_qids.csv"

def export_wikidata_qids():
    """Export all entities with Wikidata QIDs to simple CSV"""
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    print("=== EXPORT: ALL WIKIDATA QIDs ===")
    print()
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    
    # Find entities with P61 (Wikidata IDs)
    print("Scanning database for entities with Wikidata IDs...")
    
    wikidata_mappings = []
    total_processed = 0
    redirect_count = 0
    entities_with_p61 = 0
    
    for entity in collection.find():
        total_processed += 1
        if total_processed % 20000 == 0:
            print(f"  Processed {total_processed:,} entities...")
        
        qid = entity['qid']
        properties = entity.get('properties', {})
        
        # Skip redirect entities
        if 'redirect' in properties:
            redirect_count += 1
            continue
        
        # Check for P61 (Wikidata ID)
        if 'P61' in properties:
            entities_with_p61 += 1
            
            # Extract Wikidata QIDs
            for claim in properties['P61']:
                wikidata_qid = claim.get('value', '').strip()
                if wikidata_qid and wikidata_qid.startswith('Q'):
                    wikidata_mappings.append((qid, wikidata_qid))
                    break  # Use first valid Wikidata QID
    
    print(f"  Processed {total_processed:,} entities total")
    print(f"  Skipped {redirect_count:,} redirect entities")
    print(f"  Entities with P61: {entities_with_p61:,}")
    print(f"  Valid Wikidata mappings: {len(wikidata_mappings):,}")
    print()
    
    # Export to CSV
    print(f"Exporting {len(wikidata_mappings):,} Wikidata mappings to {output_path}")
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow(['qid', 'wikidata_qid'])
        
        # Sort by local QID for consistent output
        sorted_mappings = sorted(wikidata_mappings, key=lambda x: int(x[0][1:]) if x[0][1:].isdigit() else 0)
        
        # Write data rows
        for local_qid, wikidata_qid in sorted_mappings:
            writer.writerow([local_qid, wikidata_qid])
    
    print(f"  OK Saved {output_path}")
    print()
    print("=== EXPORT SUMMARY ===")
    print(f"Total entities with Wikidata links: {len(wikidata_mappings):,}")
    print(f"CSV format: Column 1 = Local QID, Column 2 = Wikidata QID")
    print(f"File saved: {output_path}")
    
    client.close()
    
    return {
        'total_mappings': len(wikidata_mappings),
        'entities_with_p61': entities_with_p61,
        'output_file': output_path
    }

if __name__ == "__main__":
    import time
    start_time = time.time()
    results = export_wikidata_qids()
    duration = time.time() - start_time
    print(f"\nCompleted in {duration:.1f} seconds")