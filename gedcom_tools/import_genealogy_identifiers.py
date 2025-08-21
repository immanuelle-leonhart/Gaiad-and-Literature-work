#!/usr/bin/env python3
"""
Import Genealogical Identifiers from CSV

Imports additional genealogical identifiers from the wikidata_genealogy_data.csv
file into the MongoDB database. This adds external identifiers for various
genealogy sites and databases.

The CSV contains local QID, Wikidata QID, and many genealogical property columns.
Most are blank but some contain valuable external site identifiers.
"""

import pymongo
import csv
import sys
from collections import Counter

# Configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
CSV_FILE = r"C:\Users\Immanuelle\Documents\GitHub\Gaiad-Genealogy\analysis\wikidata_genealogy_data.csv"

# Map Wikidata property IDs to their meanings (for reference)
PROPERTY_MEANINGS = {
    'P7931': 'FamilySearch person ID',
    'P6821': 'Geni.com profile ID', 
    'P8857': 'AllPeople.net ID',
    'P7969': 'Genealogy.net person ID',
    'P9129': 'MyHeritage family tree person ID',
    'P3217': 'Benezit Dictionary of Artists ID',
    'P6996': 'WeRelate person ID',
    'P2889': 'Genealogics.org person ID',
    'P4193': 'Prabook ID',
    'P535': 'Find a Grave memorial ID',
    'P4108': 'Open Library subject ID',
    'P7352': 'Persée author ID',
    'P8094': 'Encyclopedia of Brno History ID',
    'P9644': 'FamilyTreeDNA ID',
    'P6192': 'Rodovid person ID',
    'P2503': 'Geneanet person ID',
    'P4116': 'Genealogie Online Stamboom ID',
    'P3051': 'Roglo person ID',
    'P9195': 'Familypedia person ID',
    'P4620': 'Database of Knights, Dames and people of Medieval Spain ID',
    'P9280': 'Genealogy of the fortified houses of Salento ID',
    'P5452': 'Angelfire ID',
    'P7434': 'Moesgaard ID',
    'P9495': 'TheGenealogist person ID',
    'P5871': 'Pedigree of the Hungarian nation ID',
    'P8462': 'GeneNet ID',
    'P1185': 'Rodovid person ID',
    'P13492': 'Database of Southern African Bird Atlas projects ID',
    'P7929': 'Ancestry.com person ID',
    'P8143': 'Daisy person ID',
    'P8356': 'Genealogy database ID',
    'P8172': 'FamAG ID',
    'P4963': 'The Genealogy Register ID',
    'P6303': 'Genealogy of Medieval German nobility ID',
    'P5259': 'WikiTree person ID',
    'P5324': 'Oxford Dictionary of National Biography ID',
    'P4819': 'Genealogical Research Directory ID',
    'P5316': 'FamiLinx person ID',
    'P5536': 'GenTeam person ID',
    'P4820': 'Genealogy Links ID',
    'P4638': 'Malarone ID',
    'P4159': 'Lemon Tree Database ID',
    'P7607': 'Forebears.io surname ID',
    'P2949': 'WikiTree ID',
    'P1819': 'Genealogics.org person ID'
}

