#!/usr/bin/env python3
"""
Analyze missing Jewish genealogy records from Geni that should have been preserved.
Focus on records that:
1. Extend into the 1500s 
2. Lack Wikidata links (making them notable enough to keep)
3. May have been incorrectly removed during date standardization or trimming
"""

import re
from collections import defaultdict, Counter

def analyze_jewish_records_streaming(file_path):
    """
    Analyze GEDCOM file for Jewish/Geni records using streaming approach.
    Look for patterns that indicate Jewish genealogy from Geni.
    """
    
    jewish_indicators = [
        r'geni\.com',
        r'judaica',
        r'jewish',
        r'rabbi',
        r'cohen',
        r'levy',
        r'israel',
        r'jerusalem',
        r'hebrew',
        r'synagogue',
        r'torah',
        r'talmud',
        r'ashkenazi',
        r'sephardi',
        r'yeshiva'
    ]
    
    wikidata_indicators = [
        r'wikidata',
        r'Q\d+',  # Wikidata Q-IDs
        r'wikipedia'
    ]
    
    results = {
        'jewish_records': [],
        'date_issues': [],
        'wikidata_status': {'has_wikidata': 0, 'no_wikidata': 0},
        'date_ranges': Counter(),
        'suspicious_dates': []
    }
    
    current_individual = None
    individual_data = {}
    line_count = 0
    
    print(f"Analyzing {file_path}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                line_count += 1
                if line_count % 100000 == 0:
                    print(f"Processed {line_count:,} lines, found {len(results['jewish_records'])} Jewish records...")
                
                line = line.strip()
                
                # Start of individual record
                if line.startswith('0 @I') and line.endswith('@ INDI'):
                    # Process previous individual if it was Jewish
                    if current_individual and individual_data.get('is_jewish'):
                        results['jewish_records'].append(individual_data.copy())
                        
                        # Check date ranges
                        for date_field in ['birth_date', 'death_date']:
                            date_val = individual_data.get(date_field, '')
                            if date_val:
                                year_match = re.search(r'\b(1[5-9]\d\d)\b', date_val)
                                if year_match:
                                    year = int(year_match.group(1))
                                    results['date_ranges'][f"{year//50*50}s"] += 1
                                    
                                    # Check for suspicious date conversions
                                    if 'BC' in date_val and year >= 1500:
                                        results['suspicious_dates'].append({
                                            'name': individual_data.get('name', ''),
                                            'date_field': date_field,
                                            'date_value': date_val,
                                            'suspected_year': year
                                        })
                        
                        # Check Wikidata status
                        if individual_data.get('has_wikidata'):
                            results['wikidata_status']['has_wikidata'] += 1
                        else:
                            results['wikidata_status']['no_wikidata'] += 1
                    
                    # Start new individual
                    current_individual = line.split()[1].strip('@')
                    individual_data = {
                        'id': current_individual,
                        'name': '',
                        'birth_date': '',
                        'death_date': '',
                        'notes': [],
                        'sources': [],
                        'is_jewish': False,
                        'has_wikidata': False,
                        'line_number': line_num
                    }
                
                elif current_individual:
                    # Name
                    if line.startswith('1 NAME'):
                        individual_data['name'] = line[7:].strip()
                    
                    # Birth/Death events
                    elif line.startswith('1 BIRT'):
                        individual_data['in_birth'] = True
                    elif line.startswith('1 DEAT'):
                        individual_data['in_death'] = True
                    elif line.startswith('2 DATE'):
                        if individual_data.get('in_birth'):
                            individual_data['birth_date'] = line[7:].strip()
                            individual_data['in_birth'] = False
                        elif individual_data.get('in_death'):
                            individual_data['death_date'] = line[7:].strip()
                            individual_data['in_death'] = False
                    
                    # Notes and sources
                    elif line.startswith('1 NOTE'):
                        note = line[7:].strip()
                        individual_data['notes'].append(note)
                    elif line.startswith('2 CONT'):
                        if individual_data['notes']:
                            individual_data['notes'][-1] += ' ' + line[7:].strip()
                    elif line.startswith('1 SOUR'):
                        individual_data['sources'].append(line[7:].strip())
                    
                    # Check for Jewish indicators in any field
                    line_lower = line.lower()
                    for indicator in jewish_indicators:
                        if re.search(indicator, line_lower):
                            individual_data['is_jewish'] = True
                            break
                    
                    # Check for Wikidata indicators
                    for indicator in wikidata_indicators:
                        if re.search(indicator, line_lower):
                            individual_data['has_wikidata'] = True
                            break
    
    except Exception as e:
        print(f"Error processing file: {e}")
        return results
    
    # Process final individual
    if current_individual and individual_data.get('is_jewish'):
        results['jewish_records'].append(individual_data.copy())
    
    print(f"Completed analysis: {line_count:,} total lines processed")
    return results

def compare_jewish_records(original_file, trimmed_file):
    """Compare Jewish records between original and trimmed files."""
    
    print("Analyzing original file for Jewish records...")
    original_results = analyze_jewish_records_streaming(original_file)
    
    print("Analyzing trimmed file for Jewish records...")
    trimmed_results = analyze_jewish_records_streaming(trimmed_file)
    
    original_count = len(original_results['jewish_records'])
    trimmed_count = len(trimmed_results['jewish_records'])
    lost_count = original_count - trimmed_count
    
    print("\n" + "="*80)
    print("JEWISH GENEALOGY ANALYSIS RESULTS")
    print("="*80)
    
    print(f"Original file Jewish records: {original_count:,}")
    print(f"Trimmed file Jewish records: {trimmed_count:,}")
    print(f"Lost Jewish records: {lost_count:,}")
    
    if lost_count > 0:
        loss_percentage = (lost_count / original_count) * 100
        print(f"Loss percentage: {loss_percentage:.1f}%")
    
    print(f"\nWikidata status in original:")
    print(f"  - With Wikidata links: {original_results['wikidata_status']['has_wikidata']:,}")
    print(f"  - Without Wikidata links: {original_results['wikidata_status']['no_wikidata']:,}")
    
    print(f"\nWikidata status in trimmed:")
    print(f"  - With Wikidata links: {trimmed_results['wikidata_status']['has_wikidata']:,}")
    print(f"  - Without Wikidata links: {trimmed_results['wikidata_status']['no_wikidata']:,}")
    
    # Show date range distribution
    print(f"\nDate ranges in original file:")
    for date_range, count in sorted(original_results['date_ranges'].items()):
        print(f"  - {date_range}: {count:,}")
    
    print(f"\nDate ranges in trimmed file:")
    for date_range, count in sorted(trimmed_results['date_ranges'].items()):
        print(f"  - {date_range}: {count:,}")
    
    # Show suspicious date conversions
    if original_results['suspicious_dates']:
        print(f"\nSUSPICIOUS DATE CONVERSIONS in original ({len(original_results['suspicious_dates'])}):")
        for issue in original_results['suspicious_dates'][:10]:
            print(f"  - {issue['name']}: {issue['date_field']} = '{issue['date_value']}' (suspected year: {issue['suspected_year']})")
    
    if trimmed_results['suspicious_dates']:
        print(f"\nSUSPICIOUS DATE CONVERSIONS in trimmed ({len(trimmed_results['suspicious_dates'])}):")
        for issue in trimmed_results['suspicious_dates'][:10]:
            print(f"  - {issue['name']}: {issue['date_field']} = '{issue['date_value']}' (suspected year: {issue['suspected_year']})")
    
    # Analysis and recommendations
    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)
    
    wikidata_lost = original_results['wikidata_status']['no_wikidata'] - trimmed_results['wikidata_status']['no_wikidata']
    
    if wikidata_lost > 0:
        print(f"❌ CRITICAL: {wikidata_lost:,} Jewish records WITHOUT Wikidata links were lost!")
        print("   These should have been preserved according to the 'notable enough' rule.")
    
    if original_results['suspicious_dates'] or trimmed_results['suspicious_dates']:
        print("❌ CRITICAL: Suspicious date conversions found!")
        print("   Some 1500s dates may have been incorrectly marked as BC.")
    
    # Check for 1500s losses specifically
    original_1500s = sum(count for date_range, count in original_results['date_ranges'].items() 
                        if '1500' in date_range or '1550' in date_range)
    trimmed_1500s = sum(count for date_range, count in trimmed_results['date_ranges'].items() 
                       if '1500' in date_range or '1550' in date_range)
    
    if original_1500s > trimmed_1500s:
        print(f"❌ ISSUE: Lost {original_1500s - trimmed_1500s:,} Jewish records from 1500s period")
    
    return {
        'original': original_results,
        'trimmed': trimmed_results,
        'lost_count': lost_count,
        'wikidata_lost': wikidata_lost
    }

def main():
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python jewish_genealogy_analyzer.py <original_file> <trimmed_file>")
        sys.exit(1)
    
    original_file = sys.argv[1]
    trimmed_file = sys.argv[2]
    
    results = compare_jewish_records(original_file, trimmed_file)

if __name__ == "__main__":
    main()