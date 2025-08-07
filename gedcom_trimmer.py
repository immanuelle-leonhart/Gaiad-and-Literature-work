#!/usr/bin/env python3
"""
Script to trim down large GEDCOM files by various criteria:
- Keep only individuals with specific name patterns
- Keep only individuals within date ranges
- Keep only individuals with sources/references
- Keep connected family groups
"""

import re
import logging
from typing import Dict, List, Set, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GedcomTrimmer:
    def __init__(self, input_file: str):
        self.input_file = input_file
        self.lines = []
        self.individuals = {}
        self.families = {}
        self.sources = {}
        self.notes = {}
        
    def load_gedcom(self):
        """Load and parse GEDCOM file"""
        logger.info(f"Loading GEDCOM file: {self.input_file}")
        
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                self.lines = f.readlines()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(self.input_file, 'r', encoding='latin-1') as f:
                self.lines = f.readlines()
                
        logger.info(f"Loaded {len(self.lines):,} lines")
        
    def analyze_content(self):
        """Analyze GEDCOM content and structure"""
        current_record = None
        current_type = None
        
        individual_count = 0
        family_count = 0
        source_count = 0
        note_count = 0
        
        for line in self.lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for new records
            if line.startswith('0 @') and line.endswith('@ INDI'):
                current_type = 'INDI'
                individual_count += 1
                match = re.search(r'0 @(.+?)@ INDI', line)
                if match:
                    current_record = match.group(1)
                    self.individuals[current_record] = {'lines': [line], 'names': []}
                    
            elif line.startswith('0 @') and line.endswith('@ FAM'):
                current_type = 'FAM'
                family_count += 1
                match = re.search(r'0 @(.+?)@ FAM', line)
                if match:
                    current_record = match.group(1)
                    self.families[current_record] = {'lines': [line]}
                    
            elif line.startswith('0 @') and line.endswith('@ SOUR'):
                current_type = 'SOUR'
                source_count += 1
                match = re.search(r'0 @(.+?)@ SOUR', line)
                if match:
                    current_record = match.group(1)
                    self.sources[current_record] = {'lines': [line]}
                    
            elif line.startswith('0 @') and line.endswith('@ NOTE'):
                current_type = 'NOTE'
                note_count += 1
                match = re.search(r'0 @(.+?)@ NOTE', line)
                if match:
                    current_record = match.group(1)
                    self.notes[current_record] = {'lines': [line]}
                    
            elif line.startswith('0 '):
                # Other record type, reset
                current_record = None
                current_type = None
                
            else:
                # Add line to current record
                if current_record and current_type:
                    if current_type == 'INDI' and current_record in self.individuals:
                        self.individuals[current_record]['lines'].append(line)
                        # Extract names
                        if line.startswith('1 NAME') or line.startswith('2 GIVN') or line.startswith('2 SURN'):
                            self.individuals[current_record]['names'].append(line)
                            
                    elif current_type == 'FAM' and current_record in self.families:
                        self.families[current_record]['lines'].append(line)
                        
                    elif current_type == 'SOUR' and current_record in self.sources:
                        self.sources[current_record]['lines'].append(line)
                        
                    elif current_type == 'NOTE' and current_record in self.notes:
                        self.notes[current_record]['lines'].append(line)
        
        print(f"\nGEDCOM Analysis Results:")
        print(f"  Individuals: {individual_count:,}")
        print(f"  Families: {family_count:,}")
        print(f"  Sources: {source_count:,}")
        print(f"  Notes: {note_count:,}")
        
    def get_individuals_with_pattern(self, name_pattern: str) -> Set[str]:
        """Get individuals whose names match a pattern"""
        matching_ids = set()
        pattern = re.compile(name_pattern, re.IGNORECASE)
        
        for indi_id, indi_data in self.individuals.items():
            for name_line in indi_data['names']:
                if pattern.search(name_line):
                    matching_ids.add(indi_id)
                    break
                    
        return matching_ids
        
    def get_individuals_with_sources(self) -> Set[str]:
        """Get individuals that have source references"""
        with_sources = set()
        
        for indi_id, indi_data in self.individuals.items():
            for line in indi_data['lines']:
                if line.strip().startswith('1 SOUR') or line.strip().startswith('2 SOUR'):
                    with_sources.add(indi_id)
                    break
                    
        return with_sources
        
    def get_connected_individuals(self, seed_ids: Set[str], generations: int = 2) -> Set[str]:
        """Get all individuals connected to seed individuals within N generations"""
        connected = set(seed_ids)
        
        for _ in range(generations):
            new_connections = set()
            
            # Find family connections
            for fam_id, fam_data in self.families.items():
                family_members = set()
                
                for line in fam_data['lines']:
                    # Look for HUSB, WIFE, CHIL references
                    match = re.search(r'1 (HUSB|WIFE|CHIL) @(.+?)@', line)
                    if match:
                        family_members.add(match.group(2))
                
                # If any current connected individual is in this family,
                # add all family members
                if family_members.intersection(connected):
                    new_connections.update(family_members)
                    
            connected.update(new_connections)
            
        return connected
        
    def create_trimmed_gedcom(self, keep_individuals: Set[str], output_file: str):
        """Create a new GEDCOM with only specified individuals and related records"""
        logger.info(f"Creating trimmed GEDCOM with {len(keep_individuals)} individuals")
        
        # Find related families
        keep_families = set()
        for fam_id, fam_data in self.families.items():
            for line in fam_data['lines']:
                match = re.search(r'1 (HUSB|WIFE|CHIL) @(.+?)@', line)
                if match and match.group(2) in keep_individuals:
                    keep_families.add(fam_id)
                    break
        
        # Find related sources and notes (referenced by kept individuals)
        keep_sources = set()
        keep_notes = set()
        
        for indi_id in keep_individuals:
            if indi_id in self.individuals:
                for line in self.individuals[indi_id]['lines']:
                    # Source references
                    match = re.search(r'1 SOUR @(.+?)@', line)
                    if match:
                        keep_sources.add(match.group(1))
                    
                    # Note references
                    match = re.search(r'1 NOTE @(.+?)@', line)
                    if match:
                        keep_notes.add(match.group(1))
        
        # Write trimmed GEDCOM
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write("0 HEAD\n")
            f.write("1 SOUR GedcomTrimmer\n")
            f.write("2 NAME GEDCOM Trimmer Tool\n")
            f.write("1 GEDC\n")
            f.write("2 VERS 5.5.1\n")
            f.write("2 FORM LINEAGE-LINKED\n")
            f.write("1 CHAR UTF-8\n")
            f.write(f"1 DATE {datetime.now().strftime('%d %b %Y').upper()}\n")
            f.write(f"1 NOTE Trimmed from {self.input_file}\n")
            f.write(f"2 CONT Original had {len(self.individuals)} individuals\n")
            f.write(f"2 CONT Trimmed to {len(keep_individuals)} individuals\n")
            f.write("\n")
            
            # Write individuals
            for indi_id in sorted(keep_individuals):
                if indi_id in self.individuals:
                    for line in self.individuals[indi_id]['lines']:
                        f.write(line + '\n')
                    f.write('\n')
            
            # Write families
            for fam_id in sorted(keep_families):
                if fam_id in self.families:
                    for line in self.families[fam_id]['lines']:
                        f.write(line + '\n')
                    f.write('\n')
            
            # Write sources
            for sour_id in sorted(keep_sources):
                if sour_id in self.sources:
                    for line in self.sources[sour_id]['lines']:
                        f.write(line + '\n')
                    f.write('\n')
                        
            # Write notes  
            for note_id in sorted(keep_notes):
                if note_id in self.notes:
                    for line in self.notes[note_id]['lines']:
                        f.write(line + '\n')
                    f.write('\n')
            
            # Write trailer
            f.write("0 TRLR\n")
            
        logger.info(f"Trimmed GEDCOM saved to: {output_file}")
        logger.info(f"  Individuals: {len(keep_individuals)}")
        logger.info(f"  Families: {len(keep_families)}")  
        logger.info(f"  Sources: {len(keep_sources)}")
        logger.info(f"  Notes: {len(keep_notes)}")

