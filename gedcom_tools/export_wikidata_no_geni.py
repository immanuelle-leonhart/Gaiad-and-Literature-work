#!/usr/bin/env python3
"""
Export Wikidata QIDs for entities without Geni IDs

Creates a CSV file with:
- QID (from this database)
- Wikidata QID

Only includes entities that:
- Have Wikidata ID (P61)
- Do NOT have Geni ID (P62)
- Are not redirect entities
"""

import pymongo
import csv
import time

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

def export_wikidata_no_geni():
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    print("=== EXPORTING WIKIDATA QIDs WITHOUT GENI IDs ===")
    print()
    
    output_file = "wikidata_no_geni.csv"
    
    # Open CSV file for writing
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow(['QID', 'Wikidata_QID'])
        
        exported_count = 0
        total_checked = 0
        
        print("Scanning database for entities with Wikidata but no Geni...")
        
        for entity in collection.find():
            total_checked += 1
            if total_checked % 10000 == 0:
                print(f"  Checked {total_checked:,} entities, exported {exported_count:,}...")
            
            properties = entity.get('properties', {})
            
            # Skip redirect entities
            if 'redirect' in properties:
                continue
            
            # Check if has Wikidata (P61) but no Geni (P62)
            has_wikidata = 'P61' in properties
            has_geni = 'P62' in properties
            
            if has_wikidata and not has_geni:
                qid = entity['qid']
                
                # Get Wikidata QID(s) - there might be multiple
                wikidata_claims = properties['P61']
                for claim in wikidata_claims:
                    wikidata_qid = claim.get('value', '')
                    if wikidata_qid:
                        writer.writerow([qid, wikidata_qid])
                        exported_count += 1
                        break  # Only take first Wikidata QID if multiple
        
        print(f"  Checked {total_checked:,} entities total")
    
    print()
    print("=== EXPORT COMPLETE ===")
    print(f"Exported {exported_count:,} entries to {output_file}")
    print()
    print("CSV format:")
    print("  Column 1: QID (from this database)")
    print("  Column 2: Wikidata_QID")
    print("  Criteria: Has Wikidata ID, no Geni ID, not redirect")
    
    client.close()
    return exported_count

if __name__ == "__main__":
    start_time = time.time()
    count = export_wikidata_no_geni()
    duration = time.time() - start_time
    print(f"Completed in {duration:.1f} seconds")