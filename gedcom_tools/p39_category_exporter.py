#!/usr/bin/env python3
"""
P39 Category Analysis Exporter

Exports CSV files for the 4 P39 categories:
1. No identifiers only (has P39 Q153721 but not Q153722)
2. No relatives only (has P39 Q153722 but not Q153721)  
3. Both no identifiers AND no relatives (has both P39 Q153721 and Q153722)
4. Has both identifiers AND relatives (has neither P39 classification)

Each CSV includes: QID, English label, description, identifier properties, relationship properties.
"""

import pymongo
import csv
import os

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

# P39 classifications
NO_IDENTIFIERS_QID = "Q153721"  # Individual without identifiers
NO_RELATIVES_QID = "Q153722"    # People without relatives

# Output directory
OUTPUT_DIR = "analysis"

def get_entity_identifiers(properties):
    """Extract identifier information from entity properties"""
    identifiers = {}
    
    def extract_value(claim):
        """Extract string value from claim, handling both string and dict formats"""
        value = claim.get('value', '')
        if isinstance(value, dict):
            return value.get('id', str(value))
        return str(value) if value else ''
    
    # P61 - Wikidata ID
    if 'P61' in properties:
        wikidata_ids = [extract_value(claim) for claim in properties['P61']]
        identifiers['wikidata_ids'] = '; '.join(filter(None, wikidata_ids))
    else:
        identifiers['wikidata_ids'] = ''
    
    # P62 - Geni ID  
    if 'P62' in properties:
        geni_ids = [extract_value(claim) for claim in properties['P62']]
        identifiers['geni_ids'] = '; '.join(filter(None, geni_ids))
    else:
        identifiers['geni_ids'] = ''
    
    # P63 - UUID
    if 'P63' in properties:
        uuid_ids = [extract_value(claim) for claim in properties['P63']]
        identifiers['uuid_ids'] = '; '.join(filter(None, uuid_ids))
    else:
        identifiers['uuid_ids'] = ''
    
    return identifiers

def get_entity_relationships(properties):
    """Extract relationship information from entity properties"""
    relationships = {}
    
    def extract_value(claim):
        """Extract string value from claim, handling both string and dict formats"""
        value = claim.get('value', '')
        if isinstance(value, dict):
            return value.get('id', str(value))
        return str(value) if value else ''
    
    # P47 - Father
    if 'P47' in properties:
        fathers = [extract_value(claim) for claim in properties['P47']]
        relationships['fathers'] = '; '.join(filter(None, fathers))
    else:
        relationships['fathers'] = ''
    
    # P20 - Child
    if 'P20' in properties:
        children = [extract_value(claim) for claim in properties['P20']]
        relationships['children'] = '; '.join(filter(None, children))
    else:
        relationships['children'] = ''
    
    # P48 - Mother
    if 'P48' in properties:
        mothers = [extract_value(claim) for claim in properties['P48']]
        relationships['mothers'] = '; '.join(filter(None, mothers))
    else:
        relationships['mothers'] = ''
    
    # P42 - Spouse
    if 'P42' in properties:
        spouses = [extract_value(claim) for claim in properties['P42']]
        relationships['spouses'] = '; '.join(filter(None, spouses))
    else:
        relationships['spouses'] = ''
    
    return relationships

def check_p39_classifications(properties):
    """Check which P39 classifications an entity has"""
    has_no_identifiers = False
    has_no_relatives = False
    
    if 'P39' in properties:
        for claim in properties['P39']:
            value = claim.get('value', '')
            if isinstance(value, dict):
                value = value.get('id', '')
            
            if value == NO_IDENTIFIERS_QID:
                has_no_identifiers = True
            elif value == NO_RELATIVES_QID:
                has_no_relatives = True
    
    return has_no_identifiers, has_no_relatives

