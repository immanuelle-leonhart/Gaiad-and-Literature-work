#!/usr/bin/env python3
"""
GEDCOM Date Pattern Analyzer
Analyzes all date patterns in a GEDCOM file and exports to CSV for review.
"""

import re
import sys
import csv
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Set

def extract_all_dates(gedcom_file: str) -> Dict[str, List[Tuple[str, str, int]]]:
    """
    Extract all date patterns from GEDCOM file.
    Returns dict mapping date_type -> [(original_date, context, line_num), ...]
    """
    date_patterns = defaultdict(list)
    current_individual = None
    current_context = None
    
    with open(gedcom_file, 'r', encoding='utf-8', errors='replace') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Track current individual
            if line.startswith('0 @') and ' INDI' in line:
                current_individual = line.split()[1]
            elif line.startswith('0 @') and ' FAM' in line:
                current_individual = line.split()[1]
            
            # Track context (BIRT, DEAT, MARR, etc.)
            if re.match(r'^1 (BIRT|DEAT|MARR|DIV|BAPM|CHR|BURI|EVEN)', line):
                current_context = line.split()[1]
            elif line.startswith('1 '):
                current_context = None
            
            # Extract dates
            if re.match(r'^2 DATE ', line):
                date_str = line[7:].strip()  # Remove "2 DATE "
                if date_str:
                    context_info = f"{current_individual or 'Unknown'}:{current_context or 'Unknown'}"
                    date_patterns[date_str].append((date_str, context_info, line_num))
    
    return date_patterns

def categorize_date_patterns(date_patterns: Dict[str, List]) -> Dict[str, List[Tuple[str, int]]]:
    """Categorize dates by their format patterns."""
    categories = {
        'standard_ad': [],           # 1066, JAN 1066, 15 JAN 1066
        'standard_bc': [],           # 1066 BC, JAN 1066 BC, 15 JAN 1066 BC
        'non_standard_bc': [],       # Various BC formats
        'mya_dates': [],             # Million years ago
        'approximate': [],           # ABT, CAL, EST dates
        'range_dates': [],           # BET...AND, AFT, BEF
        'partial_dates': [],         # Just year, just month/year
        'modern_dates': [],          # Recent dates (1800+)
        'problematic': [],           # Unparseable or strange formats
        'empty_or_invalid': []       # Empty or clearly invalid
    }
    
    for date_str, occurrences in date_patterns.items():
        count = len(occurrences)
        
        if not date_str or date_str.isspace():
            categories['empty_or_invalid'].append((date_str, count))
            continue
            
        date_upper = date_str.upper()
        
        # MYA dates
        if 'MYA' in date_upper:
            categories['mya_dates'].append((date_str, count))
        # Approximate dates
        elif any(prefix in date_upper for prefix in ['ABT', 'CAL', 'EST', 'CIRCA', 'ABOUT']):
            categories['approximate'].append((date_str, count))
        # Range dates
        elif any(word in date_upper for word in ['BET', 'AND', 'AFT', 'BEF', 'FROM', 'TO']):
            categories['range_dates'].append((date_str, count))
        # BC dates - various formats
        elif any(bc_marker in date_upper for bc_marker in ['BC', 'B.C.', 'BCE', 'B.C.E.']):
            # Check if it follows standard format
            standard_bc_pattern = re.match(r'^(\d{1,2}\s+)?([A-Z]{3}\s+)?\d{1,4}\s+B\.?C\.?E?$', date_upper)
            if standard_bc_pattern:
                categories['standard_bc'].append((date_str, count))
            else:
                categories['non_standard_bc'].append((date_str, count))
        # Modern dates (likely AD)
        elif re.search(r'\b(1[8-9]\d{2}|20\d{2})\b', date_str):
            categories['modern_dates'].append((date_str, count))
        # Standard AD dates
        elif re.match(r'^(\d{1,2}\s+)?([A-Z]{3}\s+)?\d{1,4}$', date_upper):
            categories['standard_ad'].append((date_str, count))
        # Partial dates (just year, month/year)
        elif re.match(r'^\d{1,4}$', date_str) or re.match(r'^[A-Z]{3}\s+\d{1,4}$', date_upper):
            categories['partial_dates'].append((date_str, count))
        else:
            categories['problematic'].append((date_str, count))
    
    return categories

def analyze_bc_formats(non_standard_bc_dates: List[Tuple[str, int]]) -> Dict[str, int]:
    """Analyze different BC format patterns."""
    bc_patterns = defaultdict(int)
    
    for date_str, count in non_standard_bc_dates:
        date_upper = date_str.upper()
        
        if 'B.C.E.' in date_upper:
            bc_patterns['B.C.E. format'] += count
        elif 'BCE' in date_upper:
            bc_patterns['BCE format'] += count
        elif 'B.C.' in date_upper:
            bc_patterns['B.C. format'] += count
        elif ' BC' in date_upper:
            bc_patterns['BC format'] += count
        else:
            bc_patterns['Other BC format'] += count
    
    return bc_patterns

def export_to_csv(categories: Dict[str, List], output_file: str):
    """Export analysis results to CSV."""
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Category', 'Date_Pattern', 'Occurrence_Count', 'Needs_Standardization'])
        
        for category, date_list in categories.items():
            needs_standardization = category in ['non_standard_bc', 'problematic', 'empty_or_invalid']
            
            # Sort by occurrence count (descending)
            sorted_dates = sorted(date_list, key=lambda x: x[1], reverse=True)
            
            for date_pattern, count in sorted_dates:
                writer.writerow([category, date_pattern, count, 'YES' if needs_standardization else 'NO'])

def main():
    if len(sys.argv) != 3:
        print("Usage: python gedcom_date_analyzer.py <input_gedcom> <output_csv>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    print(f"Analyzing dates in {input_file}...")
    
    # Extract all dates
    date_patterns = extract_all_dates(input_file)
    print(f"Found {len(date_patterns)} unique date patterns")
    
    # Categorize dates
    categories = categorize_date_patterns(date_patterns)
    
    # Print summary
    print("\n=== DATE PATTERN SUMMARY ===")
    for category, date_list in categories.items():
        if date_list:
            total_occurrences = sum(count for _, count in date_list)
            print(f"{category:20}: {len(date_list):5} patterns, {total_occurrences:6} total occurrences")
    
    # Analyze BC formats specifically
    if categories['non_standard_bc']:
        print("\n=== NON-STANDARD BC FORMAT ANALYSIS ===")
        bc_patterns = analyze_bc_formats(categories['non_standard_bc'])
        for pattern, count in bc_patterns.items():
            print(f"{pattern:20}: {count:6} occurrences")
    
    # Export to CSV
    export_to_csv(categories, output_file)
    print(f"\nDetailed analysis exported to {output_file}")
    
    # Show most problematic dates
    if categories['problematic']:
        print("\n=== TOP PROBLEMATIC DATES (first 10) ===")
        sorted_problematic = sorted(categories['problematic'], key=lambda x: x[1], reverse=True)
        for date_pattern, count in sorted_problematic[:10]:
            print(f"{count:4}x: '{date_pattern}'")

if __name__ == "__main__":
    main()