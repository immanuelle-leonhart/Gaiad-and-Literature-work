#!/usr/bin/env python3
"""
Test basic mwclient access to evolutionism.miraheze.org
"""

import mwclient
import requests
import json

def test_mwclient():
    print("Testing mwclient access...")
    
    try:
        # Login with mwclient
        site = mwclient.Site("evolutionism.miraheze.org", path="/w/")
        site.login("Immanuelle", "1996ToOmega!")
        print("SUCCESS: mwclient login successful")
        
        # Test basic page access
        test_page = site.pages["Main Page"]
        if test_page.exists:
            print("SUCCESS: Can access Main Page")
        else:
            print("ERROR: Cannot access Main Page")
        
        # Test creating a page
        test_page_name = "User:Immanuelle/Test"
        test_page = site.pages[test_page_name]
        test_content = "This is a test page created by the GEDCOM uploader."
        
        try:
            test_page.save(test_content, summary="Test page creation")
            print("SUCCESS: Can create/edit pages")
        except Exception as e:
            print(f"ERROR: Cannot create pages: {e}")
        
        # Test API access with cookies
        session = requests.Session()
        for cookie in site.connection.cookies:
            session.cookies.set(cookie.name, cookie.value, domain=cookie.domain)
        
        print("Testing API access with authenticated session...")
        api_url = "https://evolutionism.miraheze.org/w/api.php"
        
        # Try basic siteinfo query
        params = {
            'action': 'query',
            'meta': 'siteinfo',
            'siprop': 'general',
            'format': 'json'
        }
        
        try:
            response = session.get(api_url, params=params)
            if response.status_code == 200:
                data = response.json()
                if 'query' in data:
                    print("SUCCESS: Basic API queries work")
                    sitename = data['query']['general']['sitename']
                    print(f"  Site: {sitename}")
                else:
                    print("ERROR: API query returned unexpected format")
            else:
                print(f"ERROR: API query failed with status {response.status_code}")
        except Exception as e:
            print(f"ERROR: API query error: {e}")
        
        # Try to get tokens
        params = {
            'action': 'query',
            'meta': 'tokens',
            'format': 'json'
        }
        
        try:
            response = session.get(api_url, params=params)
            if response.status_code == 200:
                data = response.json()
                if 'query' in data and 'tokens' in data['query']:
                    print("SUCCESS: Can get CSRF tokens")
                    token = data['query']['tokens']['csrftoken']
                    print(f"  Token: {token[:10]}...")
                else:
                    print("ERROR: No tokens in response")
            else:
                print(f"ERROR: Token request failed with status {response.status_code}")
        except Exception as e:
            print(f"ERROR: Token request error: {e}")
        
        # Test if Wikibase is available
        params = {
            'action': 'wbsearchentities',
            'search': 'test',
            'language': 'en',
            'limit': 1,
            'format': 'json'
        }
        
        try:
            response = session.get(api_url, params=params)
            if response.status_code == 200:
                data = response.json()
                print("SUCCESS: Wikibase API is available")
            else:
                print(f"ERROR: Wikibase API failed with status {response.status_code}")
        except Exception as e:
            print(f"ERROR: Wikibase API error: {e}")
            
    except Exception as e:
        print(f"ERROR: mwclient login failed: {e}")

if __name__ == "__main__":
    test_mwclient()