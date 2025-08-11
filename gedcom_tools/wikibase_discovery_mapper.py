#!/usr/bin/env python3
"""
WIKIBASE DISCOVERY AND MAPPING PROGRAM

This program systematically discovers what items already exist in the wikibase
and attempts to map them back to their original GEDCOM IDs by examining:
1. Item labels/names 
2. GEDCOM REFN properties
3. Content patterns

This prevents creating duplicates and provides a complete mapping.
"""

import requests
import json
import sys
import time
import mwclient
from typing import Dict, List, Optional, Set, Tuple

class WikibaseDiscoveryMapper:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        
        # Authentication
        self.site = None
        self.session = None
        self.csrf_token = None
        self.api_url = "https://evolutionism.miraheze.org/w/api.php"
        
        # Discovered mappings
        self.qid_to_gedcom = {}       # Q123 -> @I456@
        self.gedcom_to_qid = {}       # @I456@ -> Q123
        self.item_categories = {}     # Q123 -> "main_gaiad" | "japanese" | "chinese" | "unknown"
        
        # Statistics
        self.stats = {
            'total_items_found': 0,
            'gaiad_characters': 0,
            'gaiad_families': 0,
            'japanese_items': 0,
            'chinese_items': 0,
            'unknown_items': 0,
            'mapped_items': 0,
            'unmapped_items': 0
        }
    
    def login(self):
        """Login and setup authenticated session."""
        print(f"Logging in as {self.username}...")
        
        try:
            self.site = mwclient.Site("evolutionism.miraheze.org", path="/w/")
            self.session = requests.Session()
            
            self.session.headers.update({
                'User-Agent': 'WikibaseDiscoveryMapper/1.0 (https://evolutionism.miraheze.org/wiki/User:Immanuelle)'
            })
            
            self.site.login(self.username, self.password)
            
            # Copy cookies
            for cookie in self.site.connection.cookies:
                self.session.cookies.set(cookie.name, cookie.value, domain=cookie.domain)
            
            # Get CSRF token
            response = self.session.get(self.api_url, params={
                'action': 'query',
                'meta': 'tokens',
                'format': 'json'
            })
            
            data = response.json()
            if 'query' in data and 'tokens' in data['query']:
                self.csrf_token = data['query']['tokens']['csrftoken']
                print(f"Login successful! CSRF token: {self.csrf_token[:10]}...")
                return True
            else:
                print(f"Error getting CSRF token: {data}")
                return False
                
        except Exception as e:
            print(f"Login failed: {e}")
            return False
    
    def discover_all_items(self):
        """Systematically discover all items in the wikibase."""
        print("Discovering all items in wikibase...")
        
        batch_size = 100
        start_qid = 1  # Start from Q1
        max_consecutive_missing = 500  # Much larger gap to be thorough
        consecutive_missing = 0
        
        while consecutive_missing < max_consecutive_missing:
            qids_to_check = [f"Q{i}" for i in range(start_qid, start_qid + batch_size)]
            qids_param = '|'.join(qids_to_check)
            
            response = self.session.get(self.api_url, params={
                'action': 'wbgetentities',
                'ids': qids_param,
                'props': 'labels|descriptions|claims',
                'format': 'json'
            })
            
            data = response.json()
            if 'entities' not in data:
                break
            
            found_any_this_batch = False
            
            for qid in qids_to_check:
                if qid in data['entities'] and 'missing' not in data['entities'][qid]:
                    found_any_this_batch = True
                    consecutive_missing = 0
                    
                    entity = data['entities'][qid]
                    self.stats['total_items_found'] += 1
                    
                    # Analyze this item
                    self.analyze_item(qid, entity)
                    
                    if self.stats['total_items_found'] % 100 == 0:
                        print(f"  Discovered {self.stats['total_items_found']:,} items so far...")
                else:
                    consecutive_missing += 1
            
            if not found_any_this_batch:
                consecutive_missing += batch_size
            
            start_qid += batch_size
            time.sleep(0.1)  # Rate limiting
        
        print(f"Discovery completed! Found {self.stats['total_items_found']:,} total items")
    
    def analyze_item(self, qid, entity):
        """Analyze a single item to categorize it and map to GEDCOM if possible."""
        
        # Get basic info
        label = None
        description = None
        if 'labels' in entity and 'en' in entity['labels']:
            label = entity['labels']['en']['value']
        if 'descriptions' in entity and 'en' in entity['descriptions']:
            description = entity['descriptions']['en']['value']
        
        # Determine category based on instance of claims and patterns
        category = "unknown"
        instance_of_279 = False  # Gaiad character
        instance_of_280 = False  # Gaiad family
        
        gedcom_refns = []
        
        if 'claims' in entity:
            for prop_id, claims in entity['claims'].items():
                for claim in claims:
                    try:
                        mainsnak = claim.get('mainsnak', {})
                        datavalue = mainsnak.get('datavalue', {})
                        
                        # Check instance of
                        if prop_id == 'P39':  # Instance of property
                            if isinstance(datavalue, dict):
                                value = datavalue.get('value', {})
                                if isinstance(value, dict):
                                    numeric_id = value.get('numeric-id')
                                    if numeric_id == 279:
                                        instance_of_279 = True
                                    elif numeric_id == 280:
                                        instance_of_280 = True
                        
                        # Check for GEDCOM REFN
                        elif prop_id == 'P41':  # GEDCOM REFN property
                            if isinstance(datavalue, dict):
                                if datavalue.get('type') == 'monolingualtext':
                                    text = datavalue.get('value', {}).get('text', '')
                                    if text:
                                        gedcom_refns.append(text)
                                elif datavalue.get('type') == 'string':
                                    text = datavalue.get('value', '')
                                    if text:
                                        gedcom_refns.append(text)
                        
                    except (AttributeError, TypeError):
                        continue
        
        # Categorize the item
        if instance_of_279:
            # Check if it's Japanese/Chinese by QID range or label patterns
            qid_num = int(qid[1:])
            if qid_num >= 2500 and qid_num <= 30000:  # Japanese range observed
                if label and any(x in label.lower() for x in ['japanese', 'japan']):
                    category = "japanese"
                else:
                    # Could be main Gaiad or Japanese without clear markers
                    category = "main_gaiad"  # Default to main for now
            else:
                category = "main_gaiad"
            self.stats['gaiad_characters'] += 1
        elif instance_of_280:
            category = "main_gaiad"  # Families are mostly main Gaiad
            self.stats['gaiad_families'] += 1
        else:
            # Other items (properties, etc.)
            self.stats['unknown_items'] += 1
        
        self.item_categories[qid] = category
        
        # Try to map to GEDCOM ID
        mapped_gedcom_id = None
        
        # Method 1: Direct REFN mapping
        for refn in gedcom_refns:
            if refn.startswith('@I') and refn.endswith('@'):
                mapped_gedcom_id = refn
                break
            elif refn.startswith('@F') and refn.endswith('@'):
                mapped_gedcom_id = refn
                break
        
        # Method 2: Name-based mapping (would need GEDCOM data loaded)
        # TODO: Implement if needed
        
        if mapped_gedcom_id:
            self.qid_to_gedcom[qid] = mapped_gedcom_id
            self.gedcom_to_qid[mapped_gedcom_id] = qid
            self.stats['mapped_items'] += 1
        else:
            self.stats['unmapped_items'] += 1
        
        # Print some interesting finds
        if self.stats['total_items_found'] <= 20 or self.stats['total_items_found'] % 1000 == 0:
            print(f"  {qid}: {label} ({category})")
            if gedcom_refns:
                print(f"    REFNs: {gedcom_refns}")
    
    def save_discovery_results(self):
        """Save all discovery results to files."""
        print("Saving discovery results...")
        
        # Main mapping file
        with open('wikibase_discovery_mapping.txt', 'w', encoding='utf-8') as f:
            f.write("# Wikibase Discovery and Mapping Results\n")
            f.write(f"# Generated by wikibase_discovery_mapper.py\n")
            f.write(f"# Total items discovered: {self.stats['total_items_found']:,}\n\n")
            
            # Statistics
            f.write("# Statistics\n")
            for key, value in self.stats.items():
                f.write(f"# {key}: {value:,}\n")
            f.write("\n")
            
            # QID to GEDCOM mappings
            f.write("# QID to GEDCOM Mappings\n")
            for qid, gedcom_id in sorted(self.qid_to_gedcom.items(), key=lambda x: int(x[0][1:])):
                category = self.item_categories.get(qid, "unknown")
                f.write(f"{qid}\t{gedcom_id}\t{category}\n")
            f.write("\n")
        
        # Category breakdown file
        with open('wikibase_categories.txt', 'w', encoding='utf-8') as f:
            f.write("# Wikibase Items by Category\n\n")
            
            categories = {}
            for qid, category in self.item_categories.items():
                if category not in categories:
                    categories[category] = []
                categories[category].append(qid)
            
            for category, qids in categories.items():
                f.write(f"# {category.upper()} ({len(qids)} items)\n")
                for qid in sorted(qids, key=lambda x: int(x[1:])):
                    gedcom_id = self.qid_to_gedcom.get(qid, "NO_MAPPING")
                    f.write(f"{qid}\t{gedcom_id}\n")
                f.write("\n")
    
    def run_discovery(self):
        """Main discovery function."""
        print("Starting comprehensive wikibase discovery...")
        
        if not self.login():
            return False
        
        self.discover_all_items()
        self.save_discovery_results()
        
        print(f"\nDISCOVERY COMPLETED!")
        print(f"Total items found: {self.stats['total_items_found']:,}")
        print(f"Gaiad characters: {self.stats['gaiad_characters']:,}")
        print(f"Gaiad families: {self.stats['gaiad_families']:,}")
        print(f"Japanese items: {self.stats['japanese_items']:,}")
        print(f"Chinese items: {self.stats['chinese_items']:,}")
        print(f"Unknown items: {self.stats['unknown_items']:,}")
        print(f"Successfully mapped: {self.stats['mapped_items']:,}")
        print(f"Unmapped items: {self.stats['unmapped_items']:,}")
        
        return True

def main():
    mapper = WikibaseDiscoveryMapper("Immanuelle", "1996ToOmega!")
    success = mapper.run_discovery()
    
    if success:
        print("Discovery completed successfully!")
    else:
        print("Discovery failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()