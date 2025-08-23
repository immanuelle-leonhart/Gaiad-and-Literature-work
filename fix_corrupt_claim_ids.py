#!/usr/bin/env python3
"""
Fix corrupt claim IDs in the MongoDB database
"""
import pymongo
import uuid
import re

def fix_corrupt_claim_ids():
    """Fix entities with corrupt claim IDs"""
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['gaiad_processing_db']
    collection = db['entities']
    
    print("=== FIXING CORRUPT CLAIM IDS ===")
    print()
    
    fixed_entities = 0
    fixed_claims = 0
    
    # Find entities with corrupt claim IDs
    for entity in collection.find():
        qid = entity['qid']
        properties = entity.get('properties', {})
        entity_needs_fix = False
        
        # Check each property for corrupt claim IDs
        for prop_id, claims in properties.items():
            if prop_id == 'redirect':
                continue
                
            for claim in claims:
                claim_id = claim.get('claim_id', '')
                
                # Check for corrupt patterns
                is_corrupt = False
                
                # Pattern 1: Old format like Q151436_P62_6000000041303977074
                if re.match(r'^Q\d+_P\d+_', claim_id):
                    is_corrupt = True
                
                # Pattern 2: UUID with suffix like Q151436$UUID_url
                if '_url' in claim_id or '_' in claim_id and '$' in claim_id:
                    is_corrupt = True
                
                # Pattern 3: Missing or invalid claim ID
                if not claim_id or not claim_id.startswith('Q'):
                    is_corrupt = True
                
                if is_corrupt:
                    # Generate new UUID claim ID
                    new_uuid = str(uuid.uuid4()).upper()
                    new_claim_id = f"{qid}${new_uuid}"
                    claim['claim_id'] = new_claim_id
                    
                    if not entity_needs_fix:
                        print(f"Fixing {qid}...")
                        entity_needs_fix = True
                    
                    print(f"  {prop_id}: {claim_id[:50]}... -> {new_claim_id}")
                    fixed_claims += 1
        
        # Update entity if it had corrupt claim IDs
        if entity_needs_fix:
            collection.update_one(
                {'qid': qid},
                {'$set': {'properties': properties}}
            )
            fixed_entities += 1
            print()
    
    print(f"=== SUMMARY ===")
    print(f"Fixed {fixed_entities} entities")
    print(f"Fixed {fixed_claims} corrupt claim IDs")
    
    client.close()
    return fixed_entities, fixed_claims

if __name__ == "__main__":
    fix_corrupt_claim_ids()