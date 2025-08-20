#!/usr/bin/env python3
"""
Process Edge Case Properties

Handles the remaining P11, P7, and P8 properties that have special formats
not handled by the main processing script.
"""

import pymongo
import re
from collections import Counter

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

class EdgeCasePropertiesProcessor:
    def __init__(self, mongo_uri=MONGO_URI):
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db[COLLECTION_NAME]
        
        print(f"Connected to MongoDB: {DATABASE_NAME}.{COLLECTION_NAME}")

    def process_unknown_sex_properties(self):
        """Process remaining P11 properties with 'u'/'U' values (unknown)"""
        print("Processing unknown sex properties...")
        
        processed = 0
        converted = 0
        bulk_operations = []
        
        for entity in self.collection.find({'properties.P11': {'$exists': True}}):
            processed += 1
            if processed % 1000 == 0:
                print(f"  Processed {processed} entities, converted {converted} unknown sex properties...")
            
            properties = entity.get('properties', {})
            qid = entity['qid']
            p11_claims = properties['P11']
            new_p55_claims = []
            
            for claim in p11_claims:
                value = claim.get('value', '')
                claim_type = claim.get('type', '')
                
                # Handle monolingualtext format with 'u'/'U' values
                if claim_type == 'monolingualtext' and isinstance(value, dict) and 'text' in value:
                    text_value = value['text'].lower().strip()
                    if text_value in ['u', 'unknown', 'unspecified']:
                        # Map to "unknown" sex value Q153721
                        new_p55_claims.append({
                            'value': {'entity-type': 'item', 'numeric-id': 153721, 'id': 'Q153721'},
                            'type': 'wikibase-entityid',
                            'claim_id': claim.get('claim_id', f"{qid}_sex_unknown")
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
        
        print(f"OK Converted {converted} unknown sex properties (P11 -> P55)")
        return converted

    def format_date_value_advanced(self, date_str):
        """Advanced date formatting for edge cases"""
        if not date_str:
            return None
            
        date_str = str(date_str).strip()
        
        # Remove parentheses and special characters
        date_str = re.sub(r'[()–—-]', '', date_str).strip()
        
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
        
        # Handle month and year (MAY 1541, OCT 1733)
        month_year_match = re.match(r'^([A-Z]{3})\s+(\d{4})$', date_str.upper())
        if month_year_match:
            month_abbr, year = month_year_match.groups()
            month_map = {
                'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
                'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
                'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
            }
            month = month_map.get(month_abbr, '00')
            
            return {
                'time': f'+{year}-{month}-00T00:00:00Z',
                'timezone': 0,
                'before': 0,
                'after': 0,
                'precision': 10,
                'calendarmodel': 'http://www.wikidata.org/entity/Q1985727'
            }
        
        # Handle full dates (1 JAN 503, 12 JAN 1534)
        date_match = re.match(r'^(\d{1,2})\s+([A-Z]{3})\s+(\d{1,4})$', date_str.upper())
        if date_match:
            day, month_abbr, year = date_match.groups()
            month_map = {
                'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
                'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
                'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
            }
            month = month_map.get(month_abbr, '00')
            day = day.zfill(2)
            year = year.zfill(4)
            
            return {
                'time': f'+{year}-{month}-{day}T00:00:00Z',
                'timezone': 0,
                'before': 0,
                'after': 0,
                'precision': 11,
                'calendarmodel': 'http://www.wikidata.org/entity/Q1985727'
            }
        
        # Handle other formats (try to extract year)
        year_match = re.search(r'\b(\d{3,4})\b', date_str)
        if year_match:
            year = int(year_match.group(1))
            return {
                'time': f'+{year:04d}-00-00T00:00:00Z',
                'timezone': 0,
                'before': 0,
                'after': 0,
                'precision': 9,
                'calendarmodel': 'http://www.wikidata.org/entity/Q1985727'
            }
        
        return None

    def process_complex_date_properties(self):
        """Process remaining P7/P8 properties with complex formats"""
        print("Processing complex date properties...")
        
        processed = 0
        converted = 0
        bulk_operations = []
        
        # Process P7 and P8 entities
        for entity in self.collection.find({'$or': [{'properties.P7': {'$exists': True}}, {'properties.P8': {'$exists': True}}]}):
            processed += 1
            if processed % 1000 == 0:
                print(f"  Processed {processed} entities, converted {converted} date properties...")
            
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
                        formatted_date = self.format_date_value_advanced(date_text)
                        if formatted_date:
                            new_p56_claims.append({
                                'value': formatted_date,
                                'type': 'time',
                                'claim_id': claim.get('claim_id', f"{qid}_birth_{len(new_p56_claims)}")
                            })
                    elif claim_type == 'string':
                        formatted_date = self.format_date_value_advanced(value)
                        if formatted_date:
                            new_p56_claims.append({
                                'value': formatted_date,
                                'type': 'time',
                                'claim_id': claim.get('claim_id', f"{qid}_birth_{len(new_p56_claims)}")
                            })
                
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
                        formatted_date = self.format_date_value_advanced(date_text)
                        if formatted_date:
                            new_p57_claims.append({
                                'value': formatted_date,
                                'type': 'time',
                                'claim_id': claim.get('claim_id', f"{qid}_death_{len(new_p57_claims)}")
                            })
                    elif claim_type == 'string':
                        formatted_date = self.format_date_value_advanced(value)
                        if formatted_date:
                            new_p57_claims.append({
                                'value': formatted_date,
                                'type': 'time',
                                'claim_id': claim.get('claim_id', f"{qid}_death_{len(new_p57_claims)}")
                            })
                
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
        
        print(f"OK Converted {converted} complex date properties (P7/P8 -> P56/P57)")
        return converted

    def run_all_edge_case_processing(self):
        """Run all edge case property processing"""
        print("PROCESSING EDGE CASE PROPERTIES")
        print("=" * 50)
        
        # Process unknown sex properties
        sex_converted = self.process_unknown_sex_properties()
        print()
        
        # Process complex date properties
        date_converted = self.process_complex_date_properties()
        print()
        
        print("=" * 50)
        print("EDGE CASE PROCESSING COMPLETE")
        print("=" * 50)
        print(f"Unknown sex properties converted: {sex_converted}")
        print(f"Complex date properties converted: {date_converted}")
        print(f"Total edge case conversions: {sex_converted + date_converted}")

    def close(self):
        """Close MongoDB connection"""
        self.client.close()

def main():
    processor = EdgeCasePropertiesProcessor()
    
    try:
        processor.run_all_edge_case_processing()
    finally:
        processor.close()

if __name__ == "__main__":
    main()