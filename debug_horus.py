#!/usr/bin/env python3
"""
Debug QID loading and DEFAULTSORT formatting
"""

from zodiac_wiki_pages import load_year_qids, build_page, Wiki

def test_qid_loading():
    """Test QID loading"""
    print("Testing QID loading...")
    qid_mapping = load_year_qids()
    
    print(f"Loaded {len(qid_mapping)} QID mappings")
    
    # Test some known mappings
    test_cases = ["Sagittarius 1", "Sagittarius 19", "Capricorn 1", "Horus 1"]
    for page_name in test_cases:
        qid = qid_mapping.get(page_name, "NOT FOUND")
        print(f"  {page_name}: {qid}")
    
    return qid_mapping

def test_page_generation():
    """Test page generation with QID links and DEFAULTSORT"""
    print("\nTesting page generation...")
    
    wiki = Wiki("https://evolutionism.miraheze.org/w/api.php")
    wiki.login_bot("Immanuelle", "1996ToOmega!")
    
    # Test Sagittarius 1 (should have QID)
    title, text = build_page(1, 1, wiki)
    
    print(f"Generated page: {title}")
    
    # Check for QID link
    if "{{q|Q" in text:
        print("✅ QID link found")
        # Extract QID
        import re
        qid_match = re.search(r'\{\{q\|(Q\d+)\}\}', text)
        if qid_match:
            print(f"   QID: {qid_match.group(1)}")
    else:
        print("❌ QID link NOT found")
    
    # Check DEFAULTSORT formatting
    if "{{DEFAULTSORT:01宮01日}}" in text:
        print("✅ DEFAULTSORT correctly formatted with zero-padding")
    elif "{{DEFAULTSORT:" in text:
        import re
        sort_match = re.search(r'\{\{DEFAULTSORT:([^}]+)\}\}', text)
        if sort_match:
            print(f"❌ DEFAULTSORT format: {sort_match.group(1)} (should be 01宮01日)")
        else:
            print("❌ DEFAULTSORT found but couldn't parse")
    else:
        print("❌ DEFAULTSORT NOT found")
    
    # Test with different month/day
    title2, text2 = build_page(5, 15, wiki)  # Aries 15
    print(f"\nTesting {title2}:")
    
    sort_match = re.search(r'\{\{DEFAULTSORT:([^}]+)\}\}', text2)
    if sort_match:
        print(f"DEFAULTSORT: {sort_match.group(1)}")
        if sort_match.group(1) == "05宮15日":
            print("✅ Correct formatting for double-digit values")
        else:
            print("❌ Incorrect formatting for double-digit values")
    
    return title, text

if __name__ == "__main__":
    try:
        qid_mapping = test_qid_loading()
        title, text = test_page_generation()
        print("\n✅ Debug tests completed")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()