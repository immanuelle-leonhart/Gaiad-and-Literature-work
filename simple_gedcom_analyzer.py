#!/usr/bin/env python3
"""
Simple GEDCOM Analyzer for Trimming Analysis
Uses basic text processing to avoid encoding issues
"""

import re
from collections import defaultdict

def analyze_gedcom_simple(file_path):
    """Simple analysis focusing on key metrics"""
    print(f"Analyzing GEDCOM file: {file_path}")
    
    total_individuals = 0
    birth_years = []
    identifier_counts = defaultdict(int)
    post_1200_stats = defaultdict(int)
    
    try:
        with open(file_path, 'r', encoding='latin1') as f:  # More permissive encoding
            current_person_birth_year = None
            current_person_has_geni = False
            current_person_has_wikidata = False
            in_individual = False
            line_count = 0
            
            for line in f:
                line_count += 1
                if line_count % 200000 == 0:
                    print(f"  Processed {line_count:,} lines...")
                
                line = line.strip()
                if not line:
                    continue
                
                # Check for individual record start
                if line.startswith('0 ') and ' INDI ' in line:
                    # Process previous individual
                    if in_individual:
                        total_individuals += 1
                        if current_person_birth_year and current_person_birth_year >= 1200:
                            post_1200_stats['total'] += 1
                            if current_person_has_geni:
                                post_1200_stats['with_geni'] += 1
                            if current_person_has_wikidata:
                                post_1200_stats['with_wikidata'] += 1
                        
                        if current_person_has_geni and current_person_has_wikidata:
                            identifier_counts['both'] += 1
                        elif current_person_has_geni:
                            identifier_counts['geni_only'] += 1
                        elif current_person_has_wikidata:
                            identifier_counts['wikidata_only'] += 1
                        else:
                            identifier_counts['none'] += 1
                    
                    # Reset for new individual
                    in_individual = True
                    current_person_birth_year = None
                    current_person_has_geni = False
                    current_person_has_wikidata = False
                
                elif in_individual:
                    # Look for birth date
                    if line.startswith('2 DATE '):
                        date_str = line[7:]
                        # Simple year extraction
                        year_match = re.search(r'\b(\d{4})\b', date_str)
                        if year_match:
                            year = int(year_match.group(1))
                            # Assume this is birth date if we don't have one yet
                            if current_person_birth_year is None:
                                current_person_birth_year = year
                                birth_years.append(year)
                    
                    # Look for identifiers in notes
                    elif line.startswith('1 NOTE ') or line.startswith('2 CONT '):
                        note_content = line[7:] if line.startswith('1 NOTE ') else line[7:]
                        if 'geni.com' in note_content.lower():
                            current_person_has_geni = True
                        elif 'wikidata.org' in note_content.lower():
                            current_person_has_wikidata = True
            
            # Process last individual
            if in_individual:
                total_individuals += 1
                if current_person_birth_year and current_person_birth_year >= 1200:
                    post_1200_stats['total'] += 1
                    if current_person_has_geni:
                        post_1200_stats['with_geni'] += 1
                    if current_person_has_wikidata:
                        post_1200_stats['with_wikidata'] += 1
                
                if current_person_has_geni and current_person_has_wikidata:
                    identifier_counts['both'] += 1
                elif current_person_has_geni:
                    identifier_counts['geni_only'] += 1
                elif current_person_has_wikidata:
                    identifier_counts['wikidata_only'] += 1
                else:
                    identifier_counts['none'] += 1
    
    except Exception as e:
        print(f"Error reading file: {e}")
        return None
    
    # Analysis
    birth_years = [y for y in birth_years if y > 0]  # Filter out invalid years
    
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
    
    # Report
    print("\n" + "="*60)
    print("GEDCOM TRIMMING ANALYSIS REPORT")
    print("="*60)
    
    print(f"\nTotal individuals: {total_individuals:,}")
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
    print(f"  People born after 1200 CE: {post_1200_stats['total']:,}")
    print(f"  Post-1200 with GENI identifiers: {post_1200_stats['with_geni']:,}")
    print(f"  Post-1200 with Wikidata identifiers: {post_1200_stats['with_wikidata']:,}")
    
    potential_savings = (post_1200_stats['total'] / total_individuals * 100) if total_individuals else 0
    conservative_removal = post_1200_stats['total'] - post_1200_stats['with_geni']
    conservative_savings = (conservative_removal / total_individuals * 100) if total_individuals else 0
    
    print(f"  Potential file size reduction (all post-1200): {potential_savings:.1f}%")
    print(f"  Conservative reduction (post-1200 without GENI): {conservative_savings:.1f}%")
    
    print(f"\nTRIMMING RECOMMENDATIONS:")
    print(f"  1. CONSERVATIVE: Remove {conservative_removal:,} people born after 1200 CE without GENI identifiers")
    print(f"     This preserves all GENI-linked people (more stable identifiers)")
    print(f"     Estimated file size reduction: {conservative_savings:.1f}%")
    print(f"  2. MODERATE: Keep only people with Wikidata OR born before 1200 CE")
    print(f"  3. AGGRESSIVE: Remove all people born after 1200 CE")
    print(f"     Estimated file size reduction: {potential_savings:.1f}%")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python simple_gedcom_analyzer.py <gedcom_file>")
        sys.exit(1)
    
    analyze_gedcom_simple(sys.argv[1])