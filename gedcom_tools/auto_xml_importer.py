#!/usr/bin/env python3
"""
Automatic XML File Importer

Imports each of the 120-part XML files one by one automatically.
No user interaction required - continues even after failures.
"""

import os
import glob
import subprocess
import sys
import time
from pathlib import Path

# Configuration
EXPORTS_DIR = "exports_with_labels"
USERNAME = "Immanuelle"
PASSWORD = "1996ToOmega!"
WIKIBASE_URL = "https://evolutionism.miraheze.org"

def find_xml_files():
    """Find all 120-part XML files"""
    pattern = os.path.join(EXPORTS_DIR, "gaiad_wikibase_export_with_labels_120part_*.xml")
    files = glob.glob(pattern)
    
    # Sort by part number
    def extract_part_number(filename):
        basename = os.path.basename(filename)
        # Extract number from filename like "gaiad_wikibase_export_with_labels_120part_001.xml"
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
        
        print(f"Running import...")
        start_time = time.time()
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=900,  # 15 minute timeout per file
            cwd=os.getcwd()
        )
        
        duration = time.time() - start_time
        print(f"Import duration: {duration:.1f} seconds")
        
        if result.returncode == 0:
            print("SUCCESS: File imported successfully")
            # Show last few lines of output
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                print("Last output:", lines[-1] if lines else "None")
            return True
        else:
            print(f"FAILED: Import returned code {result.returncode}")
            if result.stderr:
                print("Error:", result.stderr[-500:])
            return False
            
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT: Import took longer than 15 minutes")
        return False
    except Exception as e:
        print(f"ERROR: Exception during import: {e}")
        return False

def main():
    print("=== AUTOMATIC XML FILE IMPORTER ===")
    print()
    
    # Find all XML files
    xml_files = find_xml_files()
    
    if not xml_files:
        print("ERROR: No 120-part XML files found!")
        print(f"Looking in: {EXPORTS_DIR}")
        return
    
    total_files = len(xml_files)
    print(f"Found {total_files} XML files to import")
    print("This will run automatically without user interaction.")
    print()
    
    # Import each file
    successful_imports = 0
    failed_imports = 0
    failed_files = []
    start_time = time.time()
    
    for i, xml_file in enumerate(xml_files, 1):
        print(f"\n{'='*60}")
        
        success = import_single_file(xml_file, i, total_files)
        
        if success:
            successful_imports += 1
            print(f"OK Part {i} completed successfully")
        else:
            failed_imports += 1
            failed_files.append(os.path.basename(xml_file))
            print(f"FAILED Part {i} failed - continuing anyway")
        
        # Show progress
        progress = (i / total_files) * 100
        elapsed = time.time() - start_time
        estimated_remaining = (elapsed / i) * (total_files - i) if i > 0 else 0
        
        print(f"Progress: {progress:.1f}% ({i}/{total_files})")
        print(f"Elapsed: {elapsed/60:.1f}min, Est. remaining: {estimated_remaining/60:.1f}min")
        
        # Brief pause between imports
        if i < total_files:
            time.sleep(1)
    
    # Final summary
    total_time = time.time() - start_time
    print(f"\n{'='*60}")
    print("=== IMPORT SUMMARY ===")
    print(f"Total files: {total_files}")
    print(f"Successful imports: {successful_imports}")
    print(f"Failed imports: {failed_imports}")
    print(f"Total time: {total_time/60:.1f} minutes")
    
    if failed_files:
        print(f"\nFailed files:")
        for failed_file in failed_files[:10]:  # Show first 10
            print(f"  - {failed_file}")
        if len(failed_files) > 10:
            print(f"  ... and {len(failed_files) - 10} more")
    
    if successful_imports > 0:
        success_rate = (successful_imports / total_files) * 100
        print(f"\nSuccess rate: {success_rate:.1f}%")
        avg_time = total_time / successful_imports
        print(f"Average time per file: {avg_time:.1f} seconds")
    
    if failed_imports == 0:
        print("\nSUCCESS: All files imported successfully!")
    elif successful_imports > failed_imports:
        print(f"\nMOSTLY SUCCESSFUL: {successful_imports} imports completed")
    else:
        print(f"\nMANY ISSUES: {failed_imports} failures")
        print("May need to try even smaller chunks")

if __name__ == "__main__":
    main()