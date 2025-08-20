#!/usr/bin/env python3
"""
MONGODB XML IMPORTER

Fast bulk import of Wikibase XML exports into MongoDB for efficient processing.
This replaces the slow Wikibase API approach with MongoDB bulk operations.

MongoDB Schema:
- Database: wikibase_import
- Collection: entities
- Primary Key: qid (e.g., "Q12345")
- Document Structure:
  {
    "_id": "Q12345",
    "qid": "Q12345", 
    "entity_type": "item",
    "labels": {"en": "Label text", "de": "German label"},
    "descriptions": {"en": "Description text"},
    "aliases": {"en": ["alias1", "alias2"]},
    "properties": {
      "P39": [{"value": "Q153720", "type": "wikibase-item"}],
      "P44": [{"value": "Q123456", "type": "external-id"}],
      "P43": [{"value": "123456789", "type": "external-id"}]
    }
  }
"""

import xml.etree.ElementTree as ET
import pymongo
import json
import re
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

# Thread-safe counters
import threading
counter_lock = threading.Lock()
stats = {
    'processed': 0,
    'items': 0,
    'properties': 0,
    'errors': 0
}

class WikibaseXMLImporter:
    def __init__(self, mongo_uri=MONGO_URI):
        # Initialize MongoDB connection
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db[COLLECTION_NAME]
        
        # Create index on QID for fast lookups
        self.collection.create_index("qid", unique=True)
        
        print(f"Connected to MongoDB: {DATABASE_NAME}.{COLLECTION_NAME}")
        
    def parse_wikibase_xml(self, xml_content):
        """Parse Wikibase XML export and extract entities"""
        entities = []
        
        try:
            # Parse XML
            root = ET.fromstring(xml_content)
            
            # Define namespace
            namespace = {'mw': 'http://www.mediawiki.org/xml/export-0.11/'}
            
            # Find all pages in the MediaWiki XML
            for page in root.findall('.//mw:page', namespace):
                try:
                    # Get page info
                    title_elem = page.find('mw:title', namespace)
                    if title_elem is None or not title_elem.text:
                        continue
                        
                    title = title_elem.text
                    
                    # Check if this is an Item or Property
                    if title.startswith('Item:Q'):
                        qid = title.replace('Item:', '')
                        entity_type = 'item'
                    elif title.startswith('Property:P'):
                        qid = title.replace('Property:', '')
                        entity_type = 'property'
                    elif title.startswith('Q') and title[1:].isdigit():
                        # Handle bare QID format
                        qid = title
                        entity_type = 'item'
                    elif title.startswith('P') and title[1:].isdigit():
                        # Handle bare PID format
                        qid = title
                        entity_type = 'property'
                    else:
                        continue  # Skip non-entity pages
                    
                    # Get revision content
                    revision = page.find('mw:revision', namespace)
                    if revision is None:
                        continue
                        
                    # Find text element in revision
                    text_elem = revision.find('mw:text', namespace)
                    if text_elem is None or text_elem.text is None:
                        continue
                    
                    # Parse JSON content from the text
                    try:
                        entity_data = json.loads(text_elem.text)
                    except json.JSONDecodeError:
                        continue
                    
                    # Extract structured data
                    parsed_entity = self.parse_entity_data(qid, entity_type, entity_data)
                    if parsed_entity:
                        entities.append(parsed_entity)
                        
                except Exception as e:
                    with counter_lock:
                        stats['errors'] += 1
                    print(f"Error parsing page: {e}")
                    continue
                    
        except ET.ParseError as e:
            print(f"XML Parse Error: {e}")
            return []
            
        return entities
    
    def parse_entity_data(self, qid, entity_type, data):
        """Parse entity JSON data into MongoDB document structure"""
        try:
            entity = {
                "_id": qid,
                "qid": qid,
                "entity_type": entity_type,
                "labels": {},
                "descriptions": {},
                "aliases": {},
                "properties": {}
            }
            
            # Extract labels - handle both dict and list formats
            if 'labels' in data:
                labels_data = data['labels']
                if isinstance(labels_data, dict):
                    # Standard format: {"en": {"value": "Label", "language": "en"}}
                    for lang, label_data in labels_data.items():
                        if isinstance(label_data, dict) and 'value' in label_data:
                            entity['labels'][lang] = label_data['value']
                elif isinstance(labels_data, list):
                    # List format: [{"value": "Label", "language": "en"}]
                    for label_data in labels_data:
                        if isinstance(label_data, dict) and 'value' in label_data and 'language' in label_data:
                            entity['labels'][label_data['language']] = label_data['value']
            
            # Extract descriptions - handle both dict and list formats
            if 'descriptions' in data:
                descriptions_data = data['descriptions']
                if isinstance(descriptions_data, dict):
                    # Standard format: {"en": {"value": "Description", "language": "en"}}
                    for lang, desc_data in descriptions_data.items():
                        if isinstance(desc_data, dict) and 'value' in desc_data:
                            entity['descriptions'][lang] = desc_data['value']
                elif isinstance(descriptions_data, list):
                    # List format: [{"value": "Description", "language": "en"}]
                    for desc_data in descriptions_data:
                        if isinstance(desc_data, dict) and 'value' in desc_data and 'language' in desc_data:
                            entity['descriptions'][desc_data['language']] = desc_data['value']
            
            # Extract aliases - handle both dict and list formats
            if 'aliases' in data:
                aliases_data = data['aliases']
                if isinstance(aliases_data, dict):
                    # Standard format: {"en": [{"value": "Alias1"}, {"value": "Alias2"}]}
                    for lang, alias_list in aliases_data.items():
                        if isinstance(alias_list, list):
                            entity['aliases'][lang] = [alias['value'] for alias in alias_list if isinstance(alias, dict) and 'value' in alias]
                elif isinstance(aliases_data, list):
                    # List format: [{"value": "Alias", "language": "en"}]
                    alias_dict = {}
                    for alias_data in aliases_data:
                        if isinstance(alias_data, dict) and 'value' in alias_data and 'language' in alias_data:
                            lang = alias_data['language']
                            if lang not in alias_dict:
                                alias_dict[lang] = []
                            alias_dict[lang].append(alias_data['value'])
                    entity['aliases'] = alias_dict
            
            # Extract properties/claims
            if 'claims' in data:
                claims_data = data['claims']
                if isinstance(claims_data, dict):
                    for prop_id, claims in claims_data.items():
                        if isinstance(claims, list):
                            entity['properties'][prop_id] = []
                            
                            for claim in claims:
                                if isinstance(claim, dict) and 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
                                    datavalue = claim['mainsnak']['datavalue']
                                    claim_data = {
                                        'value': datavalue.get('value'),
                                        'type': datavalue.get('type'),
                                        'claim_id': claim.get('id')
                                    }
                                    entity['properties'][prop_id].append(claim_data)
            
            return entity
            
        except Exception as e:
            print(f"Error parsing entity {qid}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def import_xml_file(self, xml_file_path):
        """Import a single XML file"""
        print(f"Processing: {xml_file_path}")
        
        try:
            with open(xml_file_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
        except Exception as e:
            print(f"Error reading {xml_file_path}: {e}")
            return 0
        
        # Parse entities from XML
        entities = self.parse_wikibase_xml(xml_content)
        
        if not entities:
            print(f"No entities found in {xml_file_path}")
            return 0
        
        # Bulk insert into MongoDB
        try:
            # Use ordered=False for better performance, continue on errors
            result = self.collection.insert_many(entities, ordered=False)
            inserted_count = len(result.inserted_ids)
            
            with counter_lock:
                stats['processed'] += inserted_count
                for entity in entities:
                    if entity['entity_type'] == 'item':
                        stats['items'] += 1
                    else:
                        stats['properties'] += 1
            
            print(f"OK {xml_file_path}: {inserted_count} entities imported")
            return inserted_count
            
        except pymongo.errors.BulkWriteError as e:
            # Handle duplicate key errors (entities that already exist)
            inserted_count = e.details.get('nInserted', 0)
            duplicate_count = len(e.details.get('writeErrors', []))
            
            with counter_lock:
                stats['processed'] += inserted_count
                
            print(f"OK {xml_file_path}: {inserted_count} new, {duplicate_count} duplicates")
            return inserted_count
            
        except Exception as e:
            print(f"ERROR importing {xml_file_path}: {e}")
            return 0
    
    def import_all_xml_files(self, xml_directory="xml_imports", max_workers=4):
        """Import all XML files using parallel processing"""
        xml_files = []
        
        # Find all XML files
        for filename in os.listdir(xml_directory):
            if filename.endswith('.xml'):
                xml_files.append(os.path.join(xml_directory, filename))
        
        if not xml_files:
            print(f"No XML files found in {xml_directory}")
            return
        
        print(f"Found {len(xml_files)} XML files to import")
        print(f"Using {max_workers} parallel workers")
        
        start_time = time.time()
        
        # Clear existing collection (optional)
        print("Clearing existing collection...")
        self.collection.delete_many({})
        
        # Process files in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(self.import_xml_file, xml_file): xml_file 
                            for xml_file in xml_files}
            
            for future in as_completed(future_to_file):
                xml_file = future_to_file[future]
                try:
                    count = future.result()
                except Exception as e:
                    print(f"Error processing {xml_file}: {e}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Print final statistics
        print("\n" + "="*50)
        print("IMPORT COMPLETE")
        print("="*50)
        print(f"Total entities processed: {stats['processed']:,}")
        print(f"Items: {stats['items']:,}")
        print(f"Properties: {stats['properties']:,}")
        print(f"Errors: {stats['errors']:,}")
        print(f"Time taken: {duration:.2f} seconds")
        print(f"Rate: {stats['processed'] / duration:.0f} entities/second")
        
        # Verify collection count
        total_in_db = self.collection.count_documents({})
        print(f"Total in MongoDB: {total_in_db:,}")
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()

def main():
    importer = WikibaseXMLImporter()
    
    try:
        # Import all XML files
        importer.import_all_xml_files(max_workers=6)  # Adjust workers based on system
        
    finally:
        importer.close()

if __name__ == "__main__":
    main()