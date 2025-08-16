#!/usr/bin/env python3
"""
Test script to verify Overview section preservation for a single zodiac page
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from zodiac_wiki_pages import Wiki, build_page, extract_overview_section

# Test configuration
API_URL = "https://evolutionism.miraheze.org/w/api.php"
USERNAME = "Immanuelle"
PASSWORD = "1996ToOmega!"
TEST_PAGE = "Sagittarius 1"  # Known page with Overview section

def test_overview_extraction():
    """Test the Overview section extraction"""
    print("Testing Overview section extraction...")
    
    wiki = Wiki(API_URL)
    wiki.login_bot(USERNAME, PASSWORD)
    
    # Get existing content
    existing_content = wiki.get_page_content(TEST_PAGE)
    print(f"Got page content: {len(existing_content)} characters")
    
    # Extract Overview section
    overview_content = extract_overview_section(existing_content)
    print(f"\nExtracted Overview section ({len(overview_content)} characters):")
    print("=" * 50)
    print(overview_content)
    print("=" * 50)
    
    return overview_content

def test_page_generation():
    """Test page generation with Overview preservation"""
    print("\nTesting page generation with Overview preservation...")
    
    wiki = Wiki(API_URL)
    wiki.login_bot(USERNAME, PASSWORD)
    
    # Test with Sagittarius 1 (month_idx=1, day=1)
    title, text = build_page(1, 1, wiki)
    
    print(f"Generated page title: {title}")
    print(f"Generated content length: {len(text)} characters")
    
    # Check if Overview section is preserved
    if "== Overview ==" in text:
        print("✅ Overview section found in generated content")
        
        # Extract the overview from generated content to verify
        overview_in_generated = extract_overview_section(text)
        print(f"Overview in generated content ({len(overview_in_generated)} characters):")
        print("-" * 30)
        print(overview_in_generated)
        print("-" * 30)
    else:
        print("❌ Overview section NOT found in generated content")
    
    return title, text

if __name__ == "__main__":
    print("Testing zodiac page Overview preservation...")
    
    try:
        # Test extraction
        overview = test_overview_extraction()
        
        # Test generation
        title, content = test_page_generation()
        
        print(f"\n✅ Tests completed successfully!")
        print(f"   - Overview extraction: {'✅' if overview else '❌'}")
        print(f"   - Page generation: {'✅' if '== Overview ==' in content else '❌'}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()