def main():
    input_file = "C:\\Users\\Immanuelle\\Documents\\Github\\Gaiad-Genealogy\\geni plus wikidata after merge.ged"
    
    trimmer = GedcomTrimmer(input_file)
    
    print("=== GEDCOM Trimmer ===")
    print(f"Input file: {input_file}")
    print(f"Size: {os.path.getsize(input_file) / (1024*1024):.1f} MB")
    
    # Load and analyze
    trimmer.load_gedcom()
    trimmer.analyze_content()
    
    # Example: Keep individuals with Roman/Latin names
    print(f"\n=== Finding individuals with Roman/Latin patterns ===")
    roman_patterns = [
        r'\b(Caesar|Augustus|Marcus|Lucius|Gaius|Julius|Claudius|Titus|Vespasian|Trajan|Hadrian|Antoninus|Severus)\b',
        r'\b(Olybrius|Probus|Maximus|Felix|Victor|Valentinian|Theodosius|Honorius|Arcadius)\b',
        r'\b(ius|us|a)$',  # Common Roman endings
    ]
    
    roman_individuals = set()
    for pattern in roman_patterns:
        matches = trimmer.get_individuals_with_pattern(pattern)
        roman_individuals.update(matches)
        print(f"  Pattern '{pattern}': {len(matches)} matches")
    
    print(f"Total individuals with Roman patterns: {len(roman_individuals)}")
    
    # Get connected individuals (family networks)
    if roman_individuals:
        print(f"\n=== Expanding to connected families ===")
        connected = trimmer.get_connected_individuals(roman_individuals, generations=3)
        print(f"Connected individuals (3 generations): {len(connected)}")
        
        # Create trimmed file
        output_file = "C:\\Users\\Immanuelle\\Documents\\Github\\Gaiad-Genealogy\\roman_lineages_trimmed.ged"
        trimmer.create_trimmed_gedcom(connected, output_file)
    
    # Example: Keep only individuals with sources
    print(f"\n=== Finding individuals with sources ===")
    with_sources = trimmer.get_individuals_with_sources()
    print(f"Individuals with sources: {len(with_sources)}")
    
    if with_sources:
        output_file = "C:\\Users\\Immanuelle\\Documents\\Github\\Gaiad-Genealogy\\sourced_individuals.ged"
        trimmer.create_trimmed_gedcom(with_sources, output_file)

if __name__ == "__main__":
    import os
    main()