#!/usr/bin/env python3
"""
Analyze the date standardization issues based on the logs and analysis files.
Focus on what went wrong and what data was lost.
"""

import csv
import re
from collections import Counter, defaultdict

def analyze_standardization_log():
    """Analyze the date standardization log for patterns."""
    log_file = r"C:\Users\Immanuelle\Documents\Github\Gaiad-Genealogy\date_standardization_log.csv"
    
    changes = {
        'mya_to_bc': 0,
        'bc_format_fixes': 0,
        'dash_fixes': 0,
        'parenthetical_fixes': 0,
        'suspicious_changes': []
    }
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            
            for row in reader:
                if len(row) < 2:
                    continue
                    
                line_num = row[0]
                description = row[1]
                
                if 'Converted MYA to BC' in description:
                    changes['mya_to_bc'] += 1
                elif 'Standardized BC format' in description:
                    changes['bc_format_fixes'] += 1
                elif 'Fixed dash in BC date' in description:
                    changes['dash_fixes'] += 1
                elif 'Fixed parenthetical BC' in description:
                    changes['parenthetical_fixes'] += 1
                
                # Look for suspicious conversions
                if '1[5-9]\\d\\d|20\\d\\d' in description or 'BC' in description:
                    # Extract the actual change
                    match = re.search(r"'([^']+)' -> '([^']+)'", description)
                    if match:
                        old_val, new_val = match.groups()
                        # Check if this looks like a recent year incorrectly marked BC
                        if 'BC' in new_val:
                            year_match = re.search(r'(\d{4})', new_val)
                            if year_match:
                                year = int(year_match.group(1))
                                if 1500 <= year <= 2024:
                                    changes['suspicious_changes'].append({
                                        'line': line_num,
                                        'old': old_val,
                                        'new': new_val,
                                        'year': year,
                                        'reason': 'Recent year marked as BC'
                                    })
    
    except Exception as e:
        print(f"Error reading standardization log: {e}")
        return changes
    
    return changes

def analyze_comprehensive_analysis():
    """Analyze the comprehensive date analysis for patterns."""
    analysis_file = r"C:\Users\Immanuelle\Documents\Github\Gaiad-Genealogy\comprehensive_date_analysis.csv"
    
    date_stats = {
        'total_entries': 0,
        'bc_dates': 0,
        'ad_dates': 0,
        'extreme_bc': 0,
        'recent_years': 0,
        'patterns': Counter()
    }
    
    try:
        with open(analysis_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            
            for row in reader:
                if len(row) < 4:
                    continue
                
                category = row[0]
                date_pattern = row[1]
                count = int(row[2])
                needs_std = row[3]
                
                date_stats['total_entries'] += count
                date_stats['patterns'][category] += count
                
                if 'bc' in category.lower() or 'BC' in date_pattern:
                    date_stats['bc_dates'] += count
                    
                    # Check for extreme BC dates
                    bc_match = re.search(r'(\d+)\s*BC', date_pattern)
                    if bc_match:
                        year = int(bc_match.group(1))
                        if year > 10000:
                            date_stats['extreme_bc'] += count
                
                if 'ad' in category.lower() or ('BC' not in date_pattern and re.search(r'\b(1[5-9]\d\d|20\d\d)\b', date_pattern)):
                    date_stats['ad_dates'] += count
                    
                    # Check for recent years
                    year_match = re.search(r'\b(1[5-9]\d\d|20\d\d)\b', date_pattern)
                    if year_match:
                        date_stats['recent_years'] += count
    
    except Exception as e:
        print(f"Error reading comprehensive analysis: {e}")
        return date_stats
    
    return date_stats

def main():
    print("GEDCOM Date Standardization Issue Analysis")
    print("=" * 50)
    
    print("\n1. Analyzing standardization log...")
    log_analysis = analyze_standardization_log()
    
    print(f"Changes made:")
    print(f"  - MYA to BC conversions: {log_analysis['mya_to_bc']}")
    print(f"  - BC format fixes: {log_analysis['bc_format_fixes']}")
    print(f"  - Dash fixes: {log_analysis['dash_fixes']}")
    print(f"  - Parenthetical fixes: {log_analysis['parenthetical_fixes']}")
    
    if log_analysis['suspicious_changes']:
        print(f"\nSUSPICIOUS CHANGES FOUND ({len(log_analysis['suspicious_changes'])}):")
        for change in log_analysis['suspicious_changes'][:10]:
            print(f"  Line {change['line']}: '{change['old']}' -> '{change['new']}' (Year: {change['year']})")
    
    print("\n2. Analyzing comprehensive date analysis...")
    date_stats = analyze_comprehensive_analysis()
    
    print(f"Date statistics:")
    print(f"  - Total date entries: {date_stats['total_entries']:,}")
    print(f"  - BC dates: {date_stats['bc_dates']:,}")
    print(f"  - AD dates: {date_stats['ad_dates']:,}")
    print(f"  - Extreme BC dates (>10k years): {date_stats['extreme_bc']:,}")
    print(f"  - Recent years (1500+): {date_stats['recent_years']:,}")
    
    print("\nTop date patterns:")
    for pattern, count in date_stats['patterns'].most_common(10):
        print(f"  - {pattern}: {count:,}")
    
    print("\n" + "=" * 50)
    print("SUMMARY OF ISSUES:")
    print("=" * 50)
    
    if log_analysis['suspicious_changes']:
        print("❌ MAJOR ISSUE: Recent years were incorrectly marked as BC")
        print("   This suggests some AD dates were accidentally converted to BC")
        print("   This could explain missing genealogical records from recent periods")
    
    if date_stats['extreme_bc'] > 0:
        print(f"⚠️  WARNING: {date_stats['extreme_bc']:,} extremely ancient BC dates found")
        print("   These might be conversion errors from MYA (Million Years Ago)")
    
    if date_stats['recent_years'] < 100000:  # Estimate for normal genealogical data
        print("⚠️  WARNING: Fewer recent year records than expected")
        print("   Some genealogical data from 1500+ may have been lost")
    
    print("\nRECOMMENDATIONS:")
    print("1. Review the suspicious BC conversions manually")
    print("2. Check if Jewish genealogy records from Geni were in the 1500+ range")
    print("3. Consider reverting problematic conversions")
    print("4. Create a more conservative date standardization approach")

if __name__ == "__main__":
    main()