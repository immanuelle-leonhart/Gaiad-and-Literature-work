#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import json
import pymongo
import os
import glob
from collections import defaultdict

def parse_xml_redirects(xml_file):
    """Parse XML file to extract redirect relationships"""
    print(f"Parsing {xml_file}...")
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error parsing {xml_file}: {e}")
        return {}
    
    redirects = {}
    parsed_entities = 0
    
    # Find all pages in the XML
    for page in root.findall('.//page'):
        parsed_entities += 1
        
        title_elem = page.find('title')
        if title_elem is None:
            continue
            
        title = title_elem.text
        if not title or not title.startswith('Item:Q'):
            continue
            
        # Extract QID from title
        source_qid = title.replace('Item:', '')
        
        # Check if this page has a redirect element (MediaWiki style)
        redirect_elem = page.find('redirect')
        if redirect_elem is not None:
            redirect_title = redirect_elem.get('title', '')
            if redirect_title.startswith('Item:Q'):
                target_qid = redirect_title.replace('Item:', '')
                redirects[source_qid] = target_qid
                print(f"  Found MediaWiki redirect: {source_qid} -> {target_qid}")
                continue
        
        # Get the JSON content
        revision = page.find('revision')
        if revision is None:
            continue
            
        text_elem = revision.find('text')
        if text_elem is None or text_elem.text is None:
            continue
            
        try:
            # Parse the JSON content
            entity_data = json.loads(text_elem.text)
            
            # Check if this is a Wikibase redirect (various formats)
            if entity_data.get('type') == 'item':
                # Method 1: Check for redirects field
                if 'redirects' in entity_data:
                    redirect_info = entity_data['redirects']
                    if 'to' in redirect_info:
                        target_qid = redirect_info['to']
                        redirects[source_qid] = target_qid
                        print(f"  Found Wikibase redirect: {source_qid} -> {target_qid}")
                
                # Method 2: Check if entity is mostly empty (potential redirect)
                elif (not entity_data.get('labels') and 
                      not entity_data.get('descriptions') and
                      not entity_data.get('aliases') and
                      not entity_data.get('claims')):
                    # This might be a redirect that was exported as empty entity
                    continue
                    
                # Method 3: Check for redirect in claims or sitelinks
                elif 'sitelinks' in entity_data:
                    for sitelink in entity_data['sitelinks'].values():
                        if sitelink.get('title', '').startswith('#REDIRECT'):
                            # Parse redirect from sitelink
                            redirect_text = sitelink['title']
                            # Extract target from #REDIRECT [[Item:Q12345]]
                            import re
                            match = re.search(r'Item:Q(\d+)', redirect_text)
                            if match:
                                target_qid = f"Q{match.group(1)}"
                                redirects[source_qid] = target_qid
                                print(f"  Found sitelink redirect: {source_qid} -> {target_qid}")
            
        except json.JSONDecodeError:
            # Skip malformed JSON
            continue
    
    print(f"  Parsed {parsed_entities} entities from {xml_file}")
    return redirects

def find_xml_files():
    """Find all XML export files"""
    xml_files = []
    
    # Check common export directories
    export_dirs = [
        'exports_with_labels',
        'exports_with_labels_240part', 
        'exports_with_labels_120part',
        'exports_with_labels_60part'
    ]
    
    for export_dir in export_dirs:
        if os.path.exists(export_dir):
            # Look for XML files in this directory
            pattern = os.path.join(export_dir, '*.xml')
            files = glob.glob(pattern)
            xml_files.extend(files)
    
    # Also check root directory
    root_files = glob.glob('*.xml')
    xml_files.extend(root_files)
    
    return sorted(xml_files)

def import_redirects_to_mongodb(redirects):
    """Import redirect relationships to MongoDB"""
    print(f"Importing {len(redirects)} redirects to MongoDB...")
    
    # Connect to MongoDB
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['gaiad_processing_db']
    collection = db['entities']
    
    imported_count = 0
    not_found_count = 0
    already_redirect_count = 0
    
    for source_qid, target_qid in redirects.items():
        # Check if source entity exists
        entity = collection.find_one({'qid': source_qid})
        if not entity:
            not_found_count += 1
            continue
            
        # Check if it's already a redirect
        properties = entity.get('properties', {})
        if 'redirect' in properties:
            already_redirect_count += 1
            continue
            
        # Create redirect property
        redirect_claim = {
            'value': target_qid,
            'type': 'redirect',
            'claim_id': f'{source_qid}_redirect_{target_qid}'
        }
        
        # Update entity to be a redirect
        # Clear labels, descriptions, aliases and set redirect property
        update_data = {
            'properties': {'redirect': [redirect_claim]},
            'labels': {},
            'descriptions': {},
            'aliases': {}
        }
        
        result = collection.update_one(
            {'qid': source_qid},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            imported_count += 1
            if imported_count % 1000 == 0:
                print(f"  Imported {imported_count} redirects...")
    
    client.close()
    
    print(f"Import complete:")
    print(f"  Redirects imported: {imported_count}")
    print(f"  Entities not found: {not_found_count}")
    print(f"  Already redirects: {already_redirect_count}")
    
    return imported_count

def parse_csv_redirects(csv_file):
    """Parse CSV file to extract redirect relationships"""
    print(f"Parsing {csv_file}...")
    
    import csv
    redirects = {}
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # CSV format: entity_without_ids -> entity_with_ids
                source_qid = row.get('entity_without_ids', '').strip()
                target_qid = row.get('entity_with_ids', '').strip()
                
                # Validate QID format
                if source_qid.startswith('Q') and target_qid.startswith('Q'):
                    redirects[source_qid] = target_qid
    
    except Exception as e:
        print(f"Error parsing {csv_file}: {e}")
        return {}
    
    print(f"  Found {len(redirects)} redirects in CSV")
    return redirects

def main():
    print("=== CSV REDIRECT IMPORT ===")
    print()
    
    # Check for CSV file with redirect mappings
    csv_file = "potential_duplicates_quick.csv"
    if not os.path.exists(csv_file):
        print(f"CSV file {csv_file} not found!")
        return
    
    print(f"Found CSV file: {csv_file}")
    print(f"File size: {os.path.getsize(csv_file) / (1024 * 1024):.1f} MB")
    print()
    
    # Parse CSV for redirects
    all_redirects = parse_csv_redirects(csv_file)
    
    print(f"Total redirects found: {len(all_redirects)}")
    
    if all_redirects:
        # Show some examples
        print("\nSample redirects:")
        for i, (source, target) in enumerate(list(all_redirects.items())[:10]):
            print(f"  {source} -> {target}")
        
        # Import to MongoDB
        print()
        imported = import_redirects_to_mongodb(all_redirects)
        
        if imported > 0:
            print(f"\nSUCCESS: Imported {imported} redirects to MongoDB!")
        else:
            print("\nNo new redirects were imported.")
    else:
        print("No redirects found in CSV file.")

if __name__ == '__main__':
    main()