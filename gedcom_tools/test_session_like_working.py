#!/usr/bin/env python3
"""
Test API access exactly like the working shinto bot does it
"""

import mwclient
import requests

def test_like_working_bot():
    print("Testing API access like the working shinto bot...")
    
    # Step 1: Login with mwclient (like the working bot)
    site = mwclient.Site("evolutionism.miraheze.org", path="/w/")
    site.login("Immanuelle", "1996ToOmega!")
    print("SUCCESS: Logged in with mwclient")
    
    # Step 2: Create separate session for API calls (like the working bot)
    session = requests.Session()
    
    # Set proper User-Agent header (this was the missing piece!)
    session.headers.update({
        'User-Agent': 'GedcomWikibaseUploader/1.0 (https://evolutionism.miraheze.org/wiki/User:Immanuelle; Immanuelle@example.com)'
    })
    
    # Copy ALL cookies from mwclient to the session
    if hasattr(site.connection, 'cookies'):
        for cookie in site.connection.cookies:
            session.cookies.set(cookie.name, cookie.value, domain=cookie.domain, path=cookie.path)
            print(f"Copied cookie: {cookie.name}")
    
    # Step 3: Try API call with the authenticated session
    api_url = "https://evolutionism.miraheze.org/w/api.php"
    
    # Test 1: Basic siteinfo (like the working bot does)
    print("\nTesting basic API call...")
    try:
        response = session.get(api_url, params={
            "action": "query",
            "meta": "siteinfo", 
            "siprop": "general",
            "format": "json"
        }, timeout=30)
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if 'query' in data:
                sitename = data['query']['general']['sitename']
                print(f"SUCCESS: Got site info for {sitename}")
            else:
                print(f"Unexpected response: {data}")
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"API call failed: {e}")
    
    # Test 2: Try to get tokens
    print("\nTesting token request...")
    try:
        response = session.get(api_url, params={
            "action": "query",
            "meta": "tokens",
            "format": "json"
        }, timeout=30)
        
        print(f"Token response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Token response: {data}")
        else:
            print(f"Token error: {response.text}")
            
    except Exception as e:
        print(f"Token request failed: {e}")
    
    # Test 3: Try wikibase search
    print("\nTesting wikibase search...")
    try:
        response = session.get(api_url, params={
            "action": "wbsearchentities",
            "search": "test",
            "language": "en", 
            "limit": 1,
            "format": "json"
        }, timeout=30)
        
        print(f"Wikibase response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Wikibase API works! Response: {data}")
        else:
            print(f"Wikibase error: {response.text}")
            
    except Exception as e:
        print(f"Wikibase request failed: {e}")

if __name__ == "__main__":
    test_like_working_bot()