#!/usr/bin/env python3
"""
MONGODB MERGE MAPPER

Creates merge mapping CSV files for duplicate entity resolution.
Instead of complex API-based merging, this creates mapping files that can be 
used for bulk find-and-replace operations on the final XML export.
"""

import pymongo
import csv
import re
from collections import defaultdict
import Levenshtein  # pip install python-Levenshtein

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

class MongoDBMergeMapper:
    def __init__(self, mongo_uri=MONGO_URI):
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db[COLLECTION_NAME]
        
        print(f"Connected to MongoDB: {DATABASE_NAME}.{COLLECTION_NAME}")
    
    def find_name_duplicates(self, similarity_threshold=0.85):
        """Find potential duplicates based on name similarity"""
        print("Finding name-based duplicates...")
        
        # Group entities by similar names
        name_groups = defaultdict(list)
        
        for entity in self.collection.find({"entity_type": "item", "labels.en": {"$exists": True}}):
            qid = entity['qid']
            name = entity['labels']['en'].strip().lower()
            
            # Normalize name
            normalized = re.sub(r'[^\w\s]', '', name)
            normalized = re.sub(r'\s+', ' ', normalized)
            
            if len(normalized) > 2:  # Skip very short names
                name_groups[normalized].append({
                    'qid': qid,
                    'name': entity['labels']['en'],
                    'description': entity.get('descriptions', {}).get('en', ''),
                    'properties': list(entity.get('properties', {}).keys())
                })
        
        # Find groups with multiple entities
        duplicate_pairs = []
        
        for normalized_name, entities in name_groups.items():
            if len(entities) > 1:
                # Check each pair in the group
                for i in range(len(entities)):
                    for j in range(i + 1, len(entities)):
                        entity1, entity2 = entities[i], entities[j]
                        
                        # Calculate similarity
                        similarity = Levenshtein.ratio(entity1['name'], entity2['name'])
                        
                        if similarity >= similarity_threshold:
                            # Determine which should be the primary (more properties = primary)
                            if len(entity1['properties']) >= len(entity2['properties']):
                                primary, secondary = entity1, entity2
                            else:
                                primary, secondary = entity2, entity1
                            
                            duplicate_pairs.append({
                                'primary_qid': primary['qid'],
                                'secondary_qid': secondary['qid'],
                                'primary_name': primary['name'],
                                'secondary_name': secondary['name'],
                                'similarity': similarity,
                                'reason': 'name_similarity',
                                'primary_properties': len(primary['properties']),
                                'secondary_properties': len(secondary['properties'])
                            })
        
        print(f"Found {len(duplicate_pairs)} potential name duplicates")
        return duplicate_pairs
    
    def find_identifier_duplicates(self):
        """Find duplicates based on shared external identifiers"""
        print("Finding identifier-based duplicates...")
        
        duplicate_pairs = []
        
        # Group by Wikidata QID
        wikidata_groups = defaultdict(list)
        for entity in self.collection.find({"properties.P44": {"$exists": True}}):
            p44_claims = entity['properties']['P44']
            for claim in p44_claims:
                wikidata_qid = claim.get('value')
                if wikidata_qid:
                    wikidata_groups[wikidata_qid].append(entity)
        
        for wikidata_qid, entities in wikidata_groups.items():
            if len(entities) > 1:
                # Use the one with the most properties as primary
                primary = max(entities, key=lambda e: len(e.get('properties', {})))
                
                for entity in entities:
                    if entity['qid'] != primary['qid']:
                        duplicate_pairs.append({
                            'primary_qid': primary['qid'],
                            'secondary_qid': entity['qid'],
                            'primary_name': primary.get('labels', {}).get('en', ''),
                            'secondary_name': entity.get('labels', {}).get('en', ''),
                            'similarity': 1.0,
                            'reason': f'shared_wikidata_{wikidata_qid}',
                            'primary_properties': len(primary.get('properties', {})),
                            'secondary_properties': len(entity.get('properties', {}))
                        })
        
        # Group by Geni ID
        geni_groups = defaultdict(list)
        for entity in self.collection.find({"properties.P43": {"$exists": True}}):
            p43_claims = entity['properties']['P43']
            for claim in p43_claims:
                geni_id = claim.get('value')
                if geni_id:
                    geni_groups[geni_id].append(entity)
        
        for geni_id, entities in geni_groups.items():
            if len(entities) > 1:
                primary = max(entities, key=lambda e: len(e.get('properties', {})))
                
                for entity in entities:
                    if entity['qid'] != primary['qid']:
                        duplicate_pairs.append({
                            'primary_qid': primary['qid'],
                            'secondary_qid': entity['qid'],
                            'primary_name': primary.get('labels', {}).get('en', ''),
                            'secondary_name': entity.get('labels', {}).get('en', ''),
                            'similarity': 1.0,
                            'reason': f'shared_geni_{geni_id}',
                            'primary_properties': len(primary.get('properties', {})),
                            'secondary_properties': len(entity.get('properties', {}))
                        })
        
        print(f"Found {len(duplicate_pairs)} identifier duplicates")
        return duplicate_pairs
    
    def generate_merge_mapping_csv(self, filename="merge_mapping.csv"):
        """Generate comprehensive merge mapping CSV"""
        print("Generating merge mapping CSV...")
        
        # Find all types of duplicates
        name_duplicates = self.find_name_duplicates()
        identifier_duplicates = self.find_identifier_duplicates()
        
        # Combine and deduplicate
        all_duplicates = name_duplicates + identifier_duplicates
        
        # Remove duplicates (same pair suggested by multiple methods)
        seen_pairs = set()
        unique_duplicates = []
        
        for dup in all_duplicates:
            pair_key = tuple(sorted([dup['primary_qid'], dup['secondary_qid']]))
            if pair_key not in seen_pairs:
                seen_pairs.add(pair_key)
                unique_duplicates.append(dup)
        
        # Sort by similarity score
        unique_duplicates.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Write CSV
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Primary_QID', 'Secondary_QID', 'Primary_Name', 'Secondary_Name',
                'Similarity', 'Reason', 'Primary_Properties', 'Secondary_Properties',
                'Action', 'Status'
            ])
            
            for dup in unique_duplicates:
                writer.writerow([
                    dup['primary_qid'],
                    dup['secondary_qid'],
                    dup['primary_name'],
                    dup['secondary_name'],
                    f"{dup['similarity']:.3f}",
                    dup['reason'],
                    dup['primary_properties'],
                    dup['secondary_properties'],
                    'MERGE',  # Default action
                    'PENDING'  # Default status
                ])
        
        print(f"✓ Generated {filename} with {len(unique_duplicates)} merge candidates")
        return len(unique_duplicates)
    
    def apply_merge_mapping(self, mapping_file="merge_mapping.csv"):
        """Apply approved merges from CSV file (modifies MongoDB)"""
        print(f"Applying merges from {mapping_file}...")
        
        applied_merges = 0
        
        with open(mapping_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                if row['Action'] == 'MERGE' and row['Status'] == 'APPROVED':
                    primary_qid = row['Primary_QID']
                    secondary_qid = row['Secondary_QID']
                    
                    # Get both entities
                    primary = self.collection.find_one({"_id": primary_qid})
                    secondary = self.collection.find_one({"_id": secondary_qid})
                    
                    if primary and secondary:
                        # Merge properties from secondary into primary
                        merged_properties = primary.get('properties', {}).copy()
                        
                        for prop_id, claims in secondary.get('properties', {}).items():
                            if prop_id not in merged_properties:
                                merged_properties[prop_id] = claims
                            else:
                                # Combine claims, avoid duplicates
                                existing_values = [c.get('value') for c in merged_properties[prop_id]]
                                for claim in claims:
                                    if claim.get('value') not in existing_values:
                                        merged_properties[prop_id].append(claim)
                        
                        # Update primary entity
                        self.collection.update_one(
                            {"_id": primary_qid},
                            {"$set": {"properties": merged_properties}}
                        )
                        
                        # Delete secondary entity
                        self.collection.delete_one({"_id": secondary_qid})
                        
                        applied_merges += 1
                        print(f"  Merged {secondary_qid} -> {primary_qid}")
        
        print(f"✓ Applied {applied_merges} merges")
        return applied_merges
    
    def create_replacement_mapping(self, mapping_file="merge_mapping.csv", output_file="qid_replacements.csv"):
        """Create QID replacement mapping for XML post-processing"""
        print(f"Creating QID replacement mapping from {mapping_file}...")
        
        replacements = []
        
        with open(mapping_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                if row['Action'] == 'MERGE' and row['Status'] == 'APPROVED':
                    replacements.append({
                        'old_qid': row['Secondary_QID'],
                        'new_qid': row['Primary_QID'],
                        'reason': row['Reason']
                    })
        
        # Write replacement mapping
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Old_QID', 'New_QID', 'Reason'])
            
            for replacement in replacements:
                writer.writerow([
                    replacement['old_qid'],
                    replacement['new_qid'],
                    replacement['reason']
                ])
        
        print(f"✓ Created {output_file} with {len(replacements)} QID replacements")
        return len(replacements)
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()

def main():
    import sys
    
    mapper = MongoDBMergeMapper()
    
    try:
        if len(sys.argv) > 1:
            if sys.argv[1] == '--apply':
                # Apply approved merges
                mapper.apply_merge_mapping()
            elif sys.argv[1] == '--replacements':
                # Create replacement mapping
                mapper.create_replacement_mapping()
        else:
            # Generate merge mapping
            mapper.generate_merge_mapping_csv()
    finally:
        mapper.close()

if __name__ == "__main__":
    main()