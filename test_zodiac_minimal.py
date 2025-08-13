#!/usr/bin/env python3
"""
Minimal test of zodiac page creation without Unicode display issues
"""

import sys
sys.path.append('.')
from zodiac_wiki_pages import build_page, Wiki, API_URL, USERNAME, PASSWORD, SUMMARY
import requests

def test_minimal():
    print("=== TESTING MINIMAL ZODIAC PAGE CREATION ===")
    
    wiki = Wiki(API_URL)
    wiki.login_bot(USERNAME, PASSWORD)
    
    # Test creating just Sagittarius 1
    print("Creating Sagittarius 1...")
    try:
        title, content = build_page(1, 1)  # Sagittarius 1
        result = wiki.edit(title, content, SUMMARY)
        print(f"Edit result: {result}")
        
        # Check if the page exists
        page_url = f"https://evolutionism.miraheze.org/wiki/{title.replace(' ', '_')}"
        check_response = requests.get(page_url)
        if check_response.status_code == 200 and "Sagittarius 1 is the 1st day" in check_response.text:
            print(f"SUCCESS: Page created at {page_url}")
        else:
            print(f"FAILED: Page not found or incorrect content")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test creating Horus 1 (intercalary)
    print("\nCreating Horus 1...")
    try:
        title, content = build_page(14, 1)  # Horus 1
        result = wiki.edit(title, content, SUMMARY)
        print(f"Edit result: {result}")
        
        # Check if the page exists
        page_url = f"https://evolutionism.miraheze.org/wiki/{title.replace(' ', '_')}"
        check_response = requests.get(page_url)
        if check_response.status_code == 200 and "Horus 1 is the 365th day" in check_response.text:
            print(f"SUCCESS: Intercalary page created at {page_url}")
        else:
            print(f"FAILED: Intercalary page not found or incorrect content")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_minimal()