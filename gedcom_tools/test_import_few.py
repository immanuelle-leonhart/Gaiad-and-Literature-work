#!/usr/bin/env python3
"""
Test Import Script - Import first few files to test timing
"""

import os
import time
import sys
sys.path.append('gedcom_tools')
from direct_xml_importer import DirectXMLImporter

def main():
    print("=== TEST IMPORT - FIRST 5 FILES ===")
    print()
    
    importer = DirectXMLImporter()
    
    # Authenticate
    if not importer.login():
        print("FATAL: Authentication failed")
        return False
    
    print()
    
    # Find first 5 files
    xml_files = importer.find_xml_files()[:5]  # Only first 5 files
    
    if not xml_files:
        print("ERROR: No XML files found!")
        return False
    
    print(f"Testing with {len(xml_files)} files:")
    for i, xml_file in enumerate(xml_files, 1):
        print(f"  {i}. {os.path.basename(xml_file)}")
    print()
    
    # Import each file
    start_time = time.time()
    
    for i, xml_file in enumerate(xml_files, 1):
        print(f"\n{'='*50}")
        
        success = importer.import_xml_file(xml_file, i, len(xml_files))
        
        if success:
            print(f"SUCCESS: File {i} completed")
        else:
            print(f"FAILED: File {i} failed")
    
    # Summary
    total_time = time.time() - start_time
    print(f"\n{'='*50}")
    print("=== TEST SUMMARY ===")
    print(f"Files processed: {len(xml_files)}")
    print(f"Successful: {importer.stats['files_successful']}")
    print(f"Failed: {importer.stats['files_failed']}")
    print(f"Total time: {total_time:.1f} seconds")
    print(f"Average per file: {total_time/len(xml_files):.1f} seconds")
    print(f"Estimated time for all 120 files: {total_time/len(xml_files)*120/60:.1f} minutes")
    
    return True

if __name__ == "__main__":
    main()