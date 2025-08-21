#!/usr/bin/env python3
"""
Add P39 "People without relatives" (Q153722)

Adds P39 property with value Q153722 (People without relatives) to all entities that:
- Do NOT have P47 (Father)
- Do NOT have P20 (Child)  
- Do NOT have P48 (Mother)
- Do NOT have P42 (Spouse)
- Are not redirect entities

This helps identify individuals potentially created in error or orphaned entries.
"""

import pymongo
import time

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

# Target value to add
NO_RELATIVES_QID = "Q153722"  # People without relatives

# Relationship properties to check
RELATIONSHIP_PROPERTIES = {'P47', 'P20', 'P48', 'P42'}  # Father, Child, Mother, Spouse

def add_no_relatives_p39():
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    print("=== ADDING P39 'People without relatives' (Q153722) ===")
    print()
    print("Criteria: Entities lacking ALL of these relationship properties:")
    print("  P47 (Father)")
    print("  P20 (Child)")
    print("  P48 (Mother)")
    print("  P42 (Spouse)")
    print()
    
    # Step 1: Find entities without any relationships
    print("Scanning database for entities without family relationships...")
    
    entities_without_relatives = []
    entities_with_father = 0
    entities_with_child = 0
    entities_with_mother = 0
    entities_with_spouse = 0
    entities_with_any_relationship = 0
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
        
        # Check for relationship properties
        has_father = 'P47' in properties
        has_child = 'P20' in properties
        has_mother = 'P48' in properties
        has_spouse = 'P42' in properties
        
        # Count for statistics
        if has_father:
            entities_with_father += 1
        if has_child:
            entities_with_child += 1
        if has_mother:
            entities_with_mother += 1
        if has_spouse:
            entities_with_spouse += 1
        
        # Check if entity has any relationships
        has_any_relationship = has_father or has_child or has_mother or has_spouse
        
        if has_any_relationship:
            entities_with_any_relationship += 1
        else:
            # This entity has no family relationships
            entities_without_relatives.append({
                'qid': qid,
                'entity': entity
            })
    
    print(f"  Checked {total_checked:,} entities total")
    print()
    
    # Step 2: Display statistics
    active_entities = total_checked - redirect_entities
    
    print("=== RELATIONSHIP STATISTICS ===")
    print(f"Active entities: {active_entities:,}")
    print(f"Redirect entities: {redirect_entities:,}")
    print(f"Entities with P47 (Father): {entities_with_father:,}")
    print(f"Entities with P20 (Child): {entities_with_child:,}")
    print(f"Entities with P48 (Mother): {entities_with_mother:,}")
    print(f"Entities with P42 (Spouse): {entities_with_spouse:,}")
    print(f"Entities with ANY relationship: {entities_with_any_relationship:,}")
    print(f"Entities WITHOUT any relationships: {len(entities_without_relatives):,}")
    print()
    
    if not entities_without_relatives:
        print("No entities found without family relationships")
        client.close()
        return
    
    # Step 3: Filter entities that already have P39 with this value
    print("Checking which entities already have P39 People without relatives...")
    
    entities_to_update = []
    entities_already_have_p39 = 0
    
    for entity_info in entities_without_relatives:
        entity = entity_info['entity']
        properties = entity.get('properties', {})
        
        # Check if entity already has P39 with our target value
        already_has_target_p39 = False
        
        if 'P39' in properties:
            for claim in properties['P39']:
                value = claim.get('value', '')
                if isinstance(value, str) and value == NO_RELATIVES_QID:
                    already_has_target_p39 = True
                    break
                elif isinstance(value, dict) and value.get('id') == NO_RELATIVES_QID:
                    already_has_target_p39 = True
                    break
        
        if already_has_target_p39:
            entities_already_have_p39 += 1
        else:
            entities_to_update.append(entity_info)
    
    print(f"Entities already having P39 People without relatives: {entities_already_have_p39:,}")
    print(f"Entities needing P39 People without relatives: {len(entities_to_update):,}")
    print()
    
    if not entities_to_update:
        print("All entities already have the correct P39 value")
        client.close()
        return
    
    # Step 4: Add P39 property to entities
    print("Adding P39 People without relatives to entities...")
    
    bulk_ops = []
    entities_updated = 0
    
    for entity_info in entities_to_update:
        qid = entity_info['qid']
        entity = entity_info['entity']
        properties = entity.get('properties', {})
        
        # Create new P39 claim
        new_claim = {
            'value': NO_RELATIVES_QID,
            'type': 'wikibase-item',
            'claim_id': f"{qid}_P39_{NO_RELATIVES_QID}"
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
            
            if isinstance(value, str) and value == NO_RELATIVES_QID:
                entities_with_new_p39 += 1
                break
            elif isinstance(value, dict) and value.get('id') == NO_RELATIVES_QID:
                entities_with_new_p39 += 1
                break
    
    print(f"Entities now having P39 People without relatives: {entities_with_new_p39:,}")
    
    # Step 6: Cross-check with other P39 values for overlap analysis
    print()
    print("Analyzing overlap with other P39 categories...")
    
    entities_with_no_identifiers = 0
    entities_with_both_categories = 0
    
    for entity in collection.find({'properties.P39': {'$exists': True}}):
        p39_claims = entity.get('properties', {}).get('P39', [])
        
        has_no_identifiers = False
        has_no_relatives = False
        
        for claim in p39_claims:
            value = claim.get('value', '')
            if isinstance(value, dict):
                value = value.get('id', '')
            
            if value == "Q153721":  # Individual without identifiers
                has_no_identifiers = True
                entities_with_no_identifiers += 1
            elif value == NO_RELATIVES_QID:  # People without relatives
                has_no_relatives = True
        
        if has_no_identifiers and has_no_relatives:
            entities_with_both_categories += 1
    
    print(f"Entities with P39 Individual without identifiers: {entities_with_no_identifiers:,}")
    print(f"Entities with BOTH no identifiers AND no relatives: {entities_with_both_categories:,}")
    
    # Final statistics
    print()
    print("=== FINAL RESULTS ===")
    print(f"Entities examined: {len(entities_without_relatives):,}")
    print(f"Entities already had P39: {entities_already_have_p39:,}")
    print(f"Entities updated with new P39: {entities_updated:,}")
    print(f"Total entities with P39 People without relatives: {entities_with_new_p39:,}")
    print(f"Entities with both P39 categories: {entities_with_both_categories:,}")
    
    if entities_updated > 0:
        print()
        print("SUCCESS: P39 People without relatives added to all qualifying entities!")
        print("All entities without family relationships are now properly categorized.")
        print("This helps identify potentially erroneous or orphaned genealogical entries.")
    else:
        print()
        print("INFO: No updates needed - all entities already properly categorized.")
    
    client.close()
    
    return {
        'entities_examined': len(entities_without_relatives),
        'entities_updated': entities_updated,
        'entities_already_had_p39': entities_already_have_p39,
        'final_count': entities_with_new_p39,
        'both_categories': entities_with_both_categories
    }

if __name__ == "__main__":
    start_time = time.time()
    results = add_no_relatives_p39()
    duration = time.time() - start_time
    print(f"\nCompleted in {duration:.1f} seconds")