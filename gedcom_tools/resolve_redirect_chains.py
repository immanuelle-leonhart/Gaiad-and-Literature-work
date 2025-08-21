#!/usr/bin/env python3
"""
Resolve Redirect Chains and Fix References

Handles existing redirects from XML import and resolves chains:
Q136398 -> Q115039 -> Q12345 should all point to Q12345

Strategy:
1. Find all redirect entities (both from XML import and our merges)
2. Resolve redirect chains to find final targets
3. Update all references throughout database to point to final targets
4. Handle cases where XML redirects weren't properly imported
"""

import pymongo
import time
from collections import defaultdict

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

class RedirectChainResolver:
    def __init__(self, mongo_uri=MONGO_URI):
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db[COLLECTION_NAME]
        
        self.stats = {
            'redirects_found': 0,
            'chains_resolved': 0,
            'references_updated': 0,
            'entities_updated': 0,
            'xml_redirects_fixed': 0
        }
        
        print(f"Connected to MongoDB: {DATABASE_NAME}.{COLLECTION_NAME}")
    
    def find_all_redirects(self):
        """Find all redirect entities and their targets"""
        print("Finding all redirect entities...")
        
        redirects = {}  # redirect_qid -> immediate_target_qid
        redirect_entities = []
        
        for entity in self.collection.find():
            qid = entity['qid']
            properties = entity.get('properties', {})
            
            # Check for redirect property (from our merges)
            if 'redirect' in properties:
                target_qid = properties['redirect'][0]['value']
                redirects[qid] = target_qid
                redirect_entities.append(entity)
                continue
            
            # Check if entity might be an XML redirect that wasn't properly parsed
            # Look for entities with minimal data that might be redirects
            if (len(properties) == 0 and 
                len(entity.get('labels', {})) == 0 and
                len(entity.get('descriptions', {})) == 0):
                
                # This might be an XML redirect - we'll investigate further
                redirect_entities.append(entity)
        
        self.stats['redirects_found'] = len(redirects)
        print(f"  Found {len(redirects):,} explicit redirect entities")
        print(f"  Found {len(redirect_entities):,} total potential redirects")
        
        return redirects, redirect_entities
    
    def detect_xml_redirects(self, potential_redirects, known_redirects):
        """Detect XML redirects that weren't properly imported"""
        print("Detecting XML redirects that weren't properly imported...")
        
        xml_redirects = {}
        
        # Look for patterns that suggest XML redirects
        for entity in potential_redirects:
            qid = entity['qid']
            
            # Skip if already known as redirect
            if qid in known_redirects:
                continue
            
            # Check if this QID appears in any references - if it does,
            # but the entity is empty, it might be an XML redirect
            entity_is_referenced = False
            target_candidate = None
            
            # Quick scan to see if this empty entity is referenced
            sample_count = 0
            for other_entity in self.collection.find().limit(1000):
                sample_count += 1
                properties = other_entity.get('properties', {})
                
                for prop_id, claims in properties.items():
                    for claim in claims:
                        value = claim.get('value')
                        
                        if isinstance(value, str) and value == qid:
                            entity_is_referenced = True
                            # This empty entity is being referenced - suspicious
                            break
                        elif isinstance(value, dict) and value.get('id') == qid:
                            entity_is_referenced = True
                            break
                    
                    if entity_is_referenced:
                        break
                
                if entity_is_referenced:
                    break
            
            if entity_is_referenced:
                print(f"  Found referenced empty entity: {qid} (likely XML redirect)")
                # We'll need to determine the target through other means
        
        return xml_redirects
    
    def resolve_redirect_chains(self, redirects):
        """Resolve redirect chains to find final targets"""
        print("Resolving redirect chains...")
        
        final_targets = {}  # any_qid -> final_target_qid
        chains_found = 0
        
        def find_final_target(qid, visited=None):
            """Recursively find the final target, avoiding cycles"""
            if visited is None:
                visited = set()
            
            if qid in visited:
                # Cycle detected - return the QID itself
                print(f"    WARNING: Redirect cycle detected involving {qid}")
                return qid
            
            if qid not in redirects:
                # This is the final target
                return qid
            
            visited.add(qid)
            target = redirects[qid]
            return find_final_target(target, visited)
        
        # Resolve all redirects
        for redirect_qid in redirects:
            final_target = find_final_target(redirect_qid)
            final_targets[redirect_qid] = final_target
            
            # Check if this was a chain
            if redirects[redirect_qid] != final_target:
                chains_found += 1
                print(f"    Chain: {redirect_qid} -> {redirects[redirect_qid]} -> {final_target}")
        
        # Also map direct entities to themselves for easier lookup
        all_entities = set()
        for entity in self.collection.find({}, {'qid': 1}):
            all_entities.add(entity['qid'])
        
        for qid in all_entities:
            if qid not in final_targets:
                final_targets[qid] = qid
        
        self.stats['chains_resolved'] = chains_found
        print(f"  Resolved {chains_found:,} redirect chains")
        print(f"  Final mapping covers {len(final_targets):,} QIDs")
        
        return final_targets
    
    def update_all_references(self, final_targets):
        """Update all references throughout database to point to final targets"""
        print("Updating all references to point to final targets...")
        
        bulk_ops = []
        entities_checked = 0
        entities_updated = 0
        references_updated = 0
        
        for entity in self.collection.find():
            entities_checked += 1
            if entities_checked % 10000 == 0:
                print(f"  Checked {entities_checked:,} entities...")
            
            # Skip redirect entities themselves
            if 'redirect' in entity.get('properties', {}):
                continue
            
            entity_has_updates = False
            updates = {}
            
            # Check all properties for references
            properties = entity.get('properties', {})
            for prop_id, claims in properties.items():
                updated_claims = []
                claims_updated = False
                
                for claim in claims:
                    updated_claim = claim.copy()
                    value = claim.get('value')
                    
                    # Check different value types for QID references
                    if isinstance(value, str) and value.startswith('Q'):
                        if value in final_targets and final_targets[value] != value:
                            # This reference needs updating
                            updated_claim['value'] = final_targets[value]
                            claims_updated = True
                            references_updated += 1
                    elif isinstance(value, dict) and 'id' in value:
                        ref_qid = value.get('id')
                        if ref_qid and ref_qid.startswith('Q'):
                            if ref_qid in final_targets and final_targets[ref_qid] != ref_qid:
                                # This reference needs updating
                                updated_claim['value'] = value.copy()
                                updated_claim['value']['id'] = final_targets[ref_qid]
                                claims_updated = True
                                references_updated += 1
                    
                    updated_claims.append(updated_claim)
                
                if claims_updated:
                    updates[f'properties.{prop_id}'] = updated_claims
                    entity_has_updates = True
            
            # Add to batch if entity needs updates
            if entity_has_updates:
                bulk_ops.append(
                    pymongo.UpdateOne(
                        {'qid': entity['qid']},
                        {'$set': updates}
                    )
                )
                entities_updated += 1
                
                # Execute batch when full
                if len(bulk_ops) >= 1000:
                    self.collection.bulk_write(bulk_ops)
                    bulk_ops = []
        
        # Execute final batch
        if bulk_ops:
            self.collection.bulk_write(bulk_ops)
        
        print(f"  Checked {entities_checked:,} entities")
        print(f"  Updated {entities_updated:,} entities")
        print(f"  Updated {references_updated:,} references")
        
        self.stats['references_updated'] = references_updated
        self.stats['entities_updated'] = entities_updated
    
    def verify_no_redirect_references(self, redirects):
        """Verify no references point to redirect entities"""
        print("Verifying no references point to redirect entities...")
        
        bad_references = 0
        entities_checked = 0
        
        for entity in self.collection.find():
            entities_checked += 1
            if entities_checked % 20000 == 0:
                print(f"  Checked {entities_checked:,} entities...")
            
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
                        bad_references += 1
                        if bad_references <= 5:  # Show first 5 examples
                            print(f"    BAD: {entity['qid']} prop {prop_id} -> {referenced_qid}")
        
        print(f"  Checked {entities_checked:,} entities")
        print(f"  Bad references found: {bad_references:,}")
        
        return bad_references
    
    def run_redirect_chain_resolution(self):
        """Run complete redirect chain resolution process"""
        start_time = time.time()
        
        print("REDIRECT CHAIN RESOLUTION PROCESS")
        print("=" * 60)
        print("Step 1: Find all redirect entities")
        print("Step 2: Detect XML redirects that weren't properly imported")
        print("Step 3: Resolve redirect chains to final targets")
        print("Step 4: Update all references to point to final targets")
        print("Step 5: Verify no references point to redirects")
        print("=" * 60)
        print()
        
        # Step 1: Find all redirects
        redirects, potential_redirects = self.find_all_redirects()
        
        if not redirects:
            print("No redirects found - nothing to resolve")
            return
        
        print()
        
        # Step 2: Detect XML redirects (future enhancement)
        xml_redirects = self.detect_xml_redirects(potential_redirects, redirects)
        
        print()
        
        # Step 3: Resolve redirect chains
        final_targets = self.resolve_redirect_chains(redirects)
        
        print()
        
        # Step 4: Update all references
        self.update_all_references(final_targets)
        
        print()
        
        # Step 5: Verify results
        bad_refs = self.verify_no_redirect_references(redirects)
        
        duration = time.time() - start_time
        
        print()
        print("=" * 60)
        print("REDIRECT CHAIN RESOLUTION COMPLETE")
        print("=" * 60)
        print("RESULTS:")
        print(f"  Redirects found: {self.stats['redirects_found']:,}")
        print(f"  Chains resolved: {self.stats['chains_resolved']:,}")
        print(f"  XML redirects fixed: {self.stats['xml_redirects_fixed']:,}")
        print(f"  References updated: {self.stats['references_updated']:,}")
        print(f"  Entities updated: {self.stats['entities_updated']:,}")
        print(f"  Bad references remaining: {bad_refs:,}")
        print(f"  Duration: {duration:.1f} seconds")
        
        if bad_refs == 0:
            print()
            print("SUCCESS: All redirect chains resolved!")
            print("All references now point to final targets")
        else:
            print()
            print(f"WARNING: {bad_refs:,} bad references still exist")
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()

def main():
    resolver = RedirectChainResolver()
    
    try:
        resolver.run_redirect_chain_resolution()
    finally:
        resolver.close()

if __name__ == "__main__":
    main()