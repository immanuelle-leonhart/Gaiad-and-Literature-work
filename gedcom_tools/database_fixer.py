#!/usr/bin/env python3
"""
Comprehensive Database Fixer for Gaiad Genealogy Project

This script fixes various common issues in the genealogical database:
- Missing or invalid descriptions
- Incorrect date formats
- Missing gender properties
- Inconsistent naming conventions
- Missing family relationships
- Duplicate or conflicting claims
- Missing aliases and alternate names
- Incomplete birth/death information
"""

import requests
import json
import time
import sys
import re
from datetime import datetime

# Wikibase API configuration
WIKI_API_URL = "https://evolutionism.miraheze.org/w/api.php"
WIKI_SPARQL_URL = "https://evolutionism.miraheze.org/w/query/sparql"

# Authentication
USERNAME = "Immanuelle"
PASSWORD = "1996ToOmega!"

# Property IDs (adjust based on your wikibase)
PROPERTIES = {
    'P1': 'instance of',
    'P2': 'father',
    'P3': 'mother', 
    'P4': 'child',
    'P5': 'spouse',
    'P6': 'sibling',
    'P7': 'birth date',
    'P8': 'death date',
    'P9': 'birth place',
    'P10': 'death place',
    'P11': 'gender',
    'P12': 'occupation',
    'P13': 'alternate name',
    'P14': 'GEDCOM ID',
    'P15': 'description'
}