def export_p39_categories():
    """Export all 4 P39 categories to CSV files"""
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    print("=== P39 CATEGORY ANALYSIS EXPORT ===")
    print()
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Initialize category lists
    categories = {
        'no_identifiers_only': [],
        'no_relatives_only': [],
        'both_issues': [],
        'has_both': []
    }
    
    # Process all active entities
    print("Analyzing all active entities...")
    total_processed = 0
    redirect_count = 0
    
    for entity in collection.find():
        total_processed += 1
        if total_processed % 20000 == 0:
            print(f"  Processed {total_processed:,} entities...")
        
        qid = entity['qid']
        properties = entity.get('properties', {})
        labels = entity.get('labels', {})
        descriptions = entity.get('descriptions', {})
        
        # Skip redirect entities
        if 'redirect' in properties:
            redirect_count += 1
            continue
        
        # Get basic info
        english_label = labels.get('en', '')
        english_description = descriptions.get('en', '')
        
        # Check P39 classifications
        has_no_identifiers, has_no_relatives = check_p39_classifications(properties)
        
        # Get identifier and relationship info
        identifiers = get_entity_identifiers(properties)
        relationships = get_entity_relationships(properties)
        
        # Create entity record
        entity_record = {
            'qid': qid,
            'english_label': english_label,
            'english_description': english_description,
            'wikidata_ids': identifiers['wikidata_ids'],
            'geni_ids': identifiers['geni_ids'], 
            'uuid_ids': identifiers['uuid_ids'],
            'fathers': relationships['fathers'],
            'children': relationships['children'],
            'mothers': relationships['mothers'],
            'spouses': relationships['spouses'],
            'has_p39_no_identifiers': 'Yes' if has_no_identifiers else 'No',
            'has_p39_no_relatives': 'Yes' if has_no_relatives else 'No'
        }
        
        # Categorize entity
        if has_no_identifiers and has_no_relatives:
            categories['both_issues'].append(entity_record)
        elif has_no_identifiers and not has_no_relatives:
            categories['no_identifiers_only'].append(entity_record)
        elif not has_no_identifiers and has_no_relatives:
            categories['no_relatives_only'].append(entity_record)
        else:
            categories['has_both'].append(entity_record)
    
    print(f"  Processed {total_processed:,} entities total")
    print(f"  Skipped {redirect_count:,} redirect entities")
    print()
    
    # CSV field names
    fieldnames = [
        'qid', 'english_label', 'english_description',
        'wikidata_ids', 'geni_ids', 'uuid_ids',
        'fathers', 'children', 'mothers', 'spouses',
        'has_p39_no_identifiers', 'has_p39_no_relatives'
    ]
    
    # Export each category to CSV
    category_info = {
        'no_identifiers_only': {
            'filename': 'no_identifiers_only.csv',
            'description': 'Entities with identifiers but no family relationships'
        },
        'no_relatives_only': {
            'filename': 'no_relatives_only.csv', 
            'description': 'Entities with family relationships but no identifiers'
        },
        'both_issues': {
            'filename': 'both_no_identifiers_and_no_relatives.csv',
            'description': 'Entities lacking both identifiers and family relationships'
        },
        'has_both': {
            'filename': 'has_identifiers_and_relatives.csv',
            'description': 'Entities with both identifiers and family relationships'
        }
    }
    
    print("=== EXPORTING CSV FILES ===")
    
    for category_key, info in category_info.items():
        entities_list = categories[category_key]
        filename = os.path.join(OUTPUT_DIR, info['filename'])
        
        print(f"Exporting {len(entities_list):,} entities to {filename}")
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            # Add comment row explaining the category
            comment_row = {field: '' for field in fieldnames}
            comment_row['qid'] = f"# {info['description']}"
            writer.writerow(comment_row)
            
            # Write entity data
            for entity_record in entities_list:
                writer.writerow(entity_record)
        
        print(f"  OK Saved {filename}")
    
    print()
    print("=== EXPORT SUMMARY ===")
    print(f"No identifiers only: {len(categories['no_identifiers_only']):,} entities")
    print(f"No relatives only: {len(categories['no_relatives_only']):,} entities") 
    print(f"Both issues: {len(categories['both_issues']):,} entities")
    print(f"Has both: {len(categories['has_both']):,} entities")
    print(f"Total active entities: {sum(len(cat) for cat in categories.values()):,}")
    print()
    print("SUCCESS: All P39 category CSV files exported!")
    print(f"Files saved to {OUTPUT_DIR}/ directory")
    
    client.close()
    
    return {
        'no_identifiers_only': len(categories['no_identifiers_only']),
        'no_relatives_only': len(categories['no_relatives_only']),
        'both_issues': len(categories['both_issues']),
        'has_both': len(categories['has_both'])
    }

if __name__ == "__main__":
    import time
    start_time = time.time()
    results = export_p39_categories()
    duration = time.time() - start_time
    print(f"\nCompleted in {duration:.1f} seconds")