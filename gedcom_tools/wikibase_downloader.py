#!/usr/bin/env python3
"""
WIKIBASE DOWNLOADER

Downloads all entities from Evolutionism Wikibase (Q1-Q160000 and all properties)
in JSON format for local processing. Only downloads current revision of each entity.
"""

import requests
import json
import os
import time
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Wikibase Downloader/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
    })
    retry_strategy = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def download_entities_batch(session, entity_ids, output_dir):
    """Download a batch of entities (max 50 per API request)"""
    if not entity_ids:
        return 0
    
    batch_size = 50  # API limit
    downloaded = 0
    
    for i in range(0, len(entity_ids), batch_size):
        batch = entity_ids[i:i + batch_size]
        batch_str = '|'.join(batch)
        
        params = {
            'action': 'wbgetentities',
            'ids': batch_str,
            'format': 'json'
        }
        
        try:
            response = session.get('https://evolutionism.miraheze.org/w/api.php', 
                                 params=params, timeout=60)
            
            if response.status_code != 200:
                print(f"  Error: HTTP {response.status_code} for batch {batch[0]}-{batch[-1]}")
                continue
                
            data = response.json()
            
            if 'entities' not in data:
                print(f"  Error: No entities in response for batch {batch[0]}-{batch[-1]}")
                continue
            
            # Save each entity to individual file
            for entity_id, entity_data in data['entities'].items():
                if 'missing' in entity_data:
                    continue  # Skip missing entities
                
                entity_file = output_dir / f"{entity_id}.json"
                with open(entity_file, 'w', encoding='utf-8') as f:
                    json.dump(entity_data, f, indent=2, ensure_ascii=False)
                
                downloaded += 1
            
            print(f"  Downloaded batch {batch[0]}-{batch[-1]}: {len([e for e in data['entities'].values() if 'missing' not in e])} entities")
            time.sleep(0.1)  # Rate limiting
            
        except Exception as e:
            print(f"  Error downloading batch {batch[0]}-{batch[-1]}: {e}")
            continue
    
    return downloaded

def get_all_properties(session):
    """Get all property IDs from the wikibase"""
    print("Getting list of all properties...")
    
    properties = []
    continue_param = None
    
    while True:
        params = {
            'action': 'query',
            'list': 'allpages',
            'apnamespace': 120,  # Property namespace
            'aplimit': 500,
            'format': 'json'
        }
        
        if continue_param:
            params['apcontinue'] = continue_param
        
        try:
            response = session.get('https://evolutionism.miraheze.org/w/api.php', 
                                 params=params, timeout=30)
            data = response.json()
            
            if 'query' in data and 'allpages' in data['query']:
                for page in data['query']['allpages']:
                    title = page['title']
                    if title.startswith('Property:P'):
                        prop_id = title.replace('Property:', '')
                        properties.append(prop_id)
            
            # Check if there's more data
            if 'continue' in data and 'apcontinue' in data['continue']:
                continue_param = data['continue']['apcontinue']
            else:
                break
                
        except Exception as e:
            print(f"Error getting properties: {e}")
            break
    
    print(f"Found {len(properties)} properties")
    return properties

def main():
    print("=" * 60)
    print("WIKIBASE DOWNLOADER")
    print("Downloading Evolutionism Wikibase for local processing")
    print("=" * 60)
    
    # Create output directories
    base_dir = Path("wikibase_download")
    items_dir = base_dir / "items"
    properties_dir = base_dir / "properties"
    
    base_dir.mkdir(exist_ok=True)
    items_dir.mkdir(exist_ok=True)
    properties_dir.mkdir(exist_ok=True)
    
    session = create_session()
    
    # Download properties first
    print("\n1. DOWNLOADING PROPERTIES")
    print("-" * 40)
    
    properties = get_all_properties(session)
    if properties:
        downloaded_props = download_entities_batch(session, properties, properties_dir)
        print(f"Downloaded {downloaded_props} properties to {properties_dir}")
    
    # Download items Q1-Q160000
    print("\n2. DOWNLOADING ITEMS (Q1-Q160000)")
    print("-" * 40)
    
    total_items = 160000
    batch_size = 1000  # Process 1000 entities at a time for progress updates
    downloaded_items = 0
    
    for start_q in range(1, total_items + 1, batch_size):
        end_q = min(start_q + batch_size - 1, total_items)
        
        print(f"\nProcessing Q{start_q}-Q{end_q}...")
        
        # Create list of QIDs for this batch
        qids = [f"Q{i}" for i in range(start_q, end_q + 1)]
        
        # Download this batch
        batch_downloaded = download_entities_batch(session, qids, items_dir)
        downloaded_items += batch_downloaded
        
        progress = (end_q / total_items) * 100
        print(f"  Progress: {progress:.1f}% ({downloaded_items} items downloaded)")
        
        # Save progress info
        progress_file = base_dir / "download_progress.json"
        progress_data = {
            "last_completed_batch": end_q,
            "total_downloaded": downloaded_items,
            "timestamp": time.time()
        }
        with open(progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2)
    
    # Create summary
    summary = {
        "download_completed": time.time(),
        "total_items": downloaded_items,
        "total_properties": len(properties),
        "source": "https://evolutionism.miraheze.org/",
        "namespaces": ["Item", "Property"],
        "revision": "current"
    }
    
    summary_file = base_dir / "download_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n" + "=" * 60)
    print("DOWNLOAD COMPLETE")
    print(f"Items downloaded: {downloaded_items}")
    print(f"Properties downloaded: {len(properties)}")
    print(f"Output directory: {base_dir.absolute()}")
    print(f"Total size: {sum(f.stat().st_size for f in base_dir.rglob('*.json')) / (1024*1024):.1f} MB")
    print("=" * 60)

if __name__ == '__main__':
    main()