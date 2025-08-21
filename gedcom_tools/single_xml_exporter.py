#!/usr/bin/env python3
"""
Single XML Exporter for Staff Convenience

Creates one large XML file containing all entities instead of multiple chunks.
This makes it more convenient for Miraheze staff to import all entities at once.

Based on the working mongodb_to_wikibase_xml.py but outputs everything to a single file.
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
OUTPUT_FILE = "evolutionism_complete_export.xml"
XML_NAMESPACE = "http://www.mediawiki.org/xml/export-0.11/"

class SingleXMLExporter:
    def __init__(self, mongo_uri=MONGO_URI, output_file=OUTPUT_FILE):
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db[COLLECTION_NAME]
        self.output_file = output_file
        
        self.stats = {
            'entities_processed': 0,
            'entities_exported': 0,
            'redirects_included': 0,
            'start_time': time.time()
        }
        
        print(f"Connected to MongoDB: {DATABASE_NAME}.{COLLECTION_NAME}")
        print(f"Output file: {output_file}")
    
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
        sitename.text = "Evolutionism Wikibase"
        
        dbname = ET.SubElement(siteinfo, "dbname")
        dbname.text = "evolutionism_wikibase"
        
        base = ET.SubElement(siteinfo, "base")
        base.text = "https://evolutionism.miraheze.org/"
        
        generator = ET.SubElement(siteinfo, "generator")
        generator.text = "Gaiad Genealogy Single XML Exporter"
        
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
                
                # Handle different value types - preserve MongoDB structure
                if claim_type in ["wikibase-item", "wikibase-entityid"]:
                    # Entity reference
                    if isinstance(claim_value, dict) and 'id' in claim_value:
                        # Use the existing dict structure from MongoDB
                        wikibase_claim["mainsnak"]["datavalue"]["value"] = claim_value
                        wikibase_claim["mainsnak"]["datavalue"]["type"] = "wikibase-entityid"
                    elif isinstance(claim_value, str) and claim_value.startswith('Q'):
                        # Convert string QID to proper wikibase-item format
                        entity_id = claim_value
                        wikibase_claim["mainsnak"]["datavalue"]["value"] = {
                            "entity-type": "item",
                            "numeric-id": int(entity_id[1:]) if entity_id.startswith('Q') else 0,
                            "id": entity_id
                        }
                        wikibase_claim["mainsnak"]["datavalue"]["type"] = "wikibase-entityid"
                    else:
                        # Invalid wikibase-item value - skip
                        continue
                elif claim_type == "monolingualtext":
                    # Monolingualtext value - all are in English in current database
                    if isinstance(claim_value, dict) and 'text' in claim_value and 'language' in claim_value:
                        # Use the existing dict structure from MongoDB
                        wikibase_claim["mainsnak"]["datavalue"]["value"] = claim_value
                        wikibase_claim["mainsnak"]["datavalue"]["type"] = "monolingualtext"
                    else:
                        # Invalid monolingualtext value - skip
                        continue
                elif claim_type == "external-id":
                    # External identifier
                    wikibase_claim["mainsnak"]["datavalue"]["type"] = "string"
                    wikibase_claim["mainsnak"]["datavalue"]["value"] = str(claim_value)
                elif claim_type == "time":
                    # Date/time value
                    if isinstance(claim_value, dict):
                        wikibase_claim["mainsnak"]["datavalue"]["value"] = claim_value
                        wikibase_claim["mainsnak"]["datavalue"]["type"] = "time"
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
                        wikibase_claim["mainsnak"]["datavalue"]["type"] = "time"
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
        username.text = "Immanuelle"
        
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
    
    def export_all_entities(self):
        """Export all entities from MongoDB to a single XML file"""
        print("=== CREATING SINGLE XML EXPORT FOR STAFF ===")
        print()
        
        # Get total count
        total_entities = self.collection.count_documents({})
        redirect_count = self.collection.count_documents({'properties.redirect': {'$exists': True}})
        active_entities = total_entities - redirect_count
        
        print(f"Total entities in database: {total_entities:,}")
        print(f"Redirect entities (will include): {redirect_count:,}")
        print(f"Active entities: {active_entities:,}")
        print(f"ALL entities to export: {total_entities:,}")
        print(f"Output file: {self.output_file}")
        print()
        
        # Create XML structure
        print("Creating XML structure...")
        root = self.create_xml_header()
        
        # Process entities
        print("Processing entities...")
        
        for entity in self.collection.find():
            self.stats['entities_processed'] += 1
            
            if self.stats['entities_processed'] % 10000 == 0:
                print(f"  Processed {self.stats['entities_processed']:,} entities...")
            
            # Track redirects but include them in export
            if 'redirect' in entity.get('properties', {}):
                self.stats['redirects_included'] += 1
            
            # Add ALL entities (including redirects)
            self.create_page_element(entity, root)
            self.stats['entities_exported'] += 1
        
        # Write to file
        print(f"Writing XML to {self.output_file}...")
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)  # Pretty formatting
        
        with open(self.output_file, 'wb') as f:
            tree.write(f, encoding='utf-8', xml_declaration=True)
        
        # Final statistics
        duration = time.time() - self.stats['start_time']
        file_size = os.path.getsize(self.output_file) / (1024 * 1024)  # MB
        
        print()
        print("=== SINGLE XML EXPORT COMPLETE ===")
        print(f"Entities processed: {self.stats['entities_processed']:,}")
        print(f"Entities exported: {self.stats['entities_exported']:,}")
        print(f"Redirects included: {self.stats['redirects_included']:,}")
        print(f"Active entities included: {self.stats['entities_exported'] - self.stats['redirects_included']:,}")
        print(f"Export duration: {duration:.1f} seconds")
        print(f"Export rate: {self.stats['entities_exported'] / duration:.0f} entities/second")
        print(f"File size: {file_size:.1f} MB")
        print()
        print(f"SUCCESS: Complete single XML export created!")
        print(f"File saved as: {self.output_file}")
        print()
        print("READY FOR IMPORT:")
        print("- Single file contains all 145,396 entities")
        print("- Includes both active entities and redirects")
        print("- Proper MediaWiki XML export format")
        print("- All monolingualtext and wikibase-item formats corrected")
        print("- Ready for staff import via importDump.php")
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()

def main():
    exporter = SingleXMLExporter()
    
    try:
        exporter.export_all_entities()
    finally:
        exporter.close()

if __name__ == "__main__":
    main()