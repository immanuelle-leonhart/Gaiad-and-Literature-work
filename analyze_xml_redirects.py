#!/usr/bin/env python3
"""
Analyze XML imports to find redirects that should have been imported
"""
import xml.etree.ElementTree as ET
import os
import json
from collections import defaultdict

def analyze_xml_redirects():
    xml_dir = "xml_imports"
    redirects_found = {}  # source_qid -> target_qid
    total_pages = 0
    redirect_count = 0
    
    print("=== ANALYZING XML IMPORTS FOR REDIRECTS ===")
    print()
    
    # Get all XML files
    xml_files = []
    for filename in os.listdir(xml_dir):
        if filename.endswith('.xml') and 'part_' in filename:
            xml_files.append(os.path.join(xml_dir, filename))
    
    xml_files.sort()  # Process in order
    print(f"Found {len(xml_files)} XML import files")
    print()
    
    # Process each file
    for xml_file in xml_files:
        print(f"Processing {os.path.basename(xml_file)}...")
        
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Namespace
            ns = {'mw': 'http://www.mediawiki.org/xml/export-0.11/'}
            
            file_pages = 0
            file_redirects = 0
            
            for page in root.findall('.//mw:page', ns):
                file_pages += 1
                total_pages += 1
                
                # Check for redirect element
                redirect_elem = page.find('mw:redirect', ns)
                if redirect_elem is not None:
                    # This is a redirect page
                    file_redirects += 1
                    redirect_count += 1
                    
                    # Get source QID from title
                    title_elem = page.find('mw:title', ns)
                    if title_elem is not None:
                        title = title_elem.text
                        if title.startswith('Item:Q'):
                            source_qid = title.replace('Item:', '')
                            
                            # Get target from redirect title attribute
                            redirect_title = redirect_elem.get('title', '')
                            if redirect_title.startswith('Item:Q'):
                                target_qid = redirect_title.replace('Item:', '')
                                redirects_found[source_qid] = target_qid
                                
                                if len(redirects_found) <= 10:  # Show first 10 examples
                                    print(f"  Found redirect: {source_qid} -> {target_qid}")
            
            print(f"  Pages: {file_pages}, Redirects: {file_redirects}")
            
        except Exception as e:
            print(f"  ERROR: {e}")
    
    print()
    print(f"=== REDIRECT ANALYSIS COMPLETE ===")
    print(f"Total pages processed: {total_pages:,}")
    print(f"Total redirects found: {redirect_count:,}")
    print(f"Redirect mappings extracted: {len(redirects_found):,}")
    
    return redirects_found

def check_database_redirects(xml_redirects):
    """Check if XML redirects were properly imported to MongoDB"""
    import pymongo
    
    print()
    print("=== CHECKING DATABASE REDIRECT STATUS ===")
    print()
    
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['gaiad_processing_db']
    collection = db['entities']
    
    # Check each redirect from XML
    properly_imported = 0
    missing_as_redirect = 0
    missing_completely = 0
    empty_entities = 0
    
    sample_issues = []
    
    for source_qid, target_qid in list(xml_redirects.items())[:100]:  # Check first 100
        source_entity = collection.find_one({'qid': source_qid})
        
        if not source_entity:
            missing_completely += 1
            if len(sample_issues) < 10:
                sample_issues.append(f"MISSING: {source_qid} -> {target_qid} (entity doesn't exist)")
        else:
            # Check if it's a proper redirect
            properties = source_entity.get('properties', {})
            labels = source_entity.get('labels', {})
            descriptions = source_entity.get('descriptions', {})
            aliases = source_entity.get('aliases', {})
            
            if 'redirect' in properties:
                # Check if redirect target matches
                redirect_claims = properties['redirect']
                if redirect_claims and redirect_claims[0].get('value') == target_qid:
                    properly_imported += 1
                else:
                    if len(sample_issues) < 10:
                        actual_target = redirect_claims[0].get('value') if redirect_claims else 'NONE'
                        sample_issues.append(f"BAD TARGET: {source_qid} -> expected {target_qid}, got {actual_target}")
            else:
                # Not a redirect - check if it's an empty entity
                if not labels and not descriptions and not aliases:
                    empty_entities += 1
                    if len(sample_issues) < 10:
                        sample_issues.append(f"EMPTY ENTITY: {source_qid} -> {target_qid} (should be redirect)")
                else:
                    missing_as_redirect += 1
                    if len(sample_issues) < 10:
                        sample_issues.append(f"NOT REDIRECT: {source_qid} -> {target_qid} (has content instead)")
    
    print(f"Sample of 100 XML redirects checked:")
    print(f"  Properly imported as redirects: {properly_imported}")
    print(f"  Empty entities (should be redirects): {empty_entities}")
    print(f"  Regular entities (should be redirects): {missing_as_redirect}")
    print(f"  Missing completely: {missing_completely}")
    print()
    
    if sample_issues:
        print("Sample issues found:")
        for issue in sample_issues:
            print(f"  {issue}")
    
    client.close()
    return {
        'properly_imported': properly_imported,
        'empty_entities': empty_entities,
        'missing_as_redirect': missing_as_redirect,
        'missing_completely': missing_completely
    }

if __name__ == "__main__":
    # Find redirects in XML files
    xml_redirects = analyze_xml_redirects()
    
    # Check database status
    if xml_redirects:
        stats = check_database_redirects(xml_redirects)
        
        print()
        print("=== CONCLUSION ===")
        if stats['empty_entities'] > 0:
            print(f"ISSUE CONFIRMED: {stats['empty_entities']} entities that should be redirects are empty entities instead")
            print("The redirect import process did not work correctly.")
            print()
            print("SOLUTION NEEDED:")
            print("1. Extract all redirects from XML imports")  
            print("2. Convert empty entities to proper redirects")
            print("3. Update references to point to redirect targets")
        else:
            print("No redirect import issues found in sample.")