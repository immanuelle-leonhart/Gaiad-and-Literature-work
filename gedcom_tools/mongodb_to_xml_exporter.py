#!/usr/bin/env python3
"""
MONGODB TO WIKIBASE XML EXPORTER

Exports processed MongoDB data back to Wikibase XML format for import.
This completes the MongoDB processing pipeline.
"""

import pymongo
import json
import xml.etree.ElementTree as ET
import xml.dom.minidom
import os
import time
from datetime import datetime

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

class MongoDBToXMLExporter:
    def __init__(self, mongo_uri=MONGO_URI):
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db[COLLECTION_NAME]
        
        print(f"Connected to MongoDB: {DATABASE_NAME}.{COLLECTION_NAME}")
    
    def entity_to_json(self, entity):
        """Convert MongoDB entity back to Wikibase JSON format"""
        qid = entity['qid']
        entity_type = entity['entity_type']
        
        # Build Wikibase JSON structure
        wikibase_json = {
            "id": qid,
            "type": entity_type,
            "labels": {},
            "descriptions": {},
            "aliases": {},
            "claims": {}
        }
        
        # Convert labels
        for lang, label in entity.get('labels', {}).items():
            wikibase_json['labels'][lang] = {
                "language": lang,
                "value": label
            }
        
        # Convert descriptions
        for lang, description in entity.get('descriptions', {}).items():
            wikibase_json['descriptions'][lang] = {
                "language": lang,
                "value": description
            }
        
        # Convert aliases
        for lang, alias_list in entity.get('aliases', {}).items():
            wikibase_json['aliases'][lang] = []
            for alias in alias_list:
                wikibase_json['aliases'][lang].append({
                    "language": lang,
                    "value": alias
                })
        
        # Convert properties to claims
        for prop_id, claims in entity.get('properties', {}).items():
            wikibase_json['claims'][prop_id] = []
            
            for claim in claims:
                claim_data = {
                    "id": claim.get('claim_id', f"{qid}${prop_id}$1"),
                    "mainsnak": {
                        "snaktype": "value",
                        "property": prop_id,
                        "datavalue": {
                            "value": claim['value'],
                            "type": claim.get('type', 'string')
                        }
                    },
                    "type": "statement",
                    "rank": "normal"
                }
                
                # Handle special types
                if claim.get('type') == 'wikibase-item':
                    claim_data['mainsnak']['datavalue'] = {
                        "value": {
                            "entity-type": "item",
                            "id": claim['value']
                        },
                        "type": "wikibase-entityid"
                    }
                elif claim.get('type') == 'time':
                    # claim['value'] should already be a time object
                    claim_data['mainsnak']['datavalue'] = {
                        "value": claim['value'],
                        "type": "time"
                    }
                
                wikibase_json['claims'][prop_id].append(claim_data)
        
        return wikibase_json
    
    def create_xml_page(self, entity, revision_id=1):
        """Create XML page element for an entity"""
        qid = entity['qid']
        entity_type = entity['entity_type']
        
        # Determine page title
        if entity_type == 'item':
            title = f"Item:{qid}"
            namespace = "120"
        else:
            title = f"Property:{qid}"
            namespace = "122"
        
        # Create page element
        page = ET.Element('page')
        
        # Add page metadata
        ET.SubElement(page, 'title').text = title
        ET.SubElement(page, 'ns').text = namespace
        ET.SubElement(page, 'id').text = str(abs(hash(qid)) % 1000000)  # Generate page ID
        
        # Create revision
        revision = ET.SubElement(page, 'revision')
        ET.SubElement(revision, 'id').text = str(revision_id)
        ET.SubElement(revision, 'timestamp').text = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Create contributor
        contributor = ET.SubElement(revision, 'contributor')
        ET.SubElement(contributor, 'username').text = 'MongoDB Processor'
        ET.SubElement(contributor, 'id').text = '1'
        
        # Add comment
        ET.SubElement(revision, 'comment').text = 'Processed via MongoDB bulk operations'
        
        # Add content model
        ET.SubElement(revision, 'model').text = f'wikibase-{entity_type}'
        ET.SubElement(revision, 'format').text = 'application/json'
        
        # Add entity JSON as text content
        entity_json = self.entity_to_json(entity)
        text_elem = ET.SubElement(revision, 'text')
        text_elem.text = json.dumps(entity_json, ensure_ascii=False, separators=(',', ':'))
        
        return page
    
    def export_to_xml(self, output_file="processed_entities.xml", batch_size=5000):
        """Export all entities to XML format"""
        print(f"Exporting entities to {output_file}...")
        
        # Get total count
        total_entities = self.collection.count_documents({})
        print(f"Total entities to export: {total_entities:,}")
        
        # Create root element
        root = ET.Element('mediawiki')
        root.set('xmlns', 'http://www.mediawiki.org/xml/export-0.10/')
        root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        root.set('xsi:schemaLocation', 'http://www.mediawiki.org/xml/export-0.10/ http://www.mediawiki.org/xml/export-0.10.xsd')
        root.set('version', '0.10')
        root.set('xml:lang', 'en')
        
        # Add site info
        siteinfo = ET.SubElement(root, 'siteinfo')
        ET.SubElement(siteinfo, 'sitename').text = 'Processed Wikibase'
        ET.SubElement(siteinfo, 'dbname').text = 'processedwikibase'
        ET.SubElement(siteinfo, 'base').text = 'http://localhost:8080/wiki/Main_Page'
        ET.SubElement(siteinfo, 'generator').text = 'MongoDB Processor 1.0'
        
        # Add namespaces
        namespaces = ET.SubElement(siteinfo, 'namespaces')
        ns_item = ET.SubElement(namespaces, 'namespace')
        ns_item.set('key', '120')
        ns_item.set('case', 'first-letter')
        ns_item.text = 'Item'
        
        ns_prop = ET.SubElement(namespaces, 'namespace')
        ns_prop.set('key', '122')
        ns_prop.set('case', 'first-letter')
        ns_prop.text = 'Property'
        
        # Process entities in batches
        processed = 0
        revision_id = 1
        
        # Sort by QID for consistent ordering
        for entity in self.collection.find({}).sort('qid', 1):
            page = self.create_xml_page(entity, revision_id)
            root.append(page)
            
            processed += 1
            revision_id += 1
            
            if processed % 1000 == 0:
                print(f"  Exported {processed:,} entities...")
        
        # Write XML to file
        print("Writing XML file...")
        tree = ET.ElementTree(root)
        
        # Format XML nicely
        rough_string = ET.tostring(root, 'utf-8')
        reparsed = xml.dom.minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
        
        print(f"✓ Exported {processed:,} entities to {output_file}")
        return processed
    
    def export_split_xml(self, output_dir="processed_xml", entities_per_file=5000):
        """Export entities to multiple XML files for easier import"""
        print(f"Exporting entities to multiple XML files in {output_dir}/...")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Get total count
        total_entities = self.collection.count_documents({})
        print(f"Total entities to export: {total_entities:,}")
        
        file_count = 0
        entity_count = 0
        current_entities = []
        
        for entity in self.collection.find({}).sort('qid', 1):
            current_entities.append(entity)
            entity_count += 1
            
            if len(current_entities) >= entities_per_file:
                # Write current batch to file
                file_count += 1
                filename = os.path.join(output_dir, f"processed_export_part_{file_count}.xml")
                self.write_xml_batch(current_entities, filename, file_count)
                current_entities = []
                print(f"  Exported part {file_count}: {entity_count:,} total entities")
        
        # Write remaining entities
        if current_entities:
            file_count += 1
            filename = os.path.join(output_dir, f"processed_export_part_{file_count}.xml")
            self.write_xml_batch(current_entities, filename, file_count)
            print(f"  Exported part {file_count}: {entity_count:,} total entities")
        
        print(f"✓ Exported {entity_count:,} entities to {file_count} XML files")
        return entity_count, file_count
    
    def write_xml_batch(self, entities, filename, batch_num):
        """Write a batch of entities to XML file"""
        # Create root element
        root = ET.Element('mediawiki')
        root.set('xmlns', 'http://www.mediawiki.org/xml/export-0.10/')
        root.set('version', '0.10')
        root.set('xml:lang', 'en')
        
        # Add minimal siteinfo
        siteinfo = ET.SubElement(root, 'siteinfo')
        ET.SubElement(siteinfo, 'sitename').text = f'Processed Wikibase Batch {batch_num}'
        
        # Add entities
        revision_id = batch_num * 10000  # Offset revision IDs per batch
        for entity in entities:
            page = self.create_xml_page(entity, revision_id)
            root.append(page)
            revision_id += 1
        
        # Write file
        tree = ET.ElementTree(root)
        tree.write(filename, encoding='utf-8', xml_declaration=True)
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()

def main():
    import sys
    
    exporter = MongoDBToXMLExporter()
    
    try:
        if len(sys.argv) > 1 and sys.argv[1] == '--split':
            # Export to multiple files
            exporter.export_split_xml()
        else:
            # Export to single file
            exporter.export_to_xml()
    finally:
        exporter.close()

if __name__ == "__main__":
    main()