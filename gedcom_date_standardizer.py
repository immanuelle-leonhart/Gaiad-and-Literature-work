#!/usr/bin/env python3
"""
GEDCOM Date Standardizer
Analyzes and standardizes date formats in a GEDCOM file, with special focus on BC dates.
"""

import re
import sys
import csv
from collections import defaultdict
from typing import Optional, Dict, List, Tuple

class DateParser:
    def __init__(self):
        self.date_formats_found = defaultdict(list)
        self.parsing_stats = {
            'total_dates': 0,
            'parsed_successfully': 0,
            'bc_dates': 0,
            'mya_dates': 0,
            'parenthetical_dates': 0,
            'unparseable_dates': 0
        }
    
    def parse_gedcom_date(self, date_str: str) -> Dict:
        """Parse a GEDCOM date string and return detailed information."""
        if not date_str:
            return None
        
        original_date = date_str
        result = {
            'original': original_date,
            'year': None,
            'standardized': None,
            'format_type': 'UNKNOWN',
            'confidence': 'LOW'
        }
        
        self.parsing_stats['total_dates'] += 1
        
        # Handle parenthetical dates like "(260000000 B.C.)" or "(400MYA)"
        if date_str.startswith('(') and date_str.endswith(')'):
            self.parsing_stats['parenthetical_dates'] += 1
            date_str = date_str[1:-1]  # Remove parentheses
            result['format_type'] = 'PARENTHETICAL'
        
        # Handle million years ago (MYA) - convert to BC
        mya_match = re.search(r'([\d.]+)\s*MYA', date_str.upper())
        if mya_match:
            self.parsing_stats['mya_dates'] += 1
            mya = float(mya_match.group(1))
            bc_year = int(mya * 1000000)
            result.update({
                'year': -bc_year,
                'standardized': f'{bc_year} B.C.',
                'format_type': 'MYA',
                'confidence': 'HIGH'
            })
            self.parsing_stats['parsed_successfully'] += 1
            self.parsing_stats['bc_dates'] += 1
            self.date_formats_found['MYA'].append(original_date)
            return result
        
        # Handle B.C. dates with numbers (including scientific notation)
        bc_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:000\s*)?B\.?C\.?',  # Regular BC
            r'(\d+)\s*(?:000\s*000\s*)?B\.?C\.?',      # With thousands
            r'(\d{6,})\s*B\.?C\.?'                     # Large numbers
        ]
        
        for pattern in bc_patterns:
            bc_match = re.search(pattern, date_str.upper())
            if bc_match:
                self.parsing_stats['bc_dates'] += 1
                bc_year_str = bc_match.group(1)
                
                # Handle large numbers that might have implied thousands/millions
                if bc_year_str.isdigit():
                    bc_year = int(bc_year_str)
                    
                    # If it's a very large number, it might be in years already
                    if bc_year > 10000:  # Likely already in years
                        result.update({
                            'year': -bc_year,
                            'standardized': f'{bc_year} B.C.',
                            'format_type': 'BC_LARGE',
                            'confidence': 'HIGH'
                        })
                    else:
                        result.update({
                            'year': -bc_year,
                            'standardized': f'{bc_year} B.C.',
                            'format_type': 'BC_STANDARD',
                            'confidence': 'HIGH'
                        })
                    
                    self.parsing_stats['parsed_successfully'] += 1
                    self.date_formats_found['BC'].append(original_date)
                    return result
        
        # Remove common GEDCOM date qualifiers
        clean_date = re.sub(r'^(ABT|EST|CAL|AFT|BEF|BET|FROM|TO)\s+', '', date_str.upper())
        clean_date = re.sub(r'\s+AND\s+.*$', '', clean_date)  # Remove "AND" clauses
        
        # Handle standard BC dates (final catch)
        if 'B.C.' in clean_date or ' BC' in clean_date:
            year_match = re.search(r'(\d+)', clean_date)
            if year_match:
                bc_year = int(year_match.group(1))
                result.update({
                    'year': -bc_year,
                    'standardized': f'{bc_year} B.C.',
                    'format_type': 'BC_CLEAN',
                    'confidence': 'HIGH'
                })
                self.parsing_stats['bc_dates'] += 1
                self.parsing_stats['parsed_successfully'] += 1
                self.date_formats_found['BC_CLEAN'].append(original_date)
                return result
        
        # Handle AD dates or assume AD if no BC marker
        # Look for 4-digit year
        year_match = re.search(r'\b(\d{4})\b', clean_date)
        if year_match:
            year = int(year_match.group(1))
            
            # Special case: year 1 with BC indicators
            if year == 1 and ('B.C.' in original_date.upper() or 'BC' in original_date.upper()):
                result.update({
                    'year': -1,
                    'standardized': '1 B.C.',
                    'format_type': 'BC_YEAR_1',
                    'confidence': 'MEDIUM'
                })
                self.parsing_stats['bc_dates'] += 1
            else:
                result.update({
                    'year': year,
                    'standardized': str(year),
                    'format_type': 'AD_4DIGIT',
                    'confidence': 'HIGH'
                })
            
            self.parsing_stats['parsed_successfully'] += 1
            self.date_formats_found['AD'].append(original_date)
            return result
        
        # Look for 3-digit year (might be shorthand)
        year_match = re.search(r'\b(\d{3})\b', clean_date)
        if year_match:
            year = int(year_match.group(1))
            result.update({
                'year': year,
                'standardized': str(year),
                'format_type': 'AD_3DIGIT',
                'confidence': 'MEDIUM'
            })
            self.parsing_stats['parsed_successfully'] += 1
            self.date_formats_found['AD_SHORT'].append(original_date)
            return result
        
        # If we get here, we couldn't parse the date
        self.parsing_stats['unparseable_dates'] += 1
        self.date_formats_found['UNPARSEABLE'].append(original_date)
        return result

