#!/usr/bin/env python3
"""
MongoDB to Wikibase XML Exporter

Exports the processed MongoDB genealogical database back to Wikibase XML format
for re-import into a fresh Wikibase instance. This creates a complete export
with all entities, properties, labels, descriptions, and relationships.

The output format matches MediaWiki XML export structure compatible with:
- MediaWiki XML import
- Wikibase import tools
- Direct database restoration

Features:
- Exports all active entities (skips redirects)
- Preserves all properties and relationships
- Includes labels, descriptions, and aliases in all languages
- Maintains proper XML namespace structure
- Creates chunked output files for large datasets
"""

import pymongo
import xml.etree.ElementTree as ET
import json
import time
import os
from datetime import datetime, timezone

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

# Output configuration
OUTPUT_DIR = "wikibase_export"
CHUNK_SIZE = 5000  # Entities per XML file
XML_NAMESPACE = "http://www.mediawiki.org/xml/export-0.11/"

class WikibaseXMLExporter:
    def __init__(self, mongo_uri=MONGO_URI, output_dir=OUTPUT_DIR):
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db[COLLECTION_NAME]
        self.output_dir = output_dir
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        self.stats = {
            'entities_processed': 0,
            'entities_exported': 0,
            'redirects_skipped': 0,
            'files_created': 0,
            'start_time': time.time()
        }
        
        print(f"Connected to MongoDB: {DATABASE_NAME}.{COLLECTION_NAME}")
        print(f"Output directory: {output_dir}")
    
    def create_xml_header(self):
        """Create the MediaWiki XML export header"""
        # Create root mediawiki element with namespace
        root = ET.Element("mediawiki")
        root.set("xmlns", XML_NAMESPACE)
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.set("xsi:schemaLocation", f"{XML_NAMESPACE} http://www.mediawiki.org/xml/export-0.11.xsd")
        root.set("version", "0.11")
        root.set("xml:lang", "en")
        
        # Add siteinfo
        siteinfo = ET.SubElement(root, "siteinfo")
        sitename = ET.SubElement(siteinfo, "sitename")
        sitename.text = "Gaiad Genealogy Wikibase"
        
        dbname = ET.SubElement(siteinfo, "dbname")
        dbname.text = "gaiad_wikibase"
        
        base = ET.SubElement(siteinfo, "base")
        base.text = "https://gaiad.example.com/"
        
        generator = ET.SubElement(siteinfo, "generator")
        generator.text = "MongoDB to Wikibase XML Exporter"
        
        # Add case sensitivity
        case = ET.SubElement(siteinfo, "case")
        case.text = "first-letter"
        
        # Add namespaces
        namespaces = ET.SubElement(siteinfo, "namespaces")
        
        # Main namespace
        ns_main = ET.SubElement(namespaces, "namespace")
        ns_main.set("key", "0")
        ns_main.set("case", "first-letter")
        ns_main.text = ""
        
        # Item namespace
        ns_item = ET.SubElement(namespaces, "namespace")
        ns_item.set("key", "860")
        ns_item.set("case", "first-letter")
        ns_item.text = "Item"
        
        # Property namespace
        ns_prop = ET.SubElement(namespaces, "namespace")
        ns_prop.set("key", "862")
        ns_prop.set("case", "first-letter")
        ns_prop.text = "Property"
        
        return root
    
    def entity_to_wikibase_json(self, entity):
        """Convert MongoDB entity to Wikibase JSON format"""
        qid = entity['qid']
        entity_type = entity.get('entity_type', 'item')
        
        # Build Wikibase entity structure
        wikibase_entity = {
            "type": entity_type,
            "id": qid,
            "labels": {},
            "descriptions": {},
            "aliases": {},
            "claims": {}
        }
        
        # Convert labels
        labels = entity.get('labels', {})
        for lang, label_text in labels.items():
            if label_text:
                wikibase_entity['labels'][lang] = {
                    "language": lang,
                    "value": label_text
                }
        
        # Convert descriptions  
        descriptions = entity.get('descriptions', {})
        for lang, desc_text in descriptions.items():
            if desc_text:
                wikibase_entity['descriptions'][lang] = {
                    "language": lang,
                    "value": desc_text
                }
        
        # Convert aliases
        aliases = entity.get('aliases', {})
        for lang, alias_list in aliases.items():
            if alias_list and isinstance(alias_list, list):
                wikibase_entity['aliases'][lang] = [
                    {"language": lang, "value": alias} for alias in alias_list
                ]
        
        # Convert properties/claims
        properties = entity.get('properties', {})
        for prop_id, claims in properties.items():
            if not claims:
                continue
                
            wikibase_claims = []
            
            for claim in claims:
                claim_id = claim.get('claim_id', f"{qid}${prop_id}$generated")
                claim_value = claim.get('value')
                claim_type = claim.get('type', 'string')
                
                # Create Wikibase claim structure
                wikibase_claim = {
                    "id": claim_id,
                    "mainsnak": {
                        "snaktype": "value",
                        "property": prop_id,
                        "datavalue": {
                            "type": claim_type
                        }
                    },
                    "type": "statement",
                    "rank": "normal"
                }
                
                # Handle different value types
                if claim_type == "wikibase-item":
                    # Entity reference
                    if isinstance(claim_value, dict) and 'id' in claim_value:
                        entity_id = claim_value['id']
                    else:
                        entity_id = str(claim_value)
                    
                    wikibase_claim["mainsnak"]["datavalue"]["value"] = {
                        "entity-type": "item",
                        "numeric-id": int(entity_id[1:]) if entity_id.startswith('Q') else 0,
                        "id": entity_id
                    }
                elif claim_type == "external-id":
                    # External identifier
                    wikibase_claim["mainsnak"]["datavalue"]["type"] = "string"
                    wikibase_claim["mainsnak"]["datavalue"]["value"] = str(claim_value)
                elif claim_type == "time":
                    # Date/time value
                    if isinstance(claim_value, dict):
                        wikibase_claim["mainsnak"]["datavalue"]["value"] = claim_value
                    else:
                        # Simple date string - convert to Wikibase time format
                        wikibase_claim["mainsnak"]["datavalue"]["value"] = {
                            "time": str(claim_value),
                            "timezone": 0,
                            "before": 0,
                            "after": 0,
                            "precision": 11,
                            "calendarmodel": "http://www.wikidata.org/entity/Q1985727"
                        }
                else:
                    # String or other value
                    wikibase_claim["mainsnak"]["datavalue"]["type"] = "string"
                    wikibase_claim["mainsnak"]["datavalue"]["value"] = str(claim_value)
                
                wikibase_claims.append(wikibase_claim)
            
            wikibase_entity['claims'][prop_id] = wikibase_claims
        
        return wikibase_entity
    
    def create_page_element(self, entity, parent_element):
        """Create a MediaWiki page element for an entity"""
        qid = entity['qid']
        entity_type = entity.get('entity_type', 'item')
        properties = entity.get('properties', {})
        
        # Check if this is a redirect entity
        is_redirect = 'redirect' in properties
        
        # Determine title based on entity type
        if entity_type == 'item':
            title = f"Item:{qid}"
        else:
            title = f"Property:{qid}"
        
        # Create page element
        page = ET.SubElement(parent_element, "page")
        
        # Add title
        title_elem = ET.SubElement(page, "title")
        title_elem.text = title
        
        # Add namespace
        ns = ET.SubElement(page, "ns")
        ns.text = "860" if entity_type == 'item' else "862"
        
        # Add ID (use QID numeric part)
        id_elem = ET.SubElement(page, "id")
        id_elem.text = qid[1:] if qid.startswith(('Q', 'P')) else "0"
        
        # Add redirect element if this is a redirect
        if is_redirect:
            redirect_target = properties['redirect'][0]['value']
            redirect_elem = ET.SubElement(page, "redirect")
            redirect_elem.set("title", f"Item:{redirect_target}")
        
        # Add revision
        revision = ET.SubElement(page, "revision")
        
        # Revision ID
        rev_id = ET.SubElement(revision, "id")
        rev_id.text = qid[1:] if qid.startswith(('Q', 'P')) else "1"
        
        # Timestamp
        timestamp = ET.SubElement(revision, "timestamp")
        timestamp.text = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Contributor
        contributor = ET.SubElement(revision, "contributor")
        username = ET.SubElement(contributor, "username")
        username.text = "MongoDBExporter"
        
        # Comment
        comment = ET.SubElement(revision, "comment")
        if is_redirect:
            comment.text = "Redirect from MongoDB entity merger"
        else:
            comment.text = "Exported from MongoDB"
        
        # Content model
        model = ET.SubElement(revision, "model")
        model.text = "wikibase-item" if entity_type == 'item' else "wikibase-property"
        
        # Format
        format_elem = ET.SubElement(revision, "format")
        if is_redirect:
            format_elem.text = "application/json"
        else:
            format_elem.text = "application/json"
        
        # Text content
        text = ET.SubElement(revision, "text")
        text.set("bytes", "0")  # Will be updated after content creation
        text.set("xml:space", "preserve")
        
        if is_redirect:
            # For redirects, create simple JSON redirect structure
            redirect_target = properties['redirect'][0]['value']
            redirect_json = {
                "entity": qid,
                "redirect": redirect_target
            }
            json_text = json.dumps(redirect_json, ensure_ascii=False, separators=(',', ':'))
        else:
            # For regular entities, convert to Wikibase JSON
            wikibase_json = self.entity_to_wikibase_json(entity)
            json_text = json.dumps(wikibase_json, ensure_ascii=False, separators=(',', ':'))
        
        text.text = json_text
        
        # Update byte count
        text.set("bytes", str(len(json_text.encode('utf-8'))))
        
        return page
    
    def export_chunk(self, entities, chunk_num):
        """Export a chunk of entities to an XML file"""
        if not entities:
            return None
            
        filename = f"gaiad_wikibase_export_part_{chunk_num:03d}.xml"
        filepath = os.path.join(self.output_dir, filename)
        
        print(f"Creating {filename} with {len(entities)} entities...")
        
        # Create XML structure
        root = self.create_xml_header()
        
        # Add entities as pages
        for entity in entities:
            self.create_page_element(entity, root)
        
        # Write to file
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)  # Pretty formatting
        
        with open(filepath, 'wb') as f:
            tree.write(f, encoding='utf-8', xml_declaration=True)
        
        self.stats['files_created'] += 1
        print(f"  OK Saved {filename}")
        
        return filename
    
    def export_all_entities(self):
        """Export all entities from MongoDB to XML files"""
        print("=== MONGODB TO WIKIBASE XML EXPORT ===")
        print()
        
        # Get total count
        total_entities = self.collection.count_documents({})
        redirect_count = self.collection.count_documents({'properties.redirect': {'$exists': True}})
        active_entities = total_entities - redirect_count
        
        print(f"Total entities in database: {total_entities:,}")
        print(f"Redirect entities (will include): {redirect_count:,}")
        print(f"Active entities: {active_entities:,}")
        print(f"ALL entities to export: {total_entities:,}")
        print(f"Chunk size: {CHUNK_SIZE:,} entities per file")
        print(f"Estimated output files: {(total_entities + CHUNK_SIZE - 1) // CHUNK_SIZE}")
        print()
        
        # Process entities in chunks
        chunk_entities = []
        chunk_num = 1
        
        print("Processing entities...")
        
        for entity in self.collection.find():
            self.stats['entities_processed'] += 1
            
            if self.stats['entities_processed'] % 10000 == 0:
                print(f"  Processed {self.stats['entities_processed']:,} entities...")
            
            # Track redirects but include them in export
            if 'redirect' in entity.get('properties', {}):
                self.stats['redirects_skipped'] += 1  # Track count but don't skip
            
            # Add ALL entities to chunks (including redirects)
            chunk_entities.append(entity)
            self.stats['entities_exported'] += 1
            
            # Export chunk when full
            if len(chunk_entities) >= CHUNK_SIZE:
                self.export_chunk(chunk_entities, chunk_num)
                chunk_entities = []
                chunk_num += 1
        
        # Export final chunk if it has entities
        if chunk_entities:
            self.export_chunk(chunk_entities, chunk_num)
        
        # Final statistics
        duration = time.time() - self.stats['start_time']
        
        print()
        print("=== EXPORT COMPLETE ===")
        print(f"Entities processed: {self.stats['entities_processed']:,}")
        print(f"Entities exported: {self.stats['entities_exported']:,}")
        print(f"Redirects included: {self.stats['redirects_skipped']:,}")
        print(f"Active entities included: {self.stats['entities_exported'] - self.stats['redirects_skipped']:,}")
        print(f"XML files created: {self.stats['files_created']}")
        print(f"Export duration: {duration:.1f} seconds")
        print(f"Export rate: {self.stats['entities_exported'] / duration:.0f} entities/second")
        print()
        print(f"SUCCESS: Complete Wikibase XML export completed!")
        print(f"Files saved to: {self.output_dir}/")
        print()
        print("IMPORTANT: This export includes ALL entities:")
        print("- Active entities with full Wikibase JSON content")
        print("- Redirect entities with proper redirect XML structure")
        print("- Import will overwrite existing pages with redirects as needed")
        print()
        print("To import into Wikibase:")
        print("1. Use MediaWiki importDump.php maintenance script")
        print("2. Or import via Wikibase importers")
        print("3. Files are in MediaWiki XML export format")
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()

def main():
    exporter = WikibaseXMLExporter()
    
    try:
        exporter.export_all_entities()
    finally:
        exporter.close()

if __name__ == "__main__":
    main()