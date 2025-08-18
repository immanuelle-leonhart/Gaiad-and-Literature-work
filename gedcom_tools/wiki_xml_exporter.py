#!/usr/bin/env python3
"""
WIKI XML EXPORTER

Exports the entire Evolutionism Wikibase as MediaWiki XML dump
(current revision only) for local processing.
"""

import requests
import time
from pathlib import Path

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Wiki XML Exporter/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
    })
    return session

def request_xml_export(session):
    """Request a full XML export from Special:Export"""
    print("Requesting XML export from Evolutionism Wikibase...")
    
    # Get all pages in Item and Property namespaces
    print("Getting list of all pages...")
    
    all_pages = []
    
    # Get all items (namespace 860)
    print("  Getting items (namespace 860)...")
    continue_param = None
    while True:
        params = {
            'action': 'query',
            'list': 'allpages',
            'apnamespace': 860,  # Item namespace
            'aplimit': 500,
            'format': 'json'
        }
        
        if continue_param:
            params['apcontinue'] = continue_param
        
        response = session.get('https://evolutionism.miraheze.org/w/api.php', params=params)
        data = response.json()
        
        if 'query' in data and 'allpages' in data['query']:
            for page in data['query']['allpages']:
                title = page['title']
                # Add all items (they'll be like "Item:Q1", "Item:Q2", etc.)
                all_pages.append(title)
        
        if 'continue' in data and 'apcontinue' in data['continue']:
            continue_param = data['continue']['apcontinue']
        else:
            break
        
        time.sleep(0.1)
    
    print(f"  Found {len(all_pages)} items")
    
    # Get all properties (namespace 862)
    print("  Getting properties (namespace 862)...")
    continue_param = None
    while True:
        params = {
            'action': 'query',
            'list': 'allpages',
            'apnamespace': 862,  # Property namespace
            'aplimit': 500,
            'format': 'json'
        }
        
        if continue_param:
            params['apcontinue'] = continue_param
        
        response = session.get('https://evolutionism.miraheze.org/w/api.php', params=params)
        data = response.json()
        
        if 'query' in data and 'allpages' in data['query']:
            for page in data['query']['allpages']:
                title = page['title']
                all_pages.append(title)
        
        if 'continue' in data and 'apcontinue' in data['continue']:
            continue_param = data['continue']['apcontinue']
        else:
            break
        
        time.sleep(0.1)
    
    print(f"  Total pages: {len(all_pages)}")
    
    # Export in chunks (MediaWiki has limits)
    chunk_size = 1000
    output_file = Path("evolutionism_export.xml")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write XML header
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.10/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.mediawiki.org/xml/export-0.10/ http://www.mediawiki.org/xml/export-0.10.xsd" version="0.10" xml:lang="en">\n')
        
        # Export in chunks
        for i in range(0, len(all_pages), chunk_size):
            chunk = all_pages[i:i + chunk_size]
            print(f"Exporting chunk {i//chunk_size + 1}/{(len(all_pages) + chunk_size - 1)//chunk_size} ({len(chunk)} pages)...")
            
            # Use Special:Export API
            export_params = {
                'action': 'query',
                'export': '1',
                'exportnowrap': '1',  # Don't wrap in <mediawiki> tags (we'll add our own)
                'titles': '|'.join(chunk),
                'format': 'xml'
            }
            
            try:
                response = session.get('https://evolutionism.miraheze.org/w/api.php', 
                                     params=export_params, timeout=300)
                
                if response.status_code == 200:
                    content = response.text
                    # Extract just the <page> elements
                    start_marker = '<page>'
                    end_marker = '</page>'
                    
                    start_pos = 0
                    while True:
                        start_idx = content.find(start_marker, start_pos)
                        if start_idx == -1:
                            break
                        
                        end_idx = content.find(end_marker, start_idx)
                        if end_idx == -1:
                            break
                        
                        end_idx += len(end_marker)
                        page_xml = content[start_idx:end_idx]
                        f.write(page_xml + '\n')
                        
                        start_pos = end_idx
                    
                    print(f"  Exported {len(chunk)} pages successfully")
                else:
                    print(f"  Error: HTTP {response.status_code}")
                
            except Exception as e:
                print(f"  Error exporting chunk: {e}")
                continue
            
            time.sleep(1)  # Rate limiting
        
        # Write XML footer
        f.write('</mediawiki>\n')
    
    print(f"\nXML export complete: {output_file}")
    print(f"File size: {output_file.stat().st_size / (1024*1024):.1f} MB")
    
    return output_file

def main():
    print("=" * 60)
    print("WIKI XML EXPORTER")
    print("Exporting Evolutionism Wikibase as MediaWiki XML")
    print("=" * 60)
    
    session = create_session()
    xml_file = request_xml_export(session)
    
    print(f"\nExport complete: {xml_file}")
    print("You can now import this into a local MediaWiki/Wikibase instance")

if __name__ == '__main__':
    main()