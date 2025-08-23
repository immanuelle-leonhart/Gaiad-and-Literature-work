#!/usr/bin/env python3
"""
Debug property conversion to understand why properties are being filtered out
"""
import pymongo
import sys
import os

# Add gedcom_tools to path
sys.path.append('gedcom_tools')
from mongodb_to_wikibase_xml import WikibaseXMLExporter

def debug_property_conversion():
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['gaiad_processing_db']
    collection = db['entities']
    
    # Get Q1787
    entity = collection.find_one({'qid': 'Q1787'})
    if not entity:
        print("Q1787 not found!")
        return
    
    print("=== DEBUGGING Q1787 PROPERTY CONVERSION ===")
    print()
    
    # Test the conversion
    exporter = WikibaseXMLExporter()
    
    print("Original MongoDB properties:")
    properties = entity.get('properties', {})
    for prop_id, claims in properties.items():
        print(f"  {prop_id}: {len(claims)} claims")
        for i, claim in enumerate(claims):
            claim_type = claim.get('type', 'MISSING_TYPE')
            value = claim.get('value')
            print(f"    Claim {i+1}: type={claim_type}")
            print(f"             value={repr(value)}")
    
    print()
    print("Converting to Wikibase JSON...")
    
    # Convert to wikibase JSON
    try:
        wikibase_json = exporter.entity_to_wikibase_json(entity)
        
        print("Converted Wikibase JSON claims:")
        if 'claims' in wikibase_json:
            for prop_id, claims in wikibase_json['claims'].items():
                print(f"  {prop_id}: {len(claims)} claims converted")
                for i, claim in enumerate(claims):
                    if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
                        value = claim['mainsnak']['datavalue'].get('value')
                        data_type = claim['mainsnak']['datavalue'].get('type')
                        print(f"    Claim {i+1}: type={data_type}")
                        print(f"             value={repr(value)}")
                    else:
                        print(f"    Claim {i+1}: MISSING datavalue!")
        else:
            print("  NO CLAIMS IN CONVERTED JSON!")
            
        # Check what properties are missing
        original_props = set(properties.keys())
        converted_props = set(wikibase_json.get('claims', {}).keys())
        missing_props = original_props - converted_props
        
        if missing_props:
            print()
            print(f"MISSING PROPERTIES: {missing_props}")
            
            # Debug why each missing property was filtered out
            for missing_prop in missing_props:
                print(f"\nDEBUGGING {missing_prop}:")
                claims = properties[missing_prop]
                for i, claim in enumerate(claims):
                    claim_type = claim.get('type', 'MISSING_TYPE')
                    value = claim.get('value')
                    print(f"  Claim {i+1}:")
                    print(f"    Type: {claim_type}")
                    print(f"    Value: {repr(value)}")
                    print(f"    Value type: {type(value)}")
                    
                    # Test the filtering conditions
                    if claim_type in ["wikibase-item", "wikibase-entityid"]:
                        if isinstance(value, dict) and 'id' in value:
                            print("    -> Should pass wikibase-entityid dict test")
                        elif isinstance(value, str) and value.startswith('Q'):
                            print("    -> Should pass wikibase-entityid string test")
                        else:
                            print("    -> WOULD BE FILTERED: Invalid wikibase-item value")
                    elif claim_type == "monolingualtext":
                        if isinstance(value, dict) and 'text' in value and 'language' in value:
                            print("    -> Should pass monolingualtext test")
                        else:
                            print("    -> WOULD BE FILTERED: Invalid monolingualtext value")
                    elif claim_type == "external-id":
                        print("    -> Should pass external-id test")
                    elif claim_type == "time":
                        print("    -> Should pass time test")
                    else:
                        print("    -> Should pass string/other test")
        else:
            print()
            print("SUCCESS: All properties converted!")
            
    except Exception as e:
        print(f"ERROR during conversion: {e}")
        import traceback
        traceback.print_exc()
    
    client.close()
    exporter.close()

if __name__ == "__main__":
    debug_property_conversion()