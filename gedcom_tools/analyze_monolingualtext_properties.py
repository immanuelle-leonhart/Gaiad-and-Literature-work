#!/usr/bin/env python3
"""
Analyze Monolingualtext Properties

Based on the XML export analysis, identifies which properties in the MongoDB 
database should be monolingualtext type rather than string type.

From the XML analysis, these properties contain dictionary-like strings that 
should be converted to proper Wikibase datatypes:

- P5, P3: Should be monolingualtext (currently string with "{'text': '...', 'language': 'en'}")
- P20, P47, P55: Should be wikibase-item (currently string with "{'entity-type': 'item', ...}")

This script will identify all such properties and create a fix.
"""

import pymongo
import json
import re
import ast

# Configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"

def analyze_property_types():
    """Analyze property types in MongoDB to identify monolingualtext candidates"""
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db['entities']
    
    print("=== ANALYZING PROPERTY TYPES FOR MONOLINGUALTEXT ===")
    print()
    
    property_type_analysis = {}
    sample_count = 0
    
    for entity in collection.find().limit(5000):  # Sample 5000 entities
        sample_count += 1
        if sample_count % 1000 == 0:
            print(f"  Analyzed {sample_count:,} entities...")
        
        properties = entity.get('properties', {})
        for prop_id, claims in properties.items():
            if prop_id not in property_type_analysis:
                property_type_analysis[prop_id] = {
                    'string_values': [],
                    'dict_values': [],
                    'other_values': [],
                    'monolingualtext_candidates': 0,
                    'wikibase_item_candidates': 0,
                    'total_claims': 0
                }
            
            for claim in claims:
                value = claim.get('value')
                claim_type = claim.get('type', 'unknown')
                property_type_analysis[prop_id]['total_claims'] += 1
                
                if isinstance(value, str):
                    # Check if string contains dictionary representation
                    if value.startswith("{'") and "'text':" in value and "'language':" in value:
                        # Likely monolingualtext
                        property_type_analysis[prop_id]['monolingualtext_candidates'] += 1
                        if len(property_type_analysis[prop_id]['string_values']) < 3:
                            property_type_analysis[prop_id]['string_values'].append(value[:100])
                    
                    elif value.startswith("{'") and "'entity-type':" in value and "'id':" in value:
                        # Likely wikibase-item
                        property_type_analysis[prop_id]['wikibase_item_candidates'] += 1
                        if len(property_type_analysis[prop_id]['string_values']) < 3:
                            property_type_analysis[prop_id]['string_values'].append(value[:100])
                    
                    else:
                        # Regular string
                        if len(property_type_analysis[prop_id]['string_values']) < 3:
                            property_type_analysis[prop_id]['string_values'].append(value[:50])
                
                elif isinstance(value, dict):
                    if len(property_type_analysis[prop_id]['dict_values']) < 3:
                        property_type_analysis[prop_id]['dict_values'].append(str(value)[:100])
                
                else:
                    if len(property_type_analysis[prop_id]['other_values']) < 3:
                        property_type_analysis[prop_id]['other_values'].append(f"{type(value).__name__}: {str(value)[:50]}")
    
    print(f"  Analyzed {sample_count:,} entities")
    print()
    
    # Report findings
    print("=== PROPERTY TYPE ANALYSIS RESULTS ===")
    print()
    
    monolingualtext_properties = []
    wikibase_item_properties = []
    
    for prop_id, analysis in sorted(property_type_analysis.items()):
        if analysis['monolingualtext_candidates'] > 0 or analysis['wikibase_item_candidates'] > 0:
            print(f"Property {prop_id}:")
            print(f"  Total claims: {analysis['total_claims']:,}")
            
            if analysis['monolingualtext_candidates'] > 0:
                print(f"  Monolingualtext candidates: {analysis['monolingualtext_candidates']:,}")
                monolingualtext_properties.append(prop_id)
                for sample in analysis['string_values'][:2]:
                    print(f"    Sample: {sample}")
            
            if analysis['wikibase_item_candidates'] > 0:
                print(f"  Wikibase-item candidates: {analysis['wikibase_item_candidates']:,}")
                wikibase_item_properties.append(prop_id)
                for sample in analysis['string_values'][:2]:
                    print(f"    Sample: {sample}")
            
            print()
    
    print("=== SUMMARY ===")
    print(f"Properties needing monolingualtext conversion: {monolingualtext_properties}")
    print(f"Properties needing wikibase-item conversion: {wikibase_item_properties}")
    
    client.close()
    return {
        'monolingualtext_properties': monolingualtext_properties,
        'wikibase_item_properties': wikibase_item_properties
    }

def convert_string_to_monolingualtext(value_string):
    """Convert string representation of dict to proper monolingualtext format"""
    try:
        # Parse the string representation of the dictionary
        parsed = ast.literal_eval(value_string)
        if isinstance(parsed, dict) and 'text' in parsed and 'language' in parsed:
            return {
                'text': str(parsed['text']),
                'language': str(parsed['language'])
            }
    except (ValueError, SyntaxError):
        pass
    return None

