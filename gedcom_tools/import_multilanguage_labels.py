#!/usr/bin/env python3
"""
Import Multi-Language Labels from CSV

Processes the output_labels_all_langs_preserved.csv file to update entities with:
1. Move current English labels to aliases
2. Replace English labels with Wikidata labels (even if empty)
3. Add multi-language labels and descriptions
4. Handle 'mul' (multi-language) labels as P64 property claims
5. If no English label provided but 'mul' exists, use 'mul' as English label
"""

import pymongo
import csv
import sys
from collections import Counter

# Configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
CSV_FILE = "analysis/output_labels_all_langs_preserved.csv"

class MultiLanguageLabelImporter:
    def __init__(self, mongo_uri=MONGO_URI, csv_file=CSV_FILE):
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db['entities']
        self.csv_file = csv_file
        
        self.stats = {
            'rows_processed': 0,
            'entities_found': 0,
            'entities_updated': 0,
            'entities_not_found': 0,
            'english_labels_moved_to_aliases': 0,
            'english_labels_replaced': 0,
            'mul_labels_as_p64': 0,
            'mul_labels_as_english': 0,
            'language_labels_added': 0,
            'language_descriptions_added': 0
        }
        
        print(f"Connected to MongoDB: {DATABASE_NAME}.entities")
        print(f"CSV file: {csv_file}")
        print()
    
    def process_multilanguage_labels(self):
        """Process the CSV file and update entity labels/descriptions"""
        print("=== IMPORTING MULTI-LANGUAGE LABELS ===")
        print()
        
        print("Reading CSV file...")
        
        batch_updates = []
        batch_size = 1000
        
        with open(self.csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            print(f"CSV headers: {len(headers)} columns")
            print("Processing entities...")
            print()
            
            for row in reader:
                self.stats['rows_processed'] += 1
                
                if self.stats['rows_processed'] % 1000 == 0:
                    print(f"  Processed {self.stats['rows_processed']:,} rows...")
                
                qid = row['col1_id'].strip()
                wikidata_qid = row['wikidata_id'].strip()
                
                # Skip header row or invalid rows
                if qid == 'col1_id' or not qid.startswith('Q'):
                    continue
                
                # Find entity in MongoDB
                entity = self.collection.find_one({'qid': qid})
                if not entity:
                    self.stats['entities_not_found'] += 1
                    continue
                
                self.stats['entities_found'] += 1
                
                # Get current labels, descriptions, aliases, properties
                current_labels = entity.get('labels', {})
                current_descriptions = entity.get('descriptions', {})
                current_aliases = entity.get('aliases', {})
                current_properties = entity.get('properties', {})
                
                # Track changes for this entity
                updated = False
                
                # Step 1: Handle English label changes
                current_english_label = current_labels.get('en', '')
                new_english_label = row.get('label_en', '').strip()
                mul_label = row.get('label_mul', '').strip()
                
                # Move current English label to aliases if it exists and we're changing it
                if current_english_label and (new_english_label or mul_label):
                    if 'en' not in current_aliases:
                        current_aliases['en'] = []
                    if current_english_label not in current_aliases['en']:
                        current_aliases['en'].append(current_english_label)
                        self.stats['english_labels_moved_to_aliases'] += 1
                        updated = True
                
                # Step 2: Set new English label
                if new_english_label:
                    # Use provided English label
                    current_labels['en'] = new_english_label
                    self.stats['english_labels_replaced'] += 1
                    updated = True
                elif mul_label and not new_english_label:
                    # No English label provided but mul exists - use mul as English
                    current_labels['en'] = mul_label
                    self.stats['mul_labels_as_english'] += 1
                    updated = True
                elif new_english_label == '' and 'en' in current_labels:
                    # Explicitly empty English label - remove it
                    del current_labels['en']
                    self.stats['english_labels_replaced'] += 1
                    updated = True
                
                # Step 3: Handle mul label as P64 property if it exists and wasn't used as English
                if mul_label and new_english_label:
                    # We have both English and mul - add mul as P64 property
                    p64_claim = {
                        'value': mul_label,
                        'type': 'string',
                        'claim_id': f"{qid}_P64_{mul_label.replace(' ', '_')}"
                    }
                    current_properties['P64'] = [p64_claim]
                    self.stats['mul_labels_as_p64'] += 1
                    updated = True
                
                # Step 4: Add all other language labels
                for header in headers:
                    if header.startswith('label_') and header not in ['label_en', 'label_mul']:
                        lang_code = header.replace('label_', '')
                        label_value = row.get(header, '').strip()
                        
                        if label_value:
                            current_labels[lang_code] = label_value
                            self.stats['language_labels_added'] += 1
                            updated = True
                
                # Step 5: Add all language descriptions
                for header in headers:
                    if header.startswith('desc_') and header not in ['desc_mul']:
                        lang_code = header.replace('desc_', '')
                        desc_value = row.get(header, '').strip()
                        
                        if desc_value:
                            current_descriptions[lang_code] = desc_value
                            self.stats['language_descriptions_added'] += 1
                            updated = True
                
                # Add to batch if updated
                if updated:
                    update_doc = {
                        'labels': current_labels,
                        'descriptions': current_descriptions,
                        'aliases': current_aliases,
                        'properties': current_properties
                    }
                    
                    batch_updates.append(
                        pymongo.UpdateOne(
                            {'qid': qid},
                            {'$set': update_doc}
                        )
                    )
                    self.stats['entities_updated'] += 1
                    
                    # Execute batch when it gets large
                    if len(batch_updates) >= batch_size:
                        self.collection.bulk_write(batch_updates)
                        batch_updates = []
            
            # Execute remaining batch updates
            if batch_updates:
                self.collection.bulk_write(batch_updates)
        
        print(f"  Processed {self.stats['rows_processed']:,} rows total")
        print()
    
    def print_statistics(self):
        """Print import statistics"""
        print("=== IMPORT STATISTICS ===")
        print(f"Rows processed: {self.stats['rows_processed']:,}")
        print(f"Entities found in database: {self.stats['entities_found']:,}")
        print(f"Entities updated: {self.stats['entities_updated']:,}")
        print(f"Entities not found: {self.stats['entities_not_found']:,}")
        print()
        
        print("=== LABEL PROCESSING STATISTICS ===")
        print(f"English labels moved to aliases: {self.stats['english_labels_moved_to_aliases']:,}")
        print(f"English labels replaced: {self.stats['english_labels_replaced']:,}")
        print(f"Mul labels used as P64 property: {self.stats['mul_labels_as_p64']:,}")
        print(f"Mul labels used as English label: {self.stats['mul_labels_as_english']:,}")
        print(f"Language labels added: {self.stats['language_labels_added']:,}")
        print(f"Language descriptions added: {self.stats['language_descriptions_added']:,}")
        print()
    
    def verify_import(self):
        """Verify the import by checking some entities"""
        print("=== VERIFICATION ===")
        print()
        
        # Find entities with multiple language labels
        sample_entities = []
        for entity in self.collection.find().limit(1000):
            labels = entity.get('labels', {})
            aliases = entity.get('aliases', {})
            properties = entity.get('properties', {})
            
            # Look for entities with multiple languages or P64 property
            if (len(labels) > 1 or 
                'en' in aliases or 
                'P64' in properties):
                sample_entities.append(entity)
                if len(sample_entities) >= 5:
                    break
        
        if sample_entities:
            print("Sample entities with multi-language data:")
            for entity in sample_entities:
                qid = entity['qid']
                labels = entity.get('labels', {})
                aliases = entity.get('aliases', {})
                properties = entity.get('properties', {})
                
                print(f"{qid}:")
                
                # Show labels
                if labels:
                    print(f"  Labels ({len(labels)} languages):")
                    for lang, label in list(labels.items())[:3]:
                        print(f"    {lang}: \"{label}\"")
                    if len(labels) > 3:
                        print(f"    ... and {len(labels) - 3} more languages")
                
                # Show aliases
                if 'en' in aliases:
                    print(f"  English aliases: {aliases['en']}")
                
                # Show P64 if exists
                if 'P64' in properties:
                    p64_value = properties['P64'][0].get('value', '')
                    print(f"  P64 (Multi-language label): \"{p64_value}\"")
                
                print()
        else:
            print("No entities found with multi-language updates")
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()

def main():
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = CSV_FILE
    
    importer = MultiLanguageLabelImporter(csv_file=csv_file)
    
    try:
        importer.process_multilanguage_labels()
        importer.print_statistics()
        importer.verify_import()
        
        print("SUCCESS: Multi-language labels imported successfully!")
        print(f"Updated {importer.stats['entities_updated']:,} entities")
        print(f"Added {importer.stats['language_labels_added']:,} language labels")
        print(f"Added {importer.stats['language_descriptions_added']:,} language descriptions")
        
    finally:
        importer.close()

if __name__ == "__main__":
    main()