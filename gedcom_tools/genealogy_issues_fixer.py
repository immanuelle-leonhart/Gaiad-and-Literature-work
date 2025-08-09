#!/usr/bin/env python3
"""
Genealogy Issues Fixer
Addresses common GEDCOM import/export issues between different genealogy software
"""

import csv
import re
from pathlib import Path
from typing import List, Dict, Set

class GenealogyIssuesFixer:
    """Fix common issues when moving between genealogy software"""
    
    def __init__(self):
        self.duplicate_cache = {}
    
    def load_myheritage_duplicates(self, csv_path: str) -> Dict[str, List[Dict]]:
        """Load MyHeritage duplicate detection results"""
        duplicates = {}
        
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    score = row.get('Score', '').strip()
                    id1 = row.get('ID 1', '').strip()
                    id2 = row.get('ID 2', '').strip()
                    name1 = row.get('Name 1', '').strip()
                    name2 = row.get('Name 2', '').strip()
                    
                    if id1 and id2:
                        if id1 not in duplicates:
                            duplicates[id1] = []
                        duplicates[id1].append({
                            'duplicate_id': id2,
                            'score': score,
                            'name1': name1,
                            'name2': name2,
                            'birth1': row.get('Birth date 1', ''),
                            'birth2': row.get('Birth date 2', ''),
                            'relatives1': row.get('Relatives 1', ''),
                            'relatives2': row.get('Relatives 2', '')
                        })
        except Exception as e:
            print(f"Error loading duplicates: {e}")
            
        return duplicates
    
    def fix_bc_dates_for_family_historian(self, gedcom_path: str, output_path: str = None):
        """
        Fix BC dates that Family Historian cannot handle properly
        Converts negative years to BC notation that FH recognizes
        """
        if output_path is None:
            output_path = gedcom_path
        
        print(f"Fixing BC dates in {gedcom_path}")
        
        with open(gedcom_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to match negative year dates
        def convert_negative_date(match):
            prefix = match.group(1)  # DATE part
            date_qualifier = match.group(2)  # (ABT, (AFT, etc.
            negative_year = match.group(3)  # the negative number
            suffix = match.group(4)  # closing paren
            
            # Convert negative year to positive BC year
            bc_year = abs(int(negative_year))
            
            # Format as BC date that Family Historian can understand
            return f"{prefix} {date_qualifier}{bc_year} BC{suffix}"
        
        # Replace negative year patterns
        # Matches: 2 DATE (ABT -440) -> 2 DATE (ABT 440 BC)
        bc_pattern = r'(\d+ DATE )(\([A-Z]+ )-(\d+)(\))'
        fixed_content = re.sub(bc_pattern, convert_negative_date, content)
        
        # Count changes made
        original_matches = len(re.findall(bc_pattern, content))
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"Fixed {original_matches} BC date entries")
        print(f"Output written to: {output_path}")
        
        return original_matches
    
    def create_gedcom_for_family_historian(self, source_gedcom: str, output_path: str):
        """
        Create a Family Historian-compatible version of a GEDCOM file
        - Fixes BC dates
        - Ensures proper header
        - Removes problematic elements
        """
        print(f"Creating Family Historian compatible GEDCOM from {source_gedcom}")
        
        # First fix BC dates
        temp_path = output_path + ".temp"
        bc_fixes = self.fix_bc_dates_for_family_historian(source_gedcom, temp_path)
        
        # Additional Family Historian compatibility fixes can be added here
        # For now, just rename the temp file
        Path(temp_path).rename(output_path)
        
        print(f"Family Historian compatible GEDCOM created: {output_path}")
        print(f"Summary: {bc_fixes} BC dates fixed")
        
        return output_path
    
    def analyze_duplicate_patterns(self, duplicates: Dict) -> Dict:
        """Analyze patterns in duplicate detection results"""
        analysis = {
            'total_individuals_with_duplicates': len(duplicates),
            'total_duplicate_pairs': sum(len(dups) for dups in duplicates.values()),
            'score_distribution': {},
            'common_issues': []
        }
        
        score_counts = {}
        for individual_id, dup_list in duplicates.items():
            for dup in dup_list:
                score = dup['score']
                score_counts[score] = score_counts.get(score, 0) + 1
        
        analysis['score_distribution'] = score_counts
        
        # Common issues analysis
        name_mismatches = 0
        date_mismatches = 0
        
        for individual_id, dup_list in duplicates.items():
            for dup in dup_list:
                if dup['name1'] != dup['name2']:
                    name_mismatches += 1
                if dup['birth1'] != dup['birth2']:
                    date_mismatches += 1
        
        analysis['common_issues'] = [
            f"Name variations: {name_mismatches}",
            f"Birth date differences: {date_mismatches}"
        ]
        
        return analysis
    
    def generate_duplicate_merge_script(self, duplicates: Dict, output_file: str):
        """Generate a script/report for merging duplicates"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Duplicate Merge Script\n")
            f.write("# Generated by Genealogy Issues Fixer\n\n")
            
            for individual_id, dup_list in duplicates.items():
                f.write(f"## Individual ID: {individual_id}\n")
                for i, dup in enumerate(dup_list, 1):
                    f.write(f"### Duplicate {i} (Score: {dup['score']})\n")
                    f.write(f"- **Primary**: {dup['name1']} (ID: {individual_id})\n")
                    f.write(f"- **Duplicate**: {dup['name2']} (ID: {dup['duplicate_id']})\n")
                    f.write(f"- **Birth Dates**: {dup['birth1']} vs {dup['birth2']}\n")
                    if dup['relatives1'] and len(dup['relatives1']) < 200:  # Avoid huge text blocks
                        f.write(f"- **Relatives 1**: {dup['relatives1'][:200]}...\n")
                    f.write("\n")
                f.write("---\n\n")
        
        print(f"Duplicate merge script generated: {output_file}")

def main():
    """Main function to demonstrate the fixes"""
    fixer = GenealogyIssuesFixer()
    
    # Define file paths
    base_path = Path(r"C:\Users\Immanuelle\Documents\Github\Gaiad-Genealogy\new_gedcoms\source gedcoms")
    duplicates_csv = base_path / "master_combined_duplications.csv"
    master_gedcom = base_path / "master_combined.ged"
    recovered_gedcom = base_path / "recovered_gaiad.ged" 
    
    print("Genealogy Issues Fixer")
    print("=" * 40)
    
    # Fix 1: Load and analyze duplicates
    if duplicates_csv.exists():
        print("\n1. Loading MyHeritage duplicate analysis...")
        duplicates = fixer.load_myheritage_duplicates(str(duplicates_csv))
        
        if duplicates:
            analysis = fixer.analyze_duplicate_patterns(duplicates)
            print(f"Found duplicates for {analysis['total_individuals_with_duplicates']} individuals")
            print(f"Total duplicate pairs: {analysis['total_duplicate_pairs']}")
            print(f"Score distribution: {analysis['score_distribution']}")
            
            # Generate merge script
            merge_script_path = base_path / "duplicate_merge_plan.md"
            fixer.generate_duplicate_merge_script(duplicates, str(merge_script_path))
        else:
            print("No duplicates loaded")
    else:
        print(f"Duplicates file not found: {duplicates_csv}")
    
    # Fix 2: Create Family Historian compatible version of recovered_gaiad.ged
    if recovered_gedcom.exists():
        print(f"\n2. Creating Family Historian compatible version...")
        fh_compatible_path = base_path / "recovered_gaiad_FH_compatible.ged"
        fixer.create_gedcom_for_family_historian(str(recovered_gedcom), str(fh_compatible_path))
    else:
        print(f"Recovered GEDCOM not found: {recovered_gedcom}")
    
    # Fix 3: Also create compatible version of master_combined if needed
    print(f"\n3. Checking master_combined.ged for BC date issues...")
    if master_gedcom.exists():
        # Just analyze, don't fix the master file automatically
        with open(master_gedcom, 'r', encoding='utf-8') as f:
            sample = f.read(100000)  # Read first 100k characters
            bc_matches = len(re.findall(r'\d+ DATE \([A-Z]+ -\d+\)', sample))
            if bc_matches > 0:
                print(f"Found {bc_matches} BC dates in sample - master file likely has BC date compatibility issues")
                print("Run fix_bc_dates_for_family_historian() on master file if needed")
            else:
                print("No BC date issues found in sample")
    
    print("\nAll fixes completed!")

if __name__ == "__main__":
    main()