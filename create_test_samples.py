#!/usr/bin/env python3
"""
Create small test samples from GEDCOM files for testing merging
"""

import logging
from typing import Dict, List, Set
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GedcomSampler:
    def __init__(self):
        self.individuals = {}
        self.families = {}
        
    def parse_gedcom(self, filename: str):
        """Parse GEDCOM file"""
        current_record = None
        current_id = None
        current_content = []
        
        logger.info(f"Parsing {filename}")
        
        with open(filename, 'r', encoding='utf-8-sig', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                line = line.rstrip()
                if not line:
                    continue
                    
                parts = line.split(' ', 2)
                if len(parts) < 2:
                    current_content.append(line)
                    continue
                
                try:
                    level = int(parts[0])
                except ValueError:
                    current_content.append(line)
                    continue
                    
                # Handle record start
                if level == 0:
                    # Save previous record
                    if current_record and current_id and current_content:
                        if current_record == 'INDI':
                            self.individuals[current_id] = '\n'.join(current_content)
                        elif current_record == 'FAM':
                            self.families[current_id] = '\n'.join(current_content)
                    
                    # Start new record
                    if parts[1].startswith('@') and len(parts) > 2:
                        current_id = parts[1][1:-1]  # Remove @ symbols
                        current_record = parts[2]
                        current_content = [line]
                    else:
                        current_record = None
                        current_id = None
                        current_content = [line]
                else:
                    current_content.append(line)
            
            # Save last record
            if current_record and current_id and current_content:
                if current_record == 'INDI':
                    self.individuals[current_id] = '\n'.join(current_content)
                elif current_record == 'FAM':
                    self.families[current_id] = '\n'.join(current_content)
                    
        logger.info(f"Parsed {len(self.individuals)} individuals, {len(self.families)} families")
        
    def extract_family_cluster(self, start_individual_id: str, max_individuals: int = 50) -> Set[str]:
        """Extract a connected family cluster starting from one individual"""
        selected_individuals = set()
        selected_families = set()
        to_process = [start_individual_id]
        
        while to_process and len(selected_individuals) < max_individuals:
            individual_id = to_process.pop(0)
            if individual_id in selected_individuals or individual_id not in self.individuals:
                continue
                
            selected_individuals.add(individual_id)
            
            # Find families this individual is in
            individual_content = self.individuals[individual_id]
            family_refs = []
            
            for line in individual_content.split('\n'):
                if line.startswith('1 FAMS @') or line.startswith('1 FAMC @'):
                    family_ref = line.split('@')[1]
                    family_refs.append(family_ref)
                    
            # Add families and their members
            for family_id in family_refs:
                if family_id in self.families and family_id not in selected_families:
                    selected_families.add(family_id)
                    
                    # Find all members of this family
                    family_content = self.families[family_id]
                    for line in family_content.split('\n'):
                        if (line.startswith('1 HUSB @') or 
                            line.startswith('1 WIFE @') or 
                            line.startswith('1 CHIL @')):
                            member_ref = line.split('@')[1]
                            if member_ref not in selected_individuals and len(selected_individuals) < max_individuals:
                                to_process.append(member_ref)
                                
        return selected_individuals, selected_families
        
    def write_sample(self, individual_ids: Set[str], family_ids: Set[str], output_file: str, source_description: str):
        """Write sample GEDCOM file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write("0 HEAD\n")
            f.write("1 SOUR Test_Sample_Generator\n")
            f.write("2 NAME Test Sample Generator\n")
            f.write(f"1 NOTE Sample from {source_description}\n")
            f.write(f"1 NOTE Contains {len(individual_ids)} individuals, {len(family_ids)} families\n")
            f.write("1 GEDC\n")
            f.write("2 VERS 5.5.1\n")
            f.write("2 FORM LINEAGE-LINKED\n")
            f.write("1 CHAR UTF-8\n")
            
            # Write selected individuals
            for individual_id in sorted(individual_ids):
                if individual_id in self.individuals:
                    f.write(self.individuals[individual_id] + '\n')
                    
            # Write selected families
            for family_id in sorted(family_ids):
                if family_id in self.families:
                    f.write(self.families[family_id] + '\n')
                    
            f.write("0 TRLR\n")
            
        logger.info(f"Written sample: {output_file} ({len(individual_ids)} individuals, {len(family_ids)} families)")

def create_samples():
    # Sample from geni_plus_wikidata_cleaned.ged
    sampler1 = GedcomSampler()
    sampler1.parse_gedcom("new_gedcoms/geni_plus_wikidata_cleaned.ged")
    
    # Get some starting points - individuals with common surnames
    sample_individuals = []
    for ind_id, content in list(sampler1.individuals.items())[:1000]:  # Check first 1000
        if any(surname in content for surname in ['/Smith/', '/Garcia/', '/Rodriguez/', '/Martinez/', '/Lopez/']):
            sample_individuals.append(ind_id)
            if len(sample_individuals) >= 3:
                break
                
    if not sample_individuals:
        # Fallback - just take some random individuals
        sample_individuals = list(sampler1.individuals.keys())[:3]
        
    logger.info(f"Creating samples from geni file starting with individuals: {sample_individuals}")
    
    for i, start_ind in enumerate(sample_individuals[:2]):  # Create 2 samples
        selected_inds, selected_fams = sampler1.extract_family_cluster(start_ind, 30)
        sampler1.write_sample(selected_inds, selected_fams, 
                            f"new_gedcoms/geni_sample_{i+1}.ged", 
                            "geni_plus_wikidata_cleaned.ged")
    
    # Sample from gaiad_ftb_export_2.ged  
    sampler2 = GedcomSampler()
    sampler2.parse_gedcom("new_gedcoms/gaiad_ftb_export_2.ged")
    
    # Get some starting points from FTB
    ftb_samples = list(sampler2.individuals.keys())[100:103]  # Skip the mythological beginning
    
    logger.info(f"Creating samples from FTB file starting with individuals: {ftb_samples}")
    
    for i, start_ind in enumerate(ftb_samples[:2]):  # Create 2 samples
        selected_inds, selected_fams = sampler2.extract_family_cluster(start_ind, 30)
        sampler2.write_sample(selected_inds, selected_fams,
                            f"new_gedcoms/ftb_sample_{i+1}.ged",
                            "gaiad_ftb_export_2.ged")

if __name__ == "__main__":
    create_samples()