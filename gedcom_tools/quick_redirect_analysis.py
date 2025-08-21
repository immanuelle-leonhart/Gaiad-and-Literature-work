#!/usr/bin/env python3
"""
Quick Redirect Analysis

Fast analysis to understand the redirect situation in the database.
"""

import pymongo
import time

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

def analyze_redirects():
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    print("=== QUICK REDIRECT ANALYSIS ===")
    print()
    
    # Find all redirect entities
    redirects = {}  # redirect_qid -> target_qid
    redirect_count = 0
    
    print("Finding redirect entities...")
    for entity in collection.find():
        properties = entity.get('properties', {})
        if 'redirect' in properties:
            redirect_qid = entity['qid']
            target_qid = properties['redirect'][0]['value']
            redirects[redirect_qid] = target_qid
            redirect_count += 1
    
    print(f"Found {redirect_count:,} redirect entities")
    
    if redirect_count == 0:
        print("No redirects found")
        client.close()
        return
    
    # Check for redirect chains
    print()
    print("Checking for redirect chains...")
    
    chains_found = 0
    
    for redirect_qid, target_qid in redirects.items():
        if target_qid in redirects:
            # This is a chain!
            chains_found += 1
            if chains_found <= 10:  # Show first 10 examples
                final_target = target_qid
                chain_length = 1
                visited = {redirect_qid}
                
                while final_target in redirects and final_target not in visited:
                    visited.add(final_target)
                    final_target = redirects[final_target] 
                    chain_length += 1
                    if chain_length > 10:  # Prevent infinite loops
                        break
                
                print(f"  Chain {chains_found}: {redirect_qid} -> {target_qid} -> {final_target} (length {chain_length})")
    
    print(f"Found {chains_found:,} redirect chains")
    
    # Sample some references to redirects
    print()
    print("Checking for references to redirect entities...")
    
    redirect_references = 0
    checked = 0
    
    for entity in collection.find().limit(10000):  # Sample first 10k
        checked += 1
        
        # Skip redirect entities themselves
        if 'redirect' in entity.get('properties', {}):
            continue
        
        properties = entity.get('properties', {})
        for prop_id, claims in properties.items():
            for claim in claims:
                value = claim.get('value')
                
                referenced_qid = None
                if isinstance(value, str) and value.startswith('Q'):
                    referenced_qid = value
                elif isinstance(value, dict) and value.get('id', '').startswith('Q'):
                    referenced_qid = value['id']
                
                if referenced_qid and referenced_qid in redirects:
                    redirect_references += 1
                    if redirect_references <= 5:  # Show first 5 examples
                        print(f"  Bad ref: {entity['qid']} prop {prop_id} -> {referenced_qid} (should be {redirects[referenced_qid]})")
    
    print(f"In sample of {checked:,} entities, found {redirect_references:,} references to redirects")
    
    if redirect_references > 0:
        estimated_total = (redirect_references / checked) * 145396
        print(f"Estimated total bad references in database: {estimated_total:,.0f}")
    
    client.close()

if __name__ == "__main__":
    start_time = time.time()
    analyze_redirects()
    duration = time.time() - start_time
    print(f"\nCompleted in {duration:.1f} seconds")