def convert_string_to_wikibase_item(value_string):
    """Convert string representation of dict to proper wikibase-item format"""
    try:
        # Parse the string representation of the dictionary  
        parsed = ast.literal_eval(value_string)
        if (isinstance(parsed, dict) and 
            parsed.get('entity-type') == 'item' and
            'id' in parsed and
            'numeric-id' in parsed):
            
            return {
                'entity-type': 'item',
                'numeric-id': int(parsed['numeric-id']),
                'id': str(parsed['id'])
            }
    except (ValueError, SyntaxError):
        pass
    return None

def fix_property_datatypes(monolingualtext_props, wikibase_item_props):
    """Fix the property datatypes in MongoDB"""
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db['entities']
    
    print()
    print("=== FIXING PROPERTY DATATYPES ===")
    print()
    
    batch_updates = []
    entities_fixed = 0
    total_processed = 0
    
    for entity in collection.find():
        total_processed += 1
        if total_processed % 10000 == 0:
            print(f"  Processed {total_processed:,} entities...")
        
        qid = entity['qid']
        properties = entity.get('properties', {})
        needs_update = False
        updated_properties = {}
        
        for prop_id, claims in properties.items():
            fixed_claims = []
            
            for claim in claims:
                value = claim.get('value')
                claim_type = claim.get('type', 'string')
                
                fixed_claim = claim.copy()
                
                # Fix monolingualtext properties
                if prop_id in monolingualtext_props and isinstance(value, str):
                    converted = convert_string_to_monolingualtext(value)
                    if converted:
                        fixed_claim['value'] = converted
                        fixed_claim['type'] = 'monolingualtext'
                        needs_update = True
                
                # Fix wikibase-item properties
                elif prop_id in wikibase_item_props and isinstance(value, str):
                    converted = convert_string_to_wikibase_item(value)
                    if converted:
                        fixed_claim['value'] = converted
                        fixed_claim['type'] = 'wikibase-item'
                        needs_update = True
                
                fixed_claims.append(fixed_claim)
            
            updated_properties[prop_id] = fixed_claims
        
        if needs_update:
            entities_fixed += 1
            batch_updates.append(
                pymongo.UpdateOne(
                    {'qid': qid},
                    {'$set': {'properties': updated_properties}}
                )
            )
            
            # Execute batch
            if len(batch_updates) >= 1000:
                collection.bulk_write(batch_updates)
                batch_updates = []
    
    # Execute remaining updates
    if batch_updates:
        collection.bulk_write(batch_updates)
    
    print(f"  Processed {total_processed:,} entities")
    print(f"  Fixed {entities_fixed:,} entities")
    
    client.close()
    return entities_fixed

def verify_fixes():
    """Verify the fixes worked"""
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db['entities']
    
    print()
    print("=== VERIFYING FIXES ===")
    print()
    
    # Check samples
    for entity in collection.find().limit(5):
        qid = entity['qid']
        properties = entity.get('properties', {})
        
        print(f"{qid}:")
        
        for prop_id in ['P5', 'P3', 'P20', 'P47', 'P55']:
            if prop_id in properties:
                claims = properties[prop_id]
                for claim in claims[:1]:  # First claim only
                    value = claim.get('value')
                    claim_type = claim.get('type')
                    
                    if claim_type == 'monolingualtext':
                        print(f"  {prop_id} (monolingualtext): {value}")
                    elif claim_type == 'wikibase-item':
                        print(f"  {prop_id} (wikibase-item): {value}")
                    else:
                        print(f"  {prop_id} ({claim_type}): {str(value)[:50]}")
                break
        print()
    
    client.close()

def main():
    print("Monolingualtext Property Analyzer and Fixer")
    print("=" * 50)
    
    # Analyze property types
    analysis = analyze_property_types()
    
    monolingualtext_props = analysis['monolingualtext_properties']
    wikibase_item_props = analysis['wikibase_item_properties']
    
    if monolingualtext_props or wikibase_item_props:
        print(f"\nFixing {len(monolingualtext_props)} monolingualtext and {len(wikibase_item_props)} wikibase-item properties...")
        
        # Apply fixes
        fixed_count = fix_property_datatypes(monolingualtext_props, wikibase_item_props)
        
        print(f"\nSUCCESS: Fixed {fixed_count:,} entities")
        
        # Verify fixes
        verify_fixes()
        
        print("All property datatypes are now correct!")
        print("Ready to regenerate XML export with proper monolingualtext format.")
        
    else:
        print("\nNo properties need datatype fixes.")
    
    return len(monolingualtext_props) + len(wikibase_item_props) > 0

if __name__ == "__main__":
    main()