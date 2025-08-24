#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import json
import pymongo
import os
import glob
import csv
from collections import defaultdict
import uuid

def find_numbered_xml_files():
    """Find all numbered XML files in xml_imports directory"""
    xml_dir = "xml_imports"
    if not os.path.exists(xml_dir):
        print(f"Directory {xml_dir} not found!")
        return []
    
    # Look for numbered XML files - correct pattern for the actual files
    pattern = os.path.join(xml_dir, "evolutionism_export_part_*.xml")
    files = glob.glob(pattern)
    
    # Sort by part number
    def extract_part_number(filename):
        basename = os.path.basename(filename)
        # Handle: evolutionism_export_part_26.xml -> extract 26
        if 'part_' in basename:
            part_str = basename.split('part_')[1].replace('.xml', '')
            try:
                return int(part_str)
            except ValueError:
                return 0
        return 0
    
    files.sort(key=extract_part_number)
    return files

def parse_xml_for_labels(xml_file):
    """Extract labels and properties from XML file"""
    print(f"Parsing {xml_file}...")
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error parsing {xml_file}: {e}")
        return {}
    
    entities_data = {}
    parsed_count = 0
    
    # Handle namespaced XML - register namespace and use it
    ns = {'mw': 'http://www.mediawiki.org/xml/export-0.11/'}
    for page in root.findall('.//mw:page', ns):
        parsed_count += 1
        
        title_elem = page.find('mw:title', ns)
        if title_elem is None or not title_elem.text:
            continue
            
        title = title_elem.text
        if not title.startswith('Item:Q'):
            continue
            
        qid = title.replace('Item:', '')
        
        # Also check namespace to ensure it's an Item (namespace 860)
        ns_elem = page.find('mw:ns', ns)
        if ns_elem is not None and ns_elem.text != '860':
            continue
        
        revision = page.find('mw:revision', ns)
        if revision is None:
            continue
            
        text_elem = revision.find('mw:text', ns)
        if text_elem is None or text_elem.text is None:
            continue
            
        try:
            entity_data = json.loads(text_elem.text)
            
            if entity_data.get('type') == 'item':
                entity_info = {'qid': qid}
                
                # Extract labels
                if 'labels' in entity_data and entity_data['labels']:
                    entity_info['labels'] = entity_data['labels']
                    
                # Extract descriptions
                if 'descriptions' in entity_data and entity_data['descriptions']:
                    entity_info['descriptions'] = entity_data['descriptions']
                    
                # Extract aliases
                if 'aliases' in entity_data and entity_data['aliases']:
                    entity_info['aliases'] = entity_data['aliases']
                
                # Extract ALL claims/properties
                if 'claims' in entity_data and entity_data['claims']:
                    entity_info['claims'] = entity_data['claims']
                
                # Only store if has labels OR properties
                if ('labels' in entity_info or 'claims' in entity_info):
                    entities_data[qid] = entity_info
                    
        except json.JSONDecodeError:
            continue
    
    print(f"  Extracted data for {len(entities_data)} entities from {xml_file}")
    return entities_data

def convert_deprecated_identifiers(claims):
    """Convert deprecated identifier properties P41, P43, P44 to new format"""
    converted_claims = {}
    
    # Property mapping: old_prop -> new_prop
    identifier_mapping = {
        'P41': 'P60',  # REFN -> UUID
        'P43': 'P62',  # Old Geni -> New Geni  
        'P44': 'P61'   # Old Wikidata -> New Wikidata
    }
    
    for prop_id, prop_claims in claims.items():
        if prop_id in identifier_mapping:
            # Convert to new property ID
            new_prop_id = identifier_mapping[prop_id]
            new_claims = []
            
            for claim in prop_claims:
                # Convert claim structure from old format to new format
                new_claim = {
                    'value': claim['mainsnak']['datavalue']['value'],
                    'type': 'external-id',
                    'claim_id': f"{claim['id'].split('$')[0]}_{new_prop_id}_{claim['mainsnak']['datavalue']['value']}"
                }
                new_claims.append(new_claim)
            
            converted_claims[new_prop_id] = new_claims
        else:
            # Convert other properties from Wikibase format to MongoDB format
            converted_props = []
            for claim in prop_claims:
                if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
                    datavalue = claim['mainsnak']['datavalue']
                    
                    if datavalue['type'] == 'string':
                        new_claim = {
                            'value': datavalue['value'],
                            'type': 'external-id' if prop_id.startswith('P6') else 'string',
                            'claim_id': claim['id']
                        }
                    elif datavalue['type'] == 'wikibase-entityid':
                        new_claim = {
                            'value': datavalue['value']['id'],
                            'type': 'wikibase-item',
                            'claim_id': claim['id']
                        }
                    elif datavalue['type'] == 'time':
                        new_claim = {
                            'value': {
                                'time': datavalue['value']['time'],
                                'precision': datavalue['value']['precision'],
                                'calendar': datavalue['value']['calendarmodel']
                            },
                            'type': 'time',
                            'claim_id': claim['id']
                        }
                    elif datavalue['type'] == 'monolingualtext':
                        new_claim = {
                            'value': {
                                'text': datavalue['value']['text'],
                                'language': datavalue['value']['language']
                            },
                            'type': 'monolingualtext',
                            'claim_id': claim['id']
                        }
                    else:
                        # Default handling
                        new_claim = {
                            'value': datavalue['value'],
                            'type': 'unknown',
                            'claim_id': claim['id']
                        }
                    
                    converted_props.append(new_claim)
            
            if converted_props:
                converted_claims[prop_id] = converted_props
    
    return converted_claims

