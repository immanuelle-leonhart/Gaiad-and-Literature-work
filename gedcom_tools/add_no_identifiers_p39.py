#!/usr/bin/env python3
"""
Add P39 "Individual without identifiers" (Q153721)

Adds P39 property with value Q153721 (Individual without identifiers) to all entities that:
- Do NOT have P61 (Wikidata ID)
- Do NOT have P62 (Geni ID)
- May have P63 (UUID) but this doesn't count as a real identifier
- Are not redirect entities
"""

import pymongo
import time

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

# Target value to add
NO_IDENTIFIERS_QID = "Q153721"  # Individual without identifiers

def add_no_identifiers_p39():
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    print("=== ADDING P39 'Individual without identifiers' (Q153721) ===")
    print()
    print("Criteria: Entities lacking both P61 (Wikidata ID) and P62 (Geni ID)")
    print("Note: P63 (UUID) alone does not count as a real identifier")
    print()
    
    # Step 1: Find entities without real identifiers
    print("Scanning database for entities without real identifiers...")
    
    entities_without_ids = []
    entities_with_p61 = 0
    entities_with_p62 = 0
    entities_with_both = 0
    entities_with_p63_only = 0
    redirect_entities = 0
    total_checked = 0
    
    for entity in collection.find():
        total_checked += 1
        if total_checked % 20000 == 0:
            print(f"  Checked {total_checked:,} entities...")
        
        qid = entity['qid']
        properties = entity.get('properties', {})
        
        # Skip redirect entities
        if 'redirect' in properties:
            redirect_entities += 1
            continue
        
        has_wikidata = 'P61' in properties
        has_geni = 'P62' in properties
        has_uuid = 'P63' in properties
        
        # Count for statistics
        if has_wikidata:
            entities_with_p61 += 1
        if has_geni:
            entities_with_p62 += 1
        if has_wikidata and has_geni:
            entities_with_both += 1
        
        # Check if entity lacks real identifiers
        if not has_wikidata and not has_geni:
            # This entity lacks real identifiers
            entities_without_ids.append({
                'qid': qid,
                'has_uuid': has_uuid,
                'entity': entity
            })
            
            if has_uuid and not has_wikidata and not has_geni:
                entities_with_p63_only += 1
    
    print(f"  Checked {total_checked:,} entities total")
    print()
    
    # Step 2: Display statistics
    active_entities = total_checked - redirect_entities
    
    print("=== IDENTIFIER STATISTICS ===")
    print(f"Active entities: {active_entities:,}")
    print(f"Redirect entities: {redirect_entities:,}")
    print(f"Entities with P61 (Wikidata): {entities_with_p61:,}")
    print(f"Entities with P62 (Geni): {entities_with_p62:,}")
    print(f"Entities with both P61 + P62: {entities_with_both:,}")
    print(f"Entities with P63 only (UUID): {entities_with_p63_only:,}")
    print(f"Entities WITHOUT real identifiers: {len(entities_without_ids):,}")
    print()
    
    if not entities_without_ids:
        print("No entities found without real identifiers")
        client.close()
        return
    
    # Step 3: Filter entities that already have P39 with this value
    print("Checking which entities already have P39 Individual without identifiers...")
    
    entities_to_update = []
    entities_already_have_p39 = 0
    
    for entity_info in entities_without_ids:
        entity = entity_info['entity']
        properties = entity.get('properties', {})
        
        # Check if entity already has P39 with our target value
        already_has_target_p39 = False
        
        if 'P39' in properties:
            for claim in properties['P39']:
                value = claim.get('value', '')
                if isinstance(value, str) and value == NO_IDENTIFIERS_QID:
                    already_has_target_p39 = True
                    break
                elif isinstance(value, dict) and value.get('id') == NO_IDENTIFIERS_QID:
                    already_has_target_p39 = True
                    break
        
        if already_has_target_p39:
            entities_already_have_p39 += 1
        else:
            entities_to_update.append(entity_info)
    
    print(f"Entities already having P39 Individual without identifiers: {entities_already_have_p39:,}")
    print(f"Entities needing P39 Individual without identifiers: {len(entities_to_update):,}")
    print()
    
    if not entities_to_update:
        print("All entities already have the correct P39 value")
        client.close()
        return
    
    # Step 4: Add P39 property to entities
    print("Adding P39 Individual without identifiers to entities...")
    
    bulk_ops = []
    entities_updated = 0
    
    for entity_info in entities_to_update:
        qid = entity_info['qid']
        entity = entity_info['entity']
        properties = entity.get('properties', {})
        
        # Create new P39 claim
        new_claim = {
            'value': NO_IDENTIFIERS_QID,
            'type': 'wikibase-item',
            'claim_id': f"{qid}_P39_{NO_IDENTIFIERS_QID}"
        }
        
        # Add to existing P39 claims or create new P39 property
        if 'P39' in properties:
            # Add to existing P39 claims
            bulk_ops.append(
                pymongo.UpdateOne(
                    {'qid': qid},
                    {'$push': {'properties.P39': new_claim}}
                )
            )
        else:
            # Create new P39 property
            bulk_ops.append(
                pymongo.UpdateOne(
                    {'qid': qid},
                    {'$set': {'properties.P39': [new_claim]}}
                )
            )
        
        entities_updated += 1
        
        # Execute in batches
        if len(bulk_ops) >= 1000:
            collection.bulk_write(bulk_ops)
            bulk_ops = []
            print(f"  Updated {entities_updated:,} entities...")
    
    # Execute remaining operations
    if bulk_ops:
        collection.bulk_write(bulk_ops)
    
    print(f"  Updated {entities_updated:,} entities total")
    print()
    
    # Step 5: Verify the update
    print("Verifying P39 additions...")
    
    entities_with_new_p39 = 0
    
    for entity in collection.find({'properties.P39': {'$exists': True}}):
        p39_claims = entity.get('properties', {}).get('P39', [])
        
        for claim in p39_claims:
            value = claim.get('value', '')
            
            if isinstance(value, str) and value == NO_IDENTIFIERS_QID:
                entities_with_new_p39 += 1
                break
            elif isinstance(value, dict) and value.get('id') == NO_IDENTIFIERS_QID:
                entities_with_new_p39 += 1
                break
    
    print(f"Entities now having P39 Individual without identifiers: {entities_with_new_p39:,}")
    
    # Final statistics
    print()
    print("=== FINAL RESULTS ===")
    print(f"Entities examined: {len(entities_without_ids):,}")
    print(f"Entities already had P39: {entities_already_have_p39:,}")
    print(f"Entities updated with new P39: {entities_updated:,}")
    print(f"Total entities with P39 Individual without identifiers: {entities_with_new_p39:,}")
    
    if entities_updated > 0:
        print()
        print("SUCCESS: P39 Individual without identifiers added to all qualifying entities!")
        print("All entities without real identifiers are now properly categorized.")
    else:
        print()
        print("INFO: No updates needed - all entities already properly categorized.")
    
    client.close()
    
    return {
        'entities_examined': len(entities_without_ids),
        'entities_updated': entities_updated,
        'entities_already_had_p39': entities_already_have_p39,
        'final_count': entities_with_new_p39
    }

if __name__ == "__main__":
    start_time = time.time()
    results = add_no_identifiers_p39()
    duration = time.time() - start_time
    print(f"\nCompleted in {duration:.1f} seconds")