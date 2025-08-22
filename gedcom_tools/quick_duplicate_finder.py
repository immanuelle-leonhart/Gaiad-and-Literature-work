#!/usr/bin/env python3
"""
Quick Duplicate Name Finder

A more efficient version that processes entities in batches and focuses
on the most likely duplicates for entities without external identifiers.
"""

import pymongo
import re
from collections import defaultdict
import csv

# Configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
OUTPUT_FILE = "potential_duplicates_quick.csv"

# External identifier properties to check
EXTERNAL_ID_PROPS = ['P61', 'P62', 'P63', 'P1185', 'P1819', 'P2949', 'P4638', 'P4159', 'P7929', 'P535', 'P6821']

class QuickDuplicateFinder:
    def __init__(self, mongo_uri=MONGO_URI, output_file=OUTPUT_FILE):
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db['entities']
        self.output_file = output_file
        
        self.stats = {
            'entities_without_ids': 0,
            'entities_with_ids': 0,
            'potential_duplicates': 0,
            'exact_matches': 0
        }
        
        print(f"Connected to MongoDB: {DATABASE_NAME}.entities")
    
    def normalize_name(self, name):
        """Simple name normalization"""
        if not name:
            return ""
        
        # Convert to lowercase and remove extra spaces
        name = name.lower().strip()
        
        # Remove common titles and suffixes
        name = re.sub(r'\b(sir|lord|lady|duke|duchess|count|countess|baron|baroness|earl|prince|princess|king|queen|emperor|empress|jr\.?|sr\.?|ii|iii|iv|v)\b', '', name)
        
        # Remove extra whitespace
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name
    
    def has_external_identifiers(self, entity):
        """Check if entity has external identifiers"""
        properties = entity.get('properties', {})
        for prop in EXTERNAL_ID_PROPS:
            if prop in properties:
                return True
        return False
    
    def find_quick_duplicates(self):
        """Find exact name matches efficiently"""
        print("=== QUICK DUPLICATE NAME ANALYSIS ===")
        print()
        
        # Build name index for entities WITH identifiers
        print("Building name index for entities with identifiers...")
        name_to_entities = defaultdict(list)
        
        entities_with_ids = 0
        for entity in self.collection.find():
            # Skip redirects
            if 'redirect' in entity.get('properties', {}):
                continue
            
            if self.has_external_identifiers(entity):
                entities_with_ids += 1
                qid = entity['qid']
                labels = entity.get('labels', {})
                
                for lang, label in labels.items():
                    if label and isinstance(label, str):
                        normalized = self.normalize_name(label)
                        if normalized and len(normalized) > 2:  # Avoid very short names
                            name_to_entities[normalized].append({
                                'qid': qid,
                                'original_name': label,
                                'language': lang
                            })
        
        print(f"Indexed {entities_with_ids:,} entities with identifiers")
        print(f"Built index with {len(name_to_entities):,} unique names")
        print()
        
        # Find entities WITHOUT identifiers and check for matches
        print("Finding entities without identifiers and checking for matches...")
        duplicates = []
        entities_without_ids = 0
        entities_checked = 0
        
        for entity in self.collection.find():
            # Skip redirects
            if 'redirect' in entity.get('properties', {}):
                continue
            
            if not self.has_external_identifiers(entity):
                entities_without_ids += 1
                entities_checked += 1
                
                if entities_checked % 5000 == 0:
                    print(f"  Checked {entities_checked:,} entities without IDs...")
                
                qid = entity['qid']
                labels = entity.get('labels', {})
                found_match = False
                
                for lang, label in labels.items():
                    if label and isinstance(label, str):
                        normalized = self.normalize_name(label)
                        
                        if normalized in name_to_entities:
                            # Found exact match(es)
                            for match in name_to_entities[normalized]:
                                duplicates.append({
                                    'no_id_qid': qid,
                                    'no_id_name': label,
                                    'no_id_lang': lang,
                                    'has_id_qid': match['qid'],
                                    'has_id_name': match['original_name'],
                                    'has_id_lang': match['language'],
                                    'normalized_name': normalized
                                })
                                found_match = True
                
                if found_match:
                    self.stats['potential_duplicates'] += 1
        
        self.stats['entities_without_ids'] = entities_without_ids
        self.stats['entities_with_ids'] = entities_with_ids
        self.stats['exact_matches'] = len(duplicates)
        
        print(f"  Checked {entities_checked:,} entities without IDs total")
        print()
        
        return duplicates
    
    def save_results(self, duplicates):
        """Save results to CSV"""
        if not duplicates:
            return
        
        print(f"Saving {len(duplicates):,} potential duplicates to {self.output_file}...")
        
        with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            writer.writerow([
                'entity_without_ids',
                'name_without_ids',
                'lang_without_ids',
                'entity_with_ids',
                'name_with_ids', 
                'lang_with_ids',
                'normalized_name'
            ])
            
            for dup in duplicates:
                writer.writerow([
                    dup['no_id_qid'],
                    dup['no_id_name'],
                    dup['no_id_lang'],
                    dup['has_id_qid'],
                    dup['has_id_name'],
                    dup['has_id_lang'],
                    dup['normalized_name']
                ])
        
        print(f"Results saved to {self.output_file}")
    
    def print_statistics(self):
        """Print statistics"""
        print("=== STATISTICS ===")
        print(f"Entities with external identifiers: {self.stats['entities_with_ids']:,}")
        print(f"Entities WITHOUT external identifiers: {self.stats['entities_without_ids']:,}")
        print(f"Entities without IDs that have name matches: {self.stats['potential_duplicates']:,}")
        print(f"Total exact name matches found: {self.stats['exact_matches']:,}")
        
        if self.stats['entities_without_ids'] > 0:
            percentage = (self.stats['potential_duplicates'] / self.stats['entities_without_ids']) * 100
            print(f"Percentage of no-ID entities with potential matches: {percentage:.1f}%")
    
    def show_samples(self, duplicates):
        """Show sample matches"""
        if not duplicates:
            return
        
        print()
        print("=== SAMPLE POTENTIAL MATCHES ===")
        print("(Entity without IDs -> Entity with IDs)")
        
        for i, dup in enumerate(duplicates[:10]):
            print(f"{i+1}. {dup['no_id_qid']} (\"{dup['no_id_name']}\") -> {dup['has_id_qid']} (\"{dup['has_id_name']}\")")
        
        if len(duplicates) > 10:
            print(f"... and {len(duplicates) - 10:,} more matches")
    
    def close(self):
        """Close connection"""
        self.client.close()

def main():
    finder = QuickDuplicateFinder()
    
    try:
        duplicates = finder.find_quick_duplicates()
        
        if duplicates:
            finder.save_results(duplicates)
            finder.show_samples(duplicates)
        
        finder.print_statistics()
        
        if duplicates:
            print(f"\nSUCCESS: Found {len(duplicates):,} potential name matches!")
            print("These entities without external IDs have the same names as entities WITH IDs.")
            print("This suggests they might be the same people and could potentially be linked.")
        else:
            print("\nNo exact name matches found between entities with and without IDs.")
    
    finally:
        finder.close()

if __name__ == "__main__":
    main()