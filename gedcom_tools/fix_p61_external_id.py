#!/usr/bin/env python3
"""
Fix P61 External ID Format

The P61 properties are incorrectly stored as 'wikibase-item' type when they
should be 'external-id' type. This is causing the API import to fail with
"Type 'wikibase-item' is unsupported" errors.

This script:
1. Finds all P61 properties 
2. Converts them from wikibase-item format to external-id format
3. Preserves the actual Wikidata QID values
"""

import pymongo
import time

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

def fix_p61_external_id_format():
    """Fix P61 properties to use external-id format instead of wikibase-item"""
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    print("=== FIXING P61 EXTERNAL ID FORMAT ===")
    print()
    
    # Count entities with P61
    p61_count = 0
    for entity in collection.find():
        if 'P61' in entity.get('properties', {}):
            p61_count += 1
    
    print(f"Found {p61_count:,} entities with P61 properties")
    
    if p61_count == 0:
        print("No P61 properties found")
        client.close()
        return
    
    print("Analyzing P61 format issues...")
    
    # Check current format
    needs_fixing = []
    sample_count = 0
    
    for entity in collection.find():
        properties = entity.get('properties', {})
        if 'P61' in properties:
            qid = entity['qid']
            p61_claims = properties['P61']
            
            entity_needs_fix = False
            fixed_claims = []
            
            for claim in p61_claims:
                claim_value = claim.get('value')
                claim_type = claim.get('type', '')
                
                # Check if this is the problematic wikibase-item format
                if (isinstance(claim_value, dict) and 
                    claim_value.get('entity-type') == 'item' and
                    claim_type == 'wikibase-item'):
                    
                    # Extract the actual Wikidata QID
                    wikidata_qid = claim_value.get('id', '')
                    if wikidata_qid.startswith('Q'):
                        # Create proper external-id format
                        fixed_claim = {
                            'value': wikidata_qid,
                            'type': 'external-id',
                            'claim_id': claim.get('claim_id', f"{qid}_P61_{wikidata_qid}")
                        }
                        fixed_claims.append(fixed_claim)
                        entity_needs_fix = True
                        
                        if sample_count < 5:
                            print(f"  Sample fix for {qid}: {wikidata_qid}")
                            sample_count += 1
                
                elif isinstance(claim_value, str) and claim_value.startswith('Q'):
                    # Already in correct format
                    fixed_claims.append(claim)
                
                else:
                    # Other format - keep as is
                    fixed_claims.append(claim)
            
            if entity_needs_fix and fixed_claims:
                needs_fixing.append({
                    'qid': qid,
                    'fixed_claims': fixed_claims
                })
    
    print(f"Entities needing P61 format fixes: {len(needs_fixing):,}")
    
    if not needs_fixing:
        print("All P61 properties are already in correct format!")
        client.close()
        return
    
    print()
    print("Applying P61 format fixes...")
    
    # Apply fixes in batches
    batch_size = 1000
    fixed_count = 0
    
    for i in range(0, len(needs_fixing), batch_size):
        batch = needs_fixing[i:i + batch_size]
        bulk_ops = []
        
        for entity_fix in batch:
            qid = entity_fix['qid']
            fixed_claims = entity_fix['fixed_claims']
            
            bulk_ops.append(
                pymongo.UpdateOne(
                    {'qid': qid},
                    {'$set': {'properties.P61': fixed_claims}}
                )
            )
        
        # Execute batch
        collection.bulk_write(bulk_ops)
        fixed_count += len(batch)
        print(f"  Fixed {fixed_count:,} entities...")
    
    print(f"  Fixed {fixed_count:,} entities total")
    
    # Verify the fixes
    print()
    print("Verifying P61 fixes...")
    
    verification_samples = []
    for entity in collection.find().limit(100):
        properties = entity.get('properties', {})
        if 'P61' in properties:
            p61_claims = properties['P61']
            for claim in p61_claims:
                value = claim.get('value')
                claim_type = claim.get('type')
                
                if isinstance(value, str) and value.startswith('Q') and claim_type == 'external-id':
                    verification_samples.append({
                        'qid': entity['qid'],
                        'wikidata_qid': value
                    })
                    break
                    
            if len(verification_samples) >= 5:
                break
    
    print(f"Verified {len(verification_samples)} sample entities with correct P61 format:")
    for sample in verification_samples:
        print(f"  {sample['qid']} -> {sample['wikidata_qid']}")
    
    print()
    print("=== FIX RESULTS ===")
    print(f"Entities with P61 properties: {p61_count:,}")
    print(f"Entities fixed: {fixed_count:,}")
    print()
    
    if fixed_count > 0:
        print("SUCCESS: P61 properties fixed to external-id format!")
        print("Wikidata QIDs now use proper external identifier format:")
        print("- Type: 'external-id' (not 'wikibase-item')")
        print("- Value: 'Q12345' (direct string, not complex object)")
        print("This should resolve the API import errors.")
    
    client.close()
    
    return {
        'total_p61_entities': p61_count,
        'entities_fixed': fixed_count
    }

if __name__ == "__main__":
    start_time = time.time()
    results = fix_p61_external_id_format()
    duration = time.time() - start_time
    print(f"\nCompleted in {duration:.1f} seconds")