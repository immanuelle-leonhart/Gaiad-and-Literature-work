#!/usr/bin/env python3
"""
MONGODB BULK PROCESSOR

Performs bulk database fixes on MongoDB-imported Wikibase data.
This processes 560MB of data in minutes instead of days.

Operations:
1. Fix sex properties (P11 -> P55 with Q153718/Q153719)
2. Fix date properties (P7/P8 -> P56/P57) 
3. Extract Wikidata QIDs from REFN (P41 -> P44)
4. Extract Geni IDs from REFN (P41 -> P43)
5. Add "no identifiers" instances (P39 -> Q153720)
6. Clean REFERENCE_NUMBERS notes
7. Generate merge mapping CSV for duplicate resolution
"""

import pymongo
import re
import json
import csv
import time
from collections import defaultdict
import threading

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

class MongoDBBulkProcessor:
    def __init__(self, mongo_uri=MONGO_URI):
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db[COLLECTION_NAME]
        
        # Statistics
        self.stats = {
            'sex_fixes': 0,
            'date_fixes': 0,
            'wikidata_extractions': 0,
            'geni_extractions': 0,
            'no_identifier_instances': 0,
            'note_cleanups': 0,
            'total_processed': 0
        }
        
        print(f"Connected to MongoDB: {DATABASE_NAME}.{COLLECTION_NAME}")
        
    def fix_sex_properties_bulk(self):
        """Bulk fix sex properties: P11 string -> P55 with Q153718/Q153719"""
        print("Fixing sex properties in bulk...")
        
        # Find entities with P11 properties
        pipeline = [
            {"$match": {"properties.P11": {"$exists": True}}},
            {"$project": {"qid": 1, "properties.P11": 1}}
        ]
        
        bulk_operations = []
        count = 0
        
        for entity in self.collection.aggregate(pipeline):
            qid = entity['qid']
            p11_claims = entity['properties']['P11']
            
            new_p55_claims = []
            
            for claim in p11_claims:
                value = claim.get('value')
                if isinstance(value, str):
                    if value.lower() in ['male', 'm']:
                        new_p55_claims.append({
                            'value': 'Q153718',
                            'type': 'wikibase-item',
                            'claim_id': claim.get('claim_id')
                        })
                    elif value.lower() in ['female', 'f']:
                        new_p55_claims.append({
                            'value': 'Q153719', 
                            'type': 'wikibase-item',
                            'claim_id': claim.get('claim_id')
                        })
                elif isinstance(value, dict) and 'id' in value:
                    # Already a Wikidata item reference
                    if value['id'] in ['Q6581097', 'Q6581072']:  # Wikidata male/female
                        new_value = 'Q153718' if value['id'] == 'Q6581097' else 'Q153719'
                        new_p55_claims.append({
                            'value': new_value,
                            'type': 'wikibase-item', 
                            'claim_id': claim.get('claim_id')
                        })
            
            if new_p55_claims:
                # Add P55 and remove P11
                bulk_operations.append(
                    pymongo.UpdateOne(
                        {"_id": qid},
                        {
                            "$set": {"properties.P55": new_p55_claims},
                            "$unset": {"properties.P11": ""}
                        }
                    )
                )
                count += 1
                
                if len(bulk_operations) >= 1000:  # Batch size
                    self.collection.bulk_write(bulk_operations)
                    bulk_operations = []
                    print(f"  Processed {count} sex property fixes...")
        
        # Execute remaining operations
        if bulk_operations:
            self.collection.bulk_write(bulk_operations)
            
        self.stats['sex_fixes'] = count
        print(f"OK Fixed {count} sex properties")
    
    def fix_date_properties_bulk(self):
        """Bulk fix date properties: P7/P8 -> P56/P57"""
        print("Fixing date properties in bulk...")
        
        count = 0
        bulk_operations = []
        
        # Fix birth dates (P7 -> P56)
        for entity in self.collection.find({"properties.P7": {"$exists": True}}):
            qid = entity['qid']
            p7_claims = entity['properties']['P7']
            
            p56_claims = []
            for claim in p7_claims:
                if claim.get('type') == 'string':
                    # Convert string date to proper time format
                    formatted_date = self.format_date_value(claim.get('value', ''))
                    if formatted_date:
                        p56_claims.append({
                            'value': formatted_date,
                            'type': 'time',
                            'claim_id': claim.get('claim_id')
                        })
                elif claim.get('type') == 'time':
                    # Already time format, just move it
                    p56_claims.append(claim)
            
            if p56_claims:
                bulk_operations.append(
                    pymongo.UpdateOne(
                        {"_id": qid},
                        {
                            "$set": {"properties.P56": p56_claims},
                            "$unset": {"properties.P7": ""}
                        }
                    )
                )
                count += 1
        
        # Fix death dates (P8 -> P57)
        for entity in self.collection.find({"properties.P8": {"$exists": True}}):
            qid = entity['qid']
            p8_claims = entity['properties']['P8']
            
            p57_claims = []
            for claim in p8_claims:
                if claim.get('type') == 'string':
                    formatted_date = self.format_date_value(claim.get('value', ''))
                    if formatted_date:
                        p57_claims.append({
                            'value': formatted_date,
                            'type': 'time',
                            'claim_id': claim.get('claim_id')
                        })
                elif claim.get('type') == 'time':
                    p57_claims.append(claim)
            
            if p57_claims:
                bulk_operations.append(
                    pymongo.UpdateOne(
                        {"_id": qid},
                        {
                            "$set": {"properties.P57": p57_claims},
                            "$unset": {"properties.P8": ""}
                        }
                    )
                )
                count += 1
        
        # Execute bulk operations
        if bulk_operations:
            self.collection.bulk_write(bulk_operations)
            
        self.stats['date_fixes'] = count
        print(f"OK Fixed {count} date properties")
    
    def extract_identifiers_bulk(self):
        """Bulk extract Wikidata QIDs and Geni IDs from P41 REFN"""
        print("Extracting identifiers from REFN in bulk...")
        
        bulk_operations = []
        wikidata_count = 0
        geni_count = 0
        
        for entity in self.collection.find({"properties.P41": {"$exists": True}}):
            qid = entity['qid']
            p41_claims = entity['properties']['P41']
            
            updates = {}
            claims_to_remove = []
            
            for claim in p41_claims:
                value = claim.get('value')
                if not isinstance(value, str):
                    continue
                
                # Check for Wikidata QID
                if re.match(r'^Q\d+$', value):
                    if 'properties.P44' not in updates:
                        updates['properties.P44'] = []
                    updates['properties.P44'].append({
                        'value': value,
                        'type': 'external-id',
                        'claim_id': claim.get('claim_id')
                    })
                    
                    # Also add described at URL (P45)
                    if 'properties.P45' not in updates:
                        updates['properties.P45'] = []
                    updates['properties.P45'].append({
                        'value': f"https://wikidata.org/wiki/{value}",
                        'type': 'url',
                        'claim_id': claim.get('claim_id') + '_url'
                    })
                    
                    claims_to_remove.append(claim)
                    wikidata_count += 1
                
                # Check for Geni ID (numeric)
                elif value.isdigit():
                    if 'properties.P43' not in updates:
                        updates['properties.P43'] = []
                    updates['properties.P43'].append({
                        'value': value,
                        'type': 'external-id',
                        'claim_id': claim.get('claim_id')
                    })
                    
                    # Also add Geni URL
                    if 'properties.P45' not in updates:
                        updates['properties.P45'] = []
                    updates['properties.P45'].append({
                        'value': f"https://www.geni.com/people/{value}",
                        'type': 'url',
                        'claim_id': claim.get('claim_id') + '_geni'
                    })
                    
                    claims_to_remove.append(claim)
                    geni_count += 1
            
            if updates:
                # Remove processed REFN claims
                remaining_p41 = [c for c in p41_claims if c not in claims_to_remove]
                
                operation_data = {"$set": updates}
                if not remaining_p41:
                    operation_data["$unset"] = {"properties.P41": ""}
                else:
                    operation_data["$set"]["properties.P41"] = remaining_p41
                
                bulk_operations.append(pymongo.UpdateOne({"_id": qid}, operation_data))
                
                if len(bulk_operations) >= 1000:
                    self.collection.bulk_write(bulk_operations)
                    bulk_operations = []
                    print(f"  Processed {wikidata_count} Wikidata, {geni_count} Geni extractions...")
        
        if bulk_operations:
            self.collection.bulk_write(bulk_operations)
        
        self.stats['wikidata_extractions'] = wikidata_count
        self.stats['geni_extractions'] = geni_count
        print(f"OK Extracted {wikidata_count} Wikidata QIDs, {geni_count} Geni IDs")
    
    def add_no_identifiers_instances_bulk(self):
        """Bulk add P39:Q153720 for items with no identifiers"""
        print("Adding 'no identifiers' instances in bulk...")
        
        # Find items without key identifier properties
        pipeline = [
            {
                "$match": {
                    "entity_type": "item",
                    "$and": [
                        {"properties.P44": {"$exists": False}},  # No Wikidata ID
                        {"properties.P43": {"$exists": False}},  # No Geni ID
                        {"properties.P41": {"$exists": False}}   # No REFN
                    ]
                }
            },
            {"$project": {"qid": 1}}
        ]
        
        bulk_operations = []
        count = 0
        
        for entity in self.collection.aggregate(pipeline):
            qid = entity['qid']
            
            bulk_operations.append(
                pymongo.UpdateOne(
                    {"_id": qid},
                    {
                        "$set": {
                            "properties.P39": [{
                                'value': 'Q153720',
                                'type': 'wikibase-item',
                                'claim_id': f"{qid}_no_identifiers"
                            }]
                        }
                    }
                )
            )
            count += 1
            
            if len(bulk_operations) >= 1000:
                self.collection.bulk_write(bulk_operations)
                bulk_operations = []
                print(f"  Added {count} 'no identifiers' instances...")
        
        if bulk_operations:
            self.collection.bulk_write(bulk_operations)
        
        self.stats['no_identifier_instances'] = count
        print(f"OK Added {count} 'no identifiers' instances")
    
    def format_date_value(self, date_str):
        """Format date string into Wikibase time format"""
        if not date_str:
            return None
            
        date_str = date_str.strip()
        
        # Handle circa dates
        if date_str.lower().startswith(('abt', 'c.', 'circa')):
            date_str = re.sub(r'^(abt|c\.|circa)\s*', '', date_str, flags=re.IGNORECASE)
        
        # Handle year only
        if re.match(r'^\d{4}$', date_str):
            return {
                'time': f'+{date_str}-00-00T00:00:00Z',
                'timezone': 0,
                'before': 0,
                'after': 0,
                'precision': 9,
                'calendarmodel': 'http://www.wikidata.org/entity/Q1985727'
            }
        
        # Handle full dates (12 JAN 1534)
        date_match = re.match(r'^(\d{1,2})\s+([A-Z]{3})\s+(\d{4})$', date_str)
        if date_match:
            day, month_abbr, year = date_match.groups()
            month_map = {
                'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
                'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
                'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
            }
            month = month_map.get(month_abbr, '00')
            day = day.zfill(2)
            
            return {
                'time': f'+{year}-{month}-{day}T00:00:00Z',
                'timezone': 0,
                'before': 0,
                'after': 0,
                'precision': 11,
                'calendarmodel': 'http://www.wikidata.org/entity/Q1985727'
            }
        
        return None
    
    def generate_correspondence_csv(self, filename="mongodb_correspondence.csv"):
        """Generate correspondence CSV with all entity data"""
        print("Generating correspondence CSV...")
        
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['QID', 'Wikidata_QID', 'Geni_IDs', 'Label', 'Description', 'Properties'])
            
            count = 0
            for entity in self.collection.find({"entity_type": "item"}):
                qid = entity['qid']
                
                # Extract identifiers
                wikidata_qid = ""
                if 'P44' in entity.get('properties', {}):
                    p44_claims = entity['properties']['P44']
                    if p44_claims:
                        wikidata_qid = p44_claims[0].get('value', '')
                
                geni_ids = []
                if 'P43' in entity.get('properties', {}):
                    for claim in entity['properties']['P43']:
                        geni_id = claim.get('value')
                        if geni_id:
                            geni_ids.append(geni_id)
                
                # Get label and description
                label = entity.get('labels', {}).get('en', '')
                description = entity.get('descriptions', {}).get('en', '')
                
                # Count properties
                property_count = len(entity.get('properties', {}))
                
                writer.writerow([
                    qid,
                    wikidata_qid,
                    ';'.join(geni_ids),
                    label,
                    description,
                    str(property_count)
                ])
                
                count += 1
                if count % 10000 == 0:
                    print(f"  Generated {count} rows...")
        
        print(f"OK Generated {filename} with {count} entities")
    
    def run_all_fixes(self):
        """Run all bulk operations"""
        start_time = time.time()
        
        print("Starting MongoDB bulk processing...")
        print("="*50)
        
        # Get initial count
        total_entities = self.collection.count_documents({})
        print(f"Total entities in database: {total_entities:,}")
        
        # Run all fixes
        self.fix_sex_properties_bulk()
        self.fix_date_properties_bulk()
        self.extract_identifiers_bulk()
        self.add_no_identifiers_instances_bulk()
        self.generate_correspondence_csv()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Print summary
        print("\n" + "="*50)
        print("BULK PROCESSING COMPLETE")
        print("="*50)
        print(f"Sex property fixes: {self.stats['sex_fixes']:,}")
        print(f"Date property fixes: {self.stats['date_fixes']:,}")
        print(f"Wikidata ID extractions: {self.stats['wikidata_extractions']:,}")
        print(f"Geni ID extractions: {self.stats['geni_extractions']:,}")
        print(f"No-identifier instances: {self.stats['no_identifier_instances']:,}")
        print(f"Total processing time: {duration:.2f} seconds")
        print(f"Processing rate: {total_entities / duration:.0f} entities/second")
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()

def main():
    processor = MongoDBBulkProcessor()
    
    try:
        processor.run_all_fixes()
    finally:
        processor.close()

if __name__ == "__main__":
    main()