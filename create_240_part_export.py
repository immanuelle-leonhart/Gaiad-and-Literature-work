#!/usr/bin/env python3
"""
Create 240-part XML Export with Labels

Creates a 240-part XML export to reduce file sizes for more reliable import.
This uses the updated MongoDB to Wikibase XML exporter with smaller chunk sizes.
"""

import sys
import os
sys.path.append('gedcom_tools')
from mongodb_to_wikibase_xml import WikibaseXMLExporter

def main():
    print("=== CREATING 240-PART XML EXPORT ===")
    print()
    
    # Create exporter with custom output directory for 240-part files
    output_dir = "exports_with_labels_240part"
    exporter = WikibaseXMLExporter(output_dir=output_dir)
    
    print(f"Export will be saved to: {output_dir}/")
    print(f"Chunk size: 606 entities per file")
    print(f"Expected: exactly 240 output files")
    print()
    
    try:
        # Run the export
        exporter.export_all_entities()
        
        print()
        print("SUCCESS: 240-part export completed!")
        print(f"Files saved to: {output_dir}/")
        print()
        print("Next steps:")
        print("1. Use sequential_xml_importer.py to import these smaller files")
        print("2. Files should be more reliable due to smaller size")
        
    except Exception as e:
        print(f"ERROR: Export failed: {e}")
        return False
    finally:
        exporter.close()
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)