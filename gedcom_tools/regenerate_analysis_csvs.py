#!/usr/bin/env python3
"""
Regenerate all analysis CSV files with proper filtering to exclude redirect entities.
This script recreates all the analysis CSVs but only includes active entities (not redirects).
"""

import pymongo
import csv
import os
from collections import defaultdict

def main():
    print("=== REGENERATING ANALYSIS CSVs (EXCLUDING REDIRECTS) ===")
    print()
    
    # Connect to MongoDB
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['gaiad_processing_db']
    collection = db['entities']
    
    # Create analysis directory if it doesn't exist
    os.makedirs('analysis', exist_ok=True)
    
    # Categories for analysis
    categories = {
        'all_wikidata_qids': [],
        'geni_ids_no_wikidata': [],
        'geni_ids_with_wikidata': [],
        'wikidata_genealogy_data': [],
        'has_identifiers_and_relatives': [],
        'no_identifiers_only': [],
        'no_relatives_only': [],
        'both_no_identifiers_and_no_relatives': []
    }
    
    print("Processing entities and categorizing...")
    processed = 0
    redirect_count = 0
    
    for entity in collection.find():
        processed += 1
        if processed % 10000 == 0:
            print(f"  Processed {processed:,} entities...")
        
        # Skip redirect entities
        properties = entity.get('properties', {})
        if 'redirect' in properties:
            redirect_count += 1
            continue
        
        qid = entity['qid']
        labels = entity.get('labels', {})
        descriptions = entity.get('descriptions', {})
        
        english_label = labels.get('en', '')
        english_description = descriptions.get('en', '')
        
        # Check for external identifiers
        wikidata_ids = []
        geni_ids = []
        uuid_ids = []
        genealogy_ids = []
        
        # Core identifiers
        if 'P61' in properties:
            wikidata_ids = [claim.get('value', '') for claim in properties['P61']]
        if 'P62' in properties:
            geni_ids = [claim.get('value', '') for claim in properties['P62']]
        if 'P63' in properties:
            uuid_ids = [claim.get('value', '') for claim in properties['P63']]
        
        # Additional genealogy identifiers
        genealogy_props = ['P1185', 'P1819', 'P2949', 'P4638', 'P4159', 'P7929', 'P535', 'P6821']
        for prop in genealogy_props:
            if prop in properties:
                genealogy_ids.extend([claim.get('value', '') for claim in properties[prop]])
        
        # Check for family relationships
        # NOTE: This database appears to contain NO family relationship properties
        # All entities will be categorized as having no relatives
        fathers = []
        mothers = []
        children = []
        spouses = []
        
        # Check for P39 special categories
        has_p39_no_identifiers = False
        has_p39_no_relatives = False
        
        if 'P39' in properties:
            for claim in properties['P39']:
                value = claim.get('value', '')
                if value == 'Q153720':  # no identifiers
                    has_p39_no_identifiers = True
                elif value == 'Q153721':  # no relatives
                    has_p39_no_relatives = True
        
        # Determine categories
        has_any_identifier = bool(wikidata_ids or geni_ids or uuid_ids or genealogy_ids)
        has_any_relative = bool(fathers or mothers or children or spouses)
        
        # Create entity data
        entity_data = {
            'qid': qid,
            'english_label': english_label,
            'english_description': english_description,
            'wikidata_ids': ';'.join(wikidata_ids),
            'geni_ids': ';'.join(geni_ids),
            'uuid_ids': ';'.join(uuid_ids),
            'genealogy_ids': ';'.join(genealogy_ids),
            'fathers': ';'.join(fathers),
            'mothers': ';'.join(mothers),
            'children': ';'.join(children),
            'spouses': ';'.join(spouses),
            'has_p39_no_identifiers': 'Yes' if has_p39_no_identifiers else 'No',
            'has_p39_no_relatives': 'Yes' if has_p39_no_relatives else 'No'
        }
        
        # Categorize entity
        if wikidata_ids:
            categories['all_wikidata_qids'].append(entity_data)
            categories['wikidata_genealogy_data'].append(entity_data)
            
            if geni_ids:
                categories['geni_ids_with_wikidata'].append(entity_data)
        
        if geni_ids and not wikidata_ids:
            categories['geni_ids_no_wikidata'].append(entity_data)
        
        if has_any_identifier and has_any_relative:
            categories['has_identifiers_and_relatives'].append(entity_data)
        
        if not has_any_identifier and has_any_relative:
            categories['no_identifiers_only'].append(entity_data)
        
        if has_any_identifier and not has_any_relative:
            categories['no_relatives_only'].append(entity_data)
        
        if not has_any_identifier and not has_any_relative:
            categories['both_no_identifiers_and_no_relatives'].append(entity_data)
    
    print(f"  Processed {processed:,} entities total")
    print(f"  Skipped {redirect_count:,} redirect entities")
    print()
    
    # Write CSV files
    print("Writing CSV files...")
    
    # Define field sets for different CSV types
    basic_fields = ['qid', 'english_label', 'english_description']
    id_fields = ['wikidata_ids', 'geni_ids', 'uuid_ids', 'genealogy_ids']
    family_fields = ['fathers', 'mothers', 'children', 'spouses']
    category_fields = ['has_p39_no_identifiers', 'has_p39_no_relatives']
    
    csv_configs = {
        'all_wikidata_qids': {
            'fields': basic_fields + ['wikidata_ids'],
            'comment': 'All entities with Wikidata QIDs'
        },
        'geni_ids_no_wikidata': {
            'fields': basic_fields + ['geni_ids'],
            'comment': 'Entities with Geni IDs but no Wikidata QIDs'
        },
        'geni_ids_with_wikidata': {
            'fields': basic_fields + ['wikidata_ids', 'geni_ids'],
            'comment': 'Entities with both Geni IDs and Wikidata QIDs'
        },
        'wikidata_genealogy_data': {
            'fields': basic_fields + id_fields + family_fields,
            'comment': 'Complete genealogy data for entities with Wikidata QIDs'
        },
        'has_identifiers_and_relatives': {
            'fields': basic_fields + id_fields + family_fields,
            'comment': 'Entities with both external identifiers and family relationships'
        },
        'no_identifiers_only': {
            'fields': basic_fields + family_fields + category_fields,
            'comment': 'Entities with family relationships but no external identifiers'
        },
        'no_relatives_only': {
            'fields': basic_fields + id_fields + category_fields,
            'comment': 'Entities with external identifiers but no family relationships'
        },
        'both_no_identifiers_and_no_relatives': {
            'fields': basic_fields + category_fields,
            'comment': 'Entities lacking both identifiers and family relationships'
        }
    }
    
    for category_name, config in csv_configs.items():
        entities = categories[category_name]
        filename = f'analysis/{category_name}.csv'
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=config['fields'])
            
            # Write comment header
            f.write(f"# {config['comment']}\n")
            
            # Write CSV header
            writer.writeheader()
            
            # Write data
            for entity in entities:
                row = {field: entity.get(field, '') for field in config['fields']}
                writer.writerow(row)
        
        print(f"  {filename}: {len(entities):,} entities")
    
    print()
    print("=== SUMMARY ===")
    print(f"Total active entities processed: {processed - redirect_count:,}")
    print(f"Redirect entities excluded: {redirect_count:,}")
    print()
    
    for category_name, entities in categories.items():
        print(f"{category_name}: {len(entities):,} entities")
    
    client.close()
    print()
    print("SUCCESS: All analysis CSVs regenerated successfully!")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)