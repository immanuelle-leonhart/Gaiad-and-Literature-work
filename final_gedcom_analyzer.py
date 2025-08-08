#!/usr/bin/env python3
"""
Final GEDCOM Analyzer - Matches actual GEDCOM structure
"""

import re
from collections import defaultdict

def analyze_gedcom_final(file_path):
    """Analyze GEDCOM file with correct structure matching"""
    print(f"Analyzing GEDCOM file: {file_path}")
    
    total_individuals = 0
    birth_years = []
    identifier_counts = defaultdict(int)
    post_1200_stats = defaultdict(int)
    
    try:
        with open(file_path, 'r', encoding='latin1') as f:
            current_person_birth_year = None
            current_person_has_geni = False
            current_person_has_wikidata = False
            in_individual = False
            in_birth_event = False
            line_count = 0
            
            for line in f:
                line_count += 1
                if line_count % 200000 == 0:
                    print(f"  Processed {line_count:,} lines...")
                
                line = line.strip()
                if not line:
                    continue
                
                # Check for individual record start (format: 0 @I123@ INDI)
                if re.match(r'^0\s+@I\d+@\s+INDI', line):
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
                    in_birth_event = False
                
                elif in_individual:
                    # Check for birth event
                    if line.startswith('1 BIRT'):
                        in_birth_event = True
                    elif line.startswith('1 ') and not line.startswith('1 BIRT'):
                        in_birth_event = False
                    
                    # Look for birth date within birth event
                    elif in_birth_event and line.startswith('2 DATE '):
                        date_str = line[7:]
                        # Extract year, handling BC dates and various formats
                        if ' BC' in date_str:
                            year_match = re.search(r'(\d+)\s+BC', date_str)
                            if year_match:
                                year = -int(year_match.group(1))
                                current_person_birth_year = year
                                birth_years.append(year)
                        else:
                            year_match = re.search(r'\b(\d{4})\b', date_str)
                            if year_match:
                                year = int(year_match.group(1))
                                current_person_birth_year = year
                                birth_years.append(year)
                    
                    # Look for identifiers in notes
                    elif (line.startswith('1 NOTE ') or 
                          line.startswith('2 CONT ') or 
                          line.startswith('1 REFN ') or
                          line.startswith('1 _GENI_ID') or
                          line.startswith('1 _WIKIDATA_ID')):
                        
                        note_content = line.split(' ', 2)[2] if len(line.split(' ', 2)) > 2 else ""
                        
                        if ('geni.com' in note_content.lower() or 
                            'geni.com' in line.lower() or 
                            '_geni_id' in line.lower()):
                            current_person_has_geni = True
                        elif ('wikidata.org' in note_content.lower() or 
                              'wikidata' in line.lower() or 
                              line.startswith('1 REFN Q')):  # Wikidata QIDs as REFN
                            current_person_has_wikidata = True
                
                # End of file or new record type
                elif in_individual and line.startswith('0 '):
                    in_individual = False
            
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
    
    # Filter out clearly invalid years (too high/low)
    birth_years = [y for y in birth_years if -5000 <= y <= 2030]
    
    # Time period analysis
    periods = {
        'Ancient (before 0 CE)': len([y for y in birth_years if y < 0]),
        'Early CE (0-500)': len([y for y in birth_years if 0 <= y < 500]),
        'Medieval Early (500-1000)': len([y for y in birth_years if 500 <= y < 1000]),
        'Medieval High (1000-1200)': len([y for y in birth_years if 1000 <= y < 1200]),
        'Medieval Late (1200-1500)': len([y for y in birth_years if 1200 <= y < 1500]),
        'Early Modern (1500-1800)': len([y for y in birth_years if 1500 <= y < 1800]),
        'Modern (1800+)': len([y for y in birth_years if y >= 1800])
    }
    
    # Report
    print("\n" + "="*70)
    print("GAIAD GEDCOM TRIMMING ANALYSIS REPORT")
    print("="*70)
    
    print(f"\nFile size: 2.1 million lines")
    print(f"Total individuals: {total_individuals:,}")
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
    
    print(f"  Potential file reduction (all post-1200): {potential_savings:.1f}%")
    print(f"  Conservative reduction (post-1200 without GENI): {conservative_savings:.1f}%")
    
    print(f"\nTRIMMING STRATEGY RECOMMENDATIONS:")
    print(f"  ★ PREFERRED: Remove {conservative_removal:,} people born after 1200 CE")
    print(f"    who lack GENI identifiers (preserves stable GENI links)")
    print(f"    → Estimated file size reduction: {conservative_savings:.1f}%")
    print(f"  ")
    print(f"  • ALTERNATIVE: Use birth year 1300 or 1400 as cutoff instead")
    print(f"  • KEEP: All people with GENI identifiers (your priority)")
    print(f"  • KEEP: All pre-1200 CE people (essential antiquity)")
    
    # Create a simple trimming script proposal
    if conservative_removal > 0:
        print(f"\nNEXT STEPS:")
        print(f"  1. Create backup of current Gaiad.ged file")
        print(f"  2. Run trimming script to remove {conservative_removal:,} people")
        print(f"  3. Verify essential lineages are preserved")
        print(f"  4. Test file functionality")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python final_gedcom_analyzer.py <gedcom_file>")
        sys.exit(1)
    
    analyze_gedcom_final(sys.argv[1])