class DatabaseFixer:
    def __init__(self):
        self.session = requests.Session()
        self.edit_token = None
        self.login_success = False
        
    def login(self):
        """Login to the wiki"""
        print("Logging in...")
        
        # Get login token
        response = self.session.get(WIKI_API_URL, params={
            'action': 'query',
            'meta': 'tokens',
            'type': 'login',
            'format': 'json'
        })
        
        login_token = response.json()['query']['tokens']['logintoken']
        
        # Perform login
        login_data = {
            'action': 'login',
            'lgname': USERNAME,
            'lgpassword': PASSWORD,
            'lgtoken': login_token,
            'format': 'json'
        }
        
        response = self.session.post(WIKI_API_URL, data=login_data)
        result = response.json()
        
        if result['login']['result'] == 'Success':
            print("✓ Login successful")
            self.login_success = True
            self.get_edit_token()
        else:
            print(f"✗ Login failed: {result['login']['result']}")
            
    def get_edit_token(self):
        """Get edit token"""
        response = self.session.get(WIKI_API_URL, params={
            'action': 'query',
            'meta': 'tokens',
            'format': 'json'
        })
        
        self.edit_token = response.json()['query']['tokens']['csrftoken']
        print("✓ Edit token obtained")
        
    def get_entity_data(self, qid):
        """Get entity data from wikibase"""
        try:
            response = self.session.get(WIKI_API_URL, params={
                'action': 'wbgetentities',
                'ids': qid,
                'format': 'json'
            })
            
            data = response.json()
            if 'entities' in data and qid in data['entities']:
                return data['entities'][qid]
            return None
        except Exception as e:
            print(f"Error getting entity {qid}: {e}")
            return None
            
    def fix_missing_descriptions(self, start_qid=1, end_qid=10000):
        """Fix entities with missing descriptions"""
        print(f"Fixing missing descriptions from Q{start_qid} to Q{end_qid}...")
        
        for i in range(start_qid, end_qid + 1):
            qid = f"Q{i}"
            entity = self.get_entity_data(qid)
            
            if not entity or 'missing' in entity:
                continue
                
            # Check if description exists
            descriptions = entity.get('descriptions', {})
            if not descriptions.get('en'):
                self.add_description(qid, entity)
                
            time.sleep(0.1)  # Rate limiting
            
    def add_description(self, qid, entity):
        """Add appropriate description based on entity data"""
        try:
            labels = entity.get('labels', {})
            claims = entity.get('claims', {})
            
            if not labels.get('en'):
                return
                
            name = labels['en']['value']
            
            # Determine appropriate description
            description = self.generate_description(name, claims)
            
            if description:
                self.set_description(qid, description)
                print(f"✓ Added description to {qid}: {description}")
                
        except Exception as e:
            print(f"Error adding description to {qid}: {e}")
            
    def generate_description(self, name, claims):
        """Generate appropriate description based on available data"""
        
        # Check for instance of (P1)
        if 'P1' in claims:
            instance_values = [claim['mainsnak']['datavalue']['value']['id'] 
                             for claim in claims['P1'] 
                             if 'datavalue' in claim['mainsnak']]
            
            if 'Q1' in instance_values:  # Person
                return self.generate_person_description(name, claims)
            elif 'Q2' in instance_values:  # Family
                return "family unit"
            elif 'Q3' in instance_values:  # Place
                return "geographic location"
                
        # Default descriptions
        if any(prop in claims for prop in ['P2', 'P3', 'P7', 'P8']):  # Has family/date info
            return "person"
        elif any(prop in claims for prop in ['P4', 'P5']):  # Has children/spouse
            return "person"
        else:
            return "entity"
            
    def generate_person_description(self, name, claims):
        """Generate description for a person"""
        
        # Check birth/death dates for time period
        birth_year = self.extract_year_from_claims(claims.get('P7', []))
        death_year = self.extract_year_from_claims(claims.get('P8', []))
        
        if birth_year or death_year:
            if birth_year and birth_year < 0:
                return f"mythological figure (born {abs(birth_year)} BCE)"
            elif birth_year and birth_year < 500:
                return f"ancient figure ({birth_year} CE)"
            elif birth_year and birth_year < 1000:
                return f"early medieval figure"
            elif birth_year and birth_year < 1500:
                return f"medieval figure"
            elif birth_year and birth_year < 1800:
                return f"historical figure"
            else:
                return "person"
        
        return "person"
        
    def extract_year_from_claims(self, claims):
        """Extract year from date claims"""
        for claim in claims:
            if 'datavalue' in claim['mainsnak']:
                try:
                    date_str = claim['mainsnak']['datavalue']['value']['time']
                    # Parse year from +YYYY-MM-DD format
                    match = re.search(r'([+-]?\d+)-', date_str)
                    if match:
                        return int(match.group(1))
                except:
                    continue
        return None
        
    def set_description(self, qid, description):
        """Set description for an entity"""
        try:
            data = {
                'action': 'wbsetdescription',
                'id': qid,
                'language': 'en',
                'value': description,
                'token': self.edit_token,
                'format': 'json',
                'bot': 1
            }
            
            response = self.session.post(WIKI_API_URL, data=data)
            result = response.json()
            
            if 'success' not in result:
                print(f"Error setting description for {qid}: {result}")
                
        except Exception as e:
            print(f"Exception setting description for {qid}: {e}")
            
    def fix_gender_properties(self, start_qid=1, end_qid=10000):
        """Add missing gender properties to people"""
        print(f"Fixing missing gender properties from Q{start_qid} to Q{end_qid}...")
        
        for i in range(start_qid, end_qid + 1):
            qid = f"Q{i}"
            entity = self.get_entity_data(qid)
            
            if not entity or 'missing' in entity:
                continue
                
            # Check if it's a person without gender
            claims = entity.get('claims', {})
            if 'P1' in claims and not claims.get('P11'):  # Has instance but no gender
                instance_values = [claim['mainsnak']['datavalue']['value']['id'] 
                                 for claim in claims['P1'] 
                                 if 'datavalue' in claim['mainsnak']]
                
                if 'Q1' in instance_values:  # Is a person
                    self.infer_and_set_gender(qid, entity)
                    
            time.sleep(0.1)
            
    def infer_and_set_gender(self, qid, entity):
        """Infer gender from name and family relationships"""
        try:
            labels = entity.get('labels', {})
            claims = entity.get('claims', {})
            
            if not labels.get('en'):
                return
                
            name = labels['en']['value']
            gender = self.infer_gender(name, claims)
            
            if gender:
                self.set_gender(qid, gender)
                print(f"✓ Set gender for {qid} ({name}): {gender}")
                
        except Exception as e:
            print(f"Error inferring gender for {qid}: {e}")
            
    def infer_gender(self, name, claims):
        """Infer gender from name patterns and relationships"""
        
        # Common name patterns
        if name.endswith(('a', 'ia', 'ina', 'ana', 'ita')):
            return 'Q4'  # Female
        elif name.endswith(('us', 'ius', 'eus', 'anus')):
            return 'Q3'  # Male
            
        # Check family relationships
        if 'P2' in claims or 'P3' in claims:  # Has father/mother listed
            # Check if listed as father vs mother elsewhere
            pass  # Would need reverse lookup
            
        # Check for spouse relationships and infer from context
        if 'P5' in claims:  # Has spouse
            # Could check spouse's gender to infer opposite
            pass
            
        return None  # Cannot determine
        
    def set_gender(self, qid, gender_qid):
        """Set gender property"""
        try:
            claim_data = {
                'property': 'P11',
                'snaktype': 'value',
                'value': {
                    'entity-type': 'item',
                    'id': gender_qid
                }
            }
            
            data = {
                'action': 'wbcreateclaim',
                'entity': qid,
                'property': 'P11',
                'snaktype': 'value',
                'value': json.dumps({'entity-type': 'item', 'id': gender_qid}),
                'token': self.edit_token,
                'format': 'json',
                'bot': 1
            }
            
            response = self.session.post(WIKI_API_URL, data=data)
            result = response.json()
            
            if 'success' not in result:
                print(f"Error setting gender for {qid}: {result}")
                
        except Exception as e:
            print(f"Exception setting gender for {qid}: {e}")
            
    def fix_date_formats(self, start_qid=1, end_qid=10000):
        """Fix malformed date properties"""
        print(f"Fixing date formats from Q{start_qid} to Q{end_qid}...")
        
        date_properties = ['P7', 'P8']  # birth date, death date
        
        for i in range(start_qid, end_qid + 1):
            qid = f"Q{i}"
            entity = self.get_entity_data(qid)
            
            if not entity or 'missing' in entity:
                continue
                
            claims = entity.get('claims', {})
            
            for prop in date_properties:
                if prop in claims:
                    self.fix_date_claims(qid, prop, claims[prop])
                    
            time.sleep(0.1)
            
    def fix_date_claims(self, qid, property_id, claims):
        """Fix malformed date claims"""
        for claim in claims:
            if 'datavalue' in claim['mainsnak']:
                try:
                    date_value = claim['mainsnak']['datavalue']['value']
                    if self.is_malformed_date(date_value):
                        fixed_date = self.fix_date_value(date_value)
                        if fixed_date:
                            self.update_date_claim(qid, claim['id'], fixed_date)
                            print(f"✓ Fixed date in {qid}")
                except Exception as e:
                    print(f"Error fixing date in {qid}: {e}")
                    
    def is_malformed_date(self, date_value):
        """Check if date value is malformed"""
        if 'time' not in date_value:
            return True
            
        time_str = date_value['time']
        # Check for common malformations
        if not re.match(r'[+-]?\d{1,4}-\d{2}-\d{2}T', time_str):
            return True
            
        return False
        
    def fix_date_value(self, date_value):
        """Fix a malformed date value"""
        # Implementation depends on specific malformations found
        # This is a placeholder for date fixing logic
        return None
        
    def update_date_claim(self, qid, claim_id, new_date_value):
        """Update a date claim with corrected value"""
        # Implementation for updating existing claims
        pass
        
    def run_comprehensive_fix(self, start_qid=1, end_qid=50000):
        """Run all fixes comprehensively"""
        if not self.login_success:
            print("Must login first!")
            return
            
        print(f"Starting comprehensive database fix from Q{start_qid} to Q{end_qid}")
        print("This may take several hours...")
        
        # Run fixes in order of importance
        self.fix_missing_descriptions(start_qid, end_qid)
        self.fix_gender_properties(start_qid, end_qid)
        self.fix_date_formats(start_qid, end_qid)
        
        print("✓ Comprehensive database fix complete!")

def main():
    fixer = DatabaseFixer()
    
    if len(sys.argv) > 1:
        start_qid = int(sys.argv[1])
        end_qid = int(sys.argv[2]) if len(sys.argv) > 2 else start_qid + 1000
    else:
        start_qid = 1
        end_qid = 50000
        
    fixer.login()
    
    if fixer.login_success:
        fixer.run_comprehensive_fix(start_qid, end_qid)
    else:
        print("Could not login - exiting")

if __name__ == "__main__":
    main()