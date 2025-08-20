#!/usr/bin/env python3
"""
Process BC Dates

Handles the remaining P7/P8 properties that contain B.C. dates
and special characters not handled by previous processors.
"""

import pymongo
import re

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

class BCDateProcessor:
    def __init__(self, mongo_uri=MONGO_URI):
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db[COLLECTION_NAME]
        
        print(f"Connected to MongoDB: {DATABASE_NAME}.{COLLECTION_NAME}")

    def format_bc_date(self, date_str):
        """Format BC dates and dates with special characters"""
        if not date_str:
            return None
            
        date_str = str(date_str).strip()
        
        # Remove/replace special characters like � with -
        date_str = re.sub(r'[�–—]', '-', date_str)
        
        # Remove parentheses
        date_str = re.sub(r'[()]', '', date_str).strip()
        
        # Handle B.C. dates
        is_bc = 'B.C.' in date_str.upper() or 'BC' in date_str.upper()
        if is_bc:
            date_str = re.sub(r'\s*B\.?C\.?', '', date_str, flags=re.IGNORECASE).strip()
        
        # Handle year only (15 B.C., 76 B.C.)
        year_match = re.match(r'^(\d{1,4})$', date_str)
        if year_match:
            year = int(year_match.group(1))
            if is_bc:
                year = -year  # Negative for BC
            
            sign = '+' if year >= 0 else ''
            return {
                'time': f'{sign}{abs(year):04d}-00-00T00:00:00Z',
                'timezone': 0,
                'before': 0,
                'after': 0,
                'precision': 9,
                'calendarmodel': 'http://www.wikidata.org/entity/Q1985727'
            }
        
        # Handle day month year (1 JAN 76 B.C.)
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
            year = int(year)
            
            if is_bc:
                year = -year
            
            sign = '+' if year >= 0 else ''
            return {
                'time': f'{sign}{abs(year):04d}-{month}-{day}T00:00:00Z',
                'timezone': 0,
                'before': 0,
                'after': 0,
                'precision': 11,
                'calendarmodel': 'http://www.wikidata.org/entity/Q1985727'
            }
        
        # Handle complex ranges like "4 DEC-3067"
        range_match = re.search(r'(\d{1,2})\s+([A-Z]{3})-?(\d{1,4})', date_str.upper())
        if range_match:
            day, month_abbr, year = range_match.groups()
            month_map = {
                'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
                'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
                'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
            }
            month = month_map.get(month_abbr, '00')
            day = day.zfill(2)
            year = int(year)
            
            # Assume BC for very old dates
            if year > 100:
                year = -year
            
            sign = '+' if year >= 0 else ''
            return {
                'time': f'{sign}{abs(year):04d}-{month}-{day}T00:00:00Z',
                'timezone': 0,
                'before': 0,
                'after': 0,
                'precision': 11,
                'calendarmodel': 'http://www.wikidata.org/entity/Q1985727'
            }
        
        # Try to extract any year from the string
        year_search = re.search(r'\b(\d{1,4})\b', date_str)
        if year_search:
            year = int(year_search.group(1))
            if is_bc:
                year = -year
            
            sign = '+' if year >= 0 else ''
            return {
                'time': f'{sign}{abs(year):04d}-00-00T00:00:00Z',
                'timezone': 0,
                'before': 0,
                'after': 0,
                'precision': 9,
                'calendarmodel': 'http://www.wikidata.org/entity/Q1985727'
            }
        
        return None

    def process_bc_dates(self):
        """Process remaining P7/P8 properties with BC dates"""
        print("Processing BC dates and special characters...")
        
        processed = 0
        converted = 0
        bulk_operations = []
        
        # Find all entities with P7 or P8 properties
        for entity in self.collection.find({'$or': [{'properties.P7': {'$exists': True}}, {'properties.P8': {'$exists': True}}]}):
            processed += 1
            if processed % 100 == 0:
                print(f"  Processed {processed} entities, converted {converted} BC dates...")
            
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
                        formatted_date = self.format_bc_date(date_text)
                        if formatted_date:
                            new_p56_claims.append({
                                'value': formatted_date,
                                'type': 'time',
                                'claim_id': claim.get('claim_id', f"{qid}_birth_bc")
                            })
                    elif claim_type == 'string':
                        formatted_date = self.format_bc_date(value)
                        if formatted_date:
                            new_p56_claims.append({
                                'value': formatted_date,
                                'type': 'time',
                                'claim_id': claim.get('claim_id', f"{qid}_birth_bc")
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
                        formatted_date = self.format_bc_date(date_text)
                        if formatted_date:
                            new_p57_claims.append({
                                'value': formatted_date,
                                'type': 'time',
                                'claim_id': claim.get('claim_id', f"{qid}_death_bc")
                            })
                    elif claim_type == 'string':
                        formatted_date = self.format_bc_date(value)
                        if formatted_date:
                            new_p57_claims.append({
                                'value': formatted_date,
                                'type': 'time',
                                'claim_id': claim.get('claim_id', f"{qid}_death_bc")
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
        
        print(f"OK Converted {converted} BC dates and special characters")
        return converted

    def close(self):
        """Close MongoDB connection"""
        self.client.close()

def main():
    processor = BCDateProcessor()
    
    try:
        processor.process_bc_dates()
    finally:
        processor.close()

if __name__ == "__main__":
    main()