#!/usr/bin/env python3
"""
Debug XML generation to see if the issue is in XML export
"""
import pymongo
import sys
import os
import xml.etree.ElementTree as ET

# Add gedcom_tools to path
sys.path.append('gedcom_tools')
from mongodb_to_wikibase_xml import WikibaseXMLExporter

def debug_xml_generation():
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['gaiad_processing_db']
    collection = db['entities']
    
    # Get Q1787
    entity = collection.find_one({'qid': 'Q1787'})
    if not entity:
        print("Q1787 not found!")
        return
    
    print("=== DEBUGGING Q1787 XML GENERATION ===")
    print()
    
    # Test the full XML export process
    exporter = WikibaseXMLExporter()
    
    print("1. Converting to Wikibase JSON...")
    wikibase_json = exporter.entity_to_wikibase_json(entity)
    
    print("2. Creating XML page element...")
    root = ET.Element('mediawiki')
    exporter.create_page_element(entity, root)
    
    print("3. Extracting XML content...")
    page_element = root.find('.//page')
    if page_element is not None:
        text_element = page_element.find('.//text')
        if text_element is not None:
            xml_content = text_element.text
            
            print("4. Analyzing XML JSON content...")
            if xml_content:
                # Check if the JSON content in XML has the properties
                if '"claims"' in xml_content:
                    print("   JSON has claims section")
                    
                    # Check for specific properties
                    for prop in ['P3', 'P4', 'P5', 'P55', 'P39', 'P61']:
                        if f'"{prop}"' in xml_content:
                            print(f"   OK {prop} found in XML JSON")
                        else:
                            print(f"   ERROR {prop} MISSING from XML JSON")
                    
                    # Check for problematic claim IDs
                    if 'Q1787_P39_' in xml_content:
                        print("   WARNING: Bad claim IDs found in XML")
                        # Show a snippet of the P39 section
                        start = xml_content.find('"P39"')
                        if start != -1:
                            end = xml_content.find(']', start) + 1
                            p39_section = xml_content[start:end]
                            print(f"   P39 section: {p39_section[:200]}...")
                    else:
                        print("   OK No bad claim IDs in XML")
                    
                    # Show first 1000 chars of the XML JSON
                    print()
                    print("First 1000 chars of XML JSON content:")
                    print(xml_content[:1000])
                    print("...")
                    
                else:
                    print("   ERROR NO claims section in XML JSON!")
                    print(f"   XML content length: {len(xml_content)}")
                    print("   First 500 chars:")
                    print(xml_content[:500])
            else:
                print("   ERROR NO XML content generated!")
        else:
            print("   ERROR NO text element in XML!")
    else:
        print("   ERROR NO page element in XML!")
    
    client.close()
    exporter.close()

if __name__ == "__main__":
    debug_xml_generation()