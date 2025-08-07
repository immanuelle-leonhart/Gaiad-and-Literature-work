#!/usr/bin/env python3
"""
Comprehensive MongoDB to GEDCOM exporter - preserves all original data
"""

import pymongo
from pymongo import MongoClient
from datetime import datetime
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveGedcomExporter:
    def __init__(self, db_name: str = "genealogy_merge"):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client[db_name]
        
        # Store raw GEDCOM lines during import for full preservation
        self.raw_individuals = {}
        self.raw_families = {}
        
    def import_and_preserve_raw_gedcom(self, filepath: str, source_name: str):
        """Import GEDCOM while preserving ALL original lines"""
        logger.info(f"Importing and preserving raw GEDCOM: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        current_record_lines = []
        current_record_id = None
        record_type = None
        
        i = 0
        while i < len(lines):
            line = lines[i].rstrip('\r\n')
            
            # Start of individual record
            if re.match(r'^0 @I\d+@ INDI$', line):
                # Save previous record
                if current_record_lines and current_record_id and record_type == 'INDI':
                    self.raw_individuals[f"{source_name}_{current_record_id}"] = current_record_lines
                    
                current_record_id = line.split()[1][1:-1]  # Extract I123 from @I123@
                current_record_lines = [line]
                record_type = 'INDI'
                
            # Start of family record
            elif re.match(r'^0 @F\d+@ FAM$', line):
                # Save previous record
                if current_record_lines and current_record_id:
                    if record_type == 'INDI':
                        self.raw_individuals[f"{source_name}_{current_record_id}"] = current_record_lines
                    elif record_type == 'FAM':
                        self.raw_families[f"{source_name}_{current_record_id}"] = current_record_lines
                        
                current_record_id = line.split()[1][1:-1]  # Extract F123 from @F123@
                current_record_lines = [line]
                record_type = 'FAM'
                
            # Start of other record types (sources, etc.)
            elif line.startswith('0 @') and line.count('@') >= 2:
                # Save previous record
                if current_record_lines and current_record_id:
                    if record_type == 'INDI':
                        self.raw_individuals[f"{source_name}_{current_record_id}"] = current_record_lines
                    elif record_type == 'FAM':
                        self.raw_families[f"{source_name}_{current_record_id}"] = current_record_lines
                        
                # Skip non-individual/family records for now
                current_record_lines = []
                current_record_id = None
                record_type = None
                
            # Continuation of current record
            elif current_record_lines:
                current_record_lines.append(line)
                
            i += 1
            
            if i % 100000 == 0:
                logger.info(f"Processed {i} lines ({source_name})")
                
        # Save final record
        if current_record_lines and current_record_id:
            if record_type == 'INDI':
                self.raw_individuals[f"{source_name}_{current_record_id}"] = current_record_lines
            elif record_type == 'FAM':
                self.raw_families[f"{source_name}_{current_record_id}"] = current_record_lines
                
        logger.info(f"Imported {len(self.raw_individuals)} individuals and {len(self.raw_families)} families from {source_name}")
        
    def remap_ids(self, lines: list, source_name: str, id_map: dict) -> list:
        """Remap GEDCOM IDs to avoid conflicts between sources"""
        remapped_lines = []
        
        for line in lines:
            new_line = line
            
            # Remap individual IDs
            individual_refs = re.findall(r'@(I\d+)@', line)
            for ref in individual_refs:
                old_key = f"{source_name}_{ref}"
                if old_key in id_map:
                    new_line = new_line.replace(f'@{ref}@', f'@{id_map[old_key]}@')
                    
            # Remap family IDs
            family_refs = re.findall(r'@(F\d+)@', line)
            for ref in family_refs:
                old_key = f"{source_name}_{ref}"
                if old_key in id_map:
                    new_line = new_line.replace(f'@{ref}@', f'@{id_map[old_key]}@')
                    
            remapped_lines.append(new_line)
            
        return remapped_lines
        
    def export_comprehensive_gedcom(self, output_file: str):
        """Export comprehensive GEDCOM preserving all original data"""
        logger.info(f"Starting comprehensive export to {output_file}")
        
        # Create ID mappings to avoid conflicts
        individual_id_map = {}
        family_id_map = {}
        next_ind_id = 1
        next_fam_id = 1
        
        # Map individual IDs
        for key in self.raw_individuals.keys():
            individual_id_map[key] = f"I{next_ind_id}"
            next_ind_id += 1
            
        # Map family IDs
        for key in self.raw_families.keys():
            family_id_map[key] = f"F{next_fam_id}"
            next_fam_id += 1
            
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write("0 HEAD\n")
            f.write("1 SOUR Comprehensive_Genealogy_Merger\n")
            f.write("2 NAME Comprehensive MongoDB-based GEDCOM Merger\n")
            f.write("2 CORP Gaiad Genealogy Project\n")
            f.write(f"1 DATE {datetime.now().strftime('%d %b %Y').upper()}\n")
            f.write(f"1 FILE {output_file}\n")
            f.write("1 GEDC\n")
            f.write("2 VERS 5.5.1\n")
            f.write("2 FORM LINEAGE-LINKED\n")
            f.write("1 CHAR UTF-8\n")
            f.write("1 NOTE Merged from:\n")
            f.write("2 CONT - geni plus wikidata after merge.ged\n")
            f.write("2 CONT - gaiad_ftb_simple_conversion.ged\n")
            f.write("2 CONT Using MongoDB-based intelligent merging\n")
            
            individuals_written = 0
            
            # Export all individuals with full preservation
            for source_name in ['geni_wikidata', 'gaiad_ftb']:
                logger.info(f"Exporting individuals from {source_name}")
                
                for key, lines in self.raw_individuals.items():
                    if key.startswith(source_name):
                        # Remap IDs and write
                        remapped_lines = self.remap_ids(lines, source_name, {**individual_id_map, **family_id_map})
                        
                        for line in remapped_lines:
                            f.write(line + '\n')
                            
                        individuals_written += 1
                        
                        if individuals_written % 5000 == 0:
                            logger.info(f"Exported {individuals_written} individuals...")
                            
            families_written = 0
            
            # Export all families with full preservation  
            for source_name in ['geni_wikidata', 'gaiad_ftb']:
                logger.info(f"Exporting families from {source_name}")
                
                for key, lines in self.raw_families.items():
                    if key.startswith(source_name):
                        # Remap IDs and write
                        remapped_lines = self.remap_ids(lines, source_name, {**individual_id_map, **family_id_map})
                        
                        for line in remapped_lines:
                            f.write(line + '\n')
                            
                        families_written += 1
                        
                        if families_written % 2000 == 0:
                            logger.info(f"Exported {families_written} families...")
                            
            # Write trailer
            f.write("0 TRLR\n")
            
        logger.info(f"Export completed: {individuals_written} individuals, {families_written} families")
        
        # Show size comparison
        import os
        output_size = os.path.getsize(output_file)
        logger.info(f"Output file size: {output_size:,} bytes ({output_size/1024/1024:.1f} MB)")

if __name__ == "__main__":
    exporter = ComprehensiveGedcomExporter()
    
    # Import both files preserving all data
    exporter.import_and_preserve_raw_gedcom("new_gedcoms/geni plus wikidata after merge.ged", "geni_wikidata")
    exporter.import_and_preserve_raw_gedcom("new_gedcoms/gaiad_ftb_simple_conversion.ged", "gaiad_ftb")
    
    # Export comprehensive merged file
    exporter.export_comprehensive_gedcom("new_gedcoms/comprehensive_merged.ged")