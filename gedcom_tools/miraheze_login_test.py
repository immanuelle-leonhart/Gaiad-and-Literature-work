#!/usr/bin/env python3
"""
Test login to Miraheze wiki with CentralAuth.
"""

import requests
import json

def test_miraheze_login(username, password):
    session = requests.Session()
    
    # Step 1: Try to get a login token from the main API
    api_url = "https://evolutionism.miraheze.org/w/api.php"
    
    print("Step 1: Getting login token...")
    
    try:
        login_token_params = {
            'action': 'query',
            'meta': 'tokens',
            'type': 'login',
            'format': 'json'
        }
        
        response = session.get(api_url, params=login_token_params)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 403:
            print("403 Forbidden - API access may be restricted")
            return False
            
        response.raise_for_status()
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if 'query' not in data or 'tokens' not in data['query']:
            print("No tokens found in response")
            return False
            
        login_token = data['query']['tokens']['logintoken']
        print(f"Got login token: {login_token}")
        
    except Exception as e:
        print(f"Error getting login token: {e}")
        return False
    
    # Step 2: Try to login
    print("\nStep 2: Attempting login...")
    
    try:
        login_params = {
            'action': 'login',
            'lgname': username,
            'lgpassword': password,
            'lgtoken': login_token,
            'format': 'json'
        }
        
        response = session.post(api_url, data=login_params)
        response.raise_for_status()
        login_result = response.json()
        
        print(f"Login response: {json.dumps(login_result, indent=2)}")
        
        if 'login' in login_result:
            result = login_result['login']['result']
            print(f"Login result: {result}")
            
            if result == 'Success':
                print("Login successful!")
                return True
            else:
                print(f"Login failed: {result}")
                return False
        
    except Exception as e:
        print(f"Error during login: {e}")
        return False
    
    return False

def main():
    username = "Immanuelle"
    password = "1996ToOmega!"
    
    print("Testing Miraheze login...")
    success = test_miraheze_login(username, password)
    
    if success:
        print("\nLogin test successful! You can proceed with the uploader.")
    else:
        print("\nLogin test failed. There may be API restrictions or authentication issues.")

if __name__ == "__main__":
    main()