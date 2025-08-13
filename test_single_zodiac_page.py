#!/usr/bin/env python3
"""
Test creating a single zodiac calendar page to debug the issue
"""

import sys
sys.path.append('.')
from zodiac_wiki_pages import build_page, Wiki, API_URL, USERNAME, PASSWORD, SUMMARY

def test_single_page():
    print("=== TESTING SINGLE ZODIAC PAGE CREATION ===")
    
    # Test building page content for Sagittarius 1
    print("\n1. Building page content for Sagittarius 1...")
    try:
        title, content = build_page(1, 1)  # Sagittarius 1
        print(f"   Title: {title}")
        print(f"   Content length: {len(content)} characters")
        print(f"   Content preview: {content[:200]}...")
    except Exception as e:
        print(f"   [ERROR] Failed to build page: {e}")
        return
    
    # Test building page content for Horus 1 (intercalary)
    print("\n2. Building page content for Horus 1...")
    try:
        title_horus, content_horus = build_page(14, 1)  # Horus 1
        print(f"   Title: {title_horus}")
        print(f"   Content length: {len(content_horus)} characters")
        print(f"   Content preview: {content_horus[:200]}...")
    except Exception as e:
        print(f"   [ERROR] Failed to build Horus page: {e}")
        return
    
    # Test wiki connection and editing
    print("\n3. Testing wiki page creation...")
    try:
        wiki = Wiki(API_URL)
        wiki.login_bot(USERNAME, PASSWORD)
        
        # Try to create just one page
        test_title = "User:Immanuelle/ZodiacTest"
        result = wiki.edit(test_title, content[:500] + "...", "Testing zodiac page creation")
        print(f"   Edit result: {result}")
        
        # Check if page was created by trying to read it
        import requests
        check_response = requests.get(f"https://evolutionism.miraheze.org/wiki/{test_title.replace(' ', '_')}")
        if check_response.status_code == 200:
            print(f"   [OK] Test page accessible at: https://evolutionism.miraheze.org/wiki/{test_title.replace(' ', '_')}")
        else:
            print(f"   [WARN] Test page not accessible (status: {check_response.status_code})")
        
    except Exception as e:
        print(f"   [ERROR] Wiki test failed: {e}")

if __name__ == "__main__":
    test_single_page()