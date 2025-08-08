#!/usr/bin/env python3
"""
GEDCOM Date Scanner
Scans a GEDCOM file and reports all dates found, with statistics about date ranges.
"""

import re
import sys
from collections import defaultdict
from datetime import datetime

def parse_gedcom_date(date_str):
    """Parse a GEDCOM date string and return a normalized date."""
    if not date_str:
        return None
    
    # Remove common GEDCOM date qualifiers
    date_str = re.sub(r'^(ABT|EST|CAL|AFT|BEF|BET|FROM|TO)\s+', '', date_str.upper())
    date_str = re.sub(r'\s+AND\s+.*$', '', date_str)  # Remove "AND" clauses in date ranges
    
    # Handle various date formats
    patterns = [
        r'(\d+)\s+(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+(\d+)',  # DD MMM YYYY
        r'(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+(\d+)',         # MMM YYYY
        r'^(\d{4})$',                                                           # YYYY
        r'^(\d+)\s+BC$',                                                       # YYYY BC
        r'^(\d+)\s+(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+(\d+)\s+BC$',  # DD MMM YYYY BC
        r'^(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+(\d+)\s+BC$'   # MMM YYYY BC
    ]
    
    for pattern in patterns:
        match = re.match(pattern, date_str.strip())
        if match:
            if 'BC' in date_str:
                if len(match.groups()) == 1:  # Just year BC
                    return -int(match.group(1))
                elif len(match.groups()) == 2:  # Month Year BC
                    return -int(match.group(2))
                elif len(match.groups()) == 3:  # Day Month Year BC
                    return -int(match.group(3))
            else:
                if len(match.groups()) == 1:  # Just year
                    return int(match.group(1))
                elif len(match.groups()) == 2:  # Month Year
                    return int(match.group(2))
                elif len(match.groups()) == 3:  # Day Month Year
                    return int(match.group(3))
    
    return None

def scan_gedcom_dates(filename):
    """Scan a GEDCOM file and extract all dates."""
    dates_found = []
    date_types = defaultdict(list)
    current_record_id = None
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Track current record ID
                if line.startswith('0 @') and line.endswith('@'):
                    current_record_id = line.split()[1]
                
                # Look for date lines
                if ' DATE ' in line:
                    parts = line.split(' DATE ', 1)
                    if len(parts) == 2:
                        date_str = parts[1].strip()
                        parsed_date = parse_gedcom_date(date_str)
                        
                        # Determine the type of date based on the line structure
                        date_type = 'UNKNOWN'
                        if '1 BIRT' in line or '2 DATE' in line:
                            date_type = 'BIRTH'
                        elif '1 DEAT' in line:
                            date_type = 'DEATH'
                        elif '1 MARR' in line:
                            date_type = 'MARRIAGE'
                        elif '1 DIV' in line:
                            date_type = 'DIVORCE'
                        
                        dates_found.append({
                            'line_num': line_num,
                            'record_id': current_record_id,
                            'date_type': date_type,
                            'original': date_str,
                            'parsed': parsed_date
                        })
                        
                        if parsed_date is not None:
                            date_types[date_type].append(parsed_date)
    
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return None, None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None, None
    
    return dates_found, date_types

def main():
    if len(sys.argv) != 2:
        print("Usage: python gedcom_date_scanner.py <gedcom_file>")
        sys.exit(1)
    
    filename = sys.argv[1]
    print(f"Scanning dates in: {filename}")
    print("=" * 60)
    
    dates_found, date_types = scan_gedcom_dates(filename)
    
    if dates_found is None:
        return
    
    print(f"Total date entries found: {len(dates_found)}")
    print()
    
    # Statistics by date type
    print("Date Types Found:")
    for date_type, dates in date_types.items():
        valid_dates = [d for d in dates if d is not None]
        if valid_dates:
            min_date = min(valid_dates)
            max_date = max(valid_dates)
            print(f"  {date_type}: {len(dates)} total, {len(valid_dates)} parseable")
            print(f"    Range: {min_date} to {max_date}")
            if min_date < 0:
                print(f"    Earliest BC: {abs(min_date)} BC")
            if max_date > 0:
                print(f"    Latest AD: {max_date} AD")
        else:
            print(f"  {date_type}: {len(dates)} total, 0 parseable")
    
    # Overall statistics
    all_valid_dates = []
    for dates in date_types.values():
        all_valid_dates.extend([d for d in dates if d is not None])
    
    if all_valid_dates:
        print(f"\nOverall Date Range:")
        print(f"  Earliest: {min(all_valid_dates)}")
        print(f"  Latest: {max(all_valid_dates)}")
        
        bc_dates = [d for d in all_valid_dates if d < 0]
        ad_dates = [d for d in all_valid_dates if d > 0]
        
        if bc_dates:
            print(f"  BC dates: {len(bc_dates)} (earliest: {abs(min(bc_dates))} BC)")
        if ad_dates:
            print(f"  AD dates: {len(ad_dates)} (latest: {max(ad_dates)} AD)")
    
    # Show some examples of unparseable dates
    unparseable = [d for d in dates_found if d['parsed'] is None]
    if unparseable:
        print(f"\nSample unparseable dates ({len(unparseable)} total):")
        for i, date_entry in enumerate(unparseable[:10]):  # Show first 10
            print(f"  Line {date_entry['line_num']}: '{date_entry['original']}'")
    
    # Show extreme dates
    print(f"\nExtreme dates (first 10 of each):")
    all_dates_with_info = [(d['parsed'], d) for d in dates_found if d['parsed'] is not None]
    all_dates_with_info.sort(key=lambda x: x[0])
    
    print("Earliest dates:")
    for i, (parsed_date, info) in enumerate(all_dates_with_info[:10]):
        year_str = f"{abs(parsed_date)} BC" if parsed_date < 0 else f"{parsed_date} AD"
        print(f"  {year_str}: {info['date_type']} - {info['original']} (Line {info['line_num']})")
    
    print("Latest dates:")
    for i, (parsed_date, info) in enumerate(all_dates_with_info[-10:]):
        year_str = f"{abs(parsed_date)} BC" if parsed_date < 0 else f"{parsed_date} AD"
        print(f"  {year_str}: {info['date_type']} - {info['original']} (Line {info['line_num']})")

if __name__ == '__main__':
    main()