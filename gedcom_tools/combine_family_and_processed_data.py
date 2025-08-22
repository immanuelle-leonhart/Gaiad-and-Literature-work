#!/usr/bin/env python3
"""
COMBINE FAMILY AND PROCESSED DATA

Combines:
1. Family relationships from xml_imports directory (stable family data)
2. Processed identifiers and labels from evolutionism_complete_export.xml
3. Handles redirects by moving family relationships to targets

This creates a complete database with both family relationships and processed identifiers.
"""

import xml.etree.ElementTree as ET
import pymongo
import json
import os
import time
from collections import defaultdict

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

class FamilyDataCombiner:
    def __init__(self):
        # Connect to MongoDB
        self.client = pymongo.MongoClient(MONGO_URI)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db[COLLECTION_NAME]
        
        # Data storage
        self.family_relationships = {}  # QID -> {P20: [...], P42: [...], etc}
        self.processed_data = {}        # QID -> complete entity data
        self.redirects = {}             # redirect_qid -> target_qid
        
        print(f"Connected to MongoDB: {DATABASE_NAME}.{COLLECTION_NAME}")
    
    def extract_family_relationships_from_xml_imports(self, xml_directory="xml_imports"):
        """Extract family relationships from all XML files in xml_imports"""
        print(f"Extracting family relationships from {xml_directory}...")
        
        family_props = ['P20', 'P42', 'P47', 'P48']  # father, mother, child, spouse
        xml_files = []
        
        # Find all XML files
        for filename in os.listdir(xml_directory):
            if filename.endswith('.xml'):
                xml_files.append(os.path.join(xml_directory, filename))
        
        print(f"Found {len(xml_files)} XML files to process")
        
        processed_files = 0
        total_family_claims = 0
        
        for xml_file in xml_files:
            processed_files += 1
            print(f"  Processing {processed_files}/{len(xml_files)}: {os.path.basename(xml_file)}")
            
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                # Namespace
                ns = {'mw': 'http://www.mediawiki.org/xml/export-0.11/'}
                
                for page in root.findall('.//mw:page', ns):
                    try:
                        title_elem = page.find('mw:title', ns)
                        if title_elem is None or not title_elem.text:
                            continue
                            
                        title = title_elem.text
                        
                        # Extract QID from title
                        if title.startswith('Item:Q'):
                            qid = title.replace('Item:', '')
                        elif title.startswith('Q') and title[1:].isdigit():
                            qid = title
                        else:
                            continue
                        
                        # Get page content
                        revision = page.find('mw:revision', ns)
                        if revision is None:
                            continue
                            
                        text_elem = revision.find('mw:text', ns)
                        if text_elem is None or text_elem.text is None:
                            continue
                        
                        # Parse JSON content
                        try:
                            entity_data = json.loads(text_elem.text.strip())
                        except json.JSONDecodeError:
                            continue
                        
                        # Extract family relationships and redirects
                        if 'claims' in entity_data:
                            entity_family = {}
                            
                            for prop_id, claims in entity_data['claims'].items():
                                if prop_id in family_props:
                                    # Process family relationship claims
                                    prop_claims = []
                                    for claim in claims:
                                        try:
                                            mainsnak = claim.get('mainsnak', {})
                                            if mainsnak.get('snaktype') == 'value':
                                                datavalue = mainsnak.get('datavalue', {})
                                                value = datavalue.get('value')
                                                
                                                claim_obj = {
                                                    'value': value,
                                                    'type': 'wikibase-entityid',
                                                    'claim_id': claim.get('id', '')
                                                }
                                                prop_claims.append(claim_obj)
                                        except Exception:
                                            continue
                                    
                                    if prop_claims:
                                        entity_family[prop_id] = prop_claims
                                        total_family_claims += len(prop_claims)
                                
                                elif prop_id == 'redirect':
                                    # Handle redirects
                                    for claim in claims:
                                        try:
                                            mainsnak = claim.get('mainsnak', {})
                                            if mainsnak.get('snaktype') == 'value':
                                                datavalue = mainsnak.get('datavalue', {})
                                                target_value = datavalue.get('value')
                                                if isinstance(target_value, dict) and 'id' in target_value:
                                                    target_qid = target_value['id']
                                                    self.redirects[qid] = target_qid
                                                    print(f"    Found redirect: {qid} -> {target_qid}")
                                        except Exception:
                                            continue
                            
                            if entity_family:
                                self.family_relationships[qid] = entity_family
                                
                    except Exception as e:
                        continue
                        
            except Exception as e:
                print(f"    ERROR processing {xml_file}: {e}")
                continue
        
        print(f"Extracted family relationships:")
        print(f"  Entities with family data: {len(self.family_relationships):,}")
        print(f"  Total family claims: {total_family_claims:,}")
        print(f"  Redirects found: {len(self.redirects):,}")
    
    def extract_processed_data_from_export(self, export_file="evolutionism_complete_export.xml"):
        """Extract processed identifiers and labels from the complete export"""
        print(f"Extracting processed data from {export_file}...")
        
        try:
            tree = ET.parse(export_file)
            root = tree.getroot()
            
            # Namespace
            ns = {'mw': 'http://www.mediawiki.org/xml/export-0.11/'}
            
            processed = 0
            
            for page in root.findall('.//mw:page', ns):
                try:
                    title_elem = page.find('mw:title', ns)
                    if title_elem is None or not title_elem.text:
                        continue
                        
                    title = title_elem.text
                    
                    # Extract QID from title
                    if title.startswith('Item:Q'):
                        qid = title.replace('Item:', '')
                    elif title.startswith('Q') and title[1:].isdigit():
                        qid = title
                    else:
                        continue
                    
                    # Get page content
                    revision = page.find('mw:revision', ns)
                    if revision is None:
                        continue
                        
                    text_elem = revision.find('mw:text', ns)
                    if text_elem is None or text_elem.text is None:
                        continue
                    
                    # Parse JSON content
                    try:
                        entity_data = json.loads(text_elem.text.strip())
                    except json.JSONDecodeError:
                        continue
                    
                    # Store the complete processed entity data
                    processed_entity = {
                        'qid': qid,
                        'entity_type': 'item',
                        'labels': {},
                        'descriptions': {},
                        'aliases': {},
                        'properties': {}
                    }
                    
                    # Extract labels
                    if 'labels' in entity_data:
                        for lang, label_data in entity_data['labels'].items():
                            if isinstance(label_data, dict) and 'value' in label_data:
                                processed_entity['labels'][lang] = label_data['value']
                    
                    # Extract descriptions
                    if 'descriptions' in entity_data:
                        for lang, desc_data in entity_data['descriptions'].items():
                            if isinstance(desc_data, dict) and 'value' in desc_data:
                                processed_entity['descriptions'][lang] = desc_data['value']
                    
                    # Extract aliases
                    if 'aliases' in entity_data:
                        for lang, alias_list in entity_data['aliases'].items():
                            if isinstance(alias_list, list):
                                processed_entity['aliases'][lang] = [
                                    alias['value'] for alias in alias_list 
                                    if isinstance(alias, dict) and 'value' in alias
                                ]
                    
                    # Extract non-family properties (identifiers, etc.)
                    if 'claims' in entity_data:
                        family_props = ['P20', 'P42', 'P47', 'P48']
                        for prop_id, claims in entity_data['claims'].items():
                            if prop_id not in family_props:  # Skip family props - we get those from xml_imports
                                prop_claims = []
                                for claim in claims:
                                    try:
                                        mainsnak = claim.get('mainsnak', {})
                                        if mainsnak.get('snaktype') == 'value':
                                            datavalue = mainsnak.get('datavalue', {})
                                            value_type = datavalue.get('type')
                                            value = datavalue.get('value')
                                            
                                            claim_obj = {
                                                'value': value,
                                                'type': value_type or 'unknown',
                                                'claim_id': claim.get('id', '')
                                            }
                                            prop_claims.append(claim_obj)
                                    except Exception:
                                        continue
                                
                                if prop_claims:
                                    processed_entity['properties'][prop_id] = prop_claims
                    
                    self.processed_data[qid] = processed_entity
                    processed += 1
                    
                    if processed % 5000 == 0:
                        print(f"    Processed {processed:,} entities...")
                        
                except Exception as e:
                    continue
            
            print(f"Extracted processed data for {len(self.processed_data):,} entities")
            
        except Exception as e:
            print(f"ERROR processing export file: {e}")
    
    def resolve_redirects_and_combine(self):
        """Resolve redirects by moving family relationships to targets, then combine all data"""
        print("Resolving redirects and combining data...")
        
        # Step 1: Move family relationships from redirects to their targets
        moved_relationships = 0
        for redirect_qid, target_qid in self.redirects.items():
            if redirect_qid in self.family_relationships:
                redirect_family = self.family_relationships[redirect_qid]
                
                # Add redirect's family relationships to target
                if target_qid not in self.family_relationships:
                    self.family_relationships[target_qid] = {}
                
                for prop_id, claims in redirect_family.items():
                    if prop_id not in self.family_relationships[target_qid]:
                        self.family_relationships[target_qid][prop_id] = []
                    
                    # Add claims (allowing potential duplicates for now)
                    self.family_relationships[target_qid][prop_id].extend(claims)
                    moved_relationships += len(claims)
                
                # Remove family data from redirect entity
                del self.family_relationships[redirect_qid]
        
        print(f"Moved {moved_relationships:,} family relationship claims from {len(self.redirects):,} redirects")
        
        # Step 2: Combine processed data with family relationships
        print("Combining processed data with family relationships...")
        
        combined_entities = []
        
        # Start with all processed entities
        for qid, processed_entity in self.processed_data.items():
            # Add family relationships if they exist
            if qid in self.family_relationships:
                family_props = self.family_relationships[qid]
                processed_entity['properties'].update(family_props)
            
            combined_entities.append(processed_entity)
        
        # Add entities that have family relationships but no processed data
        family_only_count = 0
        for qid, family_props in self.family_relationships.items():
            if qid not in self.processed_data:
                # Create minimal entity with just family relationships
                family_entity = {
                    'qid': qid,
                    'entity_type': 'item',
                    'labels': {},
                    'descriptions': {},
                    'aliases': {},
                    'properties': family_props
                }
                combined_entities.append(family_entity)
                family_only_count += 1
        
        print(f"Combined data:")
        print(f"  Entities with processed data: {len(self.processed_data):,}")
        print(f"  Entities with family-only data: {family_only_count:,}")
        print(f"  Total combined entities: {len(combined_entities):,}")
        
        return combined_entities
    
    def import_to_mongodb(self, entities):
        """Import the combined entities to MongoDB"""
        print("Importing combined data to MongoDB...")
        
        # Clear existing collection
        print("Clearing existing collection...")
        self.collection.delete_many({})
        
        # Bulk import
        batch_size = 1000
        batch = []
        imported = 0
        
        for entity in entities:
            batch.append(entity)
            
            if len(batch) >= batch_size:
                self.collection.insert_many(batch)
                batch = []
                imported += len(batch)
                print(f"  Imported {imported:,} entities...")
        
        # Insert remaining batch
        if batch:
            self.collection.insert_many(batch)
            imported += len(batch)
        
        print(f"Import complete: {imported:,} entities")
        
        # Verify
        final_count = self.collection.count_documents({})
        print(f"Final count in MongoDB: {final_count:,}")
    
    def run_complete_combination(self):
        """Run the complete combination process"""
        print("=== STARTING FAMILY + PROCESSED DATA COMBINATION ===")
        print()
        
        start_time = time.time()
        
        # Step 1: Extract family relationships from xml_imports
        self.extract_family_relationships_from_xml_imports("xml_imports")
        print()
        
        # Step 2: Extract processed data from complete export
        self.extract_processed_data_from_export("evolutionism_complete_export.xml")
        print()
        
        # Step 3: Resolve redirects and combine
        combined_entities = self.resolve_redirects_and_combine()
        print()
        
        # Step 4: Import to MongoDB
        self.import_to_mongodb(combined_entities)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print()
        print("=== COMBINATION COMPLETE ===")
        print(f"Total time: {duration:.2f} seconds")
        print(f"Final database contains both family relationships and processed identifiers!")
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()

def main():
    combiner = FamilyDataCombiner()
    
    try:
        combiner.run_complete_combination()
    finally:
        combiner.close()

if __name__ == "__main__":
    main()