def scan_and_standardize_gedcom(filename: str, output_csv: str = None):
    """Scan GEDCOM file, analyze date formats, and optionally create standardized output."""
    parser = DateParser()
    all_dates = []
    
    current_record_id = None
    current_record_type = None
    
    print(f"Scanning and analyzing dates in: {filename}")
    print("=" * 60)
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Track current record
                if line.startswith('0 @') and '@' in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        current_record_id = parts[1].strip('@')
                        current_record_type = parts[2]
                
                # Look for date lines
                if ' DATE ' in line:
                    parts = line.split(' DATE ', 1)
                    if len(parts) == 2:
                        date_str = parts[1].strip()
                        parsed_date = parser.parse_gedcom_date(date_str)
                        
                        if parsed_date:
                            parsed_date.update({
                                'line_num': line_num,
                                'record_id': current_record_id,
                                'record_type': current_record_type,
                                'context': parts[0].strip()
                            })
                            all_dates.append(parsed_date)
    
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None
    
    # Print statistics
    print("Parsing Statistics:")
    print(f"  Total dates found: {parser.parsing_stats['total_dates']}")
    print(f"  Successfully parsed: {parser.parsing_stats['parsed_successfully']}")
    print(f"  BC dates: {parser.parsing_stats['bc_dates']}")
    print(f"  MYA dates: {parser.parsing_stats['mya_dates']}")
    print(f"  Parenthetical dates: {parser.parsing_stats['parenthetical_dates']}")
    print(f"  Unparseable dates: {parser.parsing_stats['unparseable_dates']}")
    print()
    
    # Show format examples
    print("Date Format Examples:")
    for format_type, examples in parser.date_formats_found.items():
        unique_examples = list(set(examples))[:5]  # Show up to 5 unique examples
        print(f"  {format_type} ({len(examples)} total):")
        for example in unique_examples:
            print(f"    '{example}'")
        print()
    
    # Show date range
    valid_dates = [d for d in all_dates if d['year'] is not None]
    if valid_dates:
        years = [d['year'] for d in valid_dates]
        min_year = min(years)
        max_year = max(years)
        
        print(f"Date Range:")
        if min_year < 0:
            print(f"  Earliest: {abs(min_year)} B.C.")
        else:
            print(f"  Earliest: {min_year} A.D.")
        
        if max_year < 0:
            print(f"  Latest: {abs(max_year)} B.C.")
        else:
            print(f"  Latest: {max_year} A.D.")
        print()
    
    # Save to CSV if requested
    if output_csv:
        print(f"Saving detailed analysis to {output_csv}...")
        with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['line_num', 'record_id', 'record_type', 'context', 'original', 
                         'year', 'standardized', 'format_type', 'confidence']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for date_info in all_dates:
                writer.writerow(date_info)
        
        print(f"Saved {len(all_dates)} date entries to {output_csv}")
    
    return all_dates, parser.date_formats_found

def create_standardized_gedcom(input_filename: str, output_filename: str, standardizations: Dict[str, str]):
    """Create a new GEDCOM file with standardized dates."""
    print(f"Creating standardized GEDCOM: {output_filename}")
    
    replacements_made = 0
    
    with open(input_filename, 'r', encoding='utf-8') as infile, \
         open(output_filename, 'w', encoding='utf-8') as outfile:
        
        for line in infile:
            original_line = line
            
            # Check if this line contains a date that needs standardization
            if ' DATE ' in line:
                for original_date, standardized_date in standardizations.items():
                    if original_date in line:
                        line = line.replace(original_date, standardized_date)
                        replacements_made += 1
                        break
            
            outfile.write(line)
    
    print(f"Made {replacements_made} date standardizations")
    print("Standardization complete!")

def main():
    if len(sys.argv) < 2:
        print("Usage: python gedcom_date_standardizer.py <gedcom_file> [csv_output] [standardized_gedcom_output]")
        print("Example: python gedcom_date_standardizer.py input.ged dates_analysis.csv standardized_input.ged")
        sys.exit(1)
    
    input_filename = sys.argv[1]
    csv_output = sys.argv[2] if len(sys.argv) > 2 else None
    standardized_output = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Scan and analyze dates
    all_dates, format_examples = scan_and_standardize_gedcom(input_filename, csv_output)
    
    if all_dates is None:
        return
    
    # If standardized output is requested, create standardization mappings
    if standardized_output:
        print("\\nCreating standardization mappings...")
        standardizations = {}
        
        for date_info in all_dates:
            if date_info['standardized'] and date_info['original'] != date_info['standardized']:
                standardizations[date_info['original']] = date_info['standardized']
        
        if standardizations:
            print(f"Found {len(standardizations)} dates to standardize")
            create_standardized_gedcom(input_filename, standardized_output, standardizations)
        else:
            print("No standardizations needed - all dates are already in standard format")

if __name__ == '__main__':
    main()