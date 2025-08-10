#!/usr/bin/env python3
"""
Inspect the current state of evolutionism.miraheze.org Wikibase.
Check existing items, properties, and find the next available QID.
"""

import requests
import json
import sys
from typing import List, Dict, Optional

class WikibaseInspector:
    def __init__(self, api_url: str = "https://evolutionism.miraheze.org/w/api.php"):
        self.api_url = api_url
        self.session = requests.Session()
    
    def get_item(self, qid: str) -> Optional[Dict]:
        """Get a specific item by QID."""
        params = {
            'action': 'wbgetentities',
            'ids': qid,
            'format': 'json'
        }
        
        try:
            response = self.session.get(self.api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'entities' in data and qid in data['entities']:
                entity = data['entities'][qid]
                if entity.get('missing') != '':
                    return entity
            return None
            
        except Exception as e:
            print(f"Error getting {qid}: {e}")
            return None
    
    def search_entities(self, search: str, limit: int = 50) -> List[Dict]:
        """Search for entities."""
        params = {
            'action': 'wbsearchentities',
            'search': search,
            'language': 'en',
            'limit': limit,
            'format': 'json'
        }
        
        try:
            response = self.session.get(self.api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'search' in data:
                return data['search']
            return []
            
        except Exception as e:
            print(f"Error searching '{search}': {e}")
            return []
    
    def get_all_properties(self) -> List[Dict]:
        """Get all properties in the wikibase."""
        params = {
            'action': 'wbgetentities',
            'type': 'property',
            'format': 'json'
        }
        
        try:
            response = self.session.get(self.api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            properties = []
            if 'entities' in data:
                for prop_id, prop_data in data['entities'].items():
                    properties.append({
                        'id': prop_id,
                        'label': prop_data.get('labels', {}).get('en', {}).get('value', 'No label'),
                        'description': prop_data.get('descriptions', {}).get('en', {}).get('value', 'No description'),
                        'datatype': prop_data.get('datatype', 'unknown')
                    })
            
            return properties
            
        except Exception as e:
            print(f"Error getting properties: {e}")
            return []
    
    def find_highest_qid(self, start: int = 1, end: int = 10000) -> int:
        """Find the highest existing QID in the given range."""
        print(f"Scanning for existing items from Q{start} to Q{end}...")
        
        highest_qid = 0
        existing_items = []
        
        # Check in batches of 50 for efficiency
        batch_size = 50
        for batch_start in range(start, end + 1, batch_size):
            batch_end = min(batch_start + batch_size - 1, end)
            
            # Create list of QIDs to check
            qids_to_check = [f"Q{i}" for i in range(batch_start, batch_end + 1)]
            qids_str = '|'.join(qids_to_check)
            
            params = {
                'action': 'wbgetentities',
                'ids': qids_str,
                'format': 'json'
            }
            
            try:
                response = self.session.get(self.api_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if 'entities' in data:
                    for qid, entity_data in data['entities'].items():
                        if entity_data.get('missing') != '':  # Item exists
                            qid_num = int(qid[1:])  # Remove 'Q' prefix
                            if qid_num > highest_qid:
                                highest_qid = qid_num
                            
                            # Store item info
                            label = "No label"
                            if 'labels' in entity_data and 'en' in entity_data['labels']:
                                label = entity_data['labels']['en']['value']
                            
                            existing_items.append({
                                'qid': qid,
                                'label': label
                            })
                
                # Progress indicator
                if batch_start % 500 == 1:
                    print(f"  Checked up to Q{batch_end}...")
                    
            except Exception as e:
                print(f"Error checking batch Q{batch_start}-Q{batch_end}: {e}")
                continue
        
        print(f"\nFound {len(existing_items)} existing items")
        if existing_items:
            print("Existing items:")
            for item in sorted(existing_items, key=lambda x: int(x['qid'][1:])):
                print(f"  {item['qid']}: {item['label']}")
        
        return highest_qid
    
    def inspect_wikibase(self):
        """Perform a complete inspection of the wikibase."""
        print("=== Wikibase Inspector ===")
        print(f"Inspecting: {self.api_url}")
        print()
        
        # Check properties
        print("1. Properties:")
        properties = self.get_all_properties()
        if properties:
            for prop in properties:
                print(f"  {prop['id']}: {prop['label']} ({prop['datatype']})")
                if prop['description'] != 'No description':
                    print(f"    Description: {prop['description']}")
        else:
            # Try alternative method to get properties
            print("  Attempting to get known properties...")
            for pid in ['P1', 'P2', 'P3', 'P4', 'P5']:
                prop = self.get_item(pid)
                if prop:
                    label = "No label"
                    if 'labels' in prop and 'en' in prop['labels']:
                        label = prop['labels']['en']['value']
                    datatype = prop.get('datatype', 'unknown')
                    print(f"  {pid}: {label} ({datatype})")
        
        print()
        
        # Find existing items
        print("2. Existing Items:")
        highest_qid = self.find_highest_qid(1, 100)
        
        if highest_qid > 0:
            print(f"\nHighest existing QID: Q{highest_qid}")
            print(f"Next available QID: Q{highest_qid + 1}")
        else:
            print("No existing items found in Q1-Q100 range")
            print("Next available QID: Q1")
        
        print()
        
        # Test specific items we know about
        print("3. Testing known items:")
        for qid in ['Q1', 'Q2', 'Q3', 'Q4', 'Q5']:
            item = self.get_item(qid)
            if item:
                label = "No label"
                if 'labels' in item and 'en' in item['labels']:
                    label = item['labels']['en']['value']
                print(f"  {qid}: {label}")
            else:
                print(f"  {qid}: Does not exist")

def main():
    inspector = WikibaseInspector()
    inspector.inspect_wikibase()

if __name__ == "__main__":
    main()