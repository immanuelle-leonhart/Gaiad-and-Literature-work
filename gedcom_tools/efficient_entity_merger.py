#!/usr/bin/env python3
"""
Efficient Entity Merger Script

High-performance batch merger that avoids per-merge database scans.
Uses single-pass approach for reference updates.

Strategy:
1. Find all duplicates by property
2. Generate merge mapping (redirect_qid -> target_qid)
3. Perform all entity merges in batch
4. Single pass through database to update all references
"""

import pymongo
import time
from collections import defaultdict, Counter

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

class EfficientEntityMerger:
    def __init__(self, mongo_uri=MONGO_URI):
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db[COLLECTION_NAME]
        
        self.stats = {
            'merges_completed': 0,
            'redirects_created': 0,
            'properties_moved': 0,
            'labels_converted_to_aliases': 0,
            'references_updated': 0,
            'entities_processed': 0
        }
        
        print(f"Connected to MongoDB: {DATABASE_NAME}.{COLLECTION_NAME}")
    
    def qid_to_number(self, qid):
        """Convert QID to number for comparison (Q12345 -> 12345)"""
        return int(qid[1:]) if qid.startswith('Q') else float('inf')
    
    def find_duplicates_by_property(self, property_id):
        """Find entities with duplicate values for given property"""
        print(f"Finding duplicates for property {property_id}...")
        
        property_map = defaultdict(list)
        total_checked = 0
        
        # Single pass to collect all duplicate groups
        for entity in self.collection.find({f'properties.{property_id}': {'$exists': True}}):
            total_checked += 1
            if total_checked % 5000 == 0:
                print(f"  Checked {total_checked:,} entities with {property_id}...")
            
            qid = entity['qid']
            claims = entity['properties'][property_id]
            
            # Get unique values from claims
            values = set()
            for claim in claims:
                value = claim.get('value', '')
                if value:
                    values.add(value)
            
            # Add entity to each value's list
            for value in values:
                property_map[value].append({
                    'qid': qid,
                    'entity': entity
                })
        
        # Find duplicates (values with more than one entity)
        duplicates = {value: entities for value, entities in property_map.items() if len(entities) > 1}
        
        print(f"  Found {len(duplicates):,} {property_id} values with duplicates")
        print(f"  Total entities involved: {sum(len(entities) for entities in duplicates.values()):,}")
        
        return duplicates
    
    def generate_merge_mapping(self, duplicates):
        """Generate mapping of redirect_qid -> target_qid"""
        print("Generating merge mapping...")
        
        merge_mapping = {}  # redirect_qid -> target_qid
        merge_groups = []   # List of (target_qid, [redirect_qids])
        
        for value, entities in duplicates.items():
            if len(entities) < 2:
                continue
            
            # Sort by QID number (lower QID is target)
            entities.sort(key=lambda x: self.qid_to_number(x['qid']))
            
            target = entities[0]  # Lowest QID
            target_qid = target['qid']
            redirect_qids = []
            
            # All others become redirects
            for i in range(1, len(entities)):
                redirect_qid = entities[i]['qid']
                merge_mapping[redirect_qid] = target_qid
                redirect_qids.append(redirect_qid)
            
            if redirect_qids:
                merge_groups.append((target_qid, redirect_qids, entities))
        
        print(f"  Generated {len(merge_mapping):,} redirects in {len(merge_groups):,} groups")
        return merge_mapping, merge_groups
    
    def batch_merge_entities(self, merge_groups):
        """Perform all entity merges in batch operations"""
        print("Performing batch entity merges...")
        
        target_updates = {}  # target_qid -> merged_data
        redirect_updates = {}  # redirect_qid -> redirect_data
        
        processed_groups = 0
        
        for target_qid, redirect_qids, entities in merge_groups:
            processed_groups += 1
            if processed_groups % 100 == 0:
                print(f"  Processed {processed_groups:,} merge groups...")
            
            target_entity = entities[0]
            
            # Start with target entity data
            merged_properties = target_entity.get('properties', {}).copy()
            merged_labels = target_entity.get('labels', {}).copy()
            merged_aliases = target_entity.get('aliases', {}).copy()
            merged_descriptions = target_entity.get('descriptions', {}).copy()
            
            properties_moved = 0
            labels_to_aliases = 0
            
            # Merge all redirect entities into target
            for i in range(1, len(entities)):
                redirect_entity = entities[i]
                redirect_qid = redirect_entity['qid']
                
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
                                    properties_moved += 1
                        else:
                            # New property
                            merged_properties[prop_id] = claims.copy()
                            properties_moved += len(claims)
                
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
                                labels_to_aliases += 1
                    else:
                        # No conflict: add label
                        merged_labels[lang] = label
                
                # Merge descriptions
                redirect_descriptions = redirect_entity.get('descriptions', {})
                for lang, desc in redirect_descriptions.items():
                    if lang not in merged_descriptions:
                        merged_descriptions[lang] = desc
                
                # Merge aliases
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
            
            # Store target update
            target_updates[target_qid] = {
                'properties': merged_properties,
                'labels': merged_labels,
                'descriptions': merged_descriptions,
                'aliases': merged_aliases
            }
            
            self.stats['properties_moved'] += properties_moved
            self.stats['labels_converted_to_aliases'] += labels_to_aliases
            self.stats['merges_completed'] += len(redirect_qids)
            self.stats['redirects_created'] += len(redirect_qids)
        
        print(f"  Processed {processed_groups:,} merge groups")
        
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
    
    def batch_update_references(self, merge_mapping):
        """Single pass through database to update all references"""
        if not merge_mapping:
            print("No references to update")
            return
            
        print(f"Updating references in single database pass...")
        print(f"Mapping {len(merge_mapping):,} redirects to targets")
        
        bulk_ops = []
        entities_checked = 0
        entities_updated = 0
        references_updated = 0
        
        for entity in self.collection.find():
            entities_checked += 1
            if entities_checked % 10000 == 0:
                print(f"  Checked {entities_checked:,} entities, updated {entities_updated:,}...")
            
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
                entities_updated += 1
                
                # Execute batch when full
                if len(bulk_ops) >= 1000:
                    self.collection.bulk_write(bulk_ops)
                    bulk_ops = []
        
        # Execute final batch
        if bulk_ops:
            self.collection.bulk_write(bulk_ops)
        
        print(f"  Processed {entities_checked:,} entities")
        print(f"  Updated {entities_updated:,} entities")
        print(f"  Updated {references_updated:,} references")
        
        self.stats['references_updated'] = references_updated
        self.stats['entities_processed'] = entities_checked
    
    def merge_property_duplicates(self, property_id, max_groups=None):
        """Efficient merge of all duplicates for a property with clean separation"""
        print(f"\n{'='*60}")
        print(f"EFFICIENTLY MERGING DUPLICATES BY PROPERTY {property_id}")
        print(f"{'='*60}")
        print(f"Using separate query for {property_id} to avoid cross-contamination")
        
        start_time = time.time()
        
        # Step 1: Find duplicates (fresh query for this property only)
        duplicates = self.find_duplicates_by_property(property_id)
        if not duplicates:
            print(f"No duplicates found for {property_id}")
            return 0
        
        # Limit processing if specified
        if max_groups:
            duplicates = dict(list(duplicates.items())[:max_groups])
            print(f"Limited to first {max_groups} duplicate groups for testing")
        
        # Step 2: Generate merge mapping
        merge_mapping, merge_groups = self.generate_merge_mapping(duplicates)
        
        # Step 3: Batch merge entities
        self.batch_merge_entities(merge_groups)
        
        # Step 4: Single pass reference update (only for this merge batch)
        self.batch_update_references(merge_mapping)
        
        duration = time.time() - start_time
        merged_count = len(merge_mapping)
        
        print(f"\nCompleted {merged_count:,} merges for {property_id} in {duration:.1f} seconds")
        print(f"This phase processed {property_id} duplicates independently")
        return merged_count
    
    def run_efficient_merge_pipeline(self, max_groups_per_property=None):
        """Run the complete efficient merge pipeline with separated phases"""
        start_time = time.time()
        
        print("EFFICIENT ENTITY MERGE PIPELINE STARTING")
        print("="*60)
        print("STRATEGY: Separate queries for each property type")
        print("- Prevents merge artifacts from being copied to proper entries")
        print("- Avoids duplication of work from pairs covered in earlier phases")
        print("- Each phase operates independently on fresh data")
        print("="*60)
        print("Phase 1: P63 (UUID) duplicates - import errors, simplest merges")
        print("Phase 2: P61 (Wikidata QID) duplicates - separate fresh query") 
        print("Phase 3: P62 (Geni ID) duplicates - separate fresh query")
        print("="*60)
        
        # Phase 1: P63 (UUID) duplicates - simplest merges (import errors)
        print("\n" + "="*60)
        print("PHASE 1: Processing P63 (UUID) duplicates")
        print("These are generally import errors and simpler to merge")
        print("="*60)
        p63_merges = self.merge_property_duplicates('P63', max_groups_per_property)
        
        # Phase 2: P61 (Wikidata QID) duplicates - fresh query
        print("\n" + "="*60)
        print("PHASE 2: Processing P61 (Wikidata QID) duplicates")
        print("Fresh query to avoid processing entities modified in Phase 1")
        print("="*60)
        p61_merges = self.merge_property_duplicates('P61', max_groups_per_property)
        
        # Phase 3: P62 (Geni ID) duplicates - fresh query
        print("\n" + "="*60)
        print("PHASE 3: Processing P62 (Geni ID) duplicates")
        print("Fresh query to avoid processing entities modified in Phases 1-2")
        print("="*60)
        p62_merges = self.merge_property_duplicates('P62', max_groups_per_property)
        
        total_duration = time.time() - start_time
        
        print(f"\n{'='*60}")
        print("EFFICIENT MERGE PIPELINE COMPLETE")
        print(f"{'='*60}")
        print("RESULTS BY PHASE:")
        print(f"  Phase 1 (P63 UUID): {p63_merges:,} merges")
        print(f"  Phase 2 (P61 Wikidata): {p61_merges:,} merges")
        print(f"  Phase 3 (P62 Geni): {p62_merges:,} merges")
        print()
        print("TOTAL STATISTICS:")
        print(f"  Total merges: {self.stats['merges_completed']:,}")
        print(f"  Redirects created: {self.stats['redirects_created']:,}")
        print(f"  Properties moved: {self.stats['properties_moved']:,}")
        print(f"  Labels->aliases: {self.stats['labels_converted_to_aliases']:,}")
        print(f"  References updated: {self.stats['references_updated']:,}")
        print(f"  Total duration: {total_duration:.1f} seconds")
        if self.stats['merges_completed'] > 0:
            print(f"  Average: {self.stats['merges_completed']/total_duration:.1f} merges/second")
        print()
        print("SUCCESS: All phases completed with clean separation")
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()

def main():
    merger = EfficientEntityMerger()
    
    try:
        # Full processing - all duplicates across entire database
        merger.run_efficient_merge_pipeline()
    finally:
        merger.close()

if __name__ == "__main__":
    main()