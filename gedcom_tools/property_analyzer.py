#!/usr/bin/env python3
"""
Property Analyzer for MongoDB Gaiad Database
Analyzes what properties actually exist and provides accurate counts
"""

import pymongo
from collections import Counter, defaultdict

def analyze_properties():
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['gaiad_processing_db']
    collection = db['entities']
    
    print("=== GAIAD DATABASE PROPERTY ANALYSIS ===")
    print()
    
    # Get total count
    total = collection.count_documents({})
    print(f"Total entities: {total:,}")
    print()
    
    # Manual property counting (more reliable)
    property_counts = Counter()
    sex_values = Counter()
    wikidata_count = 0
    geni_count = 0
    birth_date_count = 0
    death_date_count = 0
    no_identifier_count = 0
    reference_numbers_count = 0
    
    print("Analyzing all entities...")
    processed = 0
    
    for entity in collection.find():
        processed += 1
        if processed % 10000 == 0:
            print(f"  Processed {processed:,} entities...")
        
        properties = entity.get('properties', {})
        
        # Count all properties
        for prop_id in properties.keys():
            property_counts[prop_id] += 1
        
        # Specific analysis
        if 'P44' in properties:
            wikidata_count += 1
            
        if 'P43' in properties:
            geni_count += 1
            
        if 'P55' in properties:
            # Analyze sex values
            for claim in properties['P55']:
                value = claim.get('value')
                if isinstance(value, dict) and 'id' in value:
                    sex_values[value['id']] += 1
                elif isinstance(value, str):
                    sex_values[value] += 1
                    
        if 'P56' in properties:
            birth_date_count += 1
            
        if 'P57' in properties:
            death_date_count += 1
            
        if 'P39' in properties:
            for claim in properties['P39']:
                if claim.get('value') == 'Q153720':
                    no_identifier_count += 1
                    break
                    
        # Check for REFERENCE_NUMBERS in descriptions
        descriptions = entity.get('descriptions', {})
        for desc in descriptions.values():
            if 'REFERENCE_NUMBERS' in desc:
                reference_numbers_count += 1
                break
    
    print(f"  Processed {processed:,} entities total")
    print()
    
    # Results
    print("=== PROPERTY COUNTS ===")
    print("Top 20 most common properties:")
    for prop, count in property_counts.most_common(20):
        print(f"  {prop}: {count:,} entities ({count/total*100:.1f}%)")
    
    print()
    print("=== SPECIFIC ANALYSIS ===")
    print(f"Wikidata QIDs (P44): {wikidata_count:,} entities")
    print(f"Geni IDs (P43): {geni_count:,} entities") 
    print(f"Sex properties (P55): {property_counts['P55']:,} entities")
    print(f"Birth dates (P56): {birth_date_count:,} entities")
    print(f"Death dates (P57): {death_date_count:,} entities")
    print(f"'No identifiers' (P39=Q153720): {no_identifier_count:,} entities")
    print(f"REFERENCE_NUMBERS in descriptions: {reference_numbers_count:,} entities")
    
    if sex_values:
        print()
        print("Sex value breakdown:")
        for value, count in sex_values.most_common():
            print(f"  {value}: {count:,}")
    
    # Check for unprocessed properties
    print()
    print("=== UNPROCESSED PROPERTIES CHECK ===")
    unprocessed = ['P11', 'P7', 'P8', 'P41']
    for prop in unprocessed:
        count = property_counts.get(prop, 0)
        if count > 0:
            print(f"WARNING: {prop} still exists ({count:,} entities) - not fully processed!")
        else:
            print(f"OK: {prop} fully processed (0 entities)")
    
    client.close()

if __name__ == "__main__":
    analyze_properties()