class GenealogyIdentifierImporter:
    def __init__(self, mongo_uri=MONGO_URI, csv_file=CSV_FILE):
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db['entities']
        self.csv_file = csv_file
        
        self.stats = {
            'rows_processed': 0,
            'entities_found': 0,
            'entities_updated': 0,
            'identifiers_added': 0,
            'property_counts': Counter(),
            'entities_not_found': 0
        }
        
        print(f"Connected to MongoDB: {DATABASE_NAME}.entities")
        print(f"CSV file: {csv_file}")
        print()
    
    def import_identifiers(self):
        """Import genealogical identifiers from CSV"""
        print("=== IMPORTING GENEALOGICAL IDENTIFIERS ===")
        print()
        
        # Read CSV and process
        print("Reading CSV file...")
        
        with open(self.csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            print(f"CSV headers: {len(headers)} columns")
            print(f"Properties to import: {len(headers) - 2} (excluding qid, wikidata_qid)")
            print()
            
            batch_updates = []
            
            for row in reader:
                self.stats['rows_processed'] += 1
                
                if self.stats['rows_processed'] % 5000 == 0:
                    print(f"  Processed {self.stats['rows_processed']:,} rows...")
                
                qid = row['qid']
                wikidata_qid = row['wikidata_qid']
                
                # Skip header row or invalid rows
                if qid == 'qid' or not qid.startswith('Q'):
                    continue
                
                # Check if any genealogy identifiers exist in this row
                has_identifiers = False
                new_properties = {}
                
                for prop_id in headers[2:]:  # Skip qid and wikidata_qid columns
                    value = row[prop_id].strip()
                    if value:  # Non-empty value
                        has_identifiers = True
                        self.stats['property_counts'][prop_id] += 1
                        
                        # Create property claim
                        claim = {
                            'value': value,
                            'type': 'external-id',
                            'claim_id': f"{qid}_{prop_id}_{value.replace('/', '_').replace(':', '_')}"
                        }
                        
                        if prop_id not in new_properties:
                            new_properties[prop_id] = []
                        new_properties[prop_id].append(claim)
                
                # Only process if we have identifiers to add
                if has_identifiers:
                    # Check if entity exists in database
                    entity = self.collection.find_one({'qid': qid})
                    if entity:
                        self.stats['entities_found'] += 1
                        
                        # Merge with existing properties
                        existing_properties = entity.get('properties', {})
                        
                        # Add new properties (don't overwrite existing)
                        properties_updated = False
                        for prop_id, claims in new_properties.items():
                            if prop_id not in existing_properties:
                                existing_properties[prop_id] = claims
                                properties_updated = True
                                self.stats['identifiers_added'] += len(claims)
                            else:
                                # Add to existing claims (avoid duplicates)
                                existing_values = set()
                                for existing_claim in existing_properties[prop_id]:
                                    existing_values.add(existing_claim.get('value', ''))
                                
                                for new_claim in claims:
                                    if new_claim['value'] not in existing_values:
                                        existing_properties[prop_id].append(new_claim)
                                        properties_updated = True
                                        self.stats['identifiers_added'] += 1
                        
                        if properties_updated:
                            # Add to batch update
                            batch_updates.append(
                                pymongo.UpdateOne(
                                    {'qid': qid},
                                    {'$set': {'properties': existing_properties}}
                                )
                            )
                            self.stats['entities_updated'] += 1
                            
                            # Execute batch when it gets large
                            if len(batch_updates) >= 1000:
                                self.collection.bulk_write(batch_updates)
                                batch_updates = []
                    else:
                        self.stats['entities_not_found'] += 1
            
            # Execute remaining batch updates
            if batch_updates:
                self.collection.bulk_write(batch_updates)
                
        print(f"  Processed {self.stats['rows_processed']:,} rows total")
        print()
    
    def print_statistics(self):
        """Print import statistics"""
        print("=== IMPORT STATISTICS ===")
        print(f"Rows processed: {self.stats['rows_processed']:,}")
        print(f"Entities found in database: {self.stats['entities_found']:,}")
        print(f"Entities updated: {self.stats['entities_updated']:,}")
        print(f"Entities not found: {self.stats['entities_not_found']:,}")
        print(f"Total identifiers added: {self.stats['identifiers_added']:,}")
        print()
        
        print("=== PROPERTY STATISTICS ===")
        print("Identifiers added by property:")
        for prop_id, count in sorted(self.stats['property_counts'].items(), key=lambda x: x[1], reverse=True):
            meaning = PROPERTY_MEANINGS.get(prop_id, 'Unknown property')
            if count > 0:
                print(f"  {prop_id}: {count:,} ({meaning})")
        print()
        
        # Show top properties
        top_properties = sorted(self.stats['property_counts'].items(), key=lambda x: x[1], reverse=True)[:10]
        if top_properties:
            print("Top 10 most common genealogy identifiers:")
            for prop_id, count in top_properties:
                meaning = PROPERTY_MEANINGS.get(prop_id, 'Unknown property')
                print(f"  {prop_id}: {count:,} - {meaning}")
            print()
    
    def verify_import(self):
        """Verify the import by checking some entities"""
        print("=== VERIFICATION ===")
        print()
        
        # Find some entities with genealogy identifiers
        genealogy_props = list(PROPERTY_MEANINGS.keys())
        sample_entities = []
        
        for prop in genealogy_props[:5]:  # Check first 5 properties
            entity = self.collection.find_one({f'properties.{prop}': {'$exists': True}})
            if entity:
                sample_entities.append(entity)
                break
        
        if sample_entities:
            print("Sample entities with genealogy identifiers:")
            for entity in sample_entities:
                qid = entity['qid']
                label = entity.get('labels', {}).get('en', 'No label')
                properties = entity.get('properties', {})
                
                print(f"{qid} (\"{label}\"):")
                
                for prop_id in genealogy_props:
                    if prop_id in properties:
                        claims = properties[prop_id]
                        meaning = PROPERTY_MEANINGS.get(prop_id, 'Unknown')
                        print(f"  {prop_id} ({meaning}): {len(claims)} identifier(s)")
                        for claim in claims[:2]:  # Show first 2
                            print(f"    - {claim.get('value')}")
                        if len(claims) > 2:
                            print(f"    ... and {len(claims) - 2} more")
                print()
        else:
            print("No entities found with genealogy identifiers")
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()

def main():
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = CSV_FILE
    
    importer = GenealogyIdentifierImporter(csv_file=csv_file)
    
    try:
        importer.import_identifiers()
        importer.print_statistics()
        importer.verify_import()
        
        print("SUCCESS: Genealogical identifiers imported successfully!")
        print(f"Added {importer.stats['identifiers_added']:,} new external identifiers")
        print(f"Updated {importer.stats['entities_updated']:,} entities")
        
    finally:
        importer.close()

if __name__ == "__main__":
    main()