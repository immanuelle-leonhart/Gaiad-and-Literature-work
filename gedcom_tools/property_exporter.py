#!/usr/bin/env python3

import requests
import json

def export_properties():
    """Export all Properties from the remote Wikibase"""
    
    base_url = "https://evolutionism.miraheze.org/w/api.php"
    
    # Get list of all properties
    params = {
        'action': 'query',
        'format': 'json',
        'list': 'allpages',
        'apnamespace': 862,  # Property namespace
        'aplimit': 'max'
    }
    
    session = requests.Session()
    session.headers.update({'User-Agent': 'PropertyExporter/1.0'})
    
    properties = []
    
    while True:
        response = session.get(base_url, params=params)
        data = response.json()
        
        if 'query' in data and 'allpages' in data['query']:
            for page in data['query']['allpages']:
                properties.append(page['title'])
                print(f"Found property: {page['title']}")
        
        if 'continue' in data:
            params.update(data['continue'])
        else:
            break
    
    print(f"Found {len(properties)} properties total")
    
    # Now export these properties
    export_params = {
        'action': 'query',
        'format': 'json',
        'export': 1,
        'exportnowrap': 1,
        'titles': '|'.join(properties[:50])  # Start with first 50
    }
    
    response = session.get(base_url, params=export_params)
    
    # Save to file
    with open('properties_export.xml', 'w', encoding='utf-8') as f:
        f.write(response.text)
    
    print(f"Exported first 50 properties to properties_export.xml")
    print(f"Properties: {properties[:10]}...")  # Show first 10

if __name__ == "__main__":
    export_properties()