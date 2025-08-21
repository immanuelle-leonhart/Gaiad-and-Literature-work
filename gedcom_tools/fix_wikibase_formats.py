#!/usr/bin/env python3
"""
Fix Wikibase Data Formats

The export and import are failing because the data structures in MongoDB
don't match what the Wikibase API expects. This script fixes:

1. P61 properties (Wikidata QIDs) - Convert to proper external-id format
2. Labels/descriptions - Ensure proper monolingual text structure  
3. Property value formats - Match Wikibase API expectations
4. Remove unsupported data types

This creates a clean dataset that can be imported via API or XML.
"""

import pymongo
import json
import re
from collections import Counter

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

def analyze_current_state():
    """Analyze the current database state"""
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    print("=== ANALYZING CURRENT DATABASE STATE ===")
    print()
    
    total_entities = collection.count_documents({})
    print(f"Total entities: {total_entities:,}")
    
    # Check property distribution
    property_counts = Counter()
    label_issues = 0
    desc_issues = 0
    
    sample_count = 0
    for entity in collection.find().limit(1000):
        sample_count += 1
        
        # Count properties
        properties = entity.get('properties', {})
        for prop_id in properties.keys():
            property_counts[prop_id] += 1
        
        # Check labels
        labels = entity.get('labels', {})
        for lang, label in labels.items():
            if not isinstance(label, str):
                label_issues += 1
        
        # Check descriptions  
        descriptions = entity.get('descriptions', {})
        for lang, desc in descriptions.items():
            if not isinstance(desc, str):
                desc_issues += 1
    
    print(f"Sampled {sample_count:,} entities")
    print(f"Label format issues: {label_issues}")
    print(f"Description format issues: {desc_issues}")
    print()
    
    print("Top 15 properties:")
    for prop, count in property_counts.most_common(15):
        print(f"  {prop}: {count:,}")
    
    client.close()
    return property_counts