def restore_to_mongodb(all_entities_data):
    """Restore labels and properties to MongoDB entities"""
    print(f"Connecting to MongoDB...")
    
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['gaiad_processing_db']
    collection = db['entities']
    
    restored_count = 0
    not_found_count = 0
    already_has_labels_count = 0
    marked_for_batch = []
    
    total_entities = len(all_entities_data)
    processed = 0
    
    for qid, xml_data in all_entities_data.items():
        processed += 1
        if processed % 1000 == 0:
            print(f"  Processing {processed}/{total_entities} entities...")
        
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
        
        # Prepare update data
        update_data = {}
        
        if 'labels' in xml_data:
            update_data['labels'] = xml_data['labels']
            
        if 'descriptions' in xml_data:
            update_data['descriptions'] = xml_data['descriptions']
            
        if 'aliases' in xml_data:
            update_data['aliases'] = xml_data['aliases']
        
        # Convert and merge properties
        if 'claims' in xml_data:
            converted_claims = convert_deprecated_identifiers(xml_data['claims'])
            
            # Merge with existing properties
            current_properties = entity.get('properties', {})
            for prop_id, claims in converted_claims.items():
                if prop_id in current_properties:
                    # Merge claims, avoiding duplicates
                    existing_values = set()
                    for existing_claim in current_properties[prop_id]:
                        existing_values.add(str(existing_claim.get('value')))
                    
                    for new_claim in claims:
                        if str(new_claim['value']) not in existing_values:
                            current_properties[prop_id].append(new_claim)
                else:
                    current_properties[prop_id] = claims
            
            update_data['properties'] = current_properties
        
        # Mark entity as restored for batch processing
        update_data['batch_processing'] = {
            'restored_from_xml': True,
            'restored_date': '2025-01-24',
            'identifiers_converted': True
        }
        
        if update_data:
            result = collection.update_one(
                {'qid': qid},
                {'$set': update_data}
            )
            
            if result.modified_count > 0:
                restored_count += 1
                marked_for_batch.append({
                    'qid': qid,
                    'labels_restored': 'labels' in xml_data,
                    'properties_restored': 'claims' in xml_data,
                    'labels_count': len(xml_data.get('labels', {})),
                    'properties_count': len(xml_data.get('claims', {}))
                })
    
    client.close()
    
    print(f"Restoration complete:")
    print(f"  Entities restored: {restored_count}")
    print(f"  Entities not found: {not_found_count}")
    print(f"  Already had labels: {already_has_labels_count}")
    
    return marked_for_batch

def export_unlabeled_entities_csv():
    """Export all unlabeled entities to CSV for batch processing"""
    print(f"Exporting unlabeled entities to CSV...")
    
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['gaiad_processing_db']
    collection = db['entities']
    
    unlabeled_entities = []
    total_checked = 0
    
    for entity in collection.find():
        total_checked += 1
        if total_checked % 10000 == 0:
            print(f"  Checked {total_checked:,} entities...")
        
        # Skip redirect entities
        if 'redirect' in entity.get('properties', {}):
            continue
        
        labels = entity.get('labels', {})
        descriptions = entity.get('descriptions', {})
        aliases = entity.get('aliases', {})
        
        # Find entities with no labels/descriptions/aliases
        if not labels and not descriptions and not aliases:
            properties = entity.get('properties', {})
            batch_info = entity.get('batch_processing', {})
            
            unlabeled_entities.append({
                'qid': entity['qid'],
                'property_count': len(properties),
                'properties': ','.join(list(properties.keys())[:10]),  # First 10 props
                'restored_from_xml': batch_info.get('restored_from_xml', False),
                'entity_type': 'restored' if batch_info.get('restored_from_xml') else 'unlabeled'
            })
    
    client.close()
    
    # Write to CSV
    csv_filename = 'unlabeled_entities_for_batch_processing.csv'
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['qid', 'property_count', 'properties', 'restored_from_xml', 'entity_type']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for entity in unlabeled_entities:
            writer.writerow(entity)
    
    print(f"Exported {len(unlabeled_entities):,} unlabeled entities to {csv_filename}")
    
    # Statistics
    restored_count = sum(1 for e in unlabeled_entities if e['restored_from_xml'])
    print(f"  Restored from XML: {restored_count:,}")
    print(f"  Still unlabeled: {len(unlabeled_entities) - restored_count:,}")
    
    return len(unlabeled_entities)

def main():
    print("=== COMPREHENSIVE LABEL RESTORATION ===")
    print()
    
    # Find numbered XML files
    xml_files = find_numbered_xml_files()
    if not xml_files:
        print("No numbered XML files found!")
        return
    
    print(f"Found {len(xml_files)} numbered XML files")
    
    # Parse all XML files for entity data
    all_entities_data = {}
    for xml_file in xml_files:
        entities_data = parse_xml_for_labels(xml_file)
        all_entities_data.update(entities_data)
    
    print(f"\nTotal entities with data: {len(all_entities_data):,}")
    
    # Test Q85814 specifically
    if 'Q85814' in all_entities_data:
        q85814_data = all_entities_data['Q85814']
        print(f"Q85814 found:")
        print(f"  Labels: {list(q85814_data.get('labels', {}).keys())}")
        print(f"  Properties: {len(q85814_data.get('claims', {}))}")
    
    # Restore to MongoDB
    if all_entities_data:
        print()
        marked_entities = restore_to_mongodb(all_entities_data)
        print(f"Marked {len(marked_entities)} entities for batch processing")
    
    # Export all unlabeled entities to CSV
    print()
    total_unlabeled = export_unlabeled_entities_csv()
    
    print(f"\nSUCCESS: Restoration complete!")
    print(f"CSV created: unlabeled_entities_for_batch_processing.csv")

if __name__ == '__main__':
    main()