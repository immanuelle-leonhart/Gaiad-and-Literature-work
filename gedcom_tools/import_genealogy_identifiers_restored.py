#!/usr/bin/env python3
"""
Import Genealogical Identifiers from Restored CSV

Imports genealogical identifiers from the restored wikidata_genealogy_data_restored.csv
file into the MongoDB database. This adds external identifiers for various
genealogy sites and databases.
"""

import pymongo
import csv
import sys
from collections import Counter

# Configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
CSV_FILE = "analysis/wikidata_genealogy_data_restored.csv"

# Map Wikidata property IDs to their meanings (for reference)
PROPERTY_MEANINGS = {
    'P1185': 'Rodovid person ID',
    'P1819': 'Genealogics.org person ID', 
    'P2949': 'WikiTree ID',
    'P4638': 'Malarone ID',
    'P4159': 'Lemon Tree Database ID',
    'P7929': 'Ancestry.com person ID',
    'P535': 'Find a Grave memorial ID',
    'P6821': 'Geni.com profile ID',
    'P8172': 'ID',
    'P3051': 'Roglo person ID'
}

def import_genealogy_identifiers():
    """Import genealogical identifiers from CSV to MongoDB"""
    
    # Connect to MongoDB
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db["entities"]
    
    print(f"Connected to MongoDB: {DATABASE_NAME}.entities")
    print(f"Importing from: {CSV_FILE}")
    print()
    
    # Read CSV and process
    identifiers_added = Counter()
    entities_updated = 0
    entities_not_found = 0
    total_processed = 0
    
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Get all property columns (skip qid and wikidata_qid)
        property_columns = [col for col in reader.fieldnames if col.startswith('P')]
        
        print(f"Found {len(property_columns)} genealogical property columns:")
        for prop in property_columns:
            meaning = PROPERTY_MEANINGS.get(prop, 'Unknown genealogical identifier')
            print(f"  {prop}: {meaning}")
        print()
        
        batch_updates = []
        batch_size = 1000
        
        for row in reader:
            total_processed += 1
            qid = row.get('qid', '').strip()
            
            if not qid or qid == 'qid':  # Skip header or empty rows
                continue
            
            # Find entity in MongoDB
            entity = collection.find_one({'qid': qid})
            if not entity:
                entities_not_found += 1
                continue
            
            # Check for genealogical identifiers in this row
            updates = {}
            entity_has_updates = False
            
            for prop in property_columns:
                value = row.get(prop, '').strip()
                if value:  # Non-empty value
                    # Create claim in MongoDB format
                    claim = {
                        'value': value,
                        'type': 'external-id',
                        'claim_id': f"{qid}_{prop}_{value}"
                    }
                    
                    updates[f"properties.{prop}"] = [claim]
                    identifiers_added[prop] += 1
                    entity_has_updates = True
            
            if entity_has_updates:
                batch_updates.append(
                    pymongo.UpdateOne(
                        {'qid': qid},
                        {'$set': updates}
                    )
                )
                entities_updated += 1
            
            # Execute batch when it reaches batch_size
            if len(batch_updates) >= batch_size:
                collection.bulk_write(batch_updates)
                batch_updates = []
                print(f"  Processed {total_processed:,} rows, updated {entities_updated:,} entities...")
        
        # Execute remaining batch
        if batch_updates:
            collection.bulk_write(batch_updates)
    
    print()
    print("=== IMPORT COMPLETE ===")
    print(f"Total CSV rows processed: {total_processed:,}")
    print(f"Entities updated: {entities_updated:,}")
    print(f"Entities not found: {entities_not_found:,}")
    print()
    
    print("Genealogical identifiers added:")
    for prop, count in sorted(identifiers_added.items()):
        meaning = PROPERTY_MEANINGS.get(prop, 'Unknown')
        print(f"  {prop} ({meaning}): {count:,} entities")
    
    total_identifiers = sum(identifiers_added.values())
    print(f"\nTotal genealogical identifier claims added: {total_identifiers:,}")
    
    client.close()

if __name__ == "__main__":
    import_genealogy_identifiers()