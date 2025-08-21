#!/usr/bin/env python3
"""
Import XML Redirects

Scans all XML export files to find redirect pages that weren't imported
during the initial XML processing. These have the structure:

<page>
  <title>Item:Q136398</title>
  <redirect title="Item:Q115039" />
  <text>{"entity":"Q136398","redirect":"Q115039"}</text>
</page>

Strategy:
1. Scan all XML files for redirect pages
2. Import redirects as proper redirect entities in MongoDB
3. Update all references to point to final targets
"""

import pymongo
import xml.etree.ElementTree as ET
import glob
import time
import json
from collections import defaultdict

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

class XMLRedirectImporter:
    def __init__(self, mongo_uri=MONGO_URI):
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db[COLLECTION_NAME]
        
        self.stats = {
            'xml_files_processed': 0,
            'redirects_found': 0,
            'redirects_imported': 0,
            'references_updated': 0,
            'entities_updated': 0
        }
        
        print(f"Connected to MongoDB: {DATABASE_NAME}.{COLLECTION_NAME}")
    
    def find_all_xml_redirects(self, xml_directory="xml_imports"):
        """Find all redirect pages in XML export files"""
        print(f"Scanning XML files in {xml_directory} for redirects...")
        
        xml_redirects = {}  # redirect_qid -> target_qid
        xml_files = glob.glob(f"{xml_directory}/evolutionism_export_part_*.xml")
        
        for xml_file in xml_files:
            self.stats['xml_files_processed'] += 1
            print(f"  Processing {xml_file}...")
            
            try:
                # Parse XML file
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                # Define namespace
                namespace = {'mw': 'http://www.mediawiki.org/xml/export-0.11/'}
                
                # Find all pages with redirects
                for page in root.findall('.//mw:page', namespace):
                    try:
                        # Check for redirect element
                        redirect_elem = page.find('mw:redirect', namespace)
                        if redirect_elem is None:
                            continue
                        
                        # Get source QID from title
                        title_elem = page.find('mw:title', namespace)
                        if title_elem is None or not title_elem.text:
                            continue
                        
                        title = title_elem.text
                        if title.startswith('Item:Q'):
                            source_qid = title.replace('Item:', '')
                        else:
                            continue
                        
                        # Get target QID from redirect title
                        redirect_title = redirect_elem.get('title', '')
                        if redirect_title.startswith('Item:Q'):
                            target_qid = redirect_title.replace('Item:', '')
                        else:
                            continue
                        
                        # Also try to get from JSON text for verification
                        revision = page.find('mw:revision', namespace)
                        if revision is not None:
                            text_elem = revision.find('mw:text', namespace)
                            if text_elem is not None and text_elem.text:
                                try:
                                    json_data = json.loads(text_elem.text)
                                    if 'redirect' in json_data:
                                        json_target = json_data['redirect']
                                        if json_target != target_qid:
                                            print(f"    WARNING: Mismatch for {source_qid}: redirect title={target_qid}, JSON={json_target}")
                                            target_qid = json_target  # Use JSON version
                                except json.JSONDecodeError:
                                    pass
                        
                        xml_redirects[source_qid] = target_qid
                        self.stats['redirects_found'] += 1
                        
                    except Exception as e:
                        print(f"    Error processing page: {e}")
                        continue
                        
            except Exception as e:
                print(f"  Error processing file {xml_file}: {e}")
                continue
        
        print(f"  Processed {self.stats['xml_files_processed']} XML files")
        print(f"  Found {self.stats['redirects_found']} XML redirects")
        
        return xml_redirects
    
    def resolve_redirect_chains(self, xml_redirects):
        """Resolve redirect chains to find final targets"""
        print("Resolving redirect chains...")
        
        # Get existing MongoDB redirects too
        mongo_redirects = {}
        for entity in self.collection.find({'properties.redirect': {'$exists': True}}):
            qid = entity['qid']
            target = entity['properties']['redirect'][0]['value']
            mongo_redirects[qid] = target
        
        print(f"  Found {len(mongo_redirects):,} MongoDB redirects")
        
        # Combine all redirects
        all_redirects = {}
        all_redirects.update(mongo_redirects)
        all_redirects.update(xml_redirects)
        
        print(f"  Total redirects to resolve: {len(all_redirects):,}")
        
        # Resolve chains
        final_targets = {}
        chains_found = 0
        
        def find_final_target(qid, visited=None):
            """Recursively find the final target, avoiding cycles"""
            if visited is None:
                visited = set()
            
            if qid in visited:
                # Cycle detected
                print(f"    WARNING: Redirect cycle detected involving {qid}")
                return qid
            
            if qid not in all_redirects:
                # This is the final target
                return qid
            
            visited.add(qid)
            target = all_redirects[qid]
            return find_final_target(target, visited)
        
        for redirect_qid in all_redirects:
            final_target = find_final_target(redirect_qid)
            final_targets[redirect_qid] = final_target
            
            # Check if this was a chain
            if all_redirects[redirect_qid] != final_target:
                chains_found += 1
                if chains_found <= 10:  # Show first 10 examples
                    print(f"    Chain: {redirect_qid} -> {all_redirects[redirect_qid]} -> {final_target}")
        
        print(f"  Resolved {chains_found:,} redirect chains")
        return final_targets, all_redirects
    
    def import_xml_redirects(self, xml_redirects):
        """Import XML redirects as MongoDB entities"""
        print("Importing XML redirects to MongoDB...")
        
        bulk_ops = []
        imported = 0
        skipped = 0
        
        for redirect_qid, target_qid in xml_redirects.items():
            # Check if entity already exists
            existing = self.collection.find_one({'qid': redirect_qid})
            if existing:
                # Check if it's already a redirect
                if 'redirect' in existing.get('properties', {}):
                    skipped += 1
                    continue
                # Check if it has content (shouldn't overwrite real entities)
                if (existing.get('properties', {}) or 
                    existing.get('labels', {}) or 
                    existing.get('descriptions', {})):
                    skipped += 1
                    print(f"    Skipping {redirect_qid}: entity has content")
                    continue
            
            # Create redirect entity
            redirect_entity = {
                '_id': redirect_qid,
                'qid': redirect_qid,
                'entity_type': 'item',
                'properties': {
                    'redirect': [{
                        'value': target_qid,
                        'type': 'wikibase-item',
                        'claim_id': f"{redirect_qid}_redirect_to_{target_qid}"
                    }]
                },
                'labels': {},
                'descriptions': {},
                'aliases': {}
            }
            
            if existing:
                # Update existing entity
                bulk_ops.append(
                    pymongo.ReplaceOne({'qid': redirect_qid}, redirect_entity)
                )
            else:
                # Insert new entity
                bulk_ops.append(
                    pymongo.InsertOne(redirect_entity)
                )
            
            imported += 1
            
            # Execute in batches
            if len(bulk_ops) >= 1000:
                try:
                    self.collection.bulk_write(bulk_ops)
                    bulk_ops = []
                except Exception as e:
                    print(f"    Bulk write error: {e}")
                    bulk_ops = []
        
        # Execute remaining operations
        if bulk_ops:
            try:
                self.collection.bulk_write(bulk_ops)
            except Exception as e:
                print(f"    Final bulk write error: {e}")
        
        self.stats['redirects_imported'] = imported
        print(f"  Imported {imported:,} XML redirects")
        print(f"  Skipped {skipped:,} existing entities")
    
    def update_all_references_to_final_targets(self, final_targets):
        """Update all references throughout database to point to final targets"""
        print("Updating all references to point to final targets...")
        
        bulk_ops = []
        entities_checked = 0
        entities_updated = 0
        references_updated = 0
        
        for entity in self.collection.find():
            entities_checked += 1
            if entities_checked % 10000 == 0:
                print(f"  Checked {entities_checked:,} entities...")
            
            # Skip redirect entities themselves
            if 'redirect' in entity.get('properties', {}):
                continue
            
            entity_has_updates = False
            updates = {}
            
            # Check all properties for references
            properties = entity.get('properties', {})
            for prop_id, claims in properties.items():
                updated_claims = []
                claims_updated = False
                
                for claim in claims:
                    updated_claim = claim.copy()
                    value = claim.get('value')
                    
                    # Check different value types for QID references
                    if isinstance(value, str) and value.startswith('Q'):
                        if value in final_targets and final_targets[value] != value:
                            # This reference needs updating
                            updated_claim['value'] = final_targets[value]
                            claims_updated = True
                            references_updated += 1
                    elif isinstance(value, dict) and 'id' in value:
                        ref_qid = value.get('id')
                        if ref_qid and ref_qid.startswith('Q'):
                            if ref_qid in final_targets and final_targets[ref_qid] != ref_qid:
                                # This reference needs updating
                                updated_claim['value'] = value.copy()
                                updated_claim['value']['id'] = final_targets[ref_qid]
                                claims_updated = True
                                references_updated += 1
                    
                    updated_claims.append(updated_claim)
                
                if claims_updated:
                    updates[f'properties.{prop_id}'] = updated_claims
                    entity_has_updates = True
            
            # Add to batch if entity needs updates
            if entity_has_updates:
                bulk_ops.append(
                    pymongo.UpdateOne(
                        {'qid': entity['qid']},
                        {'$set': updates}
                    )
                )
                entities_updated += 1
                
                # Execute batch when full
                if len(bulk_ops) >= 1000:
                    self.collection.bulk_write(bulk_ops)
                    bulk_ops = []
        
        # Execute final batch
        if bulk_ops:
            self.collection.bulk_write(bulk_ops)
        
        print(f"  Checked {entities_checked:,} entities")
        print(f"  Updated {entities_updated:,} entities")
        print(f"  Updated {references_updated:,} references")
        
        self.stats['references_updated'] = references_updated
        self.stats['entities_updated'] = entities_updated
    
    def run_xml_redirect_import(self):
        """Run complete XML redirect import process"""
        start_time = time.time()
        
        print("XML REDIRECT IMPORT PROCESS")
        print("=" * 60)
        print("Step 1: Find all XML redirects in export files")
        print("Step 2: Resolve redirect chains to final targets")
        print("Step 3: Import XML redirects to MongoDB")
        print("Step 4: Update all references to point to final targets")
        print("=" * 60)
        print()
        
        # Step 1: Find XML redirects
        xml_redirects = self.find_all_xml_redirects()
        
        if not xml_redirects:
            print("No XML redirects found")
            return
        
        print()
        
        # Step 2: Resolve redirect chains
        final_targets, all_redirects = self.resolve_redirect_chains(xml_redirects)
        
        print()
        
        # Step 3: Import XML redirects
        self.import_xml_redirects(xml_redirects)
        
        print()
        
        # Step 4: Update all references
        self.update_all_references_to_final_targets(final_targets)
        
        duration = time.time() - start_time
        
        print()
        print("=" * 60)
        print("XML REDIRECT IMPORT COMPLETE")
        print("=" * 60)
        print("RESULTS:")
        print(f"  XML files processed: {self.stats['xml_files_processed']}")
        print(f"  XML redirects found: {self.stats['redirects_found']:,}")
        print(f"  XML redirects imported: {self.stats['redirects_imported']:,}")
        print(f"  References updated: {self.stats['references_updated']:,}")
        print(f"  Entities updated: {self.stats['entities_updated']:,}")
        print(f"  Duration: {duration:.1f} seconds")
        
        if self.stats['references_updated'] > 0:
            print(f"  Average: {self.stats['references_updated']/duration:.1f} references/second")
        
        print()
        print("SUCCESS: All XML redirects imported and references resolved!")
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()

def main():
    importer = XMLRedirectImporter()
    
    try:
        importer.run_xml_redirect_import()
    finally:
        importer.close()

if __name__ == "__main__":
    main()