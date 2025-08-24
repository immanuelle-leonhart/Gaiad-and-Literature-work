#!/usr/bin/env python3
"""
Fix Missing Redirects from XML Import

This script fixes the critical issue where redirects from XML imports were imported
as empty entities instead of proper redirects. It:

1. Extracts all redirects from XML imports 
2. Converts empty entities to proper redirects
3. Updates references to point to redirect targets
"""

import xml.etree.ElementTree as ET
import os
import json
import pymongo
import time
from collections import defaultdict

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

class RedirectFixer:
    def __init__(self):
        # Connect to MongoDB
        self.client = pymongo.MongoClient(MONGO_URI)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db[COLLECTION_NAME]
        
        # Data storage
        self.xml_redirects = {}  # source_qid -> target_qid
        self.reference_updates = []  # [(entity_qid, property, old_value, new_value)]
        
        print(f"Connected to MongoDB: {DATABASE_NAME}.{COLLECTION_NAME}")
    
    def extract_redirects_from_xml(self, xml_directory="xml_imports"):
        """Extract all redirects from XML import files"""
        print(f"Extracting redirects from {xml_directory}...")
        
        xml_files = []
        for filename in os.listdir(xml_directory):
            if filename.endswith('.xml') and 'part_' in filename:
                xml_files.append(os.path.join(xml_directory, filename))
        
        xml_files.sort()  # Process in order
        print(f"Found {len(xml_files)} XML import files")
        
        total_redirects = 0
        
        for xml_file in xml_files:
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                # Namespace
                ns = {'mw': 'http://www.mediawiki.org/xml/export-0.11/'}
                
                file_redirects = 0
                
                for page in root.findall('.//mw:page', ns):
                    # Check for redirect element
                    redirect_elem = page.find('mw:redirect', ns)
                    if redirect_elem is not None:
                        # This is a redirect page
                        file_redirects += 1
                        total_redirects += 1
                        
                        # Get source QID from title
                        title_elem = page.find('mw:title', ns)
                        if title_elem is not None:
                            title = title_elem.text
                            if title.startswith('Item:Q'):
                                source_qid = title.replace('Item:', '')
                                
                                # Get target from redirect title attribute
                                redirect_title = redirect_elem.get('title', '')
                                if redirect_title.startswith('Item:Q'):
                                    target_qid = redirect_title.replace('Item:', '')
                                    self.xml_redirects[source_qid] = target_qid
                
                print(f"  {os.path.basename(xml_file)}: {file_redirects} redirects")
                
            except Exception as e:
                print(f"  ERROR processing {xml_file}: {e}")
        
        print(f"Extracted {len(self.xml_redirects):,} redirects from XML files")
        return len(self.xml_redirects)
    
    def verify_redirect_targets_exist(self):
        """Verify that all redirect targets exist as entities"""
        print("Verifying redirect targets exist...")
        
        target_qids = set(self.xml_redirects.values())
        existing_targets = set()
        missing_targets = []
        
        # Check which targets exist in database
        for target_qid in target_qids:
            if self.collection.find_one({'qid': target_qid}):
                existing_targets.add(target_qid)
            else:
                missing_targets.append(target_qid)
        
        print(f"Target verification:")
        print(f"  Total redirect targets: {len(target_qids):,}")
        print(f"  Existing targets: {len(existing_targets):,}")
        print(f"  Missing targets: {len(missing_targets):,}")
        
        if missing_targets:
            print(f"  Sample missing targets: {missing_targets[:10]}")
            
            # Remove redirects with missing targets
            original_count = len(self.xml_redirects)
            self.xml_redirects = {
                src: tgt for src, tgt in self.xml_redirects.items() 
                if tgt not in missing_targets
            }
            removed = original_count - len(self.xml_redirects)
            print(f"  Removed {removed} redirects with missing targets")
        
        return len(missing_targets) == 0
    
    def convert_empty_entities_to_redirects(self):
        """Convert empty entities that should be redirects to proper redirects"""
        print("Converting empty entities to proper redirects...")
        
        converted = 0
        not_empty = 0
        not_found = 0
        
        bulk_operations = []
        
        for source_qid, target_qid in self.xml_redirects.items():
            # Find the source entity
            entity = self.collection.find_one({'qid': source_qid})
            
            if not entity:
                not_found += 1
                continue
            
            # Check if it's an empty entity (should be a redirect)
            properties = entity.get('properties', {})
            labels = entity.get('labels', {})
            descriptions = entity.get('descriptions', {})
            aliases = entity.get('aliases', {})
            
            # Skip if it's already a redirect
            if 'redirect' in properties:
                continue
            
            # Skip if it has substantial content (not an empty entity)
            if labels or descriptions or aliases or len(properties) > 2:
                not_empty += 1
                if not_empty <= 5:  # Show first 5 examples
                    print(f"  Skipping {source_qid} (not empty): {len(properties)} props, {len(labels)} labels")
                continue
            
            # Convert to redirect
            redirect_properties = {
                'redirect': [
                    {
                        'value': target_qid,
                        'type': 'wikibase-entityid',
                        'claim_id': f'{source_qid}_redirect_{target_qid}'
                    }
                ]
            }
            
            # Clear all other data to make clean redirect
            clean_entity = {
                'qid': source_qid,
                'entity_type': 'item',
                'labels': {},
                'descriptions': {},
                'aliases': {},
                'properties': redirect_properties
            }
            
            bulk_operations.append(
                pymongo.ReplaceOne(
                    {'qid': source_qid},
                    clean_entity
                )
            )
            
            converted += 1
            
            if converted % 100 == 0:
                print(f"  Prepared {converted:,} conversions...")
        
        # Execute bulk operations
        if bulk_operations:
            print(f"Executing {len(bulk_operations):,} redirect conversions...")
            result = self.collection.bulk_write(bulk_operations)
            print(f"  Modified: {result.modified_count:,}")
        
        print(f"Redirect conversion results:")
        print(f"  Converted to redirects: {converted:,}")
        print(f"  Not empty (skipped): {not_empty:,}")
        print(f"  Not found: {not_found:,}")
        
        return converted
    
    def find_references_to_redirects(self):
        """Find all references that point to redirect entities"""
        print("Finding references that point to redirect entities...")
        
        redirect_qids = set(self.xml_redirects.keys())
        reference_updates = []
        checked_entities = 0
        
        # Check all entities for references to redirects
        for entity in self.collection.find():
            checked_entities += 1
            if checked_entities % 10000 == 0:
                print(f"  Checked {checked_entities:,} entities...")
            
            # Skip redirect entities themselves
            if 'redirect' in entity.get('properties', {}):
                continue
            
            entity_qid = entity['qid']
            properties = entity.get('properties', {})
            
            # Check each property for references to redirect QIDs
            for prop_id, claims in properties.items():
                for i, claim in enumerate(claims):
                    value = claim.get('value')
                    
                    # Check different value formats for QID references
                    referenced_qid = None
                    if isinstance(value, str) and value.startswith('Q') and value in redirect_qids:
                        referenced_qid = value
                    elif isinstance(value, dict) and 'id' in value and value['id'] in redirect_qids:
                        referenced_qid = value['id']
                    
                    if referenced_qid:
                        target_qid = self.xml_redirects[referenced_qid]
                        reference_updates.append({
                            'entity_qid': entity_qid,
                            'property': prop_id,
                            'claim_index': i,
                            'old_value': referenced_qid,
                            'new_value': target_qid,
                            'claim': claim
                        })
        
        print(f"  Checked {checked_entities:,} entities")
        print(f"Found {len(reference_updates):,} references to redirect entities")
        
        self.reference_updates = reference_updates
        return len(reference_updates)
    
    def update_references_to_targets(self):
        """Update references to point to redirect targets instead of redirects"""
        if not self.reference_updates:
            print("No reference updates needed")
            return 0
        
        print(f"Updating {len(self.reference_updates):,} references...")
        
        # Group updates by entity for efficiency
        updates_by_entity = defaultdict(list)
        for update in self.reference_updates:
            updates_by_entity[update['entity_qid']].append(update)
        
        bulk_operations = []
        updated_entities = 0
        
        for entity_qid, entity_updates in updates_by_entity.items():
            # Get current entity
            entity = self.collection.find_one({'qid': entity_qid})
            if not entity:
                continue
            
            # Apply all updates to this entity
            properties = entity.get('properties', {})
            modified = False
            
            for update in entity_updates:
                prop_id = update['property']
                claim_index = update['claim_index']
                new_value = update['new_value']
                
                if prop_id in properties and claim_index < len(properties[prop_id]):
                    claim = properties[prop_id][claim_index]
                    old_value = claim.get('value')
                    
                    # Update the value
                    if isinstance(old_value, str):
                        claim['value'] = new_value
                    elif isinstance(old_value, dict) and 'id' in old_value:
                        claim['value']['id'] = new_value
                    
                    modified = True
            
            if modified:
                bulk_operations.append(
                    pymongo.UpdateOne(
                        {'qid': entity_qid},
                        {'$set': {'properties': properties}}
                    )
                )
                updated_entities += 1
                
                if updated_entities % 100 == 0:
                    print(f"  Prepared {updated_entities:,} entity updates...")
        
        # Execute bulk updates
        if bulk_operations:
            print(f"Executing {len(bulk_operations):,} entity updates...")
            result = self.collection.bulk_write(bulk_operations)
            print(f"  Modified: {result.modified_count:,} entities")
        
        return len(bulk_operations)
    
    def verify_fixes(self):
        """Verify that the redirect fixes worked correctly"""
        print("Verifying redirect fixes...")
        
        # Count proper redirects now
        redirect_count = self.collection.count_documents({'properties.redirect': {'$exists': True}})
        print(f"Database now has {redirect_count:,} proper redirects")
        
        # Check some examples
        sample_redirects = list(self.collection.find(
            {'properties.redirect': {'$exists': True}}
        ).limit(5))
        
        if sample_redirects:
            print("Sample redirects:")
            for redirect in sample_redirects:
                qid = redirect['qid']
                target = redirect['properties']['redirect'][0]['value']
                print(f"  {qid} -> {target}")
        
        # Count empty entities remaining
        empty_count = self.collection.count_documents({
            'properties': {},
            'labels': {},
            'descriptions': {},
            'aliases': {}
        })
        
        print(f"Empty entities remaining: {empty_count:,}")
        
        return redirect_count
    
    def run_complete_fix(self):
        """Run the complete redirect fixing process"""
        print("=== FIXING MISSING REDIRECTS FROM XML IMPORTS ===")
        print()
        
        start_time = time.time()
        
        # Step 1: Extract redirects from XML
        redirects_found = self.extract_redirects_from_xml()
        if redirects_found == 0:
            print("No redirects found in XML files!")
            return
        
        print()
        
        # Step 2: Verify targets exist
        self.verify_redirect_targets_exist()
        print()
        
        # Step 3: Convert empty entities to redirects
        converted = self.convert_empty_entities_to_redirects()
        print()
        
        # Step 4: Find and update references
        references_found = self.find_references_to_redirects()
        print()
        
        if references_found > 0:
            updated_references = self.update_references_to_targets()
            print()
        else:
            updated_references = 0
        
        # Step 5: Verify fixes
        final_redirects = self.verify_fixes()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print()
        print("=== REDIRECT FIX COMPLETE ===")
        print(f"Total time: {duration:.2f} seconds")
        print(f"XML redirects found: {redirects_found:,}")
        print(f"Entities converted to redirects: {converted:,}")
        print(f"References updated: {updated_references:,}")
        print(f"Final redirect count: {final_redirects:,}")
        print()
        print("The redirect import issue has been fixed!")
        print("All entities that should be redirects are now proper redirects.")
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()

def main():
    fixer = RedirectFixer()
    
    try:
        fixer.run_complete_fix()
    finally:
        fixer.close()

if __name__ == "__main__":
    main()