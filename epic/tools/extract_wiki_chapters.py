#!/usr/bin/env python3
"""
Extract chapters from MediaWiki XML dump
Extracts the most recent version of each "Old Gaiad/##" page
"""

import xml.etree.ElementTree as ET
import re
from pathlib import Path
from collections import defaultdict

def parse_wiki_dump(xml_file):
    """Parse MediaWiki XML dump and extract Old Gaiad chapters"""
    
    # Parse XML
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # MediaWiki namespace
    ns = {'mw': 'http://www.mediawiki.org/xml/export-0.11/'}
    
    chapters = defaultdict(list)
    
    # Find all pages
    for page in root.findall('mw:page', ns):
        title_elem = page.find('mw:title', ns)
        if title_elem is None:
            continue
            
        title = title_elem.text
        
        # Check if this is an Old Gaiad chapter
        if title and title.startswith('Old Gaiad/'):
            # Extract chapter number
            match = re.search(r'Old Gaiad/(\d+)', title)
            if match:
                chapter_num = int(match.group(1))
                
                # Get all revisions for this page
                revisions = page.findall('mw:revision', ns)
                if revisions:
                    # Sort revisions by timestamp to get most recent
                    def get_timestamp(rev):
                        ts_elem = rev.find('mw:timestamp', ns)
                        return ts_elem.text if ts_elem is not None else ''
                    
                    latest_revision = max(revisions, key=get_timestamp)
                    
                    # Extract text content
                    text_elem = latest_revision.find('mw:text', ns)
                    if text_elem is not None and text_elem.text:
                        chapters[chapter_num] = {
                            'title': title,
                            'content': text_elem.text,
                            'timestamp': get_timestamp(latest_revision)
                        }
    
    return chapters

def clean_wiki_text(text):
    """Clean MediaWiki markup from text"""
    if not text:
        return ""
    
    # Remove common MediaWiki markup
    text = re.sub(r'\[\[([^|\]]+)\|([^\]]+)\]\]', r'\2', text)  # [[link|display]] -> display
    text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)  # [[link]] -> link
    text = re.sub(r"'''([^']+)'''", r'\1', text)  # '''bold''' -> bold
    text = re.sub(r"''([^']+)''", r'\1', text)  # ''italic'' -> italic
    text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
    text = re.sub(r'\{\{[^}]+\}\}', '', text)  # Remove templates
    
    return text.strip()

def main():
    xml_file = Path('../../Evolutionism+Wiki-20250804041753.xml')
    output_dir = Path('../old-versions')
    
    if not xml_file.exists():
        print(f"XML file not found: {xml_file}")
        return
    
    print("Parsing MediaWiki XML dump...")
    chapters = parse_wiki_dump(xml_file)
    
    print(f"Found {len(chapters)} chapters")
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Write each chapter to a file
    for chapter_num in sorted(chapters.keys()):
        chapter_data = chapters[chapter_num]
        
        # Clean the content
        clean_content = clean_wiki_text(chapter_data['content'])
        
        # Create filename with zero-padded chapter number
        filename = f"old_chapter_{chapter_num:02d}.txt"
        filepath = output_dir / filename
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Old Gaiad Chapter {chapter_num}\n")
            f.write(f"# Source: {chapter_data['title']}\n")
            f.write(f"# Last updated: {chapter_data['timestamp']}\n\n")
            f.write(clean_content)
        
        print(f"Extracted: {filename} ({len(clean_content)} chars)")
    
    # Create index file
    index_file = output_dir / "chapter_index.txt"
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write("Old Gaiad Chapter Index\n")
        f.write("======================\n\n")
        for chapter_num in sorted(chapters.keys()):
            chapter_data = chapters[chapter_num]
            f.write(f"Chapter {chapter_num:2d}: old_chapter_{chapter_num:02d}.txt (updated: {chapter_data['timestamp']})\n")
    
    print(f"\nCreated index: {index_file}")
    print(f"Total chapters extracted: {len(chapters)}")

if __name__ == "__main__":
    main()