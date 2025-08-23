#!/usr/bin/env python3
"""
Automatic Sequential XML File Importer

Imports all XML files from the 240-part export (actually 59 files) automatically
without interactive prompts that could stop execution. Continues through all
files regardless of individual failures.
"""

import os
import glob
import subprocess
import sys
import time
from pathlib import Path

# Configuration for the new 240-part export
EXPORTS_DIR = "exports_with_labels_240part"
USERNAME = "Immanuelle"
PASSWORD = "1996ToOmega!"
WIKIBASE_URL = "https://evolutionism.miraheze.org"

def find_xml_files():
    """Find all XML files in the 240-part export directory"""
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
    """Import a single XML file without stopping on failure"""
    print(f"=== IMPORTING PART {part_number}/{total_parts} ===")
    print(f"File: {os.path.basename(xml_file)}")
    
    if not os.path.exists(xml_file):
        print(f"ERROR: File not found: {xml_file}")
        return False
    
    # Get file size
    file_size = os.path.getsize(xml_file) / (1024 * 1024)  # MB
    print(f"File size: {file_size:.1f} MB")
    
    try:
        # Import using single_file_importer.py
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
            if result.stdout:
                # Show last 500 chars of output for success confirmation
                output_snippet = result.stdout[-500:] if len(result.stdout) > 500 else result.stdout
                print(f"Output: {output_snippet.strip()}")
            return True
        else:
            print(f"FAILED: Import returned code {result.returncode}")
            if result.stderr:
                error_snippet = result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr
                print(f"Error: {error_snippet.strip()}")
            if result.stdout:
                output_snippet = result.stdout[-1000:] if len(result.stdout) > 1000 else result.stdout
                print(f"Output: {output_snippet.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT: Import took longer than 30 minutes")
        return False
    except Exception as e:
        print(f"ERROR: Exception during import: {e}")
        return False

def main():
    print("=== AUTOMATIC SEQUENTIAL XML FILE IMPORTER ===")
    print("This will run all files automatically without stopping on failures")
    print()
    
    # Find all XML files
    xml_files = find_xml_files()
    
    if not xml_files:
        print("ERROR: No XML files found!")
        print(f"Looking in: {EXPORTS_DIR}")
        print("Expected pattern: gaiad_wikibase_export_part_*.xml")
        return
    
    total_files = len(xml_files)
    print(f"Found {total_files} XML files to import")
    print()
    
    # Show first few files
    print("Files to import:")
    for i, xml_file in enumerate(xml_files[:10]):
        file_size = os.path.getsize(xml_file) / (1024 * 1024)
        print(f"  {i+1:3d}. {os.path.basename(xml_file)} ({file_size:.1f} MB)")
    if total_files > 10:
        print(f"  ... and {total_files - 10} more files")
    print()
    
    # Import each file - NO STOPPING ON FAILURES
    successful_imports = 0
    failed_imports = 0
    failed_files = []
    start_time = time.time()
    
    for i, xml_file in enumerate(xml_files, 1):
        print(f"\n{'='*60}")
        
        success = import_single_file(xml_file, i, total_files)
        
        if success:
            successful_imports += 1
            print(f"SUCCESS: Part {i} completed successfully")
        else:
            failed_imports += 1
            failed_files.append(os.path.basename(xml_file))
            print(f"FAILED: Part {i} failed - CONTINUING ANYWAY")
        
        # Show progress
        progress = (i / total_files) * 100
        elapsed = time.time() - start_time
        estimated_remaining = (elapsed / i) * (total_files - i) if i > 0 else 0
        
        print(f"Progress: {progress:.1f}% ({i}/{total_files})")
        print(f"Success: {successful_imports}, Failed: {failed_imports}")
        print(f"Elapsed: {elapsed/60:.1f}min, Est. remaining: {estimated_remaining/60:.1f}min")
        
        # Brief pause between imports
        if i < total_files:
            print("Waiting 3 seconds before next import...")
            time.sleep(3)
    
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
        for failed_file in failed_files:
            print(f"  - {failed_file}")
    
    if successful_imports > 0:
        success_rate = (successful_imports / total_files) * 100
        avg_time = total_time / successful_imports
        print(f"\nSuccess rate: {success_rate:.1f}%")
        print(f"Average time per successful import: {avg_time:.1f} seconds")
    
    if failed_imports == 0:
        print("\nPERFECT: All files imported successfully!")
    elif successful_imports > failed_imports:
        print(f"\nMOSTLY SUCCESSFUL: {successful_imports} imports completed")
        print(f"Only {failed_imports} failed - you can retry those individually")
    else:
        print(f"\nMANY FAILURES: {failed_imports} failures out of {total_files}")
        print("Consider smaller chunks or investigating systematic issues")
    
    print(f"\nALL {total_files} FILES PROCESSED - NO EARLY STOPPING")

if __name__ == "__main__":
    main()