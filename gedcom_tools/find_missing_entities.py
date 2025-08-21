#!/usr/bin/env python3
"""
Find Missing Entities

Looks for QIDs that are referenced in properties but don't exist 
or exist as empty entities (potential XML redirects that weren't imported).
"""

import pymongo
import time
from collections import defaultdict

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

def find_missing_entities():
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    print("=== FINDING MISSING/EMPTY ENTITIES ===")
    print()
    
    # Step 1: Get all existing QIDs and classify them
    print("Analyzing all entities...")
    
    existing_qids = set()
    empty_qids = set()
    redirect_qids = set()
    full_qids = set()
    
    entity_count = 0
    for entity in collection.find():
        entity_count += 1
        if entity_count % 20000 == 0:
            print(f"  Analyzed {entity_count:,} entities...")
        
        qid = entity['qid']
        existing_qids.add(qid)
        
        properties = entity.get('properties', {})
        labels = entity.get('labels', {})
        descriptions = entity.get('descriptions', {})
        
        if 'redirect' in properties:
            redirect_qids.add(qid)
        elif len(properties) == 0 and len(labels) == 0 and len(descriptions) == 0:
            empty_qids.add(qid)
        else:
            full_qids.add(qid)
    
    print(f"  Analyzed {entity_count:,} entities total")
    print(f"  Full entities: {len(full_qids):,}")
    print(f"  Redirect entities: {len(redirect_qids):,}")
    print(f"  Empty entities: {len(empty_qids):,}")
    print()
    
    # Step 2: Find all referenced QIDs
    print("Finding all referenced QIDs...")
    
    referenced_qids = defaultdict(int)
    entities_checked = 0
    
    for entity in collection.find():
        entities_checked += 1
        if entities_checked % 20000 == 0:
            print(f"  Checked {entities_checked:,} entities for references...")
        
        properties = entity.get('properties', {})
        for prop_id, claims in properties.items():
            for claim in claims:
                value = claim.get('value')
                
                referenced_qid = None
                if isinstance(value, str) and value.startswith('Q'):
                    referenced_qid = value
                elif isinstance(value, dict) and value.get('id', '').startswith('Q'):
                    referenced_qid = value['id']
                
                if referenced_qid:
                    referenced_qids[referenced_qid] += 1
    
    print(f"  Found {len(referenced_qids):,} unique QIDs being referenced")
    print()
    
    # Step 3: Find problematic references
    print("Analyzing problematic references...")
    
    missing_qids = []  # Referenced but don't exist at all
    empty_but_referenced = []  # Exist but empty, yet referenced
    
    for ref_qid, ref_count in referenced_qids.items():
        if ref_qid not in existing_qids:
            missing_qids.append((ref_qid, ref_count))
        elif ref_qid in empty_qids:
            empty_but_referenced.append((ref_qid, ref_count))
    
    # Sort by reference count (most referenced first)
    missing_qids.sort(key=lambda x: x[1], reverse=True)
    empty_but_referenced.sort(key=lambda x: x[1], reverse=True)
    
    print(f"Missing QIDs (referenced but don't exist): {len(missing_qids):,}")
    if missing_qids:
        print("  Top 10 missing QIDs:")
        for qid, count in missing_qids[:10]:
            print(f"    {qid}: {count:,} references")
    
    print()
    print(f"Empty but referenced QIDs: {len(empty_but_referenced):,}")
    if empty_but_referenced:
        print("  Top 10 empty but referenced QIDs:")
        for qid, count in empty_but_referenced[:10]:
            print(f"    {qid}: {count:,} references")
    
    # Step 4: Check if any of these might be XML redirects
    print()
    print("Checking for potential XML redirect patterns...")
    
    # Look for QID number patterns that might indicate XML redirects
    potential_xml_redirects = []
    
    for qid, count in empty_but_referenced[:20]:  # Check top 20
        qid_num = int(qid[1:]) if qid[1:].isdigit() else 0
        
        # Look for nearby QIDs that exist and have content
        nearby_range = 50  # Check within 50 QIDs
        nearby_targets = []
        
        for offset in range(1, nearby_range + 1):
            for direction in [-1, 1]:
                candidate_num = qid_num + (offset * direction)
                if candidate_num > 0:
                    candidate_qid = f"Q{candidate_num}"
                    if candidate_qid in full_qids:
                        nearby_targets.append(candidate_qid)
        
        if nearby_targets:
            potential_xml_redirects.append((qid, count, nearby_targets[:3]))
    
    if potential_xml_redirects:
        print(f"Found {len(potential_xml_redirects)} potential XML redirects:")
        for qid, count, targets in potential_xml_redirects:
            print(f"  {qid} ({count:,} refs) -> possible targets: {targets}")
    
    print()
    print("=== SUMMARY ===")
    print(f"Total entities: {entity_count:,}")
    print(f"QIDs being referenced: {len(referenced_qids):,}")
    print(f"Missing QIDs: {len(missing_qids):,}")
    print(f"Empty but referenced: {len(empty_but_referenced):,}")
    print(f"Potential XML redirects: {len(potential_xml_redirects)}")
    
    client.close()
    
    return {
        'missing_qids': missing_qids,
        'empty_but_referenced': empty_but_referenced,
        'potential_xml_redirects': potential_xml_redirects
    }

if __name__ == "__main__":
    start_time = time.time()
    results = find_missing_entities()
    duration = time.time() - start_time
    print(f"\nCompleted in {duration:.1f} seconds")