#!/usr/bin/env python3
"""
Export Entities Without English Labels

Creates a CSV file of all entities that lack English labels,
showing their local QID, Wikidata QID (if available), and all
their non-English labels across all languages.
"""

import pymongo
import csv
import os

# Configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
OUTPUT_FILE = "analysis/entities_without_english_labels.csv"

class NoEnglishLabelsExporter:
    def __init__(self, mongo_uri=MONGO_URI, output_file=OUTPUT_FILE):
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db['entities']
        self.output_file = output_file
        
        self.stats = {
            'entities_processed': 0,
            'entities_without_english': 0,
            'redirects_skipped': 0,
            'entities_with_wikidata_qid': 0,
            'total_non_english_labels': 0
        }
        
        print(f"Connected to MongoDB: {DATABASE_NAME}.entities")
        print(f"Output file: {output_file}")
        print()
    
    def export_entities_without_english(self):
        """Export all entities that lack English labels to CSV"""
        print("=== EXPORTING ENTITIES WITHOUT ENGLISH LABELS ===")
        print()
        
        # Create analysis directory if needed
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        
        print("Processing entities...")
        
        # Collect entities without English labels
        entities_without_english = []
        
        for entity in self.collection.find():
            self.stats['entities_processed'] += 1
            
            if self.stats['entities_processed'] % 10000 == 0:
                print(f"  Processed {self.stats['entities_processed']:,} entities...")
            
            # Skip redirect entities
            properties = entity.get('properties', {})
            if 'redirect' in properties:
                self.stats['redirects_skipped'] += 1
                continue
            
            qid = entity['qid']
            labels = entity.get('labels', {})
            
            # Check if entity lacks English label
            if 'en' not in labels or not labels['en']:
                self.stats['entities_without_english'] += 1
                
                # Get Wikidata QID if available
                wikidata_qid = ''
                if 'P61' in properties:
                    # Get first Wikidata QID
                    wikidata_claims = properties['P61']
                    if wikidata_claims:
                        wikidata_qid = wikidata_claims[0].get('value', '')
                        if wikidata_qid:
                            self.stats['entities_with_wikidata_qid'] += 1
                
                # Get all non-English labels
                non_english_labels = {}
                for lang, label_text in labels.items():
                    if lang != 'en' and label_text:
                        non_english_labels[lang] = label_text
                        self.stats['total_non_english_labels'] += 1
                
                # Only include entities that have some labels
                if non_english_labels:
                    entity_data = {
                        'local_qid': qid,
                        'wikidata_qid': wikidata_qid,
                        'non_english_labels': non_english_labels
                    }
                    entities_without_english.append(entity_data)
        
        print(f"  Processed {self.stats['entities_processed']:,} entities total")
        print(f"  Found {self.stats['entities_without_english']:,} entities without English labels")
        print()
        
        # Write CSV file
        print("Writing CSV file...")
        
        # Determine all unique languages for column headers
        all_languages = set()
        for entity_data in entities_without_english:
            all_languages.update(entity_data['non_english_labels'].keys())
        
        # Sort languages alphabetically
        sorted_languages = sorted(all_languages)
        
        # Create CSV headers
        headers = ['local_qid', 'wikidata_qid'] + [f'label_{lang}' for lang in sorted_languages]
        
        with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            
            # Write comment header
            f.write(f"# Entities without English labels - {len(entities_without_english):,} entities across {len(sorted_languages)} languages\\n")
            f.write(f"# Generated from {self.stats['entities_processed']:,} total entities ({self.stats['redirects_skipped']:,} redirects excluded)\\n")
            
            # Write CSV header
            writer.writeheader()
            
            # Write data
            for entity_data in entities_without_english:
                row = {
                    'local_qid': entity_data['local_qid'],
                    'wikidata_qid': entity_data['wikidata_qid']
                }
                
                # Add language labels
                for lang in sorted_languages:
                    row[f'label_{lang}'] = entity_data['non_english_labels'].get(lang, '')
                
                writer.writerow(row)
        
        print(f"  CSV saved: {self.output_file}")
        print()
        
        return True
    
    def print_statistics(self):
        """Print export statistics"""
        print("=== EXPORT STATISTICS ===")
        print(f"Entities processed: {self.stats['entities_processed']:,}")
        print(f"Redirects skipped: {self.stats['redirects_skipped']:,}")
        print(f"Entities without English labels: {self.stats['entities_without_english']:,}")
        print(f"Entities with Wikidata QIDs: {self.stats['entities_with_wikidata_qid']:,}")
        print(f"Total non-English label instances: {self.stats['total_non_english_labels']:,}")
        print()
        
        if self.stats['entities_without_english'] > 0:
            percentage = (self.stats['entities_without_english'] / (self.stats['entities_processed'] - self.stats['redirects_skipped'])) * 100
            print(f"Percentage without English labels: {percentage:.1f}%")
            
            if self.stats['entities_with_wikidata_qid'] > 0:
                wikidata_percentage = (self.stats['entities_with_wikidata_qid'] / self.stats['entities_without_english']) * 100
                print(f"Entities without English that have Wikidata QIDs: {wikidata_percentage:.1f}%")
        
        print()
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()

def main():
    exporter = NoEnglishLabelsExporter()
    
    try:
        success = exporter.export_entities_without_english()
        exporter.print_statistics()
        
        if success:
            print("SUCCESS: CSV export of entities without English labels completed!")
            print(f"File saved: {exporter.output_file}")
            
    finally:
        exporter.close()

if __name__ == "__main__":
    main()