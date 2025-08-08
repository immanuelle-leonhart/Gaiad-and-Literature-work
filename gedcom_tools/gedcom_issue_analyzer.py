#!/usr/bin/env python3
"""
Analyze GEDCOM files for date standardization issues and missing records.
Specifically looks for:
1. BC/AD conversion problems
2. Lost Jewish genealogy records from Geni
3. Date format inconsistencies
4. Missing persons that were in original but not in trimmed versions
"""

import sys
import re
from collections import defaultdict, Counter

def parse_gedcom_individuals(file_path):
    """Parse GEDCOM file and extract individual records with dates."""
    individuals = {}
    current_individual = None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Start of individual record
                if line.startswith('0 @I') and line.endswith('@ INDI'):
                    current_individual = line.split()[1].strip('@')
                    individuals[current_individual] = {
                        'name': '',
                        'birth_date': '',
                        'death_date': '',
                        'notes': [],
                        'sources': [],
                        'line_number': line_num
                    }
                
                # Name
                elif current_individual and line.startswith('1 NAME'):
                    individuals[current_individual]['name'] = line[7:].strip()
                
                # Birth date
                elif current_individual and line.startswith('2 DATE') and 'BIRT' in str(individuals[current_individual]):
                    individuals[current_individual]['birth_date'] = line[7:].strip()
                
                # Death date  
                elif current_individual and line.startswith('2 DATE') and 'DEAT' in str(individuals[current_individual]):
                    individuals[current_individual]['death_date'] = line[7:].strip()
                
                # Notes (might contain Geni info)
                elif current_individual and line.startswith('1 NOTE'):
                    individuals[current_individual]['notes'].append(line[7:].strip())
                elif current_individual and line.startswith('2 CONT'):
                    if individuals[current_individual]['notes']:
                        individuals[current_individual]['notes'][-1] += ' ' + line[7:].strip()
                
                # Sources
                elif current_individual and line.startswith('1 SOUR'):
                    individuals[current_individual]['sources'].append(line[7:].strip())
    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {}
    
    return individuals

def analyze_date_issues(individuals):
    """Analyze date format issues."""
    issues = {
        'suspicious_bc_ad': [],
        'malformed_dates': [],
        'extreme_dates': [],
        'inconsistent_formats': []
    }
    
    for person_id, person in individuals.items():
        name = person['name']
        birth = person['birth_date']
        death = person['death_date']
        
        for date_field, date_value in [('birth', birth), ('death', death)]:
            if not date_value:
                continue
                
            # Check for suspicious BC/AD conversions
            if 'BC' in date_value:
                # Look for dates that might have been accidentally converted
                if re.search(r'\b(1[5-9]\d\d|20\d\d)\s*BC', date_value):
                    issues['suspicious_bc_ad'].append({
                        'person': name,
                        'id': person_id,
                        'field': date_field,
                        'date': date_value,
                        'reason': 'Recent year marked as BC'
                    })
            
            # Check for extreme dates
            bc_match = re.search(r'(\d+)\s*BC', date_value)
            if bc_match and int(bc_match.group(1)) > 10000:
                issues['extreme_dates'].append({
                    'person': name,
                    'id': person_id,
                    'field': date_field,
                    'date': date_value,
                    'reason': 'Extremely ancient BC date'
                })
            
            # Check for malformed dates
            if re.search(r'BC.*AD|AD.*BC', date_value):
                issues['malformed_dates'].append({
                    'person': name,
                    'id': person_id,
                    'field': date_field,
                    'date': date_value,
                    'reason': 'Contains both BC and AD'
                })
    
    return issues

def find_geni_records(individuals):
    """Find records that mention Geni as source."""
    geni_records = []
    
    for person_id, person in individuals.items():
        name = person['name']
        
        # Check notes for Geni references
        for note in person['notes']:
            if 'geni' in note.lower() or 'judaica' in note.lower():
                geni_records.append({
                    'person': name,
                    'id': person_id,
                    'note': note
                })
        
        # Check sources for Geni
        for source in person['sources']:
            if 'geni' in source.lower():
                geni_records.append({
                    'person': name,
                    'id': person_id,
                    'source': source
                })
    
    return geni_records

