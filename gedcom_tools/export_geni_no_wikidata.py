#!/usr/bin/env python3
"""
Export Geni IDs without Wikidata IDs

Creates a CSV export of all entities that have:
- P62 (Geni ID) property
- NO P61 (Wikidata ID) property

This identifies genealogical records that could potentially be enhanced 
with Wikidata links or represent Geni-specific content.

CSV includes: QID, English label/description, Geni IDs, family relationships,
birth/death dates, and other identifier properties.
"""

import pymongo
import csv
import os

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

# Output configuration
OUTPUT_DIR = "analysis"
OUTPUT_FILE = "geni_ids_no_wikidata.csv"

def extract_value(claim):
    """Extract string value from claim, handling both string and dict formats"""
    value = claim.get('value', '')
    if isinstance(value, dict):
        return value.get('id', str(value))
    return str(value) if value else ''

def extract_multiple_values(claims):
    """Extract multiple values from claims list and join with semicolons"""
    if not claims:
        return ''
    values = [extract_value(claim) for claim in claims]
    return '; '.join(filter(None, values))

def export_geni_no_wikidata():
    """Export entities with Geni IDs but no Wikidata IDs to CSV"""
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    print("=== EXPORT: GENI IDs WITHOUT WIKIDATA IDs ===")
    print()
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    
    # Find entities with P62 but no P61
    print("Scanning database for entities with Geni IDs but no Wikidata IDs...")
    
    target_entities = []
    total_processed = 0
    redirect_count = 0
    entities_with_p62 = 0
    entities_with_p61 = 0
    entities_with_both = 0
    
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
        
        # Check for identifier properties
        has_geni = 'P62' in properties
        has_wikidata = 'P61' in properties
        
        # Count for statistics
        if has_geni:
            entities_with_p62 += 1
        if has_wikidata:
            entities_with_p61 += 1
        if has_geni and has_wikidata:
            entities_with_both += 1
        
        # Target: has Geni but NO Wikidata
        if has_geni and not has_wikidata:
            # Extract basic information
            english_label = labels.get('en', '')
            english_description = descriptions.get('en', '')
            
            # Extract identifier properties
            geni_ids = extract_multiple_values(properties.get('P62', []))
            uuid_ids = extract_multiple_values(properties.get('P63', []))
            
            # Extract relationship properties
            fathers = extract_multiple_values(properties.get('P47', []))
            children = extract_multiple_values(properties.get('P20', []))
            mothers = extract_multiple_values(properties.get('P48', []))
            spouses = extract_multiple_values(properties.get('P42', []))
            
            # Extract date properties
            birth_dates = extract_multiple_values(properties.get('P56', []))
            death_dates = extract_multiple_values(properties.get('P57', []))
            
            # Extract sex property
            sex_values = extract_multiple_values(properties.get('P55', []))
            
            # Check P39 classifications
            p39_values = extract_multiple_values(properties.get('P39', []))
            
            # Count total properties for data richness assessment
            total_properties = len(properties)
            
            # Count family relationships
            relationship_count = len([p for p in ['P47', 'P20', 'P48', 'P42'] if p in properties])
            
            target_entities.append({
                'qid': qid,
                'english_label': english_label,
                'english_description': english_description,
                'geni_ids': geni_ids,
                'uuid_ids': uuid_ids,
                'sex': sex_values,
                'birth_dates': birth_dates,
                'death_dates': death_dates,
                'fathers': fathers,
                'children': children,
                'mothers': mothers,
                'spouses': spouses,
                'relationship_count': relationship_count,
                'total_properties': total_properties,
                'p39_classifications': p39_values
            })
    
    print(f"  Processed {total_processed:,} entities total")
    print(f"  Skipped {redirect_count:,} redirect entities")
    print()
    
    # Display statistics
    active_entities = total_processed - redirect_count
    geni_no_wikidata = len(target_entities)
    
    print("=== IDENTIFIER STATISTICS ===")
    print(f"Active entities: {active_entities:,}")
    print(f"Entities with P62 (Geni): {entities_with_p62:,}")
    print(f"Entities with P61 (Wikidata): {entities_with_p61:,}")
    print(f"Entities with BOTH Geni + Wikidata: {entities_with_both:,}")
    print(f"Entities with Geni but NO Wikidata: {geni_no_wikidata:,}")
    print()
    
    if geni_no_wikidata > 0:
        geni_only_percentage = (geni_no_wikidata / entities_with_p62) * 100
        print(f"Percentage of Geni entities without Wikidata: {geni_only_percentage:.1f}%")
    
    # Export to CSV
    print(f"Exporting {geni_no_wikidata:,} entities to {output_path}")
    
    fieldnames = [
        'qid', 'english_label', 'english_description',
        'geni_ids', 'uuid_ids', 'sex',
        'birth_dates', 'death_dates',
        'fathers', 'children', 'mothers', 'spouses',
        'relationship_count', 'total_properties', 'p39_classifications'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Add comment row
        comment_row = {field: '' for field in fieldnames}
        comment_row['qid'] = '# Entities with Geni IDs (P62) but no Wikidata IDs (P61)'
        writer.writerow(comment_row)
        
        # Sort by QID for consistent output
        sorted_entities = sorted(target_entities, key=lambda x: int(x['qid'][1:]) if x['qid'][1:].isdigit() else 0)
        
        # Write entity data
        for entity_record in sorted_entities:
            writer.writerow(entity_record)
    
    print(f"  OK Saved {output_path}")
    print()
    
    # Additional analysis
    print("=== DATA RICHNESS ANALYSIS ===")
    
    # Analyze relationship coverage
    entities_with_relationships = sum(1 for e in target_entities if e['relationship_count'] > 0)
    entities_without_relationships = geni_no_wikidata - entities_with_relationships
    
    print(f"Entities with family relationships: {entities_with_relationships:,}")
    print(f"Entities without relationships: {entities_without_relationships:,}")
    
    # Analyze date coverage
    entities_with_birth_dates = sum(1 for e in target_entities if e['birth_dates'])
    entities_with_death_dates = sum(1 for e in target_entities if e['death_dates'])
    
    print(f"Entities with birth dates: {entities_with_birth_dates:,}")
    print(f"Entities with death dates: {entities_with_death_dates:,}")
    
    # Property richness
    if target_entities:
        avg_properties = sum(e['total_properties'] for e in target_entities) / len(target_entities)
        max_properties = max(e['total_properties'] for e in target_entities)
        min_properties = min(e['total_properties'] for e in target_entities)
        
        print(f"Average properties per entity: {avg_properties:.1f}")
        print(f"Property range: {min_properties} - {max_properties}")
    
    print()
    print("SUCCESS: Geni-only entities exported!")
    print(f"File saved: {output_path}")
    print()
    print("USAGE:")
    print("- Review entities for potential Wikidata linking opportunities")
    print("- Identify Geni-specific genealogical content")
    print("- Analyze data quality and completeness patterns")
    
    client.close()
    
    return {
        'total_entities': geni_no_wikidata,
        'entities_with_relationships': entities_with_relationships,
        'entities_with_birth_dates': entities_with_birth_dates,
        'entities_with_death_dates': entities_with_death_dates,
        'output_file': output_path
    }

if __name__ == "__main__":
    import time
    start_time = time.time()
    results = export_geni_no_wikidata()
    duration = time.time() - start_time
    print(f"\nCompleted in {duration:.1f} seconds")