def fix_entity_formats():
    """Fix all entity formats for Wikibase compatibility"""
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    print("\n=== FIXING ENTITY FORMATS ===")
    print()
    
    # Process entities in batches
    batch_size = 1000
    total_processed = 0
    total_fixed = 0
    
    # Get all entities
    total_entities = collection.count_documents({})
    print(f"Processing {total_entities:,} entities...")
    
    batch_updates = []
    
    for entity in collection.find():
        total_processed += 1
        if total_processed % 10000 == 0:
            print(f"  Processed {total_processed:,} entities...")
        
        qid = entity['qid']
        needs_update = False
        updates = {}
        
        # Fix labels - ensure they're simple strings
        labels = entity.get('labels', {})
        fixed_labels = {}
        for lang, label in labels.items():
            if isinstance(label, str) and label.strip():
                fixed_labels[lang] = label.strip()
            elif isinstance(label, dict) and 'value' in label:
                fixed_labels[lang] = str(label['value']).strip()
            elif label:
                fixed_labels[lang] = str(label).strip()
        
        if fixed_labels != labels:
            updates['labels'] = fixed_labels
            needs_update = True
        
        # Fix descriptions - ensure they're simple strings
        descriptions = entity.get('descriptions', {})
        fixed_descriptions = {}
        for lang, desc in descriptions.items():
            if isinstance(desc, str) and desc.strip():
                fixed_descriptions[lang] = desc.strip()
            elif isinstance(desc, dict) and 'value' in desc:
                fixed_descriptions[lang] = str(desc['value']).strip()
            elif desc:
                fixed_descriptions[lang] = str(desc).strip()
        
        if fixed_descriptions != descriptions:
            updates['descriptions'] = fixed_descriptions
            needs_update = True
        
        # Fix properties - ensure proper claim format
        properties = entity.get('properties', {})
        fixed_properties = {}
        
        for prop_id, claims in properties.items():
            if not isinstance(claims, list):
                continue
                
            fixed_claims = []
            for claim in claims:
                if not isinstance(claim, dict):
                    continue
                
                # Create proper claim structure
                fixed_claim = {
                    'type': claim.get('type', 'string'),
                    'value': claim.get('value'),
                    'claim_id': claim.get('claim_id', f"{qid}_{prop_id}_auto")
                }
                
                # Handle specific property types
                claim_value = claim.get('value')
                claim_type = claim.get('type', 'string')
                
                if prop_id in ['P61', 'P62', 'P63']:  # External IDs
                    if isinstance(claim_value, dict):
                        # Extract the actual ID string
                        if 'id' in claim_value:
                            fixed_claim['value'] = claim_value['id']
                        elif 'value' in claim_value:
                            fixed_claim['value'] = str(claim_value['value'])
                        else:
                            fixed_claim['value'] = str(claim_value)
                    else:
                        fixed_claim['value'] = str(claim_value) if claim_value else ''
                    fixed_claim['type'] = 'external-id'
                
                elif prop_id in ['P20', 'P42', 'P47', 'P48']:  # Entity references
                    if isinstance(claim_value, str) and claim_value.startswith('Q'):
                        fixed_claim['value'] = claim_value
                        fixed_claim['type'] = 'wikibase-item'
                    elif isinstance(claim_value, dict) and claim_value.get('id', '').startswith('Q'):
                        fixed_claim['value'] = claim_value['id']
                        fixed_claim['type'] = 'wikibase-item'
                    else:
                        continue  # Skip invalid entity references
                
                elif prop_id in ['P55']:  # Specific values
                    fixed_claim['value'] = str(claim_value) if claim_value else ''
                    fixed_claim['type'] = 'string'
                
                elif prop_id in ['P56', 'P57']:  # Dates
                    if isinstance(claim_value, dict):
                        fixed_claim['value'] = claim_value
                        fixed_claim['type'] = 'time'
                    else:
                        fixed_claim['value'] = str(claim_value) if claim_value else ''
                        fixed_claim['type'] = 'string'
                
                else:
                    # Default: string value
                    fixed_claim['value'] = str(claim_value) if claim_value else ''
                    fixed_claim['type'] = 'string'
                
                # Only add valid claims
                if fixed_claim['value']:
                    fixed_claims.append(fixed_claim)
            
            if fixed_claims:
                fixed_properties[prop_id] = fixed_claims
        
        if fixed_properties != properties:
            updates['properties'] = fixed_properties  
            needs_update = True
        
        # Add to batch
        if needs_update:
            total_fixed += 1
            batch_updates.append(
                pymongo.UpdateOne(
                    {'qid': qid},
                    {'$set': updates}
                )
            )
        
        # Execute batch
        if len(batch_updates) >= batch_size:
            collection.bulk_write(batch_updates)
            batch_updates = []
    
    # Execute remaining updates
    if batch_updates:
        collection.bulk_write(batch_updates)
    
    print(f"  Processed {total_processed:,} entities")
    print(f"  Fixed {total_fixed:,} entities")
    
    client.close()
    return total_fixed

def verify_fixes():
    """Verify the fixes worked"""
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    print("\n=== VERIFYING FIXES ===")
    print()
    
    # Sample a few entities
    samples = list(collection.find().limit(5))
    
    for entity in samples:
        qid = entity['qid']
        print(f"{qid}:")
        
        labels = entity.get('labels', {})
        for lang in list(labels.keys())[:2]:
            label = labels[lang]
            print(f"  Label ({lang}): '{label}' (type: {type(label).__name__})")
        
        properties = entity.get('properties', {})
        for prop_id in list(properties.keys())[:3]:
            claims = properties[prop_id]
            if claims:
                claim = claims[0]
                value = claim.get('value')
                claim_type = claim.get('type')
                print(f"  {prop_id}: '{value}' (type: {claim_type})")
        
        print()
    
    client.close()

def main():
    print("Wikibase Data Format Fixer")
    print("=" * 40)
    
    # Analyze current state
    property_counts = analyze_current_state()
    
    # Fix formats
    fixed_count = fix_entity_formats()
    
    if fixed_count > 0:
        print(f"\nSUCCESS: Fixed {fixed_count:,} entities")
        
        # Verify fixes
        verify_fixes()
        
        print("\nEntities are now formatted for Wikibase API compatibility!")
        print("Ready to regenerate XML export with proper formats.")
    else:
        print("\nNo entities needed fixing.")
    
    return fixed_count > 0

if __name__ == "__main__":
    main()