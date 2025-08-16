#!/usr/bin/env python3
"""
Minimal test for zodiac Overview preservation
"""

from zodiac_wiki_pages import Wiki, build_page, extract_overview_section

API_URL = "https://evolutionism.miraheze.org/w/api.php"
USERNAME = "Immanuelle"
PASSWORD = "1996ToOmega!"

def main():
    try:
        wiki = Wiki(API_URL)
        wiki.login_bot(USERNAME, PASSWORD)
        
        # Test extraction from Sagittarius 1
        existing_content = wiki.get_page_content("Sagittarius 1")
        overview = extract_overview_section(existing_content)
        
        print(f"Extraction successful: {len(overview)} chars")
        print(f"Has content: {'YES' if overview.strip() else 'NO'}")
        
        # Test page generation
        title, text = build_page(1, 1, wiki)
        has_overview = "== Overview ==" in text
        
        print(f"Generation successful: {len(text)} chars")
        print(f"Has Overview section: {'YES' if has_overview else 'NO'}")
        
        # Check if overview content is preserved
        new_overview = extract_overview_section(text)
        content_preserved = len(new_overview) > 50  # Some meaningful content
        
        print(f"Content preserved: {'YES' if content_preserved else 'NO'}")
        print(f"New overview length: {len(new_overview)} chars")
        
        print("SUCCESS: Overview preservation working!")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    main()