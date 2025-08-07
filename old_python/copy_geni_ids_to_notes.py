#!/usr/bin/env python3
"""
Script to copy Geni IDs from REFN lines to NOTE lines in GEDCOM files.
This ensures Geni profile information is preserved in the notes section.
"""

import re
import logging
import os
from typing import List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GeniIdCopier:
    def __init__(self, input_file: str, output_file: str):
        self.input_file = input_file
        self.output_file = output_file
        self.lines = []
        self.geni_ids_copied = 0
        
    def process_gedcom(self):
        """Process GEDCOM file to copy Geni IDs from REFN to NOTE lines"""
        logger.info(f"Processing GEDCOM file: {self.input_file}")
        
        # Read the file
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                self.lines = f.readlines()
        except UnicodeDecodeError:
            with open(self.input_file, 'r', encoding='latin-1') as f:
                self.lines = f.readlines()
                
        logger.info(f"Loaded {len(self.lines):,} lines")
        
        # Process line by line
        output_lines = []
        current_individual = None
        individual_geni_ids = []
        individual_lines = []
        
        for i, line in enumerate(self.lines):
            stripped_line = line.strip()
            
            # Check if we're starting a new individual record
            if stripped_line.startswith('0 @') and stripped_line.endswith('@ INDI'):
                # Process previous individual if it had Geni IDs
                if current_individual and individual_geni_ids:
                    # Add the individual's existing lines
                    output_lines.extend(individual_lines)
                    
                    # Add Geni ID notes at the end of the individual record
                    for geni_id in individual_geni_ids:
                        output_lines.append(f"1 NOTE Geni profile: {geni_id}\n")
                        self.geni_ids_copied += 1
                    
                elif current_individual:
                    # No Geni IDs, just add the lines as-is
                    output_lines.extend(individual_lines)
                
                # Start new individual
                match = re.search(r'0 @(.+?)@ INDI', stripped_line)
                if match:
                    current_individual = match.group(1)
                    individual_geni_ids = []
                    individual_lines = [line]
                else:
                    current_individual = None
                    individual_lines = [line]
                    
            elif current_individual is None:
                # Not in an individual record, just copy the line
                output_lines.append(line)
                
            elif stripped_line.startswith('0 '):
                # End of individual record, process it
                if individual_geni_ids:
                    # Add the individual's existing lines
                    output_lines.extend(individual_lines)
                    
                    # Add Geni ID notes at the end
                    for geni_id in individual_geni_ids:
                        output_lines.append(f"1 NOTE Geni profile: {geni_id}\n")
                        self.geni_ids_copied += 1
                else:
                    # No Geni IDs, just add the lines as-is
                    output_lines.extend(individual_lines)
                
                # Add the current line (start of new record)
                output_lines.append(line)
                current_individual = None
                individual_lines = []
                individual_geni_ids = []
                
            else:
                # Line within an individual record
                individual_lines.append(line)
                
                # Check for Geni ID in REFN
                if stripped_line.startswith('1 REFN ') or stripped_line.startswith('2 REFN '):
                    refn_value = stripped_line.split(' ', 2)[-1]
                    if refn_value.startswith('geni:'):
                        individual_geni_ids.append(refn_value)
                        logger.debug(f"Found Geni ID: {refn_value} for individual {current_individual}")
        
        # Handle the last individual if file doesn't end with a new record
        if current_individual and individual_lines:
            if individual_geni_ids:
                output_lines.extend(individual_lines)
                for geni_id in individual_geni_ids:
                    output_lines.append(f"1 NOTE Geni profile: {geni_id}\n")
                    self.geni_ids_copied += 1
            else:
                output_lines.extend(individual_lines)
        
        # Write the output file
        logger.info(f"Writing output to: {self.output_file}")
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.writelines(output_lines)
            
        logger.info(f"Processing complete!")
        logger.info(f"  Input lines: {len(self.lines):,}")
        logger.info(f"  Output lines: {len(output_lines):,}")
        logger.info(f"  Geni IDs copied to notes: {self.geni_ids_copied}")

def main():
    input_file = "C:\\Users\\Immanuelle\\Documents\\Github\\Gaiad-Genealogy\\geni plus wikidata after merge.ged"
    output_file = "C:\\Users\\Immanuelle\\Documents\\Github\\Gaiad-Genealogy\\geni_plus_wikidata_with_geni_notes.ged"
    
    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        return
        
    copier = GeniIdCopier(input_file, output_file)
    
    print("=== Geni ID to Notes Copier ===")
    print(f"Input: {input_file}")
    print(f"Size: {os.path.getsize(input_file) / (1024*1024):.1f} MB")
    print(f"Output: {output_file}")
    print()
    
    copier.process_gedcom()
    
    if os.path.exists(output_file):
        print(f"Output file size: {os.path.getsize(output_file) / (1024*1024):.1f} MB")

if __name__ == "__main__":
    main()