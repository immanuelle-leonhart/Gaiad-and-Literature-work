#!/usr/bin/env python3
"""
Proper GEDCOM Merger that preserves family relationships
Merges individuals and families while maintaining genealogical integrity
"""

import re
from typing import Dict, List, Set, Optional, Tuple
import logging
from datetime import datetime
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProperGedcomMerger:
    def __init__(self):
        self.individuals = {}  # gedcom_id -> individual_data
        self.families = {}     # gedcom_id -> family_data
        self.sources = {}      # source_id -> source_data
        
        # Mapping structures for merging
        self.geni_to_id = {}      # geni_id -> merged_individual_id
        self.wikidata_to_id = {}  # wikidata_id -> merged_individual_id
        self.name_to_ids = defaultdict(list)  # (given, surname) -> [individual_ids]
        
        # ID mapping from original to merged
        self.individual_id_mapping = {}  # old_id -> new_id
        self.family_id_mapping = {}      # old_family_id -> new_family_id
        
        self.next_individual_id = 1
        self.next_family_id = 1
        self.next_source_id = 1
        
    def extract_references(self, individual_data: Dict) -> Dict[str, str]:
        """Extract Geni and Wikidata references from individual data"""
        refs = {}
        
        # Check REFN fields
        for refn in individual_data.get('refn', []):
            if 'geni:' in refn:
                refs['geni_id'] = refn.replace('geni:', '')
            elif refn.startswith('Q') and refn[1:].isdigit():
                refs['wikidata_id'] = refn
                
        # Check notes for references
        notes = ' '.join(individual_data.get('notes', []))
        
        # Geni ID patterns
        geni_match = re.search(r'geni:(\d+)|geni\.com/people/[^/]+/(\d+)', notes)
        if geni_match:
            refs['geni_id'] = geni_match.group(1) or geni_match.group(2)
            
        # Wikidata patterns
        wikidata_match = re.search(r'(Q\d+)', notes)
        if wikidata_match:
            refs['wikidata_id'] = wikidata_match.group(1)
            
        return refs
        
    def normalize_name(self, name: str) -> str:
        """Normalize name for comparison"""
        if not name:
            return ""
        # Remove extra spaces, convert to lowercase
        return ' '.join(name.strip().split()).lower()
        
    def names_similar(self, name1: str, name2: str, threshold: float = 0.8) -> bool:
        """Check if two names are similar enough to be the same person"""
        name1_norm = self.normalize_name(name1)
        name2_norm = self.normalize_name(name2)
        
        if not name1_norm or not name2_norm:
            return False
            
        # Exact match
        if name1_norm == name2_norm:
            return True
            
        # Simple similarity check
        from difflib import SequenceMatcher
        similarity = SequenceMatcher(None, name1_norm, name2_norm).ratio()
        return similarity >= threshold
        
    def find_merge_candidate(self, individual: Dict, refs: Dict[str, str]) -> Optional[str]:
        """Find existing individual that should be merged with this one"""
        
        # Priority 1: Geni ID match
        if 'geni_id' in refs and refs['geni_id'] in self.geni_to_id:
            return self.geni_to_id[refs['geni_id']]
            
        # Priority 2: Wikidata ID match  
        if 'wikidata_id' in refs and refs['wikidata_id'] in self.wikidata_to_id:
            return self.wikidata_to_id[refs['wikidata_id']]
            
        # Priority 3: Name matching
        names = individual.get('names', [])
        if names:
            primary_name = names[0]
            given = primary_name.get('given', '')
            surname = primary_name.get('surname', '')
            
            # Look for similar names
            for existing_id in self.name_to_ids.get((given.lower(), surname.lower()), []):
                existing_individual = self.individuals[existing_id]
                existing_names = existing_individual.get('names', [])
                
                if existing_names:
                    existing_primary = existing_names[0]
                    existing_given = existing_primary.get('given', '')
                    existing_surname = existing_primary.get('surname', '')
                    
                    if (self.names_similar(given, existing_given) and 
                        self.names_similar(surname, existing_surname)):
                        return existing_id
                        
        return None
        
    def merge_individuals(self, existing_id: str, new_individual: Dict) -> None:
        """Merge new individual data into existing individual"""
        existing = self.individuals[existing_id]
        
        # Merge names (avoid duplicates)
        existing_names = {(n.get('given', ''), n.get('surname', '')) for n in existing.get('names', [])}
        for name in new_individual.get('names', []):
            name_key = (name.get('given', ''), name.get('surname', ''))
            if name_key not in existing_names:
                existing.setdefault('names', []).append(name)
                
        # Merge other fields
        for field in ['birth', 'death', 'events', 'notes', 'refn', 'sources']:
            if field in new_individual:
                if field not in existing:
                    existing[field] = new_individual[field]
                elif isinstance(existing[field], list):
                    # Merge lists, avoiding duplicates where possible
                    for item in new_individual[field]:
                        if item not in existing[field]:
                            existing[field].append(item)
                            
        # Keep track of source files
        if 'source_files' not in existing:
            existing['source_files'] = []
        if new_individual.get('source_file'):
            if new_individual['source_file'] not in existing['source_files']:
                existing['source_files'].append(new_individual['source_file'])
                
    def add_individual(self, original_id: str, individual: Dict, source_file: str) -> str:
        """Add individual to merged dataset"""
        individual['source_file'] = source_file
        refs = self.extract_references(individual)
        
        # Check for merge candidate
        merge_candidate = self.find_merge_candidate(individual, refs)
        
        if merge_candidate:
            # Merge with existing individual
            self.merge_individuals(merge_candidate, individual)
            self.individual_id_mapping[original_id] = merge_candidate
            logger.info(f"Merged {original_id} into existing {merge_candidate}")
            return merge_candidate
        else:
            # Create new individual
            new_id = f"I{self.next_individual_id}"
            self.next_individual_id += 1
            
            self.individuals[new_id] = individual
            self.individual_id_mapping[original_id] = new_id
            
            # Update reference mappings
            if 'geni_id' in refs:
                self.geni_to_id[refs['geni_id']] = new_id
            if 'wikidata_id' in refs:
                self.wikidata_to_id[refs['wikidata_id']] = new_id
                
            # Update name mapping
            names = individual.get('names', [])
            if names:
                primary_name = names[0]
                given = primary_name.get('given', '').lower()
                surname = primary_name.get('surname', '').lower()
                self.name_to_ids[(given, surname)].append(new_id)
                
            return new_id
            
    def add_family(self, original_id: str, family: Dict, source_file: str) -> str:
        """Add family to merged dataset, updating individual references"""
        family['source_file'] = source_file
        
        # Update references to individuals
        if 'husband' in family and family['husband'] in self.individual_id_mapping:
            family['husband'] = self.individual_id_mapping[family['husband']]
        if 'wife' in family and family['wife'] in self.individual_id_mapping:
            family['wife'] = self.individual_id_mapping[family['wife']]
            
        # Update children references
        if 'children' in family:
            updated_children = []
            for child_id in family['children']:
                if child_id in self.individual_id_mapping:
                    updated_children.append(self.individual_id_mapping[child_id])
                else:
                    updated_children.append(child_id)  # Keep original if not mapped
            family['children'] = updated_children
            
        new_family_id = f"F{self.next_family_id}"
        self.next_family_id += 1
        
        self.families[new_family_id] = family
        self.family_id_mapping[original_id] = new_family_id
        
        return new_family_id
        
    def update_individual_family_references(self):
        """Update FAMS and FAMC references in individuals"""
        for individual_id, individual in self.individuals.items():
            # Update FAMS (families as spouse)
            if 'fams' in individual:
                updated_fams = []
                for family_id in individual['fams']:
                    if family_id in self.family_id_mapping:
                        updated_fams.append(self.family_id_mapping[family_id])
                    else:
                        updated_fams.append(family_id)
                individual['fams'] = updated_fams
                
            # Update FAMC (family as child)
            if 'famc' in individual:
                updated_famc = []
                for family_id in individual['famc']:
                    if family_id in self.family_id_mapping:
                        updated_famc.append(self.family_id_mapping[family_id])
                    else:
                        updated_famc.append(family_id)
                individual['famc'] = updated_famc

    def parse_gedcom(self, filename: str) -> Tuple[Dict, Dict, Dict]:
        """Parse GEDCOM file and return individuals, families, sources"""
        individuals = {}
        families = {}
        sources = {}
        
        current_record = None
        current_id = None
        current_level = 0
        
        with open(filename, 'r', encoding='utf-8-sig', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                line = line.rstrip()
                if not line:
                    continue
                    
                # Parse GEDCOM line
                parts = line.split(' ', 2)
                if len(parts) < 2:
                    continue
                
                # Handle potential BOM or non-numeric level
                try:
                    level = int(parts[0])
                except ValueError:
                    # Skip lines that don't start with a valid level number
                    continue
                tag = parts[1] if not parts[1].startswith('@') else (parts[2] if len(parts) > 2 else '')
                
                # Handle record start
                if level == 0:
                    if parts[1].startswith('@') and len(parts) > 2:
                        current_id = parts[1][1:-1]  # Remove @ symbols
                        current_level = 0
                        
                        if parts[2] == 'INDI':
                            current_record = {'names': [], 'events': [], 'notes': [], 'refn': [], 'fams': [], 'famc': []}
                            individuals[current_id] = current_record
                        elif parts[2] == 'FAM':
                            current_record = {'children': [], 'events': [], 'notes': []}
                            families[current_id] = current_record
                        elif parts[2] == 'SOUR':
                            current_record = {}
                            sources[current_id] = current_record
                        else:
                            current_record = None
                    continue
                    
                if current_record is None:
                    continue
                    
                # Handle individual records
                if current_id in individuals:
                    if level == 1:
                        if tag == 'NAME':
                            name_value = parts[2] if len(parts) > 2 else ''
                            # Parse name
                            name_parts = name_value.split('/')
                            given = name_parts[0].strip() if len(name_parts) > 0 else ''
                            surname = name_parts[1].strip() if len(name_parts) > 1 else ''
                            individuals[current_id]['names'].append({'given': given, 'surname': surname, 'full': name_value})
                        elif tag == 'SEX':
                            individuals[current_id]['sex'] = parts[2] if len(parts) > 2 else ''
                        elif tag == 'REFN':
                            individuals[current_id]['refn'].append(parts[2] if len(parts) > 2 else '')
                        elif tag == 'NOTE':
                            individuals[current_id]['notes'].append(parts[2] if len(parts) > 2 else '')
                        elif tag == 'FAMS':
                            family_ref = parts[2][1:-1] if len(parts) > 2 and parts[2].startswith('@') else parts[2] if len(parts) > 2 else ''
                            if family_ref:
                                individuals[current_id]['fams'].append(family_ref)
                        elif tag == 'FAMC':
                            family_ref = parts[2][1:-1] if len(parts) > 2 and parts[2].startswith('@') else parts[2] if len(parts) > 2 else ''
                            if family_ref:
                                individuals[current_id]['famc'].append(family_ref)
                                
                # Handle family records
                elif current_id in families:
                    if level == 1:
                        if tag == 'HUSB':
                            husb_ref = parts[2][1:-1] if len(parts) > 2 and parts[2].startswith('@') else parts[2] if len(parts) > 2 else ''
                            families[current_id]['husband'] = husb_ref
                        elif tag == 'WIFE':
                            wife_ref = parts[2][1:-1] if len(parts) > 2 and parts[2].startswith('@') else parts[2] if len(parts) > 2 else ''
                            families[current_id]['wife'] = wife_ref
                        elif tag == 'CHIL':
                            child_ref = parts[2][1:-1] if len(parts) > 2 and parts[2].startswith('@') else parts[2] if len(parts) > 2 else ''
                            if child_ref:
                                families[current_id]['children'].append(child_ref)
                                
        logger.info(f"Parsed {filename}: {len(individuals)} individuals, {len(families)} families, {len(sources)} sources")
        return individuals, families, sources
        
    def write_gedcom(self, output_filename: str):
        """Write merged data to GEDCOM file"""
        with open(output_filename, 'w', encoding='utf-8') as f:
            # Write header
            f.write("0 HEAD\n")
            f.write("1 SOUR Proper_GEDCOM_Merger\n")
            f.write("2 NAME Proper GEDCOM Merger with Family Preservation\n") 
            f.write("2 CORP Gaiad Genealogy Project\n")
            f.write(f"1 DATE {datetime.now().strftime('%d %b %Y')}\n")
            f.write(f"1 FILE {output_filename}\n")
            f.write("1 GEDC\n")
            f.write("2 VERS 5.5.1\n")
            f.write("2 FORM LINEAGE-LINKED\n")
            f.write("1 CHAR UTF-8\n")
            
            # Write individuals
            for individual_id, individual in self.individuals.items():
                f.write(f"0 @{individual_id}@ INDI\n")
                
                # Write names
                for name in individual.get('names', []):
                    full_name = name.get('full', f"{name.get('given', '')} /{name.get('surname', '')}/")
                    f.write(f"1 NAME {full_name}\n")
                    if name.get('given'):
                        f.write(f"2 GIVN {name['given']}\n")
                    if name.get('surname'):
                        f.write(f"2 SURN {name['surname']}\n")
                        
                # Write sex
                if individual.get('sex'):
                    f.write(f"1 SEX {individual['sex']}\n")
                    
                # Write family references
                for family_id in individual.get('fams', []):
                    f.write(f"1 FAMS @{family_id}@\n")
                for family_id in individual.get('famc', []):
                    f.write(f"1 FAMC @{family_id}@\n")
                    
                # Write notes
                for note in individual.get('notes', []):
                    if note:
                        f.write(f"1 NOTE {note}\n")
                        
                # Write references
                for refn in individual.get('refn', []):
                    if refn:
                        f.write(f"1 REFN {refn}\n")
                        
            # Write families
            for family_id, family in self.families.items():
                f.write(f"0 @{family_id}@ FAM\n")
                
                if family.get('husband'):
                    f.write(f"1 HUSB @{family['husband']}@\n")
                if family.get('wife'):
                    f.write(f"1 WIFE @{family['wife']}@\n")
                    
                for child_id in family.get('children', []):
                    f.write(f"1 CHIL @{child_id}@\n")
                    
            f.write("0 TRLR\n")
            
        logger.info(f"Written {output_filename}: {len(self.individuals)} individuals, {len(self.families)} families")
        
    def merge_files(self, input_files: List[str], output_file: str):
        """Merge multiple GEDCOM files"""
        logger.info(f"Starting merge of {len(input_files)} files")
        
        # Process each input file
        for filename in input_files:
            logger.info(f"Processing {filename}")
            individuals, families, sources = self.parse_gedcom(filename)
            
            # Add all individuals first
            for original_id, individual in individuals.items():
                self.add_individual(original_id, individual, filename)
                
            # Then add families (after individual mapping is complete)
            for original_id, family in families.items():
                self.add_family(original_id, family, filename)
                
        # Update family references in individuals
        self.update_individual_family_references()
        
        # Write output
        self.write_gedcom(output_file)
        
        # Log merge statistics
        logger.info("Merge completed!")
        logger.info(f"Final result: {len(self.individuals)} individuals, {len(self.families)} families")
        logger.info(f"Individual merges: {len([k for k, v in self.individual_id_mapping.items() if k != v])}")

def main():
    merger = ProperGedcomMerger()
    
    input_files = [
        "new_gedcoms/geni_plus_wikidata_cleaned.ged",
        "new_gedcoms/gaiad_ftb_export_2.ged"
    ]
    
    output_file = "new_gedcoms/final_merged_attempt.ged"
    
    merger.merge_files(input_files, output_file)
    
if __name__ == "__main__":
    main()