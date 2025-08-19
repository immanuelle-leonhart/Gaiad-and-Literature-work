#!/usr/bin/env python3
"""
Debug XML parser to understand why entities aren't being found
"""

import xml.etree.ElementTree as ET
import json

def debug_xml_file(xml_file_path):
    """Debug a single XML file"""
    print(f"Debugging: {xml_file_path}")
    
    try:
        with open(xml_file_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    try:
        root = ET.fromstring(xml_content)
        print(f"Successfully parsed XML")
        
        page_count = 0
        entity_count = 0
        
        # Find all page elements (ignore namespace)
        for page in root.iter():
            if page.tag.endswith('page'):
                page_count += 1
                
                # Get title
                title_elem = page.find('title')
                if title_elem is None:
                    print(f"Page {page_count}: No title element")
                    continue
                    
                title = title_elem.text
                if not title:
                    print(f"Page {page_count}: Empty title")
                    continue
                
                print(f"Page {page_count}: Title = '{title}'")
                
                # Check if this looks like an entity
                if title.startswith('Item:Q') or title.startswith('Property:P'):
                    entity_count += 1
                    print(f"  -> This is an entity!")
                    
                    # Check for revision content
                    revision = page.find('revision')
                    if revision is None:
                        print(f"  -> No revision found")
                        continue
                        
                    text_elem = revision.find('text')
                    if text_elem is None:
                        print(f"  -> No text element in revision")
                        continue
                        
                    if text_elem.text is None:
                        print(f"  -> Text element is None")
                        continue
                    
                    print(f"  -> Text content length: {len(text_elem.text)}")
                    print(f"  -> First 100 chars: {text_elem.text[:100]}")
                    
                    # Try to parse as JSON
                    try:
                        entity_data = json.loads(text_elem.text)
                        print(f"  -> Successfully parsed JSON!")
                        print(f"  -> Keys: {list(entity_data.keys())}")
                    except json.JSONDecodeError as e:
                        print(f"  -> JSON parse error: {e}")
                    
                    if entity_count >= 3:  # Only debug first 3 entities
                        break
                        
                if page_count >= 10:  # Only check first 10 pages
                    break
        
        print(f"\nSummary:")
        print(f"Total pages checked: {page_count}")
        print(f"Entities found: {entity_count}")
        
    except ET.ParseError as e:
        print(f"XML Parse Error: {e}")

if __name__ == "__main__":
    debug_xml_file("xml_imports/evolutionism_export_part_1.xml")