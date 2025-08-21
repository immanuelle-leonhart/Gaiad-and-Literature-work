#!/usr/bin/env python3
"""
Miraheze Import Helper

Since direct API imports of 145,396 entities would be extremely slow, this script
provides guidance and tools for importing the XML files to evolutionism.miraheze.org
using the most efficient methods available.

Options:
1. File a Miraheze Phabricator task for bulk import assistance
2. Use the MediaWiki importDump.php maintenance script (requires shell access)
3. Upload smaller chunks and use the Special:Import interface
4. Contact Miraheze staff for database-level import assistance
"""

import os
import requests
import time

def analyze_export_files():
    """Analyze the exported XML files"""
    print("=== ANALYZING EXPORT FILES ===")
    print()
    
    xml_dir = "wikibase_export"
    total_size = 0
    total_files = 0
    
    if not os.path.exists(xml_dir):
        print(f"ERROR: Export directory not found: {xml_dir}")
        return
    
    files = []
    for i in range(1, 31):
        filename = f"gaiad_wikibase_export_part_{i:03d}.xml"
        filepath = os.path.join(xml_dir, filename)
        
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            total_size += size
            total_files += 1
            files.append((filename, size))
    
    print(f"Found {total_files} XML files")
    print(f"Total size: {total_size / (1024*1024):.1f} MB")
    print(f"Average file size: {(total_size / total_files) / (1024*1024):.1f} MB")
    print()
    
    # Show file breakdown
    print("File sizes:")
    for filename, size in files[:5]:
        print(f"  {filename}: {size / (1024*1024):.1f} MB")
    if len(files) > 5:
        print(f"  ... and {len(files) - 5} more files")
    
    return {
        'total_files': total_files,
        'total_size_mb': total_size / (1024*1024),
        'files': files
    }

def test_wiki_access():
    """Test access to the wiki"""
    print("=== TESTING WIKI ACCESS ===")
    print()
    
    try:
        response = requests.get("https://evolutionism.miraheze.org/w/api.php", params={
            'action': 'query',
            'meta': 'siteinfo',
            'siprop': 'general|namespaces',
            'format': 'json'
        }, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            sitename = data.get('query', {}).get('general', {}).get('sitename', 'Unknown')
            version = data.get('query', {}).get('general', {}).get('generator', 'Unknown')
            
            print(f"Wiki accessible: {sitename}")
            print(f"MediaWiki version: {version}")
            
            # Check for Wikibase
            namespaces = data.get('query', {}).get('namespaces', {})
            has_item_ns = any(ns.get('canonical') == 'Item' for ns in namespaces.values())
            has_property_ns = any(ns.get('canonical') == 'Property' for ns in namespaces.values())
            
            print(f"Wikibase installed: {'YES' if has_item_ns and has_property_ns else 'NO'}")
            
            if has_item_ns:
                item_ns_id = next(id for id, ns in namespaces.items() if ns.get('canonical') == 'Item')
                print(f"Item namespace ID: {item_ns_id}")
            
            return True
            
        else:
            print(f"ERROR: Wiki not accessible (HTTP {response.status_code})")
            return False
            
    except Exception as e:
        print(f"ERROR: Could not access wiki: {e}")
        return False

def generate_import_instructions():
    """Generate instructions for import"""
    print("=== IMPORT RECOMMENDATIONS ===")
    print()
    
    analysis = analyze_export_files()
    wiki_ok = test_wiki_access()
    
    if not analysis or not wiki_ok:
        print("Cannot provide recommendations - analysis failed")
        return
    
    total_size_mb = analysis['total_size_mb']
    
    print("Based on the analysis, here are the recommended approaches:")
    print()
    
    if total_size_mb > 100:
        print("🔸 LARGE IMPORT (>100MB) - Recommended approaches:")
        print()
        print("1. MIRAHEZE PHABRICATOR TASK (RECOMMENDED)")
        print("   - File a task at https://phabricator.miraheze.org/")
        print("   - Request bulk import assistance for Wikibase data")
        print("   - Provide the XML files via file sharing service")
        print("   - Miraheze staff can import via maintenance scripts")
        print()
        print("2. CONTACT MIRAHEZE SUPPORT")
        print("   - Join #miraheze on Libera.Chat IRC")
        print("   - Explain you need to import large Wikibase dataset")
        print("   - They may provide shell access or do server-side import")
        print()
    
    print("3. CHUNKED MANUAL IMPORT")
    print("   - Use Special:Import on the wiki")
    print("   - Upload files one at a time (may timeout on large files)")
    print("   - Start with smaller files first")
    print(f"   - You have {analysis['total_files']} files to import")
    print()
    
    print("4. API IMPORT (SLOW BUT RELIABLE)")
    print("   - Use the entity uploader script created earlier")
    print("   - Will take several hours but works reliably")
    print("   - Processes entities one by one via Wikibase API")
    print("   - Good for smaller subsets or testing")
    print()
    
    print("NEXT STEPS:")
    print("1. Try the Phabricator task approach first (fastest)")
    print("2. If no response in 24-48 hours, try IRC support")
    print("3. As backup, use the API uploader for critical entities")
    print()
    
    # Create a sample Phabricator task description
    print("=== SAMPLE PHABRICATOR TASK ===")
    print()
    print("Title: Bulk import request for Wikibase genealogical data")
    print()
    print("Description:")
    print(f"""
I have a large genealogical dataset that I need to import into my Miraheze Wikibase wiki:
https://evolutionism.miraheze.org

Dataset details:
- {analysis['total_files']} XML files in MediaWiki export format
- Total size: {total_size_mb:.1f} MB
- Contains 145,396 Wikibase entities (Items with genealogical data)
- Includes both regular entities and redirect entities from deduplication
- All files are properly formatted MediaWiki XML exports

The data is ready for import but the files are too large for Special:Import 
and would timeout. Could Miraheze staff assist with a server-side import 
using importDump.php or similar maintenance scripts?

I can provide the XML files via Google Drive, Dropbox, or any preferred 
file sharing method.

Thank you for your assistance!
""")
    
    print("Copy the above text and file it at: https://phabricator.miraheze.org/")

def main():
    print("Miraheze Import Helper for Gaiad Genealogical Database")
    print("=" * 60)
    print()
    
    generate_import_instructions()

if __name__ == "__main__":
    main()