#!/usr/bin/env python3
"""
GEDCOM Trimming Analyzer
Analyzes a GEDCOM file to provide insights for potential trimming strategies:
- People born after 1200 CE
- People with GENI vs Wikidata identifiers
- Medieval European lineages that may be excessive
- Size distribution by time period and region
"""

import re
from collections import defaultdict, Counter
from datetime import datetime

def parse_gedcom_date(date_str):
    """Parse GEDCOM date string and return year if possible"""
    if not date_str:
        return None
    
    # Remove 'ABT' (about), 'EST' (estimated), etc.
    date_str = re.sub(r'^(ABT|EST|CAL|AFT|BEF)\s+', '', date_str)
    
    # Handle BC dates
    bc_match = re.search(r'(\d+)\s+BC$', date_str)
    if bc_match:
        return -int(bc_match.group(1))
    
    # Try to extract year (4 digits)
    year_match = re.search(r'\b(\d{4})\b', date_str)
    if year_match:
        return int(year_match.group(1))
    
    return None

def extract_identifier_type(note):
    """Extract identifier type from NOTE field"""
    if not note:
        return None
    
    if 'geni.com' in note.lower():
        return 'GENI'
    elif 'wikidata.org' in note.lower():
        return 'WIKIDATA'
    
    return None

def analyze_gedcom(file_path):
    """Analyze GEDCOM file for trimming insights"""
    print(f"Analyzing GEDCOM file: {file_path}")
    
    individuals = []
    current_person = {}
    
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        for line_num, line in enumerate(f, 1):
            if line_num % 100000 == 0:
                print(f"  Processed {line_num:,} lines...")
            
            line = line.strip()
            if not line:
                continue
            
            parts = line.split(' ', 2)
            try:
                level = int(parts[0])
            except ValueError:
                continue  # Skip malformed lines
            tag = parts[1]
            value = parts[2] if len(parts) > 2 else ""
            
            if level == 0 and tag == "INDI":
                # Save previous person
                if current_person:
                    individuals.append(current_person)
                # Start new person
                current_person = {'id': value, 'birth_year': None, 'death_year': None, 'names': [], 'notes': [], 'identifiers': []}
            
            elif level == 1 and current_person:
                if tag == "NAME":
                    current_person['names'].append(value)
                elif tag == "NOTE":
                    current_person['notes'].append(value)
                elif tag == "BIRT":
                    current_person['processing_birth'] = True
                elif tag == "DEAT":
                    current_person['processing_death'] = True
                elif tag == "REFN":
                    current_person['identifiers'].append(value)
            
            elif level == 2 and current_person:
                if tag == "DATE" and current_person.get('processing_birth'):
                    current_person['birth_year'] = parse_gedcom_date(value)
                    current_person['processing_birth'] = False
                elif tag == "DATE" and current_person.get('processing_death'):
                    current_person['death_year'] = parse_gedcom_date(value)
                    current_person['processing_death'] = False
    
    # Save last person
    if current_person:
        individuals.append(current_person)
    
    print(f"Found {len(individuals):,} individuals")
    
    # Analysis
    birth_years = [p['birth_year'] for p in individuals if p['birth_year'] is not None]
    post_1200_births = [y for y in birth_years if y >= 1200]
    
    # Identifier analysis
    identifier_counts = defaultdict(int)
    for person in individuals:
        has_geni = False
        has_wikidata = False
        
        for note in person['notes']:
            id_type = extract_identifier_type(note)
            if id_type == 'GENI':
                has_geni = True
            elif id_type == 'WIKIDATA':
                has_wikidata = True
        
        if has_geni and has_wikidata:
            identifier_counts['both'] += 1
        elif has_geni:
            identifier_counts['geni_only'] += 1
        elif has_wikidata:
            identifier_counts['wikidata_only'] += 1
        else:
            identifier_counts['none'] += 1
    
    # Time period analysis
    periods = {
        'Ancient (before 0)': len([y for y in birth_years if y < 0]),
        'Early CE (0-500)': len([y for y in birth_years if 0 <= y < 500]),
        'Medieval Early (500-1000)': len([y for y in birth_years if 500 <= y < 1000]),
        'Medieval High (1000-1200)': len([y for y in birth_years if 1000 <= y < 1200]),
        'Medieval Late (1200-1500)': len([y for y in birth_years if 1200 <= y < 1500]),
        'Early Modern (1500-1800)': len([y for y in birth_years if 1500 <= y < 1800]),
        'Modern (1800+)': len([y for y in birth_years if y >= 1800])
    }
    
    # Potential savings analysis
    post_1200_with_wikidata = 0
    post_1200_with_geni = 0
    post_1200_total = 0
    
    for person in individuals:
        if person['birth_year'] and person['birth_year'] >= 1200:
            post_1200_total += 1
            has_geni = any('geni.com' in note.lower() for note in person['notes'])
            has_wikidata = any('wikidata.org' in note.lower() for note in person['notes'])
            
            if has_geni:
                post_1200_with_geni += 1
            if has_wikidata:
                post_1200_with_wikidata += 1
    
    # Report
    print("\n" + "="*60)
    print("GEDCOM TRIMMING ANALYSIS REPORT")
    print("="*60)
    
    print(f"\nTotal individuals: {len(individuals):,}")
    print(f"Individuals with birth years: {len(birth_years):,}")
    
    print(f"\nTIME PERIOD DISTRIBUTION:")
    for period, count in periods.items():
        percentage = (count / len(birth_years) * 100) if birth_years else 0
        print(f"  {period}: {count:,} ({percentage:.1f}%)")
    
    print(f"\nIDENTIFIER ANALYSIS:")
    total_with_ids = sum(identifier_counts.values())
    for id_type, count in identifier_counts.items():
        percentage = (count / total_with_ids * 100) if total_with_ids else 0
        print(f"  {id_type}: {count:,} ({percentage:.1f}%)")
    
    print(f"\n1200 CE CUTOFF ANALYSIS:")
    print(f"  People born after 1200 CE: {post_1200_total:,}")
    print(f"  Post-1200 with GENI identifiers: {post_1200_with_geni:,}")
    print(f"  Post-1200 with Wikidata identifiers: {post_1200_with_wikidata:,}")
    potential_savings = (post_1200_total / len(individuals) * 100) if individuals else 0
    print(f"  Potential file size reduction: {potential_savings:.1f}%")
    
    print(f"\nTRIMMING RECOMMENDATIONS:")
    print(f"  1. Remove people born after 1200 CE without GENI identifiers")
    print(f"     This could remove {post_1200_total - post_1200_with_geni:,} people")
    print(f"  2. Keep all people with GENI identifiers (more fragile)")
    print(f"  3. Consider keeping Wikidata-only people born before 1200 CE")
    
    return {
        'total_individuals': len(individuals),
        'post_1200_total': post_1200_total,
        'post_1200_with_geni': post_1200_with_geni,
        'identifier_counts': dict(identifier_counts),
        'periods': periods
    }

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python gedcom_trimming_analyzer.py <gedcom_file>")
        sys.exit(1)
    
    analyze_gedcom(sys.argv[1])