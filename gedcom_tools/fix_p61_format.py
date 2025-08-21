#!/usr/bin/env python3
"""
Fix P61 Wikidata Property Format

Fixes all P61 (Wikidata ID) properties to use the correct format:
- Type: 'wikibase-item' (not 'external-id')  
- Value: {'entity-type': 'item', 'numeric-id': 12345, 'id': 'Q12345'}
  (not just string 'Q12345')

This ensures proper export to Wikibase XML format.
"""

import pymongo
import re
import time

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

def fix_p61_wikidata_format():
    """Fix all P61 properties to use correct Wikibase format"""
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    print("=== FIXING P61 WIKIDATA PROPERTY FORMAT ===")
    print()
    
    # Find all entities with P61 properties
    entities_with_p61 = list(collection.find({'properties.P61': {'$exists': True}}))
    print(f"Found {len(entities_with_p61):,} entities with P61 properties")
    
    if not entities_with_p61:
        print("No P61 properties found to fix")
        client.close()
        return
    
    print()
    print("Analyzing P61 property formats...")
    
    # Analyze current formats
    needs_fixing = []
    already_correct = 0
    invalid_qids = 0
    
    for entity in entities_with_p61:
        qid = entity['qid']
        p61_claims = entity['properties']['P61']
        entity_needs_fix = False
        fixed_claims = []
        
        for claim in p61_claims:
            current_value = claim.get('value')
            current_type = claim.get('type', 'unknown')
            
            # Check if this claim needs fixing
            if (isinstance(current_value, str) and 
                current_value.startswith('Q') and 
                current_type != 'wikibase-item'):
                
                # Extract numeric ID from Wikidata QID
                match = re.match(r'^Q(\d+)$', current_value)
                if match:
                    numeric_id = int(match.group(1))
                    
                    # Create proper Wikibase format
                    fixed_claim = {
                        'value': {
                            'entity-type': 'item',
                            'numeric-id': numeric_id,
                            'id': current_value
                        },
                        'type': 'wikibase-item',
                        'claim_id': claim.get('claim_id', f"{qid}_P61_{current_value}")
                    }
                    fixed_claims.append(fixed_claim)
                    entity_needs_fix = True
                else:
                    # Invalid QID format
                    invalid_qids += 1
                    print(f"  WARNING: Invalid Wikidata QID format in {qid}: {current_value}")
                    fixed_claims.append(claim)  # Keep as-is
            
            elif (isinstance(current_value, dict) and 
                  current_value.get('entity-type') == 'item' and
                  current_type == 'wikibase-item'):
                # Already in correct format
                fixed_claims.append(claim)
            
            else:
                # Other format - might need manual review
                fixed_claims.append(claim)
        
        if entity_needs_fix:
            needs_fixing.append({
                'qid': qid,
                'fixed_claims': fixed_claims
            })
        else:
            already_correct += 1
    
    print(f"Entities needing format fixes: {len(needs_fixing):,}")
    print(f"Entities already correct: {already_correct:,}")
    print(f"Invalid QID formats found: {invalid_qids:,}")
    
    if not needs_fixing:
        print("All P61 properties are already in correct format!")
        client.close()
        return
    
    print()
    print("Applying P61 format fixes...")
    
    # Apply fixes in batches
    bulk_ops = []
    entities_fixed = 0
    
    for entity_fix in needs_fixing:
        qid = entity_fix['qid']
        fixed_claims = entity_fix['fixed_claims']
        
        # Update the P61 property with fixed format
        bulk_ops.append(
            pymongo.UpdateOne(
                {'qid': qid},
                {'$set': {'properties.P61': fixed_claims}}
            )
        )
        entities_fixed += 1
        
        # Execute in batches
        if len(bulk_ops) >= 1000:
            collection.bulk_write(bulk_ops)
            bulk_ops = []
            print(f"  Fixed {entities_fixed:,} entities...")
    
    # Execute remaining operations
    if bulk_ops:
        collection.bulk_write(bulk_ops)
    
    print(f"  Fixed {entities_fixed:,} entities total")
    print()
    
    # Verify the fixes
    print("Verifying P61 format fixes...")
    
    verification_correct = 0
    verification_samples = []
    
    for entity in collection.find({'properties.P61': {'$exists': True}}).limit(100):
        qid = entity['qid']
        p61_claims = entity['properties']['P61']
        
        for claim in p61_claims:
            value = claim.get('value')
            claim_type = claim.get('type')
            
            if (isinstance(value, dict) and 
                value.get('entity-type') == 'item' and 
                claim_type == 'wikibase-item'):
                verification_correct += 1
                if len(verification_samples) < 5:
                    verification_samples.append({
                        'qid': qid,
                        'wikidata_qid': value.get('id'),
                        'numeric_id': value.get('numeric-id')
                    })
            break  # Check first claim only
    
    print(f"Verified format: {verification_correct}/100 sample entities correct")
    
    if verification_samples:
        print()
        print("Sample corrected formats:")
        for sample in verification_samples:
            print(f"  {sample['qid']} -> {sample['wikidata_qid']} (numeric: {sample['numeric_id']})")
    
    print()
    print("=== FIX RESULTS ===")
    print(f"Entities with P61 properties: {len(entities_with_p61):,}")
    print(f"Entities fixed: {entities_fixed:,}")
    print(f"Entities already correct: {already_correct:,}")
    print(f"Invalid QID formats: {invalid_qids:,}")
    
    if entities_fixed > 0:
        print()
        print("SUCCESS: P61 properties fixed to correct Wikibase format!")
        print("All Wikidata references now use proper entity format:")
        print("- Type: 'wikibase-item'")
        print("- Value: {'entity-type': 'item', 'numeric-id': X, 'id': 'QX'}")
        print("This will export correctly to Wikibase XML format.")
    else:
        print()
        print("INFO: All P61 properties were already in correct format")
    
    client.close()
    
    return {
        'entities_found': len(entities_with_p61),
        'entities_fixed': entities_fixed,
        'already_correct': already_correct,
        'invalid_qids': invalid_qids
    }

if __name__ == "__main__":
    start_time = time.time()
    results = fix_p61_wikidata_format()
    duration = time.time() - start_time
    print(f"\nCompleted in {duration:.1f} seconds")