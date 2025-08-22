#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import pymongo
import json
import re
import time
from datetime import datetime

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

def process_wikibase_entity(content_text):
    """Process Wikibase JSON content into our MongoDB format"""
    if not content_text or not content_text.strip():
        return None
        
    try:
        wikibase_data = json.loads(content_text.strip())
    except json.JSONDecodeError:
        return None
    
    # Extract basic info
    qid = wikibase_data.get('id', '')
    entity_type = wikibase_data.get('type', 'item')
    
    # Process labels
    labels = {}
    if 'labels' in wikibase_data:
        for lang, label_data in wikibase_data['labels'].items():
            labels[lang] = label_data.get('value', '')
    
    # Process descriptions  
    descriptions = {}
    if 'descriptions' in wikibase_data:
        for lang, desc_data in wikibase_data['descriptions'].items():
            descriptions[lang] = desc_data.get('value', '')
    
    # Process aliases
    aliases = {}
    if 'aliases' in wikibase_data:
        for lang, alias_list in wikibase_data['aliases'].items():
            aliases[lang] = [alias.get('value', '') for alias in alias_list]
    
    # Process claims (properties)
    properties = {}
    if 'claims' in wikibase_data:
        for prop_id, claims in wikibase_data['claims'].items():
            prop_claims = []
            for claim in claims:
                try:
                    mainsnak = claim.get('mainsnak', {})
                    if mainsnak.get('snaktype') == 'value':
                        datavalue = mainsnak.get('datavalue', {})
                        value_type = datavalue.get('type')
                        value = datavalue.get('value')
                        
                        claim_obj = {'claim_id': claim.get('id', '')}
                        
                        if value_type == 'wikibase-entityid':
                            claim_obj['value'] = value.get('id', '')
                            claim_obj['type'] = 'wikibase-entityid'
                        elif value_type == 'string':
                            claim_obj['value'] = value
                            claim_obj['type'] = 'external-id'
                        elif value_type == 'time':
                            claim_obj['value'] = value
                            claim_obj['type'] = 'time'
                        elif value_type == 'monolingualtext':
                            claim_obj['value'] = value
                            claim_obj['type'] = 'monolingualtext'
                        else:
                            claim_obj['value'] = value
                            claim_obj['type'] = value_type or 'unknown'
                        
                        prop_claims.append(claim_obj)
                except Exception:
                    continue
            
            if prop_claims:
                properties[prop_id] = prop_claims
    
    return {
        'qid': qid,
        'entity_type': entity_type,
        'labels': labels,
        'descriptions': descriptions,
        'aliases': aliases,
        'properties': properties
    }

def import_single_xml_file(xml_file):
    """Import single XML file to MongoDB"""
    print(f"Importing from: {xml_file}")
    
    # Connect to MongoDB
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    print(f"Connected to MongoDB: {DATABASE_NAME}.{COLLECTION_NAME}")
    
    # Clear existing collection
    print("Clearing existing collection...")
    collection.delete_many({})
    
    # Parse XML
    print("Parsing XML file...")
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Namespace
    ns = {'mw': 'http://www.mediawiki.org/xml/export-0.11/'}
    
    # Import entities
    batch = []
    batch_size = 1000
    processed = 0
    imported = 0
    errors = 0
    
    start_time = time.time()
    
    for page in root.findall('.//mw:page', ns):
        try:
            title_elem = page.find('mw:title', ns)
            if title_elem is None:
                continue
                
            title = title_elem.text
            if not title or not title.startswith(('Item:', 'Property:')):
                continue
            
            # Get page content
            revision = page.find('mw:revision', ns)
            if revision is None:
                continue
                
            text_elem = revision.find('mw:text', ns)
            if text_elem is None or text_elem.text is None:
                continue
            
            content = text_elem.text.strip()
            if not content:
                continue
            
            # Process the entity
            entity_doc = process_wikibase_entity(content)
            if entity_doc:
                batch.append(entity_doc)
                imported += 1
                
                if len(batch) >= batch_size:
                    collection.insert_many(batch)
                    batch = []
                    
            processed += 1
            
            if processed % 1000 == 0:
                print(f"Processed {processed:,} pages, imported {imported:,} entities...")
                
        except Exception as e:
            errors += 1
            if errors <= 10:
                print(f"Error processing page: {e}")
    
    # Insert remaining batch
    if batch:
        collection.insert_many(batch)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "="*50)
    print("IMPORT COMPLETE")
    print("="*50)
    print(f"Pages processed: {processed:,}")
    print(f"Entities imported: {imported:,}")
    print(f"Errors: {errors:,}")
    print(f"Time taken: {duration:.2f} seconds")
    if duration > 0:
        print(f"Rate: {imported/duration:.0f} entities/second")
    
    # Verify final count
    final_count = collection.count_documents({})
    print(f"Final count in MongoDB: {final_count:,}")
    
    client.close()
    return imported

if __name__ == "__main__":
    xml_file = "evolutionism_complete_export.xml"
    import_single_xml_file(xml_file)