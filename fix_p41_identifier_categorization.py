#!/usr/bin/env python3

import pymongo
import re
import uuid
from collections import defaultdict

def categorize_identifier_value(value):
    """
    Categorize P41 identifier value to determine proper property (P60, P61, P62)
    
    Returns:
    - 'P61': Wikidata QID (Q followed by digits)
    - 'P62': Geni ID (long numeric strings, typically 6+ digits)
    - 'P60': UUID or other format
    """
    if not isinstance(value, str):
        value = str(value)
    
    value = value.strip()
    
    # Wikidata QID pattern: Q followed by digits
    if re.match(r'^Q\d+$', value):
        return 'P61'
    
    # Geni ID pattern: long numeric string (6+ digits)
    if re.match(r'^\d{6,}$', value):
        return 'P62'
    
    # Everything else goes to P60 (UUIDs, other formats)
    return 'P60'

def fix_p41_conversions():
    """Fix incorrect P41 to P60 conversions by properly categorizing identifiers"""
    print("=== FIXING P41 IDENTIFIER CATEGORIZATION ===")
    print()
    
    # Connect to MongoDB
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['gaiad_processing_db']
    collection = db['entities']
    
    # Find entities that were restored from XML (these have the incorrect conversions)
    print("Finding entities with incorrect P41 conversions...")
    restored_entities = list(collection.find({
        'batch_processing.restored_from_xml': True,
        'properties.P60': {'$exists': True}
    }))
    
    print(f"Found {len(restored_entities):,} entities to process")
    
    if not restored_entities:
        print("No entities found with P60 properties from XML restoration")
        client.close()
        return
    
    # Statistics
    stats = {
        'total_processed': 0,
        'entities_fixed': 0,
        'p60_to_p61': 0,  # P60 values moved to P61 (Wikidata)
        'p60_to_p62': 0,  # P60 values moved to P62 (Geni)
        'p60_kept': 0,    # P60 values kept as P60 (UUID)
        'total_identifiers_processed': 0
    }
    
    # Process each entity
    for entity in restored_entities:
        stats['total_processed'] += 1
        if stats['total_processed'] % 1000 == 0:
            print(f"  Processed {stats['total_processed']:,} entities...")
        
        qid = entity['qid']
        properties = entity.get('properties', {})
        
        # Get current P60 claims (these are the incorrectly categorized ones)
        p60_claims = properties.get('P60', [])
        if not p60_claims:
            continue
        
        # Categorize each P60 claim
        new_p60_claims = []
        new_p61_claims = properties.get('P61', []).copy()  # Keep existing P61
        new_p62_claims = properties.get('P62', []).copy()  # Keep existing P62
        
        entity_was_modified = False
        
        for claim in p60_claims:
            value = claim.get('value')
            stats['total_identifiers_processed'] += 1
            
            # Determine correct property
            correct_property = categorize_identifier_value(value)
            
            if correct_property == 'P61':
                # Move to P61 (Wikidata)
                new_claim = {
                    'value': value,
                    'type': 'external-id',
                    'claim_id': f"{qid}_P61_{value}"
                }
                new_p61_claims.append(new_claim)
                stats['p60_to_p61'] += 1
                entity_was_modified = True
                
            elif correct_property == 'P62':
                # Move to P62 (Geni)
                new_claim = {
                    'value': value,
                    'type': 'external-id',
                    'claim_id': f"{qid}_P62_{value}"
                }
                new_p62_claims.append(new_claim)
                stats['p60_to_p62'] += 1
                entity_was_modified = True
                
            else:
                # Keep as P60 (UUID)
                new_p60_claims.append(claim)
                stats['p60_kept'] += 1
        
        # Update entity if changes were made
        if entity_was_modified:
            update_data = {}
            
            # Update P60 (remove moved identifiers)
            if new_p60_claims:
                update_data['properties.P60'] = new_p60_claims
            else:
                # Remove P60 property entirely if no claims left
                collection.update_one(
                    {'qid': qid},
                    {'$unset': {'properties.P60': 1}}
                )
            
            # Update P61 if we have claims
            if new_p61_claims:
                update_data['properties.P61'] = new_p61_claims
            
            # Update P62 if we have claims
            if new_p62_claims:
                update_data['properties.P62'] = new_p62_claims
            
            if update_data:
                collection.update_one(
                    {'qid': qid},
                    {'$set': update_data}
                )
            
            stats['entities_fixed'] += 1
    
    client.close()
    
    print(f"  Processed {stats['total_processed']:,} entities total")
    print()
    print("=== IDENTIFIER CATEGORIZATION RESULTS ===")
    print(f"Entities modified: {stats['entities_fixed']:,}")
    print(f"Total identifiers processed: {stats['total_identifiers_processed']:,}")
    print()
    print("Identifier movements:")
    print(f"  P60 → P61 (Wikidata QIDs): {stats['p60_to_p61']:,}")
    print(f"  P60 → P62 (Geni IDs): {stats['p60_to_p62']:,}")
    print(f"  P60 kept (UUIDs/other): {stats['p60_kept']:,}")
    
    return stats

def verify_categorization():
    """Verify the categorization worked correctly"""
    print()
    print("=== VERIFICATION ===")
    
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['gaiad_processing_db']
    collection = db['entities']
    
    # Sample some entities to verify correct categorization
    p61_sample = collection.find_one({'properties.P61': {'$exists': True}})
    p62_sample = collection.find_one({'properties.P62': {'$exists': True}})
    p60_sample = collection.find_one({'properties.P60': {'$exists': True}})
    
    print("Sample verification:")
    
    if p61_sample:
        p61_values = [claim.get('value') for claim in p61_sample['properties']['P61']]
        print(f"  P61 sample values: {p61_values[:3]} (should be Wikidata QIDs)")
    
    if p62_sample:
        p62_values = [claim.get('value') for claim in p62_sample['properties']['P62']]
        print(f"  P62 sample values: {p62_values[:3]} (should be Geni IDs)")
    
    if p60_sample:
        p60_values = [claim.get('value') for claim in p60_sample['properties']['P60']]
        print(f"  P60 sample values: {p60_values[:3]} (should be UUIDs)")
    
    client.close()

def main():
    # Fix the incorrect P41 conversions
    stats = fix_p41_conversions()
    
    # Verify the fix worked
    verify_categorization()
    
    print()
    if stats['entities_fixed'] > 0:
        print("✅ SUCCESS: P41 identifier categorization fixed!")
        print(f"Fixed {stats['entities_fixed']:,} entities with proper identifier categorization")
    else:
        print("No entities needed fixing")

if __name__ == '__main__':
    main()