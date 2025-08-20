#!/usr/bin/env python3
"""
Migrate Identifier Properties

Migrates identifier properties to new external identifier format:
- P44 (Wikidata QID) -> P61 (Wikidata QID identifier)
- P43 (Geni ID) -> P62 (Geni ID identifier)  
- P60 (UUID) -> P63 (UUID Identifier)

All migrated as external-id type rather than strings.
"""

import pymongo
import time

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

class IdentifierPropertyMigrator:
    def __init__(self, mongo_uri=MONGO_URI):
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db[COLLECTION_NAME]
        
        self.stats = {
            'wikidata_migrated': 0,
            'geni_migrated': 0,
            'uuid_migrated': 0,
            'total_entities_updated': 0
        }
        
        print(f"Connected to MongoDB: {DATABASE_NAME}.{COLLECTION_NAME}")

    def migrate_identifiers(self):
        """Migrate all identifier properties to new external-id format"""
        print("Migrating identifier properties...")
        print("P44 -> P61 (Wikidata QID)")
        print("P43 -> P62 (Geni ID)")  
        print("P60 -> P63 (UUID)")
        print()
        
        processed = 0
        bulk_operations = []
        
        # Find entities with any of the old identifier properties
        query = {'$or': [
            {'properties.P44': {'$exists': True}},
            {'properties.P43': {'$exists': True}},
            {'properties.P60': {'$exists': True}}
        ]}
        
        for entity in self.collection.find(query):
            processed += 1
            if processed % 1000 == 0:
                print(f"  Processed {processed:,} entities...")
            
            qid = entity['qid']
            properties = entity.get('properties', {})
            updates = {}
            unsets = {}
            entity_updated = False
            
            # Migrate P44 (Wikidata QID) -> P61
            if 'P44' in properties:
                p44_claims = properties['P44']
                new_p61_claims = []
                
                for claim in p44_claims:
                    value = claim.get('value', '')
                    if isinstance(value, str) and value.startswith('Q'):
                        new_p61_claims.append({
                            'value': value,
                            'type': 'external-id',
                            'claim_id': claim.get('claim_id', f"{qid}_wikidata_{len(new_p61_claims)}")
                        })
                        self.stats['wikidata_migrated'] += 1
                
                if new_p61_claims:
                    updates['properties.P61'] = new_p61_claims
                    unsets['properties.P44'] = ""
                    entity_updated = True
            
            # Migrate P43 (Geni ID) -> P62  
            if 'P43' in properties:
                p43_claims = properties['P43']
                new_p62_claims = []
                
                for claim in p43_claims:
                    value = claim.get('value', '')
                    if isinstance(value, str) and value:
                        new_p62_claims.append({
                            'value': value,
                            'type': 'external-id',
                            'claim_id': claim.get('claim_id', f"{qid}_geni_{len(new_p62_claims)}")
                        })
                        self.stats['geni_migrated'] += 1
                
                if new_p62_claims:
                    updates['properties.P62'] = new_p62_claims
                    unsets['properties.P43'] = ""
                    entity_updated = True
            
            # Migrate P60 (UUID) -> P63
            if 'P60' in properties:
                p60_claims = properties['P60']
                new_p63_claims = []
                
                for claim in p60_claims:
                    value = claim.get('value', '')
                    if isinstance(value, str) and value:
                        new_p63_claims.append({
                            'value': value,
                            'type': 'external-id',
                            'claim_id': claim.get('claim_id', f"{qid}_uuid_{len(new_p63_claims)}")
                        })
                        self.stats['uuid_migrated'] += 1
                
                if new_p63_claims:
                    updates['properties.P63'] = new_p63_claims
                    unsets['properties.P60'] = ""
                    entity_updated = True
            
            if entity_updated:
                update_op = {"$set": updates}
                if unsets:
                    update_op["$unset"] = unsets
                
                bulk_operations.append(pymongo.UpdateOne({"_id": qid}, update_op))
                self.stats['total_entities_updated'] += 1
                
                if len(bulk_operations) >= 1000:
                    self.collection.bulk_write(bulk_operations)
                    bulk_operations = []
        
        # Execute remaining operations
        if bulk_operations:
            self.collection.bulk_write(bulk_operations)
        
        print(f"  Processed {processed:,} entities total")
        print()
        print("MIGRATION COMPLETE")
        print("=" * 50)
        print(f"Wikidata QIDs migrated (P44->P61): {self.stats['wikidata_migrated']:,}")
        print(f"Geni IDs migrated (P43->P62): {self.stats['geni_migrated']:,}")
        print(f"UUIDs migrated (P60->P63): {self.stats['uuid_migrated']:,}")
        print(f"Total entities updated: {self.stats['total_entities_updated']:,}")
        print(f"Total identifiers migrated: {sum([self.stats['wikidata_migrated'], self.stats['geni_migrated'], self.stats['uuid_migrated']]):,}")

    def verify_migration(self):
        """Verify migration completed successfully"""
        print()
        print("VERIFICATION")
        print("=" * 50)
        
        # Check old properties (should be 0)
        old_p44 = self.collection.count_documents({'properties.P44': {'$exists': True}})
        old_p43 = self.collection.count_documents({'properties.P43': {'$exists': True}})
        old_p60 = self.collection.count_documents({'properties.P60': {'$exists': True}})
        
        # Check new properties
        new_p61 = self.collection.count_documents({'properties.P61': {'$exists': True}})
        new_p62 = self.collection.count_documents({'properties.P62': {'$exists': True}})
        new_p63 = self.collection.count_documents({'properties.P63': {'$exists': True}})
        
        print("OLD PROPERTIES (should be 0):")
        print(f"  P44 (old Wikidata): {old_p44:,} entities")
        print(f"  P43 (old Geni): {old_p43:,} entities")
        print(f"  P60 (old UUID): {old_p60:,} entities")
        print()
        print("NEW PROPERTIES:")
        print(f"  P61 (Wikidata QID identifier): {new_p61:,} entities")
        print(f"  P62 (Geni ID identifier): {new_p62:,} entities")
        print(f"  P63 (UUID identifier): {new_p63:,} entities")
        
        if old_p44 == 0 and old_p43 == 0 and old_p60 == 0:
            print()
            print("✅ MIGRATION SUCCESSFUL - All old properties removed")
        else:
            print()
            print("⚠️  WARNING - Some old properties still exist")

    def run_migration(self):
        """Run complete migration process"""
        start_time = time.time()
        
        print("IDENTIFIER PROPERTY MIGRATION")
        print("=" * 50)
        print("Migrating to new external identifier properties:")
        print("• P44 -> P61 (Wikidata QID identifier)")
        print("• P43 -> P62 (Geni ID identifier)")
        print("• P60 -> P63 (UUID identifier)")
        print()
        
        self.migrate_identifiers()
        self.verify_migration()
        
        duration = time.time() - start_time
        print()
        print(f"Migration completed in {duration:.2f} seconds")

    def close(self):
        """Close MongoDB connection"""
        self.client.close()

def main():
    migrator = IdentifierPropertyMigrator()
    
    try:
        migrator.run_migration()
    finally:
        migrator.close()

if __name__ == "__main__":
    main()