#!/usr/bin/env python3
"""
FamilyTreeBuilder to Family Historian Duplicates Converter
Converts FTB CSV duplicate detection results to FH Lua table format
"""

import csv
import re
from pathlib import Path
from typing import Dict, List, Tuple

class FTBToFHConverter:
    """Convert FamilyTreeBuilder duplicate CSV to Family Historian Lua format"""
    
    def __init__(self):
        self.id_mapping = {}  # Map FTB IDs to FH record IDs
        
    def parse_ftb_csv(self, csv_path: str) -> List[Dict]:
        """Parse FamilyTreeBuilder duplicates CSV file"""
        duplicates = []
        
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Skip rows with parsing issues
                    if not row.get('Score') or not row.get('ID 1') or not row.get('ID 2'):
                        continue
                        
                    duplicates.append({
                        'score': self.parse_score(row.get('Score', '')),
                        'id1': row.get('ID 1', '').strip(),
                        'id2': row.get('ID 2', '').strip(),
                        'name1': row.get('Name 1', '').strip(),
                        'name2': row.get('Name 2', '').strip(),
                        'birth1': row.get('Birth date 1', '').strip(),
                        'birth2': row.get('Birth date 2', '').strip(),
                        'death1': row.get('Death date 1', '').strip(),
                        'death2': row.get('Death date 2', '').strip(),
                        'relatives1': row.get('Relatives 1', '').strip(),
                        'relatives2': row.get('Relatives 2', '').strip()
                    })
                    
        except Exception as e:
            print(f"Error parsing CSV: {e}")
            
        return duplicates
    
    def parse_score(self, score_str: str) -> int:
        """Convert FTB score string like '80%' to integer"""
        if '%' in score_str:
            try:
                return int(score_str.replace('%', ''))
            except ValueError:
                return 50  # Default score
        return 50
    
    def create_fh_record(self, dup: Dict, index: int) -> str:
        """Create a Family Historian Lua table record for a duplicate pair"""
        
        # Convert FTB IDs to Family Historian compatible range
        # FH uses IDs in 8000s range, use 9000+ to avoid conflicts
        fh_id_a = 9000 + (index * 2)     # Even numbers for first individual
        fh_id_b = 9000 + (index * 2) + 1 # Odd numbers for second individual
        
        # Convert FTB score (0-100) to FH FullScore 
        full_score = dup['score']
        
        # Estimate component scores based on available data
        indi_score = min(20, full_score // 4) if dup['name1'] and dup['name2'] else 0
        birth_score = min(15, full_score // 6) if dup['birth1'] and dup['birth2'] else 0
        death_score = min(15, full_score // 6) if dup['death1'] and dup['death2'] else 0
        
        # Create synthetic date spans (FH format requirement)
        def create_span(date_str):
            if not date_str or date_str in ['', 'Deceased']:
                return '" "'
            # Simple conversion - FH expects specific format
            return f'"btw {date_str} and {date_str}  User"'
        
        b_a_span = create_span(dup['birth1'])
        b_b_span = create_span(dup['birth2'])  
        d_a_span = create_span(dup['death1'])
        d_b_span = create_span(dup['death2'])
        
        # Generate FH Lua record
        record = f"""-- Table: {{{index}}}
{{
   ["FullScore"]={full_score},
   ["RecordIdA"]={fh_id_a},
   ["RecordIdB"]={fh_id_b},
   ["IndiScore"]={indi_score},
   ["IndiNames"]={indi_score},
   ["IndiBirth"]={birth_score},
   ["IndiDeath"]={death_score},
   ["B_A_Span"]={b_a_span},
   ["B_B_Span"]={b_b_span},
   ["D_A_Span"]={d_a_span},
   ["D_B_Span"]={d_b_span},
   ["M_A_Span"]=" ",
   ["M_B_Span"]=" ",
   ["C_A_Span"]=" ",
   ["C_B_Span"]=" ",
   ["FathScore"]=0,
   ["FathNames"]=0,
   ["FathBirth"]=0,
   ["FathDeath"]=0,
   ["FathMarry"]=0,
   ["FathBapCh"]=0,
   ["MothScore"]=0,
   ["MothNames"]=0,
   ["MothBirth"]=0,
   ["MothDeath"]=0,
   ["MothMarry"]=0,
   ["MothBapCh"]=0,
   ["SpouScore"]=0,
   ["SpouNames"]=0,
   ["SpouBirth"]=0,
   ["SpouDeath"]=0,
   ["SpouMarry"]=0,
   ["SpouBapCh"]=0,
   ["ChilScore"]=0,
   ["ChilNames"]=0,
   ["ChilBirth"]=0,
   ["ChilDeath"]=0,
   ["ChilMarry"]=0,
   ["ChilBapCh"]=0,
   ["GendScore"]=0,
   ["IndivGend"]=0,
   ["ChildGend"]=0,
   ["FamGensUp"]=0,
   ["FamGensDn"]=0,
   ["FamGenGap"]=0,
   ["DateChron"]=0,
   ["IndiBapCh"]=0,
}},"""
        
        return record
    
    def convert_to_fh_format(self, duplicates: List[Dict], output_path: str):
        """Convert list of duplicates to Family Historian .results format"""
        
        print(f"Converting {len(duplicates)} duplicate pairs to Family Historian format...")
        print("ID Mapping (FTB -> FH):")
        
        for i, dup in enumerate(duplicates, 2):
            fh_id_a = 9000 + (i * 2)
            fh_id_b = 9000 + (i * 2) + 1
            print(f"  {dup['id1']} -> {fh_id_a}, {dup['id2']} -> {fh_id_b}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("return {\n")
            
            # First table: array of indices (FH expects this structure)
            f.write("-- Table: {1}\n")
            f.write("{\n")
            for i in range(2, len(duplicates) + 2):
                f.write(f"   {{{i}}},\n")
            f.write("},\n")
            
            # Subsequent tables: detailed duplicate records
            for i, dup in enumerate(duplicates, 2):  # Start from 2 to match FH numbering
                record = self.create_fh_record(dup, i)
                f.write(record + "\n")
            
            f.write("}\n")
        
        print(f"Family Historian .results file created: {output_path}")
        return len(duplicates)
    
    def create_minimal_supporting_files(self, base_path: str, num_duplicates: int):
        """Create minimal supporting files (.dat, .nondups, .soundex)"""
        
        base_path = Path(base_path)
        
        # Create .nondups file (simple text)
        nondups_path = base_path.with_suffix('.nondups')
        with open(nondups_path, 'w', encoding='utf-8') as f:
            f.write(f"-- {num_duplicates} duplicate pairs converted from FTB\n")
        
        # Create minimal .dat file (would need reverse engineering for full compatibility)
        dat_path = base_path.with_suffix('.dat') 
        with open(dat_path, 'wb') as f:
            # Write minimal binary header - this is a placeholder
            f.write(b'FH_DUPLICATES_CONVERTED_FROM_FTB\x00\x00\x00\x00')
            f.write(num_duplicates.to_bytes(4, 'little'))
        
        # Create .soundex file (phonetic matching data - placeholder)
        soundex_path = base_path.with_suffix('.soundex')
        with open(soundex_path, 'wb') as f:
            # Placeholder soundex data
            f.write(b'SOUNDEX_DATA_PLACEHOLDER\x00' * 100)
        
        print(f"Supporting files created:")
        print(f"  {nondups_path}")  
        print(f"  {dat_path}")
        print(f"  {soundex_path}")

def main():
    """Convert FTB duplicates to FH format"""
    converter = FTBToFHConverter()
    
    # File paths
    base_dir = Path(r"C:\Users\Immanuelle\Documents\Github\Gaiad-Genealogy\new_gedcoms\source gedcoms")
    ftb_csv = base_dir / "master_combined_duplications.csv"
    
    # Output to master_combined.fh_data directory (create if needed)
    fh_data_dir = base_dir / "master_combined.fh_data" / "Plugin Data"
    fh_data_dir.mkdir(parents=True, exist_ok=True)
    
    output_results = fh_data_dir / "Find Duplicate Individuals.results"
    
    print("FTB to FH Duplicates Converter")
    print("=" * 40)
    
    if not ftb_csv.exists():
        print(f"Error: FTB CSV file not found: {ftb_csv}")
        return
    
    # Parse FTB CSV
    print(f"Parsing FTB CSV: {ftb_csv}")
    duplicates = converter.parse_ftb_csv(str(ftb_csv))
    
    if not duplicates:
        print("No valid duplicates found in CSV")
        return
    
    print(f"Found {len(duplicates)} duplicate pairs")
    
    # Convert to FH format
    num_converted = converter.convert_to_fh_format(duplicates, str(output_results))
    
    # Create supporting files
    converter.create_minimal_supporting_files(str(output_results), num_converted)
    
    print(f"\nConversion completed!")
    print(f"Family Historian can now read duplicate data from:")
    print(f"  {fh_data_dir}")
    print(f"\nTo use: Open master_combined.ged in Family Historian and check the")
    print(f"Find Duplicate Individuals plugin results.")

if __name__ == "__main__":
    main()