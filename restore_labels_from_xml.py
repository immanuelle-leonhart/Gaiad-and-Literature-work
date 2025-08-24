#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import json
import pymongo
import os
from collections import defaultdict

def extract_labels_from_xml(xml_file):
    """Extract all entity labels from XML export file"""
    print(f"Parsing {xml_file}...")
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error parsing {xml_file}: {e}")
        return {}
    
    labels_data = {}
    parsed_entities = 0
    
    for page in root.findall('.//page'):
        parsed_entities += 1
        if parsed_entities % 5000 == 0:
            print(f"  Processed {parsed_entities} entities...")
        
        title_elem = page.find('title')
        if title_elem is None or not title_elem.text:
            continue
            
        title = title_elem.text
        if not title.startswith('Item:Q'):
            continue
            
        qid = title.replace('Item:', '')
        
        revision = page.find('revision')
        if revision is None:
            continue
            
        text_elem = revision.find('text')
        if text_elem is None or text_elem.text is None:
            continue
            
        try:
            entity_data = json.loads(text_elem.text)
            
            if entity_data.get('type') == 'item':
                # Extract labels, descriptions, aliases
                entity_info = {}
                
                if 'labels' in entity_data and entity_data['labels']:
                    entity_info['labels'] = entity_data['labels']
                    
                if 'descriptions' in entity_data and entity_data['descriptions']:
                    entity_info['descriptions'] = entity_data['descriptions']
                    
                if 'aliases' in entity_data and entity_data['aliases']:
                    entity_info['aliases'] = entity_data['aliases']
                
                if entity_info:  # Only store if has any label/description/alias data
                    labels_data[qid] = entity_info
            
        except json.JSONDecodeError:
            continue
    
    print(f"  Extracted label data for {len(labels_data)} entities from {xml_file}")
    return labels_data

def restore_labels_to_mongodb(labels_data):
    """Restore labels to entities missing them in MongoDB"""
    print(f"Connecting to MongoDB...")
    
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['gaiad_processing_db']
    collection = db['entities']
    
    restored_count = 0
    not_found_count = 0
    already_has_labels_count = 0
    
    for qid, label_info in labels_data.items():
        entity = collection.find_one({'qid': qid})
        if not entity:
            not_found_count += 1
            continue
            
        # Skip redirect entities
        if 'redirect' in entity.get('properties', {}):
            continue
            
        # Check if entity already has labels
        current_labels = entity.get('labels', {})
        current_descriptions = entity.get('descriptions', {})
        current_aliases = entity.get('aliases', {})
        
        if current_labels or current_descriptions or current_aliases:
            already_has_labels_count += 1
            continue
        
        # Restore the label data
        update_data = {}
        
        if 'labels' in label_info:
            update_data['labels'] = label_info['labels']
            
        if 'descriptions' in label_info:
            update_data['descriptions'] = label_info['descriptions']
            
        if 'aliases' in label_info:
            update_data['aliases'] = label_info['aliases']
        
        if update_data:
            result = collection.update_one(
                {'qid': qid},
                {'$set': update_data}
            )
            
            if result.modified_count > 0:
                restored_count += 1
                if restored_count % 1000 == 0:
                    print(f"  Restored labels to {restored_count} entities...")
    
    client.close()
    
    print(f"Label restoration complete:")
    print(f"  Labels restored: {restored_count}")
    print(f"  Entities not found: {not_found_count}")
    print(f"  Already had labels: {already_has_labels_count}")
    
    return restored_count

def main():
    print("=== LABEL RESTORATION FROM XML EXPORTS ===")
    print()
    
    # Use the complete export file first
    xml_file = "exports_with_labels/gaiad_wikibase_complete_export.xml"
    
    if not os.path.exists(xml_file):
        print(f"XML file {xml_file} not found!")
        return
    
    print(f"Using XML export: {xml_file}")
    print(f"File size: {os.path.getsize(xml_file) / (1024 * 1024):.1f} MB")
    print()
    
    # Extract label data from XML
    labels_data = extract_labels_from_xml(xml_file)
    
    if not labels_data:
        print("No label data found in XML file!")
        return
    
    print(f"Found label data for {len(labels_data):,} entities")
    
    # Test specific entity mentioned by user
    if 'Q85814' in labels_data:
        print(f"Q85814 labels found: {list(labels_data['Q85814'].get('labels', {}).keys())}")
    
    # Restore labels to MongoDB
    print()
    restored = restore_labels_to_mongodb(labels_data)
    
    if restored > 0:
        print(f"\nSUCCESS: Restored labels to {restored} entities!")
    else:
        print("\nNo labels were restored.")

if __name__ == '__main__':
    main()