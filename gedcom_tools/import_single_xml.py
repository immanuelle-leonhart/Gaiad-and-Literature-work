#!/usr/bin/env python3

import pymongo
import xml.etree.ElementTree as ET
import sys
from datetime import datetime

def import_single_xml(xml_file):
    """Import a single XML file to MongoDB"""
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['gaiad_processing_db']
    collection = db['entities']
    
    print(f"Connected to MongoDB: {db.name}.{collection.name}")
    print(f"Importing from: {xml_file}")
    
    # Clear existing collection
    print("Clearing existing collection...")
    collection.delete_many({})
    
    # Parse and import XML
    print("Parsing XML file...")
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Find namespace
    ns = {'mw': 'http://www.mediawiki.org/xml/export-0.11/'}
    
    entities_imported = 0
    batch = []
    batch_size = 1000
    
    start_time = datetime.now()
    
    for page in root.findall('.//mw:page', ns):
        title = page.find('mw:title', ns)
        revision = page.find('mw:revision', ns)
        
        if title is not None and revision is not None:
            page_title = title.text
            content_elem = revision.find('mw:text', ns)
            
            if content_elem is not None and page_title.startswith('Q'):
                try:
                    content = content_elem.text
                    if content and content.strip():
                        # Parse JSON content
                        import json
                        entity_data = json.loads(content)
                        
                        # Add QID
                        entity_data['qid'] = page_title
                        
                        batch.append(entity_data)
                        entities_imported += 1
                        
                        if len(batch) >= batch_size:
                            collection.insert_many(batch)
                            batch = []
                            
                        if entities_imported % 5000 == 0:
                            print(f"Imported {entities_imported:,} entities...")
                            
                except Exception as e:
                    print(f"Error processing {page_title}: {e}")
                    continue
    
    # Insert remaining batch
    if batch:
        collection.insert_many(batch)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "="*50)
    print("IMPORT COMPLETE")
    print("="*50)
    print(f"Total entities imported: {entities_imported:,}")
    print(f"Time taken: {duration:.2f} seconds")
    print(f"Rate: {entities_imported/duration:.0f} entities/second")
    
    # Verify count
    final_count = collection.count_documents({})
    print(f"Final count in MongoDB: {final_count:,}")
    
    client.close()

if __name__ == "__main__":
    xml_file = sys.argv[1] if len(sys.argv) > 1 else "evolutionism_complete_export.xml"
    import_single_xml(xml_file)