#!/usr/bin/env python3
"""
Process Remaining Properties

Dedicated script to process the remaining P11 (sex) and P7/P8 (date) properties
that weren't handled by the bulk processor.
"""

import pymongo
import re
from collections import Counter

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

class RemainingPropertiesProcessor:
    def __init__(self, mongo_uri=MONGO_URI):
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db[COLLECTION_NAME]
        
        print(f"Connected to MongoDB: {DATABASE_NAME}.{COLLECTION_NAME}")

    def process_sex_properties(self):
        """Process remaining P11 sex properties -> P55"""
        print("Processing remaining P11 sex properties...")
        
        processed = 0
        converted = 0
        bulk_operations = []
        
        for entity in self.collection.find():
            processed += 1
            if processed % 10000 == 0:
                print(f"  Processed {processed:,} entities, converted {converted} sex properties...")
            
            properties = entity.get('properties', {})
            if 'P11' not in properties:
                continue
                
            qid = entity['qid']
            p11_claims = properties['P11']
            new_p55_claims = []
            
            for claim in p11_claims:
                value = claim.get('value', '')
                claim_type = claim.get('type', '')
                
                # Handle monolingualtext format
                if claim_type == 'monolingualtext' and isinstance(value, dict) and 'text' in value:
                    text_value = value['text'].lower().strip()
                    if text_value in ['male', 'm', 'man', 'q6581097']:
                        new_p55_claims.append({
                            'value': {'entity-type': 'item', 'numeric-id': 153718, 'id': 'Q153718'},
                            'type': 'wikibase-entityid',
                            'claim_id': claim.get('claim_id', f"{qid}_sex_male")
                        })
                    elif text_value in ['female', 'f', 'woman', 'q6581072']:
                        new_p55_claims.append({
                            'value': {'entity-type': 'item', 'numeric-id': 153719, 'id': 'Q153719'},
                            'type': 'wikibase-entityid', 
                            'claim_id': claim.get('claim_id', f"{qid}_sex_female")
                        })
                
                # Handle direct string format (legacy)
                elif isinstance(value, str):
                    value_lower = value.lower().strip()
                    if value_lower in ['male', 'm', 'man']:
                        new_p55_claims.append({
                            'value': {'entity-type': 'item', 'numeric-id': 153718, 'id': 'Q153718'},
                            'type': 'wikibase-entityid',
                            'claim_id': claim.get('claim_id', f"{qid}_sex_male")
                        })
                    elif value_lower in ['female', 'f', 'woman']:
                        new_p55_claims.append({
                            'value': {'entity-type': 'item', 'numeric-id': 153719, 'id': 'Q153719'},
                            'type': 'wikibase-entityid', 
                            'claim_id': claim.get('claim_id', f"{qid}_sex_female")
                        })
                
                # Handle Wikidata entity format
                elif isinstance(value, dict) and 'id' in value:
                    if value['id'] in ['Q6581097']:  # Wikidata male
                        new_p55_claims.append({
                            'value': {'entity-type': 'item', 'numeric-id': 153718, 'id': 'Q153718'},
                            'type': 'wikibase-entityid',
                            'claim_id': claim.get('claim_id', f"{qid}_sex_male_wd")
                        })
                    elif value['id'] in ['Q6581072']:  # Wikidata female
                        new_p55_claims.append({
                            'value': {'entity-type': 'item', 'numeric-id': 153719, 'id': 'Q153719'},
                            'type': 'wikibase-entityid',
                            'claim_id': claim.get('claim_id', f"{qid}_sex_female_wd")
                        })
            
            if new_p55_claims:
                # Check if entity already has P55 properties
                existing_p55 = properties.get('P55', [])
                all_p55_claims = existing_p55 + new_p55_claims
                
                bulk_operations.append(
                    pymongo.UpdateOne(
                        {"_id": qid},
                        {
                            "$set": {"properties.P55": all_p55_claims},
                            "$unset": {"properties.P11": ""}
                        }
                    )
                )
                converted += 1
                
                if len(bulk_operations) >= 1000:
                    self.collection.bulk_write(bulk_operations)
                    bulk_operations = []
        
        # Execute remaining operations
        if bulk_operations:
            self.collection.bulk_write(bulk_operations)
        
        print(f"OK Converted {converted:,} sex properties (P11 -> P55)")
        return converted

    def format_date_value(self, date_str):
        """Format date string into Wikibase time format"""
        if not date_str:
            return None
            
        date_str = str(date_str).strip()
        
        # Handle circa dates
        if date_str.lower().startswith(('abt', 'c.', 'circa')):
            date_str = re.sub(r'^(abt|c\.|circa)\s*', '', date_str, flags=re.IGNORECASE)
        
        # Handle year only
        if re.match(r'^-?\d{1,4}$', date_str):
            year = int(date_str)
            sign = '+' if year >= 0 else ''
            return {
                'time': f'{sign}{abs(year):04d}-00-00T00:00:00Z',
                'timezone': 0,
                'before': 0,
                'after': 0,
                'precision': 9,
                'calendarmodel': 'http://www.wikidata.org/entity/Q1985727'
            }
        
        # Handle full dates (12 JAN 1534)
        date_match = re.match(r'^(\d{1,2})\s+([A-Z]{3})\s+(\d{4})$', date_str.upper())
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
        
        # Handle other common formats
        # Format: YYYY-MM-DD
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return {
                'time': f'+{date_str}T00:00:00Z',
                'timezone': 0,
                'before': 0,
                'after': 0,
                'precision': 11,
                'calendarmodel': 'http://www.wikidata.org/entity/Q1985727'
            }
        
        return None

    def process_date_properties(self):
        """Process remaining P7 (birth) and P8 (death) date properties"""
        print("Processing remaining P7/P8 date properties...")
        
        processed = 0
        converted = 0
        bulk_operations = []
        
        for entity in self.collection.find():
            processed += 1
            if processed % 10000 == 0:
                print(f"  Processed {processed:,} entities, converted {converted} date properties...")
            
            properties = entity.get('properties', {})
            qid = entity['qid']
            updates = {}
            unsets = {}
            entity_updated = False
            
            # Process P7 (birth dates) -> P56
            if 'P7' in properties:
                p7_claims = properties['P7']
                new_p56_claims = []
                
                for claim in p7_claims:
                    value = claim.get('value', '')
                    claim_type = claim.get('type', 'string')
                    
                    # Handle monolingualtext format
                    if claim_type == 'monolingualtext' and isinstance(value, dict) and 'text' in value:
                        date_text = value['text']
                        formatted_date = self.format_date_value(date_text)
                        if formatted_date:
                            new_p56_claims.append({
                                'value': formatted_date,
                                'type': 'time',
                                'claim_id': claim.get('claim_id', f"{qid}_birth_{len(new_p56_claims)}")
                            })
                    elif claim_type == 'string':
                        formatted_date = self.format_date_value(value)
                        if formatted_date:
                            new_p56_claims.append({
                                'value': formatted_date,
                                'type': 'time',
                                'claim_id': claim.get('claim_id', f"{qid}_birth_{len(new_p56_claims)}")
                            })
                    elif claim_type == 'time':
                        # Already properly formatted
                        new_p56_claims.append(claim)
                
                if new_p56_claims:
                    # Merge with existing P56 if any
                    existing_p56 = properties.get('P56', [])
                    all_p56_claims = existing_p56 + new_p56_claims
                    updates['properties.P56'] = all_p56_claims
                    unsets['properties.P7'] = ""
                    entity_updated = True
            
            # Process P8 (death dates) -> P57
            if 'P8' in properties:
                p8_claims = properties['P8']
                new_p57_claims = []
                
                for claim in p8_claims:
                    value = claim.get('value', '')
                    claim_type = claim.get('type', 'string')
                    
                    # Handle monolingualtext format
                    if claim_type == 'monolingualtext' and isinstance(value, dict) and 'text' in value:
                        date_text = value['text']
                        formatted_date = self.format_date_value(date_text)
                        if formatted_date:
                            new_p57_claims.append({
                                'value': formatted_date,
                                'type': 'time',
                                'claim_id': claim.get('claim_id', f"{qid}_death_{len(new_p57_claims)}")
                            })
                    elif claim_type == 'string':
                        formatted_date = self.format_date_value(value)
                        if formatted_date:
                            new_p57_claims.append({
                                'value': formatted_date,
                                'type': 'time',
                                'claim_id': claim.get('claim_id', f"{qid}_death_{len(new_p57_claims)}")
                            })
                    elif claim_type == 'time':
                        # Already properly formatted
                        new_p57_claims.append(claim)
                
                if new_p57_claims:
                    # Merge with existing P57 if any
                    existing_p57 = properties.get('P57', [])
                    all_p57_claims = existing_p57 + new_p57_claims
                    updates['properties.P57'] = all_p57_claims
                    unsets['properties.P8'] = ""
                    entity_updated = True
            
            if entity_updated:
                update_op = {"$set": updates}
                if unsets:
                    update_op["$unset"] = unsets
                
                bulk_operations.append(pymongo.UpdateOne({"_id": qid}, update_op))
                converted += 1
                
                if len(bulk_operations) >= 1000:
                    self.collection.bulk_write(bulk_operations)
                    bulk_operations = []
        
        # Execute remaining operations
        if bulk_operations:
            self.collection.bulk_write(bulk_operations)
        
        print(f"OK Converted {converted:,} date properties (P7/P8 -> P56/P57)")
        return converted

    def run_all_processing(self):
        """Run all remaining property processing"""
        print("PROCESSING REMAINING PROPERTIES")
        print("=" * 50)
        
        total_entities = self.collection.count_documents({})
        print(f"Total entities: {total_entities:,}")
        print()
        
        # Process sex properties
        sex_converted = self.process_sex_properties()
        print()
        
        # Process date properties
        date_converted = self.process_date_properties()
        print()
        
        print("=" * 50)
        print("PROCESSING COMPLETE")
        print("=" * 50)
        print(f"Sex properties converted: {sex_converted:,}")
        print(f"Date properties converted: {date_converted:,}")
        print(f"Total conversions: {sex_converted + date_converted:,}")

    def close(self):
        """Close MongoDB connection"""
        self.client.close()

def main():
    processor = RemainingPropertiesProcessor()
    
    try:
        processor.run_all_processing()
    finally:
        processor.close()

if __name__ == "__main__":
    main()