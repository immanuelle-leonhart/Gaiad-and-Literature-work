#!/usr/bin/env python3
"""
Test single entity export to verify the fix works
"""
import pymongo
import sys
import os
import xml.etree.ElementTree as ET

# Add gedcom_tools to path
sys.path.append('gedcom_tools')
from mongodb_to_wikibase_xml import WikibaseXMLExporter

def test_single_entity_export():
    """Test exporting Q1787 to verify property export works correctly"""
    print("=== TESTING SINGLE ENTITY EXPORT (Q1787) ===")
    print()
    
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['gaiad_processing_db']
    collection = db['entities']
    
    # Get Q1787
    entity = collection.find_one({'qid': 'Q1787'})
    if not entity:
        print("ERROR: Q1787 not found!")
        return False
    
    # Create exporter
    exporter = WikibaseXMLExporter(output_dir='test_export')
    
    # Create single file export with just Q1787
    output_file = 'test_export/q1787_test.xml'
    
    print(f"Creating test export: {output_file}")
    
    # Create XML structure
    root = exporter.create_xml_header()
    
    # Add Q1787 as a page
    exporter.create_page_element(entity, root)
    
    # Write to file
    tree = ET.ElementTree(root)
    ET.indent(tree, space='  ', level=0)
    
    # Create directory if needed
    os.makedirs('test_export', exist_ok=True)
    
    with open(output_file, 'wb') as f:
        tree.write(f, encoding='utf-8', xml_declaration=True)
    
    print(f"SUCCESS: Test export created: {output_file}")
    
    # Verify the file content
    with open(output_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"File size: {len(content):,} characters")
    
    # Check for properties
    properties_found = []
    for prop in ['P3', 'P4', 'P5', 'P55', 'P39', 'P61']:
        if f'"{prop}"' in content:
            properties_found.append(prop)
    
    print(f"Properties found in export: {properties_found}")
    
    # Check for valid claim IDs (should be UUIDs, not bad format)
    if 'Q1787_P39_' in content:
        print("ERROR: Bad claim IDs still present!")
        return False
    else:
        print("SUCCESS: No bad claim IDs found")
    
    # Check for proper UUID format claim IDs
    import re
    uuid_pattern = r'Q1787\$[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}'
    uuid_matches = re.findall(uuid_pattern, content)
    
    print(f"SUCCESS: Found {len(uuid_matches)} proper UUID claim IDs")
    if uuid_matches:
        print(f"  Examples: {uuid_matches[:3]}")
    
    client.close()
    exporter.close()
    
    if len(properties_found) >= 6:  # Should find all 6 properties
        print()
        print("SUCCESS: Property export test passed!")
        print("All properties are being exported correctly.")
        print()
        print("If you're still seeing blank properties in Wikibase, the issue is likely:")
        print("1. You need to regenerate your export files with the current fixed version")
        print("2. The old cached/imported data in Wikibase needs to be updated")
        print("3. There may be an issue with the import process, not the export")
        return True
    else:
        print()
        print("ERROR: Property export test failed!")
        print(f"Only found {len(properties_found)} properties, expected 6")
        return False

if __name__ == "__main__":
    success = test_single_entity_export()
    exit(0 if success else 1)