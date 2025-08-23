#!/usr/bin/env python3
"""
Add P61 (Wikidata QID) property to Q1787
"""
import pymongo

def add_p61_to_q1787():
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['gaiad_processing_db']
    collection = db['entities']
    
    # Find Q1787
    entity = collection.find_one({'qid': 'Q1787'})
    if entity:
        print('Found Q1787')
        
        # Get current properties
        properties = entity.get('properties', {})
        
        # Add P61 with the specified value
        p61_claim = {
            'value': '6000000040978635984',
            'type': 'external-id',
            'claim_id': 'Q1787_P61_6000000040978635984'
        }
        
        # Add to P61 property (create list if doesn't exist)
        if 'P61' not in properties:
            properties['P61'] = []
        
        # Check if this value already exists
        existing_values = [claim.get('value') for claim in properties['P61']]
        if '6000000040978635984' not in existing_values:
            properties['P61'].append(p61_claim)
            
            # Update the entity with proper MongoDB syntax
            result = collection.update_one(
                {'qid': 'Q1787'},
                {'$set': {'properties': properties}}
            )
            
            if result.modified_count > 0:
                print('SUCCESS: Added P61 6000000040978635984 to Q1787')
                print(f'Q1787 now has {len(properties["P61"])} P61 claims')
            else:
                print('ERROR: Failed to update Q1787')
        else:
            print('INFO: P61 6000000040978635984 already exists on Q1787')
            
        # Show current P61 values
        if 'P61' in properties:
            print('\nCurrent P61 values:')
            for claim in properties['P61']:
                print(f'  - {claim.get("value")}')
    else:
        print('ERROR: Q1787 not found in database')
    
    client.close()

if __name__ == "__main__":
    add_p61_to_q1787()