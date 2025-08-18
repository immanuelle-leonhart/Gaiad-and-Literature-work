#!/usr/bin/env python3
"""
Check what namespaces exist in the Evolutionism Wikibase
"""

import requests
import json

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Namespace Checker/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
    })
    return session

def check_namespaces(session):
    print("Checking available namespaces...")
    
    # Get namespace info
    params = {
        'action': 'query',
        'meta': 'siteinfo',
        'siprop': 'namespaces',
        'format': 'json'
    }
    
    response = session.get('https://evolutionism.miraheze.org/w/api.php', params=params)
    data = response.json()
    
    if 'query' in data and 'namespaces' in data['query']:
        namespaces = data['query']['namespaces']
        print("\nAvailable namespaces:")
        for ns_id, ns_info in namespaces.items():
            name = ns_info.get('name', '[Main]')
            canonical = ns_info.get('canonical', '')
            print(f"  {ns_id}: {name} {f'({canonical})' if canonical else ''}")
    
    # Check a few specific namespaces for content
    test_namespaces = [0, 120, 122, 124, 146, 148]  # Common Wikibase namespaces
    
    for ns in test_namespaces:
        print(f"\nChecking namespace {ns} for content...")
        params = {
            'action': 'query',
            'list': 'allpages',
            'apnamespace': ns,
            'aplimit': 10,
            'format': 'json'
        }
        
        response = session.get('https://evolutionism.miraheze.org/w/api.php', params=params)
        data = response.json()
        
        if 'query' in data and 'allpages' in data['query']:
            pages = data['query']['allpages']
            if pages:
                print(f"  Found {len(pages)} pages (showing first few):")
                for page in pages[:5]:
                    print(f"    {page['title']}")
            else:
                print(f"  No pages found")

def main():
    session = create_session()
    check_namespaces(session)

if __name__ == '__main__':
    main()