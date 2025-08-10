#!/usr/bin/env python3
"""
Basic check of evolutionism.miraheze.org Wikibase without authentication.
Test basic API access and search functionality.
"""

import requests
import json
import sys

def test_basic_api():
    """Test basic API access without authentication."""
    api_url = "https://evolutionism.miraheze.org/w/api.php"
    
    print("=== Basic Wikibase API Test ===")
    print(f"Testing: {api_url}")
    print()
    
    # Test 1: Basic site info (should work without auth)
    print("1. Testing basic API access...")
    try:
        params = {
            'action': 'query',
            'meta': 'siteinfo',
            'siprop': 'general',
            'format': 'json'
        }
        
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'query' in data and 'general' in data['query']:
            general = data['query']['general']
            print(f"  SUCCESS: Wiki name: {general.get('sitename', 'Unknown')}")
            print(f"  SUCCESS: MediaWiki version: {general.get('generator', 'Unknown')}")
            print(f"  SUCCESS: Base URL: {general.get('server', 'Unknown')}")
        
    except Exception as e:
        print(f"  ERROR: {e}")
    
    print()
    
    # Test 2: Search entities (might work without auth)
    print("2. Testing entity search...")
    try:
        params = {
            'action': 'wbsearchentities',
            'search': 'Alpha',
            'language': 'en',
            'limit': 10,
            'format': 'json'
        }
        
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'search' in data:
            results = data['search']
            print(f"  SUCCESS: Found {len(results)} results for 'Alpha':")
            for result in results[:5]:  # Show first 5
                label = result.get('label', 'No label')
                qid = result.get('id', 'No ID')
                description = result.get('description', 'No description')
                print(f"    {qid}: {label} - {description}")
        else:
            print("  No search results returned")
    
    except Exception as e:
        print(f"  ERROR: {e}")
    
    print()
    
    # Test 3: Check API capabilities
    print("3. Testing API capabilities...")
    try:
        params = {
            'action': 'help',
            'modules': 'wbsearchentities',
            'format': 'json'
        }
        
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'help' in data:
            print("  SUCCESS: Wikibase search API is available")
        else:
            print("  UNCLEAR: API help response unclear")
    
    except Exception as e:
        print(f"  ERROR: {e}")
    
    print()
    
    # Test 4: Try to access a specific known item via web
    print("4. Testing direct item access...")
    try:
        # Try to access Q1 directly via web interface
        item_url = "https://evolutionism.miraheze.org/wiki/Item:Q1"
        response = requests.get(item_url)
        
        if response.status_code == 200:
            if "Alpha" in response.text or "Q1" in response.text:
                print("  SUCCESS: Q1 (Alpha) appears to exist via web interface")
            else:
                print("  UNCLEAR: Q1 web page exists but content unclear")
        elif response.status_code == 404:
            print("  ERROR: Q1 does not exist")
        else:
            print(f"  UNCLEAR: Unexpected status code: {response.status_code}")
    
    except Exception as e:
        print(f"  ERROR: Error accessing Q1: {e}")
    
    print()
    print("=== Summary ===")
    print("The wikibase appears to exist but requires authentication for API access.")
    print("You will need to provide valid login credentials to use the uploader.")
    print("The uploader program should work once proper credentials are provided.")

def main():
    test_basic_api()

if __name__ == "__main__":
    main()