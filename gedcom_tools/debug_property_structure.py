#!/usr/bin/env python3
"""
Debug Property Structure

Investigates exactly how P11, P7, and P8 properties are structured in the database
to understand why they're not being processed correctly.
"""

import pymongo
import json

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

def debug_properties():
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    print("=== DEBUGGING PROPERTY STRUCTURE ===")
    print()
    
    # Find entities that should have these properties
    p11_found = []
    p7_found = []
    p8_found = []
    
    print("Searching for P11, P7, P8 properties...")
    searched = 0
    
    for entity in collection.find():
        searched += 1
        if searched % 20000 == 0:
            print(f"  Searched {searched:,} entities...")
        
        properties = entity.get('properties', {})
        qid = entity['qid']
        
        if 'P11' in properties and len(p11_found) < 5:
            p11_found.append({
                'qid': qid,
                'properties': properties['P11']
            })
        
        if 'P7' in properties and len(p7_found) < 5:
            p7_found.append({
                'qid': qid,
                'properties': properties['P7']
            })
            
        if 'P8' in properties and len(p8_found) < 5:
            p8_found.append({
                'qid': qid,
                'properties': properties['P8']
            })
        
        # Stop when we have samples of all
        if len(p11_found) >= 5 and len(p7_found) >= 5 and len(p8_found) >= 5:
            break
    
    print(f"  Searched {searched:,} entities total")
    print()
    
    # Show P11 samples
    print("=== P11 SAMPLES ===")
    if p11_found:
        for sample in p11_found:
            print(f"Entity {sample['qid']}:")
            print(f"  P11 structure: {json.dumps(sample['properties'], indent=2)}")
            print()
    else:
        print("No P11 properties found!")
    
    # Show P7 samples
    print("=== P7 SAMPLES ===")
    if p7_found:
        for sample in p7_found:
            print(f"Entity {sample['qid']}:")
            print(f"  P7 structure: {json.dumps(sample['properties'], indent=2)}")
            print()
    else:
        print("No P7 properties found!")
    
    # Show P8 samples
    print("=== P8 SAMPLES ===") 
    if p8_found:
        for sample in p8_found:
            print(f"Entity {sample['qid']}:")
            print(f"  P8 structure: {json.dumps(sample['properties'], indent=2)}")
            print()
    else:
        print("No P8 properties found!")
    
    # Let's also manually check some specific entities that should have these
    print("=== MANUAL ENTITY CHECKS ===")
    
    # Check a few specific entities
    test_qids = ['Q100000', 'Q150000', 'Q16244', 'Q16245']
    for qid in test_qids:
        entity = collection.find_one({'qid': qid})
        if entity:
            properties = entity.get('properties', {})
            has_p11 = 'P11' in properties
            has_p7 = 'P7' in properties
            has_p8 = 'P8' in properties
            
            print(f"{qid}: P11={has_p11}, P7={has_p7}, P8={has_p8}")
            if has_p11:
                print(f"  P11: {properties['P11'][:2]}")  # First 2 claims
            if has_p7:
                print(f"  P7: {properties['P7'][:2]}")
            if has_p8:
                print(f"  P8: {properties['P8'][:2]}")
        else:
            print(f"{qid}: Entity not found")
    
    print()
    print("=== COUNT VERIFICATION ===")
    # Manual count to verify
    manual_p11 = 0
    manual_p7 = 0
    manual_p8 = 0
    
    for entity in collection.find().limit(10000):  # Check first 10k
        properties = entity.get('properties', {})
        if 'P11' in properties:
            manual_p11 += 1
        if 'P7' in properties:
            manual_p7 += 1
        if 'P8' in properties:
            manual_p8 += 1
    
    print(f"In first 10,000 entities:")
    print(f"  P11 found: {manual_p11}")
    print(f"  P7 found: {manual_p7}")
    print(f"  P8 found: {manual_p8}")
    
    client.close()

if __name__ == "__main__":
    debug_properties()