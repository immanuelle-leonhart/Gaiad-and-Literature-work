#!/usr/bin/env python3
"""
Entity Merger Script

Merges duplicate entities based on shared identifier properties.
Implements redirect system and global QID replacement.

Merge Strategy:
1. Lower QID is kept as target, higher QID becomes redirect
2. All properties moved from redirect to target (except QID)
3. Conflicting labels become aliases
4. Redirect gets special redirect property pointing to target
5. All references to redirect QID are updated throughout database
"""

import pymongo
import time
from collections import defaultdict, Counter

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

class EntityMerger:
    def __init__(self, mongo_uri=MONGO_URI):
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db[COLLECTION_NAME]
        
        self.stats = {
            'merges_completed': 0,
            'redirects_created': 0,
            'properties_moved': 0,
            'labels_converted_to_aliases': 0,
            'references_updated': 0
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
    
    def merge_two_entities(self, target_qid, redirect_qid):
        """Merge two entities: redirect_qid -> target_qid"""
        print(f"Merging {redirect_qid} -> {target_qid}")
        
        # Get both entities
        target_entity = self.collection.find_one({'qid': target_qid})
        redirect_entity = self.collection.find_one({'qid': redirect_qid})
        
        if not target_entity or not redirect_entity:
            print(f"  ERROR: Could not find entities {target_qid} or {redirect_qid}")
            return False
        
        # Prepare merged properties
        merged_properties = target_entity.get('properties', {}).copy()
        redirect_properties = redirect_entity.get('properties', {})
        
        # Merge all properties from redirect to target
        properties_moved = 0
        for prop_id, claims in redirect_properties.items():
            if prop_id != 'qid':  # Don't move QID property
                if prop_id in merged_properties:
                    # Merge claims, avoiding duplicates
                    existing_claim_ids = {claim.get('claim_id') for claim in merged_properties[prop_id]}
                    for claim in claims:
                        # Use claim_id for deduplication instead of value (which might be dict)
                        claim_id = claim.get('claim_id')
                        if claim_id not in existing_claim_ids:
                            merged_properties[prop_id].append(claim)
                            properties_moved += 1
                else:
                    # New property
                    merged_properties[prop_id] = claims.copy()
                    properties_moved += len(claims)
        
        # Handle labels (conflicting labels become aliases)
        merged_labels = target_entity.get('labels', {}).copy()
        merged_aliases = target_entity.get('aliases', {}).copy()
        
        redirect_labels = redirect_entity.get('labels', {})
        labels_to_aliases = 0
        
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
        
        # Merge descriptions and other aliases
        merged_descriptions = target_entity.get('descriptions', {}).copy()
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
        
        # Update target entity with merged data
        target_update = {
            'properties': merged_properties,
            'labels': merged_labels,
            'descriptions': merged_descriptions,
            'aliases': merged_aliases
        }
        
        # Create redirect entity (keep only QID and redirect property)
        redirect_update = {
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
        
        # Execute updates
        try:
            # Update target
            self.collection.update_one(
                {'qid': target_qid},
                {'$set': target_update}
            )
            
            # Update redirect
            self.collection.update_one(
                {'qid': redirect_qid},
                {'$set': redirect_update}
            )
            
            # Update statistics
            self.stats['properties_moved'] += properties_moved
            self.stats['labels_converted_to_aliases'] += labels_to_aliases
            self.stats['redirects_created'] += 1
            
            print(f"  Success: Moved {properties_moved} properties, {labels_to_aliases} labels->aliases")
            return True
            
        except Exception as e:
            print(f"  ERROR: Failed to update entities: {e}")
            return False
    
    def update_references_throughout_database(self, old_qid, new_qid):
        """Replace all references to old_qid with new_qid throughout database"""
        print(f"Updating references: {old_qid} -> {new_qid}")
        
        references_updated = 0
        entities_checked = 0
        
        for entity in self.collection.find():
            entities_checked += 1
            if entities_checked % 10000 == 0:
                print(f"    Checked {entities_checked:,} entities for references...")
            
            entity_updated = False
            updates = {}
            
            # Check all properties for references to old_qid
            properties = entity.get('properties', {})
            for prop_id, claims in properties.items():
                updated_claims = []
                claims_updated = False
                
                for claim in claims:
                    updated_claim = claim.copy()
                    value = claim.get('value')
                    
                    # Check different value types
                    if isinstance(value, str) and value == old_qid:
                        updated_claim['value'] = new_qid
                        claims_updated = True
                        references_updated += 1
                    elif isinstance(value, dict):
                        if value.get('id') == old_qid:
                            updated_claim['value'] = value.copy()
                            updated_claim['value']['id'] = new_qid
                            claims_updated = True
                            references_updated += 1
                    
                    updated_claims.append(updated_claim)
                
                if claims_updated:
                    updates[f'properties.{prop_id}'] = updated_claims
                    entity_updated = True
            
            # Update entity if references found
            if entity_updated:
                self.collection.update_one(
                    {'qid': entity['qid']},
                    {'$set': updates}
                )
        
        print(f"    Updated {references_updated:,} references in {entities_checked:,} entities")
        self.stats['references_updated'] += references_updated
        
        return references_updated
    
    def merge_duplicates_by_property(self, property_id, max_merges=None):
        """Merge all duplicates for a given property"""
        print(f"\n{'='*60}")
        print(f"MERGING DUPLICATES BY PROPERTY {property_id}")
        print(f"{'='*60}")
        
        duplicates = self.find_duplicates_by_property(property_id)
        
        if not duplicates:
            print(f"No duplicates found for {property_id}")
            return
        
        merge_count = 0
        
        for value, entities in duplicates.items():
            if max_merges and merge_count >= max_merges:
                print(f"Reached max merges limit ({max_merges})")
                break
                
            if len(entities) < 2:
                continue
            
            # Sort by QID number (lower QID is target)
            entities.sort(key=lambda x: self.qid_to_number(x['qid']))
            
            target = entities[0]  # Lowest QID
            target_qid = target['qid']
            
            print(f"\nMerging group with {property_id} value: {value}")
            print(f"  Target: {target_qid}")
            
            # Merge all others into target
            for i in range(1, len(entities)):
                redirect = entities[i]
                redirect_qid = redirect['qid']
                
                print(f"  Merging: {redirect_qid} -> {target_qid}")
                
                if self.merge_two_entities(target_qid, redirect_qid):
                    # Update all references throughout database
                    self.update_references_throughout_database(redirect_qid, target_qid)
                    merge_count += 1
                    self.stats['merges_completed'] += 1
                    
                    print(f"    Merge {merge_count} completed")
                else:
                    print(f"    Merge failed")
        
        print(f"\nCompleted {merge_count} merges for {property_id}")
        return merge_count
    
    def run_full_merge_pipeline(self):
        """Run the complete merge pipeline: P63 -> P61 -> P62"""
        start_time = time.time()
        
        print("ENTITY MERGE PIPELINE STARTING")
        print("="*60)
        print("Phase 1: P63 (UUID) duplicates")
        print("Phase 2: P61 (Wikidata QID) duplicates")
        print("Phase 3: P62 (Geni ID) duplicates")
        print("="*60)
        
        # Phase 1: P63 (UUID) duplicates - simplest merges
        print("\nPHASE 1: Processing P63 (UUID) duplicates...")
        p63_merges = self.merge_duplicates_by_property('P63')
        
        # Phase 2: P61 (Wikidata QID) duplicates  
        print("\nPHASE 2: Processing P61 (Wikidata QID) duplicates...")
        p61_merges = self.merge_duplicates_by_property('P61')
        
        # Phase 3: P62 (Geni ID) duplicates
        print("\nPHASE 3: Processing P62 (Geni ID) duplicates...")
        p62_merges = self.merge_duplicates_by_property('P62')
        
        duration = time.time() - start_time
        
        print(f"\n{'='*60}")
        print("MERGE PIPELINE COMPLETE")
        print(f"{'='*60}")
        print(f"P63 merges: {p63_merges:,}")
        print(f"P61 merges: {p61_merges:,}")
        print(f"P62 merges: {p62_merges:,}")
        print(f"Total merges: {self.stats['merges_completed']:,}")
        print(f"Redirects created: {self.stats['redirects_created']:,}")
        print(f"Properties moved: {self.stats['properties_moved']:,}")
        print(f"Labels->aliases: {self.stats['labels_converted_to_aliases']:,}")
        print(f"References updated: {self.stats['references_updated']:,}")
        print(f"Duration: {duration:.1f} seconds")
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()

def main():
    merger = EntityMerger()
    
    try:
        merger.run_full_merge_pipeline()
    finally:
        merger.close()

if __name__ == "__main__":
    main()