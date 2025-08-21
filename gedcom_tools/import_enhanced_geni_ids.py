#!/usr/bin/env python3
"""
Import Enhanced Geni IDs from CSV

Reads the enhanced CSV file with Geni IDs and adds them to entities
that currently only have Wikidata IDs. Then re-runs Geni ID deduplication.

CSV format expected:
- Column 1: QID (from this database)
- Column 2: Wikidata_QID  
- Column 3: Geni_ID (newly added)
"""

import pymongo
import csv
import time
from collections import defaultdict

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

class GeniIDImporter:
    def __init__(self, mongo_uri=MONGO_URI):
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db[COLLECTION_NAME]
        
        self.stats = {
            'csv_rows_read': 0,
            'geni_ids_imported': 0,
            'entities_updated': 0,
            'duplicates_found': 0,
            'merges_completed': 0
        }
        
        print(f"Connected to MongoDB: {DATABASE_NAME}.{COLLECTION_NAME}")
    
    def import_geni_ids_from_csv(self, csv_filename="wikidata_with_added_geni.csv"):
        """Import Geni IDs from enhanced CSV file"""
        print(f"=== IMPORTING GENI IDs FROM {csv_filename} ===")
        print()
        
        try:
            with open(csv_filename, 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                
                # Skip header row
                next(reader)
                
                bulk_ops = []
                
                for row in reader:
                    self.stats['csv_rows_read'] += 1
                    
                    if len(row) < 3:
                        continue
                        
                    qid = row[0].strip()
                    wikidata_qid = row[1].strip()
                    geni_id = row[2].strip()
                    
                    # Skip rows without Geni ID
                    if not geni_id or geni_id == '':
                        continue
                    
                    # Create P62 claim for the Geni ID
                    geni_claim = {
                        'value': geni_id,
                        'type': 'external-id',
                        'claim_id': f"{qid}_P62_{geni_id}"
                    }
                    
                    # Add to bulk operations
                    bulk_ops.append(
                        pymongo.UpdateOne(
                            {'qid': qid},
                            {'$push': {'properties.P62': geni_claim}}
                        )
                    )
                    
                    self.stats['geni_ids_imported'] += 1
                    
                    # Execute in batches
                    if len(bulk_ops) >= 1000:
                        result = self.collection.bulk_write(bulk_ops)
                        self.stats['entities_updated'] += result.modified_count
                        bulk_ops = []
                        print(f"  Imported {self.stats['geni_ids_imported']:,} Geni IDs...")
                
                # Execute remaining operations
                if bulk_ops:
                    result = self.collection.bulk_write(bulk_ops)
                    self.stats['entities_updated'] += result.modified_count
                
                print(f"  Read {self.stats['csv_rows_read']:,} CSV rows")
                print(f"  Imported {self.stats['geni_ids_imported']:,} Geni IDs")
                print(f"  Updated {self.stats['entities_updated']:,} entities")
                
        except FileNotFoundError:
            print(f"ERROR: Could not find file {csv_filename}")
            return False
        except Exception as e:
            print(f"ERROR: Failed to read CSV file: {e}")
            return False
            
        return True
    
    def find_geni_duplicates(self):
        """Find entities with duplicate Geni ID values"""
        print("Finding Geni ID duplicates...")
        
        geni_map = defaultdict(list)
        total_checked = 0
        
        for entity in self.collection.find({'properties.P62': {'$exists': True}}):
            total_checked += 1
            if total_checked % 5000 == 0:
                print(f"  Checked {total_checked:,} entities with P62...")
            
            qid = entity['qid']
            claims = entity['properties']['P62']
            
            # Get unique values from claims
            values = set()
            for claim in claims:
                value = claim.get('value', '')
                if value:
                    values.add(value)
            
            # Add entity to each value's list
            for value in values:
                geni_map[value].append({
                    'qid': qid,
                    'entity': entity
                })
        
        # Find duplicates (values with more than one entity)
        duplicates = {value: entities for value, entities in geni_map.items() if len(entities) > 1}
        
        print(f"  Found {len(duplicates):,} Geni ID values with duplicates")
        total_entities = sum(len(entities) for entities in duplicates.values())
        print(f"  Total entities involved: {total_entities:,}")
        
        self.stats['duplicates_found'] = len(duplicates)
        return duplicates
    
    def qid_to_number(self, qid):
        """Convert QID to number for comparison (Q12345 -> 12345)"""
        return int(qid[1:]) if qid.startswith('Q') else float('inf')
    
    def merge_geni_duplicates(self, duplicates):
        """Merge entities with duplicate Geni IDs using efficient batch processing"""
        if not duplicates:
            print("No duplicates to merge")
            return 0
            
        print("Merging Geni ID duplicates...")
        
        merge_mapping = {}  # redirect_qid -> target_qid
        target_updates = {}  # target_qid -> merged_data
        redirect_updates = {}  # redirect_qid -> redirect_data
        
        merge_groups = 0
        
        for value, entities in duplicates.items():
            if len(entities) < 2:
                continue
            
            merge_groups += 1
            if merge_groups % 100 == 0:
                print(f"  Processing merge group {merge_groups:,}...")
            
            # Sort by QID number (lower QID is target)
            entities.sort(key=lambda x: self.qid_to_number(x['qid']))
            
            target = entities[0]  # Lowest QID
            target_qid = target['qid']
            target_entity = target['entity']
            
            # Start with target entity data
            merged_properties = target_entity.get('properties', {}).copy()
            merged_labels = target_entity.get('labels', {}).copy()
            merged_aliases = target_entity.get('aliases', {}).copy()
            merged_descriptions = target_entity.get('descriptions', {}).copy()
            
            # Merge all redirect entities into target
            for i in range(1, len(entities)):
                redirect = entities[i]
                redirect_qid = redirect['qid']
                redirect_entity = redirect['entity']
                
                merge_mapping[redirect_qid] = target_qid
                
                # Merge properties
                redirect_properties = redirect_entity.get('properties', {})
                for prop_id, claims in redirect_properties.items():
                    if prop_id != 'qid':
                        if prop_id in merged_properties:
                            # Merge claims, avoiding duplicates by claim_id
                            existing_claim_ids = {claim.get('claim_id') for claim in merged_properties[prop_id]}
                            for claim in claims:
                                claim_id = claim.get('claim_id')
                                if claim_id not in existing_claim_ids:
                                    merged_properties[prop_id].append(claim)
                        else:
                            # New property
                            merged_properties[prop_id] = claims.copy()
                
                # Handle labels (conflicts become aliases)
                redirect_labels = redirect_entity.get('labels', {})
                for lang, label in redirect_labels.items():
                    if lang in merged_labels:
                        if merged_labels[lang] != label:
                            # Conflict: add redirect label as alias
                            if lang not in merged_aliases:
                                merged_aliases[lang] = []
                            if label not in merged_aliases[lang]:
                                merged_aliases[lang].append(label)
                    else:
                        # No conflict: add label
                        merged_labels[lang] = label
                
                # Merge descriptions and aliases
                redirect_descriptions = redirect_entity.get('descriptions', {})
                for lang, desc in redirect_descriptions.items():
                    if lang not in merged_descriptions:
                        merged_descriptions[lang] = desc
                
                redirect_aliases = redirect_entity.get('aliases', {})
                for lang, aliases in redirect_aliases.items():
                    if lang not in merged_aliases:
                        merged_aliases[lang] = []
                    for alias in aliases:
                        if alias not in merged_aliases[lang]:
                            merged_aliases[lang].append(alias)
                
                # Create redirect entry (preserve _id for MongoDB)
                redirect_updates[redirect_qid] = {
                    '_id': redirect_qid,  # Preserve MongoDB _id
                    'qid': redirect_qid,
                    'entity_type': redirect_entity.get('entity_type', 'item'),
                    'properties': {
                        'redirect': [{
                            'value': target_qid,
                            'type': 'wikibase-item',
                            'claim_id': f"{redirect_qid}_redirect_to_{target_qid}"
                        }]
                    },
                    'labels': {},
                    'descriptions': {},
                    'aliases': {}
                }
                
                self.stats['merges_completed'] += 1
            
            # Store target update
            target_updates[target_qid] = {
                'properties': merged_properties,
                'labels': merged_labels,
                'descriptions': merged_descriptions,
                'aliases': merged_aliases
            }
        
        print(f"  Processed {merge_groups:,} merge groups")
        
        # Execute batch updates
        print("Executing batch database updates...")
        
        # Update targets in batches
        if target_updates:
            target_ops = []
            for qid, update_data in target_updates.items():
                target_ops.append(
                    pymongo.UpdateOne({'qid': qid}, {'$set': update_data})
                )
                
                if len(target_ops) >= 1000:
                    self.collection.bulk_write(target_ops)
                    target_ops = []
            
            if target_ops:
                self.collection.bulk_write(target_ops)
            
            print(f"  Updated {len(target_updates):,} target entities")
        
        # Update redirects in batches
        if redirect_updates:
            redirect_ops = []
            for qid, update_data in redirect_updates.items():
                redirect_ops.append(
                    pymongo.ReplaceOne({'qid': qid}, update_data)
                )
                
                if len(redirect_ops) >= 1000:
                    self.collection.bulk_write(redirect_ops)
                    redirect_ops = []
            
            if redirect_ops:
                self.collection.bulk_write(redirect_ops)
            
            print(f"  Updated {len(redirect_updates):,} redirect entities")
        
        # Update references throughout database
        if merge_mapping:
            print("Updating references throughout database...")
            bulk_ops = []
            entities_checked = 0
            references_updated = 0
            
            for entity in self.collection.find():
                entities_checked += 1
                if entities_checked % 10000 == 0:
                    print(f"    Checked {entities_checked:,} entities...")
                
                # Skip redirect entities themselves
                if 'redirect' in entity.get('properties', {}):
                    continue
                
                entity_has_updates = False
                updates = {}
                
                # Check all properties for references
                properties = entity.get('properties', {})
                for prop_id, claims in properties.items():
                    updated_claims = []
                    claims_updated = False
                    
                    for claim in claims:
                        updated_claim = claim.copy()
                        value = claim.get('value')
                        
                        # Check different value types for QID references
                        if isinstance(value, str) and value in merge_mapping:
                            updated_claim['value'] = merge_mapping[value]
                            claims_updated = True
                            references_updated += 1
                        elif isinstance(value, dict) and value.get('id') in merge_mapping:
                            updated_claim['value'] = value.copy()
                            updated_claim['value']['id'] = merge_mapping[value['id']]
                            claims_updated = True
                            references_updated += 1
                        
                        updated_claims.append(updated_claim)
                    
                    if claims_updated:
                        updates[f'properties.{prop_id}'] = updated_claims
                        entity_has_updates = True
                
                # Add to batch if entity needs updates
                if entity_has_updates:
                    bulk_ops.append(
                        pymongo.UpdateOne(
                            {'qid': entity['qid']},
                            {'$set': updates}
                        )
                    )
                    
                    # Execute batch when full
                    if len(bulk_ops) >= 1000:
                        self.collection.bulk_write(bulk_ops)
                        bulk_ops = []
            
            # Execute final batch
            if bulk_ops:
                self.collection.bulk_write(bulk_ops)
            
            print(f"    Updated {references_updated:,} references in {entities_checked:,} entities")
        
        return len(merge_mapping)
    
    def run_import_and_deduplication(self, csv_filename="wikidata_with_added_geni.csv"):
        """Run complete import and deduplication process"""
        start_time = time.time()
        
        print("GENI ID IMPORT AND DEDUPLICATION PROCESS")
        print("=" * 60)
        print("Step 1: Import Geni IDs from enhanced CSV")
        print("Step 2: Find new Geni ID duplicates")
        print("Step 3: Merge duplicate entities")
        print("=" * 60)
        print()
        
        # Step 1: Import Geni IDs
        if not self.import_geni_ids_from_csv(csv_filename):
            print("Failed to import Geni IDs")
            return
        
        print()
        
        # Step 2: Find duplicates
        duplicates = self.find_geni_duplicates()
        
        print()
        
        # Step 3: Merge duplicates
        merges = self.merge_geni_duplicates(duplicates)
        
        duration = time.time() - start_time
        
        print()
        print("=" * 60)
        print("IMPORT AND DEDUPLICATION COMPLETE")
        print("=" * 60)
        print("RESULTS:")
        print(f"  CSV rows read: {self.stats['csv_rows_read']:,}")
        print(f"  Geni IDs imported: {self.stats['geni_ids_imported']:,}")
        print(f"  Entities updated with new Geni IDs: {self.stats['entities_updated']:,}")
        print(f"  Duplicate Geni ID groups found: {self.stats['duplicates_found']:,}")
        print(f"  Entity merges completed: {self.stats['merges_completed']:,}")
        print(f"  Duration: {duration:.1f} seconds")
        
        if merges > 0:
            print(f"  Average: {merges/duration:.1f} merges/second")
        
        print()
        print("SUCCESS: All new Geni IDs imported and duplicates resolved!")
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()

def main():
    importer = GeniIDImporter()
    
    try:
        importer.run_import_and_deduplication()
    finally:
        importer.close()

if __name__ == "__main__":
    main()