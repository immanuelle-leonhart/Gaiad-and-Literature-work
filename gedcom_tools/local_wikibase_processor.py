#!/usr/bin/env python3
"""
LOCAL WIKIBASE PROCESSOR

Processes downloaded Wikibase entities locally without API calls.
Much faster than remote processing for bulk operations.
"""

import json
import os
import time
import csv
import re
from pathlib import Path
from collections import defaultdict

class LocalWikibaseProcessor:
    def __init__(self, wikibase_dir="wikibase_download"):
        self.base_dir = Path(wikibase_dir)
        self.items_dir = self.base_dir / "items"
        self.properties_dir = self.base_dir / "properties"
        self.changes = []  # Track all changes to export later
        
        if not self.base_dir.exists():
            raise FileNotFoundError(f"Wikibase directory not found: {self.base_dir}")
    
    def load_entity(self, entity_id):
        """Load an entity from local files"""
        if entity_id.startswith('Q'):
            entity_file = self.items_dir / f"{entity_id}.json"
        elif entity_id.startswith('P'):
            entity_file = self.properties_dir / f"{entity_id}.json"
        else:
            return None
        
        if not entity_file.exists():
            return None
        
        try:
            with open(entity_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    def save_entity(self, entity_id, entity_data):
        """Save modified entity locally"""
        if entity_id.startswith('Q'):
            entity_file = self.items_dir / f"{entity_id}.json"
        elif entity_id.startswith('P'):
            entity_file = self.properties_dir / f"{entity_id}.json"
        else:
            return False
        
        try:
            with open(entity_file, 'w', encoding='utf-8') as f:
                json.dump(entity_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    def add_change_log(self, entity_id, change_type, details):
        """Log a change for later export"""
        self.changes.append({
            'entity_id': entity_id,
            'change_type': change_type,
            'details': details,
            'timestamp': time.time()
        })
    
    def fix_sex_property(self, entity_id, entity_data):
        """Convert P11 (deprecated sex) to P55 (sex/gender)"""
        if 'claims' not in entity_data:
            return False
        
        modified = False
        
        if 'P11' in entity_data['claims']:
            # Move P11 claims to P55
            if 'P55' not in entity_data['claims']:
                entity_data['claims']['P55'] = []
            
            for claim in entity_data['claims']['P11']:
                # Update property ID in claim
                claim['mainsnak']['property'] = 'P55'
                entity_data['claims']['P55'].append(claim)
                modified = True
            
            # Remove old P11 claims
            del entity_data['claims']['P11']
            self.add_change_log(entity_id, 'fix_sex_property', 'P11 → P55')
        
        return modified
    
    def fix_date_properties(self, entity_id, entity_data):
        """Convert P7/P8 to P56/P57"""
        if 'claims' not in entity_data:
            return False
        
        modified = False
        
        # P7 (birth date) → P56 (birth date)
        if 'P7' in entity_data['claims']:
            if 'P56' not in entity_data['claims']:
                entity_data['claims']['P56'] = []
            
            for claim in entity_data['claims']['P7']:
                claim['mainsnak']['property'] = 'P56'
                entity_data['claims']['P56'].append(claim)
                modified = True
            
            del entity_data['claims']['P7']
            self.add_change_log(entity_id, 'fix_date_properties', 'P7 → P56')
        
        # P8 (death date) → P57 (death date)
        if 'P8' in entity_data['claims']:
            if 'P57' not in entity_data['claims']:
                entity_data['claims']['P57'] = []
            
            for claim in entity_data['claims']['P8']:
                claim['mainsnak']['property'] = 'P57'
                entity_data['claims']['P57'].append(claim)
                modified = True
            
            del entity_data['claims']['P8']
            self.add_change_log(entity_id, 'fix_date_properties', 'P8 → P57')
        
        return modified
    
    def extract_identifiers_from_refn(self, entity_id, entity_data):
        """Extract Wikidata QIDs, Geni IDs, and UUIDs from REFN properties"""
        if 'claims' not in entity_data:
            return False
        
        modified = False
        refn_claims_to_remove = []
        
        if 'P41' in entity_data['claims']:
            for i, claim in enumerate(entity_data['claims']['P41']):
                if 'datavalue' not in claim['mainsnak']:
                    continue
                
                refn_value = claim['mainsnak']['datavalue']['value']
                
                # Check for Wikidata QID (Q followed by numbers)
                if re.match(r'^Q\d+$', refn_value):
                    # Add to P44 (Wikidata entity ID)
                    if 'P44' not in entity_data['claims']:
                        entity_data['claims']['P44'] = []
                    
                    new_claim = {
                        'mainsnak': {
                            'snaktype': 'value',
                            'property': 'P44',
                            'datavalue': {
                                'value': refn_value,
                                'type': 'string'
                            }
                        },
                        'type': 'statement',
                        'rank': 'normal'
                    }
                    entity_data['claims']['P44'].append(new_claim)
                    refn_claims_to_remove.append(i)
                    modified = True
                    self.add_change_log(entity_id, 'extract_wikidata_id', refn_value)
                
                # Check for Geni ID (numbers, possibly with letters)
                elif re.match(r'^\d+$', refn_value) or 'geni' in refn_value.lower():
                    # Add to P43 (Geni ID)
                    if 'P43' not in entity_data['claims']:
                        entity_data['claims']['P43'] = []
                    
                    new_claim = {
                        'mainsnak': {
                            'snaktype': 'value',
                            'property': 'P43',
                            'datavalue': {
                                'value': refn_value,
                                'type': 'string'
                            }
                        },
                        'type': 'statement',
                        'rank': 'normal'
                    }
                    entity_data['claims']['P43'].append(new_claim)
                    refn_claims_to_remove.append(i)
                    modified = True
                    self.add_change_log(entity_id, 'extract_geni_id', refn_value)
                
                # Check for UUID (hex string, usually 32 chars)
                elif re.match(r'^[A-F0-9]{8,32}$', refn_value, re.IGNORECASE):
                    # Add to P60 (UUID REFN)
                    if 'P60' not in entity_data['claims']:
                        entity_data['claims']['P60'] = []
                    
                    new_claim = {
                        'mainsnak': {
                            'snaktype': 'value',
                            'property': 'P60',
                            'datavalue': {
                                'value': refn_value,
                                'type': 'string'
                            }
                        },
                        'type': 'statement',
                        'rank': 'normal'
                    }
                    entity_data['claims']['P60'].append(new_claim)
                    refn_claims_to_remove.append(i)
                    modified = True
                    self.add_change_log(entity_id, 'extract_uuid', refn_value)
            
            # Remove processed REFN claims (in reverse order to preserve indices)
            for i in reversed(refn_claims_to_remove):
                del entity_data['claims']['P41'][i]
            
            # Remove P41 entirely if empty
            if not entity_data['claims']['P41']:
                del entity_data['claims']['P41']
        
        return modified
    
    def get_entity_csv_data(self, entity_id, entity_data):
        """Extract CSV correspondence data from entity"""
        en_label = ""
        if 'labels' in entity_data and 'en' in entity_data['labels']:
            en_label = entity_data['labels']['en']['value']
        
        wikidata_qids = []
        geni_ids = []
        uuids = []
        
        if 'claims' in entity_data:
            # Extract Wikidata QIDs
            if 'P44' in entity_data['claims']:
                for claim in entity_data['claims']['P44']:
                    if 'datavalue' in claim['mainsnak']:
                        wikidata_qids.append(claim['mainsnak']['datavalue']['value'])
            
            # Extract Geni IDs
            if 'P43' in entity_data['claims']:
                for claim in entity_data['claims']['P43']:
                    if 'datavalue' in claim['mainsnak']:
                        geni_ids.append(claim['mainsnak']['datavalue']['value'])
            
            # Extract UUIDs
            if 'P60' in entity_data['claims']:
                for claim in entity_data['claims']['P60']:
                    if 'datavalue' in claim['mainsnak']:
                        uuids.append(claim['mainsnak']['datavalue']['value'])
        
        return {
            'evolutionism_qid': entity_id,
            'wikidata_qid': '|'.join(wikidata_qids),
            'geni_id': '|'.join(geni_ids),
            'en_label': en_label,
            'uuid': '|'.join(uuids)
        }
    
    def process_all_entities(self):
        """Process all entities with the comprehensive database fixer logic"""
        print("Starting local processing of all entities...")
        
        # Get all entity files
        entity_files = list(self.items_dir.glob("Q*.json"))
        total_entities = len(entity_files)
        
        print(f"Found {total_entities} entities to process")
        
        processed = 0
        modified = 0
        csv_data = []
        
        for entity_file in entity_files:
            entity_id = entity_file.stem  # Get filename without extension
            
            entity_data = self.load_entity(entity_id)
            if not entity_data:
                continue
            
            entity_modified = False
            
            # Apply all fixes
            if self.fix_sex_property(entity_id, entity_data):
                entity_modified = True
            
            if self.fix_date_properties(entity_id, entity_data):
                entity_modified = True
            
            if self.extract_identifiers_from_refn(entity_id, entity_data):
                entity_modified = True
            
            # Save if modified
            if entity_modified:
                self.save_entity(entity_id, entity_data)
                modified += 1
            
            # Add to CSV data
            csv_row = self.get_entity_csv_data(entity_id, entity_data)
            csv_data.append(csv_row)
            
            processed += 1
            
            # Progress update
            if processed % 1000 == 0:
                progress = (processed / total_entities) * 100
                print(f"Progress: {progress:.1f}% ({processed}/{total_entities}) - {modified} modified")
        
        # Save CSV correspondence file
        print("Saving CSV correspondence file...")
        with open('qid_correspondence_local.csv', 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['evolutionism_qid', 'wikidata_qid', 'geni_id', 'en_label', 'uuid']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
        
        # Save change log
        print("Saving change log...")
        with open('local_processing_changes.json', 'w', encoding='utf-8') as f:
            json.dump(self.changes, f, indent=2, ensure_ascii=False)
        
        print(f"\nProcessing complete!")
        print(f"Total entities: {total_entities}")
        print(f"Modified entities: {modified}")
        print(f"Changes made: {len(self.changes)}")
        print(f"CSV saved: qid_correspondence_local.csv")
        print(f"Change log: local_processing_changes.json")

def main():
    print("=" * 60)
    print("LOCAL WIKIBASE PROCESSOR")
    print("Processing downloaded Wikibase entities")
    print("=" * 60)
    
    try:
        processor = LocalWikibaseProcessor()
        processor.process_all_entities()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please run wikibase_downloader.py first to download the database")

if __name__ == '__main__':
    main()