def compare_files(original_file, trimmed_file):
    """Compare original and trimmed files to find missing records."""
    print("Parsing original file...")
    original_individuals = parse_gedcom_individuals(original_file)
    print(f"Found {len(original_individuals)} individuals in original file")
    
    print("Parsing trimmed file...")
    trimmed_individuals = parse_gedcom_individuals(trimmed_file)
    print(f"Found {len(trimmed_individuals)} individuals in trimmed file")
    
    # Find missing individuals
    missing_ids = set(original_individuals.keys()) - set(trimmed_individuals.keys())
    print(f"Found {len(missing_ids)} missing individuals")
    
    # Analyze date issues in both files
    print("\nAnalyzing date issues in original file...")
    original_issues = analyze_date_issues(original_individuals)
    
    print("Analyzing date issues in trimmed file...")
    trimmed_issues = analyze_date_issues(trimmed_individuals)
    
    # Find Geni records
    print("Finding Geni records in original file...")
    original_geni = find_geni_records(original_individuals)
    
    print("Finding Geni records in trimmed file...")
    trimmed_geni = find_geni_records(trimmed_individuals)
    
    return {
        'original_count': len(original_individuals),
        'trimmed_count': len(trimmed_individuals),
        'missing_count': len(missing_ids),
        'missing_individuals': [original_individuals[pid] for pid in list(missing_ids)[:100]],  # First 100
        'original_issues': original_issues,
        'trimmed_issues': trimmed_issues,
        'original_geni': original_geni,
        'trimmed_geni': trimmed_geni
    }

def main():
    if len(sys.argv) != 3:
        print("Usage: python gedcom_issue_analyzer.py <original_file> <trimmed_file>")
        sys.exit(1)
    
    original_file = sys.argv[1]
    trimmed_file = sys.argv[2]
    
    print(f"Comparing {original_file} vs {trimmed_file}")
    
    results = compare_files(original_file, trimmed_file)
    
    print("\n" + "="*80)
    print("ANALYSIS RESULTS")
    print("="*80)
    
    print(f"Original file: {results['original_count']} individuals")
    print(f"Trimmed file: {results['trimmed_count']} individuals") 
    print(f"Missing individuals: {results['missing_count']}")
    
    if results['missing_individuals']:
        print(f"\nFirst {len(results['missing_individuals'])} missing individuals:")
        for person in results['missing_individuals']:
            print(f"  - {person['name']} (ID: {person.get('id', 'unknown')})")
            if person['birth_date']:
                print(f"    Birth: {person['birth_date']}")
            if person['death_date']:
                print(f"    Death: {person['death_date']}")
    
    print(f"\nSuspicious BC/AD dates in original: {len(results['original_issues']['suspicious_bc_ad'])}")
    for issue in results['original_issues']['suspicious_bc_ad'][:10]:
        print(f"  - {issue['person']}: {issue['date']} ({issue['reason']})")
    
    print(f"\nSuspicious BC/AD dates in trimmed: {len(results['trimmed_issues']['suspicious_bc_ad'])}")
    for issue in results['trimmed_issues']['suspicious_bc_ad'][:10]:
        print(f"  - {issue['person']}: {issue['date']} ({issue['reason']})")
    
    print(f"\nGeni records in original: {len(results['original_geni'])}")
    print(f"Geni records in trimmed: {len(results['trimmed_geni'])}")
    print(f"Lost Geni records: {len(results['original_geni']) - len(results['trimmed_geni'])}")
    
    if len(results['original_geni']) > len(results['trimmed_geni']):
        print("\nSome Geni records appear to have been lost during trimming!")

if __name__ == "__main__":
    main()