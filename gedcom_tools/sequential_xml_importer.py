#!/usr/bin/env python3
"""
Sequential XML File Importer

Imports each of the 120-part XML files one by one to avoid memory issues.
This allows us to handle large datasets by processing them in smaller chunks.
"""

import os
import glob
import subprocess
import sys
import time
from pathlib import Path

# Configuration
EXPORTS_DIR = "exports_with_labels_240part"
USERNAME = "Immanuelle"
PASSWORD = "1996ToOmega!"
WIKIBASE_URL = "https://evolutionism.miraheze.org"

def find_xml_files():
    """Find all 240-part XML files"""
    pattern = os.path.join(EXPORTS_DIR, "gaiad_wikibase_export_part_*.xml")
    files = glob.glob(pattern)
    
    # Sort by part number
    def extract_part_number(filename):
        basename = os.path.basename(filename)
        # Extract number from filename like "gaiad_wikibase_export_part_001.xml"
        parts = basename.split('_')
        for part in parts:
            if part.endswith('.xml'):
                return int(part.replace('.xml', ''))
        return 0
    
    files.sort(key=extract_part_number)
    return files

def import_single_file(xml_file, part_number, total_parts):
    """Import a single XML file"""
    print(f"=== IMPORTING PART {part_number}/{total_parts} ===")
    print(f"File: {os.path.basename(xml_file)}")
    
    if not os.path.exists(xml_file):
        print(f"ERROR: File not found: {xml_file}")
        return False
    
    # Get file size
    file_size = os.path.getsize(xml_file) / (1024 * 1024)  # MB
    print(f"File size: {file_size:.1f} MB")
    
    try:
        # Import using single_file_importer.py (designed for individual files)
        cmd = [
            sys.executable,
            "gedcom_tools/single_file_importer.py",
            xml_file,
            USERNAME,
            PASSWORD
        ]
        
        print(f"Running: {' '.join(cmd)}")
        start_time = time.time()
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800,  # 30 minute timeout per file
            cwd=os.getcwd()
        )
        
        duration = time.time() - start_time
        print(f"Import duration: {duration:.1f} seconds")
        
        if result.returncode == 0:
            print("SUCCESS: File imported successfully")
            print("STDOUT:", result.stdout[-500:] if result.stdout else "No output")
            return True
        else:
            print(f"FAILED: Import returned code {result.returncode}")
            print("STDERR:", result.stderr[-1000:] if result.stderr else "No error output")
            print("STDOUT:", result.stdout[-1000:] if result.stdout else "No output")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT: Import took longer than 30 minutes")
        return False
    except Exception as e:
        print(f"ERROR: Exception during import: {e}")
        return False

def main():
    print("=== SEQUENTIAL XML FILE IMPORTER ===")
    print()
    
    # Find all XML files
    xml_files = find_xml_files()
    
    if not xml_files:
        print("ERROR: No 120-part XML files found!")
        print(f"Looking in: {EXPORTS_DIR}")
        print("Expected pattern: gaiad_wikibase_export_with_labels_120part_*.xml")
        return
    
    total_files = len(xml_files)
    print(f"Found {total_files} XML files to import")
    print()
    
    # Show first few files
    print("Files to import:")
    for i, xml_file in enumerate(xml_files[:10]):
        print(f"  {i+1:3d}. {os.path.basename(xml_file)}")
    if total_files > 10:
        print(f"  ... and {total_files - 10} more files")
    print()
    
    # Import each file
    successful_imports = 0
    failed_imports = 0
    failed_files = []
    
    for i, xml_file in enumerate(xml_files, 1):
        print(f"\n{'='*60}")
        
        success = import_single_file(xml_file, i, total_files)
        
        if success:
            successful_imports += 1
            print(f"OK Part {i} completed successfully")
        else:
            failed_imports += 1
            failed_files.append(os.path.basename(xml_file))
            print(f"FAILED Part {i} failed")
            
            # Ask if we should continue after failures
            if failed_imports >= 150:
                print(f"\n{failed_imports} consecutive failures detected.")
                print("This might indicate a systematic issue.")
                response = input("Continue with remaining files? (y/n): ").lower().strip()
                if response != 'y':
                    print("Stopping import process.")
                    break
        
        # Brief pause between imports
        if i < total_files:
            print("Waiting 2 seconds before next import...")
            time.sleep(2)
    
    # Final summary
    print(f"\n{'='*60}")
    print("=== IMPORT SUMMARY ===")
    print(f"Total files: {total_files}")
    print(f"Successful imports: {successful_imports}")
    print(f"Failed imports: {failed_imports}")
    
    if failed_files:
        print(f"\nFailed files:")
        for failed_file in failed_files:
            print(f"  - {failed_file}")
    
    if successful_imports > 0:
        success_rate = (successful_imports / (successful_imports + failed_imports)) * 100
        print(f"\nSuccess rate: {success_rate:.1f}%")
    
    if failed_imports == 0:
        print("\nSUCCESS: All files imported successfully!")
    elif successful_imports > failed_imports:
        print(f"\nMOSTLY SUCCESSFUL: {successful_imports} imports completed")
        print(f"You may want to retry the {failed_imports} failed files")
    else:
        print(f"\nISSUES DETECTED: {failed_imports} failures")
        print("Consider using smaller file chunks or checking for systematic issues")

if __name__ == "__main__":
    main()