#!/usr/bin/env python3
"""
GEDCOM Date Standardizer
Standardizes all date formats in a GEDCOM file to follow GEDCOM 5.5.1 specification.

GEDCOM Date Standards:
- AD dates: "15 JAN 1066" or "JAN 1066" or "1066"
- BC dates: "15 JAN 1066 BC" or "JAN 1066 BC" or "1066 BC"
- Approximate: "ABT 1066", "EST 1066"  
- Ranges: "BET 1060 AND 1070", "AFT 1066", "BEF 1066"
"""

import re
import sys
import csv
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

class GedcomDateStandardizer:
    def __init__(self):
        self.changes_made = []
        self.error_log = []
        
        # Month name mappings
        self.month_names = {
            'JAN': 'JAN', 'JANUARY': 'JAN',
            'FEB': 'FEB', 'FEBRUARY': 'FEB', 
            'MAR': 'MAR', 'MARCH': 'MAR',
            'APR': 'APR', 'APRIL': 'APR',
            'MAY': 'MAY',
            'JUN': 'JUN', 'JUNE': 'JUN',
            'JUL': 'JUL', 'JULY': 'JUL',
            'AUG': 'AUG', 'AUGUST': 'AUG',
            'SEP': 'SEP', 'SEPTEMBER': 'SEP', 'SEPT': 'SEP',
            'OCT': 'OCT', 'OCTOBER': 'OCT',
            'NOV': 'NOV', 'NOVEMBER': 'NOV',
            'DEC': 'DEC', 'DECEMBER': 'DEC'
        }
    
    def standardize_date_string(self, date_str: str, line_num: int) -> str:
        """Standardize a single date string."""
        if not date_str or not date_str.strip():
            return date_str
        
        original = date_str
        date_str = date_str.strip()
        
        # Handle problematic dates with en-dashes or em-dashes instead of minus signs
        if '–' in date_str or '—' in date_str:
            # These appear to be BC dates with wrong dash characters
            date_str = date_str.replace('–', ' BC').replace('—', ' BC')
            # Remove parentheses if present
            date_str = date_str.replace('(', '').replace(')', '')
            self.changes_made.append((line_num, f"Fixed dash in BC date: '{original}' -> '{date_str}'"))
        
        # Handle parenthetical BC dates: (260000000 B.C.) -> 260000000 BC
        paren_bc_match = re.match(r'^\((\d+(?:\.\d+)?)\s*B\.?C\.?\)$', date_str, re.IGNORECASE)
        if paren_bc_match:
            year = paren_bc_match.group(1)
            date_str = f"{year} BC"
            self.changes_made.append((line_num, f"Fixed parenthetical BC: '{original}' -> '{date_str}'"))
        
        # Handle MYA dates - convert to BC
        mya_match = re.search(r'\((\d+(?:\.\d+)?)\s*MYA\)', date_str, re.IGNORECASE)
        if mya_match:
            mya_value = float(mya_match.group(1))
            bc_year = int(mya_value * 1000000)
            date_str = f"{bc_year} BC"
            self.changes_made.append((line_num, f"Converted MYA to BC: '{original}' -> '{date_str}'"))
        
        # Standardize B.C. to BC
        if 'B.C.' in date_str.upper():
            date_str = re.sub(r'B\.C\.E?', 'BC', date_str, flags=re.IGNORECASE)
            self.changes_made.append((line_num, f"Standardized BC format: '{original}' -> '{date_str}'"))
        elif 'BCE' in date_str.upper():
            date_str = re.sub(r'BCE', 'BC', date_str, flags=re.IGNORECASE)
            self.changes_made.append((line_num, f"Standardized BCE to BC: '{original}' -> '{date_str}'"))
        
        # Handle approximate dates
        date_str = re.sub(r'\bABOUT\b', 'ABT', date_str, flags=re.IGNORECASE)
        date_str = re.sub(r'\bCIRCA\b', 'ABT', date_str, flags=re.IGNORECASE)
        date_str = re.sub(r'\bCALCULATED\b', 'CAL', date_str, flags=re.IGNORECASE)
        date_str = re.sub(r'\bESTIMATED\b', 'EST', date_str, flags=re.IGNORECASE)
        
        # Standardize month names
        for full_name, abbrev in self.month_names.items():
            date_str = re.sub(r'\b' + full_name + r'\b', abbrev, date_str, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        date_str = ' '.join(date_str.split())
        
        # Log if we made changes
        if date_str != original:
            if not any(change[0] == line_num for change in self.changes_made):
                self.changes_made.append((line_num, f"General standardization: '{original}' -> '{date_str}'"))
        
        return date_str
    
    def standardize_gedcom_file(self, input_file: str, output_file: str) -> Dict[str, int]:
        """Standardize all dates in a GEDCOM file."""
        print(f"Standardizing dates in {input_file}")
        
        stats = defaultdict(int)
        
        with open(input_file, 'r', encoding='utf-8', errors='replace') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:
            
            for line_num, line in enumerate(infile, 1):
                original_line = line
                
                # Check if this is a date line
                if line.strip().startswith('2 DATE '):
                    stats['total_date_lines'] += 1
                    
                    # Extract the date part
                    prefix = line[:7]  # "2 DATE "
                    date_part = line[7:].rstrip('\n\r')
                    
                    # Standardize the date
                    standardized_date = self.standardize_date_string(date_part, line_num)
                    
                    # Reconstruct the line
                    line = prefix + standardized_date + '\n'
                    
                    if line != original_line:
                        stats['lines_modified'] += 1
                
                outfile.write(line)
                
                # Progress indicator
                if line_num % 100000 == 0:
                    print(f"Processed {line_num:,} lines...")
        
        return dict(stats)
    
    def export_changes_log(self, log_file: str):
        """Export all changes made to a CSV file."""
        with open(log_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Line_Number', 'Change_Description'])
            
            for line_num, description in self.changes_made:
                writer.writerow([line_num, description])
    
    def print_summary(self, stats: Dict[str, int]):
        """Print standardization summary."""
        print("\n=== GEDCOM DATE STANDARDIZATION SUMMARY ===")
        print(f"Total date lines processed: {stats.get('total_date_lines', 0):,}")
        print(f"Lines modified: {stats.get('lines_modified', 0):,}")
        print(f"Changes made: {len(self.changes_made):,}")
        
        if self.error_log:
            print(f"Errors encountered: {len(self.error_log):,}")
            print("\nFirst 10 errors:")
            for error in self.error_log[:10]:
                print(f"  {error}")

def main():
    if len(sys.argv) not in [3, 4]:
        print("Usage: python gedcom_date_standardizer.py <input_gedcom> <output_gedcom> [changes_log.csv]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    log_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    standardizer = GedcomDateStandardizer()
    
    try:
        # Perform standardization
        stats = standardizer.standardize_gedcom_file(input_file, output_file)
        
        # Print summary
        standardizer.print_summary(stats)
        
        # Export changes log if requested
        if log_file:
            standardizer.export_changes_log(log_file)
            print(f"\nChanges log exported to: {log_file}")
        
        print(f"\nStandardized GEDCOM saved to: {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()