#!/usr/bin/env python3
"""
SIMPLE XML EXPORT using MediaWiki Special:Export page directly
This bypasses API limits by using the web interface
"""

import requests
import time
from urllib.parse import urlencode

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Simple XML Export/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
    })
    return session

def login_to_wiki(session):
    """Login to get access to Special:Export"""
    # Get login token
    token_params = {'action': 'query', 'meta': 'tokens', 'type': 'login', 'format': 'json'}
    response = session.get('https://evolutionism.miraheze.org/w/api.php', params=token_params, timeout=30)
    if response.status_code != 200:
        return False
    token_data = response.json()
    login_token = token_data['query']['tokens']['logintoken']
    
    # Login
    login_data = {'action': 'login', 'lgname': 'Immanuelle', 'lgpassword': '1996ToOmega!', 'lgtoken': login_token, 'format': 'json'}
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=login_data)
    return response.json().get('login', {}).get('result') == 'Success'

def export_via_special_page(session, page_list, output_file):
    """Use Special:Export page to export pages"""
    
    # Convert list to text (one title per line)
    pages_text = '\n'.join(page_list)
    
    # Prepare form data for Special:Export
    form_data = {
        'pages': pages_text,
        'curonly': '1',  # Current revisions only
        'templates': '0',  # Don't include templates
        'wpDownload': '1',  # Download instead of display
        'wpExport': 'Export'
    }
    
    print(f"Exporting {len(page_list)} pages via Special:Export...")
    
    try:
        response = session.post(
            'https://evolutionism.miraheze.org/wiki/Special:Export',
            data=form_data,
            timeout=600,  # 10 minute timeout
            stream=True
        )
        
        if response.status_code == 200:
            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = output_file.stat().st_size
            print(f"Export successful: {file_size / (1024*1024):.1f} MB")
            return True
        else:
            print(f"Export failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Export error: {e}")
        return False

def get_all_pages(session):
    """Get list of all pages to export"""
    print("Getting list of all pages...")
    
    all_pages = []
    
    # Get items from namespace 860
    print("  Getting items (namespace 860)...")
    continue_param = None
    while True:
        params = {
            'action': 'query',
            'list': 'allpages',
            'apnamespace': 860,
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
    
    print(f"  Found {len(all_pages)} items")
    
    # Get properties from namespace 862
    print("  Getting properties (namespace 862)...")
    continue_param = None
    while True:
        params = {
            'action': 'query',
            'list': 'allpages',
            'apnamespace': 862,
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
    return all_pages

def main():
    print("=" * 60)
    print("SIMPLE XML EXPORT")
    print("Using Special:Export page directly")
    print("=" * 60)
    
    session = create_session()
    
    if not login_to_wiki(session):
        print("Failed to login!")
        return
    
    print("Login successful!")
    
    # Get all pages
    all_pages = get_all_pages(session)
    
    if not all_pages:
        print("No pages found to export!")
        return
    
    # Export in smaller chunks (Special:Export has limits too)
    chunk_size = 5000  # Smaller chunks
    output_files = []
    
    for i in range(0, len(all_pages), chunk_size):
        chunk = all_pages[i:i + chunk_size]
        output_file = f"evolutionism_export_part_{i//chunk_size + 1}.xml"
        
        print(f"\nExporting chunk {i//chunk_size + 1} ({len(chunk)} pages)...")
        
        if export_via_special_page(session, chunk, Path(output_file)):
            output_files.append(output_file)
            print(f"Saved: {output_file}")
        else:
            print(f"Failed to export chunk {i//chunk_size + 1}")
        
        time.sleep(2)  # Rate limiting
    
    print(f"\nExport complete! Created {len(output_files)} files:")
    for file in output_files:
        print(f"  {file}")

if __name__ == '__main__':
    from pathlib import Path
    main()