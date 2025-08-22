#!/usr/bin/env python3
"""
Find Potential Duplicate Names for Entities Without External Identifiers

This script identifies entities that have no external genealogical identifiers
and searches for other entities in the database with similar or identical names
that might represent the same person.

This helps identify potential matches that could be linked or merged.
"""

import pymongo
import re
from collections import defaultdict
from difflib import SequenceMatcher
import csv

# Configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
OUTPUT_FILE = "potential_duplicate_names.csv"

# External identifier properties to check
EXTERNAL_ID_PROPS = [
    'P61',   # Wikidata QID
    'P62',   # Geni ID
    'P63',   # UUID
    'P1185', # Rodovid person ID
    'P1819', # Genealogics.org person ID
    'P2949', # WikiTree ID
    'P4638', # Malarone ID
    'P4159', # Lemon Tree Database ID
    'P7929', # Ancestry.com person ID
    'P535',  # Find a Grave memorial ID
    'P6821', # Geni.com profile ID
    'P8172', # FamAG ID
    'P3051'  # Roglo person ID
]

class DuplicateNameFinder:
    def __init__(self, mongo_uri=MONGO_URI, output_file=OUTPUT_FILE):
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db['entities']
        self.output_file = output_file
        
        self.stats = {
            'total_entities': 0,
            'entities_with_identifiers': 0,
            'entities_without_identifiers': 0,
            'entities_with_labels': 0,
            'potential_duplicates_found': 0,
            'exact_matches': 0,
            'similar_matches': 0
        }
        
        # Build name index for faster searching
        self.name_index = defaultdict(list)  # name -> [qids]
        
        print(f"Connected to MongoDB: {DATABASE_NAME}.entities")
        print(f"Output file: {output_file}")
    
    def normalize_name(self, name):
        """Normalize a name for comparison"""
        if not name:
            return ""
        
        # Convert to lowercase
        name = name.lower()
        
        # Remove common titles and suffixes
        name = re.sub(r'\b(sir|lord|lady|duke|duchess|count|countess|baron|baroness|earl|prince|princess|king|queen|emperor|empress)\b', '', name)
        name = re.sub(r'\b(jr\.?|sr\.?|ii|iii|iv|v|vi|vii|viii|ix|x)\b', '', name)
        name = re.sub(r'\b(of|von|van|de|del|della|du|da|le|la|el|al)\b', '', name)
        
        # Remove extra whitespace and punctuation
        name = re.sub(r'[^\w\s]', ' ', name)
        name = re.sub(r'\s+', ' ', name)
        name = name.strip()
        
        return name
    
    def build_name_index(self):
        """Build an index of all entity names for faster searching"""
        print("Building name index...")
        
        for entity in self.collection.find():
            self.stats['total_entities'] += 1
            
            if self.stats['total_entities'] % 10000 == 0:
                print(f"  Indexed {self.stats['total_entities']:,} entities...")
            
            qid = entity['qid']
            
            # Skip redirect entities
            if 'redirect' in entity.get('properties', {}):
                continue
            
            # Get labels
            labels = entity.get('labels', {})
            if labels:
                self.stats['entities_with_labels'] += 1
                
                # Index all language labels
                for lang, label in labels.items():
                    if label and isinstance(label, str):
                        normalized = self.normalize_name(label)
                        if normalized:
                            self.name_index[normalized].append({
                                'qid': qid,
                                'original_name': label,
                                'language': lang
                            })
        
        print(f"  Indexed {self.stats['total_entities']:,} entities")
        print(f"  Built index with {len(self.name_index):,} unique normalized names")
        print()
    
    def has_external_identifiers(self, entity):
        """Check if entity has any external genealogical identifiers"""
        properties = entity.get('properties', {})
        
        for prop in EXTERNAL_ID_PROPS:
            if prop in properties:
                return True
        return False
    
    def similarity_score(self, name1, name2):
        """Calculate similarity score between two names"""
        return SequenceMatcher(None, name1, name2).ratio()
    
    def find_duplicates_for_entity(self, entity):
        """Find potential duplicates for a single entity"""
        qid = entity['qid']
        labels = entity.get('labels', {})
        
        if not labels:
            return []
        
        potential_duplicates = []
        
        for lang, label in labels.items():
            if not label or not isinstance(label, str):
                continue
            
            normalized = self.normalize_name(label)
            if not normalized:
                continue
            
            # Look for exact matches
            if normalized in self.name_index:
                for match in self.name_index[normalized]:
                    if match['qid'] != qid:  # Don't match with self
                        potential_duplicates.append({
                            'target_qid': qid,
                            'target_name': label,
                            'target_lang': lang,
                            'match_qid': match['qid'],
                            'match_name': match['original_name'],
                            'match_lang': match['language'],
                            'similarity': 1.0,
                            'match_type': 'exact'
                        })
            
            # Look for similar matches (fuzzy matching)
            for index_name, matches in self.name_index.items():
                if index_name != normalized:  # Skip exact matches (already found)
                    similarity = self.similarity_score(normalized, index_name)
                    
                    # Only consider high similarity matches
                    if similarity >= 0.85:
                        for match in matches:
                            if match['qid'] != qid:  # Don't match with self
                                potential_duplicates.append({
                                    'target_qid': qid,
                                    'target_name': label,
                                    'target_lang': lang,
                                    'match_qid': match['qid'],
                                    'match_name': match['original_name'],
                                    'match_lang': match['language'],
                                    'similarity': similarity,
                                    'match_type': 'similar'
                                })
        
        return potential_duplicates
    
    def find_all_duplicates(self):
        """Find potential duplicates for all entities without external identifiers"""
        print("=== FINDING ENTITIES WITHOUT EXTERNAL IDENTIFIERS ===")
        print()
        
        entities_without_ids = []
        all_duplicates = []
        
        # Find entities without external identifiers
        for entity in self.collection.find():
            # Skip redirect entities
            if 'redirect' in entity.get('properties', {}):
                continue
            
            if not self.has_external_identifiers(entity):
                self.stats['entities_without_identifiers'] += 1
                entities_without_ids.append(entity)
            else:
                self.stats['entities_with_identifiers'] += 1
        
        print(f"Entities with external identifiers: {self.stats['entities_with_identifiers']:,}")
        print(f"Entities WITHOUT external identifiers: {self.stats['entities_without_identifiers']:,}")
        print()
        
        print("=== SEARCHING FOR POTENTIAL DUPLICATES ===")
        print(f"Analyzing {len(entities_without_ids):,} entities without identifiers...")
        print()
        
        # Find duplicates for entities without identifiers
        processed = 0
        for entity in entities_without_ids:
            processed += 1
            
            if processed % 1000 == 0:
                print(f"  Processed {processed:,} entities...")
            
            duplicates = self.find_duplicates_for_entity(entity)
            
            if duplicates:
                self.stats['potential_duplicates_found'] += 1
                
                for dup in duplicates:
                    if dup['match_type'] == 'exact':
                        self.stats['exact_matches'] += 1
                    else:
                        self.stats['similar_matches'] += 1
                
                all_duplicates.extend(duplicates)
        
        print(f"  Processed {processed:,} entities total")
        print()
        
        return all_duplicates
    
    def save_results(self, duplicates):
        """Save results to CSV file"""
        print(f"Saving results to {self.output_file}...")
        
        with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'target_qid',
                'target_name', 
                'target_lang',
                'match_qid',
                'match_name',
                'match_lang',
                'similarity_score',
                'match_type'
            ])
            
            # Sort by similarity score (highest first)
            sorted_duplicates = sorted(duplicates, key=lambda x: x['similarity'], reverse=True)
            
            # Write data
            for dup in sorted_duplicates:
                writer.writerow([
                    dup['target_qid'],
                    dup['target_name'],
                    dup['target_lang'],
                    dup['match_qid'],
                    dup['match_name'],
                    dup['match_lang'],
                    f"{dup['similarity']:.3f}",
                    dup['match_type']
                ])
        
        print(f"Results saved to {self.output_file}")
    
    def print_statistics(self):
        """Print analysis statistics"""
        print()
        print("=== DUPLICATE NAME ANALYSIS STATISTICS ===")
        print(f"Total entities: {self.stats['total_entities']:,}")
        print(f"Entities with labels: {self.stats['entities_with_labels']:,}")
        print(f"Entities with external identifiers: {self.stats['entities_with_identifiers']:,}")
        print(f"Entities WITHOUT external identifiers: {self.stats['entities_without_identifiers']:,}")
        print()
        print(f"Entities with potential duplicates: {self.stats['potential_duplicates_found']:,}")
        print(f"Exact name matches found: {self.stats['exact_matches']:,}")
        print(f"Similar name matches found: {self.stats['similar_matches']:,}")
        print(f"Total potential duplicate pairs: {self.stats['exact_matches'] + self.stats['similar_matches']:,}")
        print()
        
        if self.stats['entities_without_identifiers'] > 0:
            percentage = (self.stats['potential_duplicates_found'] / self.stats['entities_without_identifiers']) * 100
            print(f"Percentage of entities without IDs that have potential duplicates: {percentage:.1f}%")
    
    def show_samples(self, duplicates):
        """Show sample duplicate matches"""
        if not duplicates:
            return
        
        print()
        print("=== SAMPLE POTENTIAL DUPLICATES ===")
        
        # Show some exact matches
        exact_matches = [d for d in duplicates if d['match_type'] == 'exact']
        if exact_matches:
            print("Exact name matches:")
            for i, dup in enumerate(exact_matches[:5]):
                print(f"  {i+1}. {dup['target_qid']} (\"{dup['target_name']}\") matches {dup['match_qid']} (\"{dup['match_name']}\")")
        
        # Show some similar matches
        similar_matches = [d for d in duplicates if d['match_type'] == 'similar']
        if similar_matches:
            print("Similar name matches:")
            for i, dup in enumerate(sorted(similar_matches, key=lambda x: x['similarity'], reverse=True)[:5]):
                print(f"  {i+1}. {dup['target_qid']} (\"{dup['target_name']}\") ~ {dup['match_qid']} (\"{dup['match_name']}\") (similarity: {dup['similarity']:.3f})")
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()

def main():
    finder = DuplicateNameFinder()
    
    try:
        # Build name index
        finder.build_name_index()
        
        # Find duplicates
        duplicates = finder.find_all_duplicates()
        
        # Save results
        if duplicates:
            finder.save_results(duplicates)
            finder.show_samples(duplicates)
        
        # Print statistics
        finder.print_statistics()
        
        if duplicates:
            print(f"\nSUCCESS: Found {len(duplicates):,} potential duplicate name matches!")
            print(f"Results saved to: {finder.output_file}")
            print("\nThese results can help identify:")
            print("- Entities that might represent the same person")
            print("- Potential matches for genealogical database linking")
            print("- Candidates for manual review and possible merging")
        else:
            print("\nNo potential duplicate names found.")
        
    finally:
        finder.close()

if __name__ == "__main__":
    main()