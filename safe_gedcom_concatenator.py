#!/usr/bin/env python3
"""
Safe GEDCOM concatenator - preserves all relationships by using ID offsets
"""

import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SafeGedcomConcatenator:
    def __init__(self):
        self.individual_offset = 0
        self.family_offset = 0
        
    def find_max_ids(self, filepath: str):
        """Find the maximum individual and family IDs in a GEDCOM file"""
        max_ind_id = 0
        max_fam_id = 0
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                # Find individual IDs
                if re.match(r'^0 @I(\d+)@ INDI$', line):
                    ind_id = int(re.match(r'^0 @I(\d+)@ INDI$', line).group(1))
                    max_ind_id = max(max_ind_id, ind_id)
                    
                # Find family IDs
                elif re.match(r'^0 @F(\d+)@ FAM$', line):
                    fam_id = int(re.match(r'^0 @F(\d+)@ FAM$', line).group(1))
                    max_fam_id = max(max_fam_id, fam_id)
                    
        return max_ind_id, max_fam_id
        
    def offset_ids_in_line(self, line: str, ind_offset: int, fam_offset: int):
        """Offset all individual and family ID references in a line"""
        # Offset individual IDs @I123@ -> @I(123+offset)@
        def offset_individual_id(match):
            original_id = int(match.group(1))
            new_id = original_id + ind_offset
            return f"@I{new_id}@"
            
        def offset_family_id(match):
            original_id = int(match.group(1))
            new_id = original_id + fam_offset
            return f"@F{new_id}@"
            
        # Apply offsets
        line = re.sub(r'@I(\d+)@', offset_individual_id, line)
        line = re.sub(r'@F(\d+)@', offset_family_id, line)
        
        return line
        
    def concatenate_gedcom_files(self, file1: str, file2: str, output_file: str):
        """Safely concatenate two GEDCOM files with proper ID offsetting"""
        logger.info(f"Starting safe concatenation of {file1} and {file2}")
        
        # Find max IDs in first file to determine offset for second file
        max_ind_1, max_fam_1 = self.find_max_ids(file1)
        logger.info(f"File 1 max IDs: I{max_ind_1}, F{max_fam_1}")
        
        # Offsets for second file (add buffer to be safe)
        ind_offset = max_ind_1 + 1000
        fam_offset = max_fam_1 + 1000
        
        with open(output_file, 'w', encoding='utf-8') as out_f:
            # Write combined header
            out_f.write("0 HEAD\n")
            out_f.write("1 SOUR Safe_GEDCOM_Concatenator\n")
            out_f.write("2 NAME Safe GEDCOM File Concatenator\n")
            out_f.write("2 CORP Gaiad Genealogy Project\n")
            out_f.write("1 DEST GEDCOM\n")
            out_f.write("1 DATE 07 AUG 2025\n")
            out_f.write(f"1 FILE {output_file}\n")
            out_f.write("1 GEDC\n")
            out_f.write("2 VERS 5.5.1\n")
            out_f.write("2 FORM LINEAGE-LINKED\n")
            out_f.write("1 CHAR UTF-8\n")
            out_f.write("1 NOTE Combined from multiple genealogy files:\n")
            out_f.write(f"2 CONT - {file1}\n")
            out_f.write(f"2 CONT - {file2}\n")
            out_f.write("2 CONT All family relationships preserved\n")
            
            # Copy first file (skip its header and trailer)
            logger.info("Copying first file...")
            records_written = 0
            with open(file1, 'r', encoding='utf-8', errors='ignore') as f1:
                in_header = True
                for line in f1:
                    line = line.rstrip('\r\n')
                    
                    # Skip header
                    if in_header:
                        if line.startswith('0 @') and '@' in line[2:]:
                            in_header = False
                        else:
                            continue
                            
                    # Skip trailer
                    if line.strip() == '0 TRLR':
                        break
                        
                    # Write the line as-is (no ID offsetting needed for first file)
                    out_f.write(line + '\n')
                    
                    if line.startswith('0 @'):
                        records_written += 1
                        if records_written % 5000 == 0:
                            logger.info(f"Copied {records_written} records from file 1")
                            
            logger.info(f"Completed file 1: {records_written} records")
            
            # Copy second file with ID offsetting (skip its header and trailer)
            logger.info(f"Copying second file with offsets: +{ind_offset} individuals, +{fam_offset} families")
            records_written = 0
            with open(file2, 'r', encoding='utf-8', errors='ignore') as f2:
                in_header = True
                for line in f2:
                    line = line.rstrip('\r\n')
                    
                    # Skip header
                    if in_header:
                        if line.startswith('0 @') and '@' in line[2:]:
                            in_header = False
                        else:
                            continue
                            
                    # Skip trailer
                    if line.strip() == '0 TRLR':
                        break
                        
                    # Apply ID offsets to preserve relationships
                    line = self.offset_ids_in_line(line, ind_offset, fam_offset)
                    out_f.write(line + '\n')
                    
                    if line.startswith('0 @'):
                        records_written += 1
                        if records_written % 5000 == 0:
                            logger.info(f"Copied {records_written} records from file 2")
                            
            logger.info(f"Completed file 2: {records_written} records")
            
            # Write trailer
            out_f.write("0 TRLR\n")
            
        # Final statistics
        import os
        output_size = os.path.getsize(output_file)
        logger.info(f"Concatenation completed!")
        logger.info(f"Output file: {output_file}")
        logger.info(f"Size: {output_size:,} bytes ({output_size/1024/1024:.1f} MB)")
        
        # Verify the result
        with open(output_file, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f)
        logger.info(f"Total lines: {line_count:,}")

if __name__ == "__main__":
    concatenator = SafeGedcomConcatenator()
    concatenator.concatenate_gedcom_files(
        "new_gedcoms/geni plus wikidata after merge.ged",
        "new_gedcoms/gaiad_ftb_simple_conversion.ged", 
        "new_gedcoms/safely_merged.ged"
    )