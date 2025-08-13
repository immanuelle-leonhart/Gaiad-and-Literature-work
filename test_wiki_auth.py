#!/usr/bin/env python3
"""
Test script to debug wiki authentication and editing permissions
"""

import requests
import json

API_URL = "https://evolutionism.miraheze.org/w/api.php"
USERNAME = "Immanuelle"
PASSWORD = "1996ToOmega!"
USER_AGENT = "WikiAuthTest/1.0 (testing permissions)"

def test_wiki_access():
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    
    print("=== TESTING WIKI API ACCESS ===")
    
    # Test 1: Basic API access
    print("\n1. Testing basic API access...")
    try:
        response = session.get(API_URL, params={
            'action': 'query',
            'meta': 'siteinfo',
            'format': 'json'
        })
        data = response.json()
        print(f"   [OK] API accessible: {data['query']['general']['sitename']}")
    except Exception as e:
        print(f"   [ERROR] API access failed: {e}")
        return
    
    # Test 2: Login token
    print("\n2. Getting login token...")
    try:
        response = session.get(API_URL, params={
            'action': 'query',
            'meta': 'tokens',
            'type': 'login',
            'format': 'json'
        })
        token_data = response.json()
        login_token = token_data['query']['tokens']['logintoken']
        print(f"   [OK] Login token obtained: {login_token[:20]}...")
    except Exception as e:
        print(f"   [ERROR] Login token failed: {e}")
        return
    
    # Test 3: Login attempt
    print("\n3. Attempting login...")
    try:
        login_response = session.post(API_URL, data={
            'action': 'login',
            'lgname': USERNAME,
            'lgpassword': PASSWORD,
            'lgtoken': login_token,
            'format': 'json'
        })
        login_result = login_response.json()
        print(f"   Login response: {json.dumps(login_result, indent=2)}")
        
        if login_result.get('login', {}).get('result') == 'Success':
            print("   [OK] Login successful")
        else:
            print(f"   [ERROR] Login failed: {login_result}")
            return
    except Exception as e:
        print(f"   [ERROR] Login attempt failed: {e}")
        return
    
    # Test 4: Get CSRF token
    print("\n4. Getting CSRF token...")
    try:
        csrf_response = session.get(API_URL, params={
            'action': 'query',
            'meta': 'tokens',
            'type': 'csrf',
            'format': 'json'
        })
        csrf_data = csrf_response.json()
        csrf_token = csrf_data['query']['tokens']['csrftoken']
        print(f"   [OK] CSRF token obtained: {csrf_token[:20]}...")
    except Exception as e:
        print(f"   [ERROR] CSRF token failed: {e}")
        return
    
    # Test 5: Check user info
    print("\n5. Checking user information...")
    try:
        user_response = session.get(API_URL, params={
            'action': 'query',
            'meta': 'userinfo',
            'uiprop': 'rights|groups',
            'format': 'json'
        })
        user_data = user_response.json()
        userinfo = user_data['query']['userinfo']
        print(f"   User: {userinfo.get('name', 'Anonymous')}")
        print(f"   Groups: {userinfo.get('groups', [])}")
        print(f"   Rights: {userinfo.get('rights', [])[:10]}...")  # First 10 rights
        
        if 'edit' in userinfo.get('rights', []):
            print("   [OK] User has edit rights")
        else:
            print("   [ERROR] User lacks edit rights")
            
        if 'bot' in userinfo.get('groups', []):
            print("   [OK] User has bot flag")
        else:
            print("   [WARN] User lacks bot flag (not required but recommended)")
            
    except Exception as e:
        print(f"   [ERROR] User info failed: {e}")
        return
    
    # Test 6: Test edit (create a test page)
    print("\n6. Testing page edit...")
    test_title = "User:Immanuelle/Test"
    test_content = "Test page for debugging wiki access - " + str(int(time.time()))
    
    try:
        edit_response = session.post(API_URL, data={
            'action': 'edit',
            'title': test_title,
            'text': test_content,
            'summary': 'Testing wiki edit access',
            'token': csrf_token,
            'format': 'json'
        })
        edit_result = edit_response.json()
        print(f"   Edit response: {json.dumps(edit_result, indent=2)}")
        
        if 'edit' in edit_result and edit_result['edit'].get('result') == 'Success':
            print("   [OK] Edit successful!")
        else:
            print(f"   [ERROR] Edit failed: {edit_result}")
            
    except Exception as e:
        print(f"   [ERROR] Edit test failed: {e}")

if __name__ == "__main__":
    import time
    test_wiki_access()