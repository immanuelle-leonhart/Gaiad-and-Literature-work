#!/usr/bin/env python3
"""
MongoDB to GEDCOM Exporter
Final phase: Export merged and deduplicated genealogy data back to GEDCOM format
"""

import pymongo
from pymongo import MongoClient
from typing import Dict, List, Set, Optional, Any
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class MongoToGedcomExporter:
    def __init__(self, db_name: str = "genealogy_merge"):
        """Initialize MongoDB connection"""
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client[db_name]
        
        self.individuals = self.db.individuals
        self.families = self.db.families
        
        # ID mapping for GEDCOM export
        self.individual_id_map = {}
        self.family_id_map = {}
        self.next_individual_id = 1
        self.next_family_id = 1
        
    def generate_gedcom_header(self) -> str:
        """Generate GEDCOM header"""
        header = []
        header.append("0 HEAD")
        header.append("1 SOUR Advanced_Genealogy_Merger")
        header.append("2 NAME Advanced Genealogy Merger with MongoDB")
        header.append("2 CORP Gaiad Genealogy Project")
        header.append("1 DEST GEDCOM")
        header.append(f"1 DATE {datetime.now().strftime('%d %b %Y').upper()}")
        header.append("1 FILE merged_genealogy.ged")
        header.append("1 GEDC")
        header.append("2 VERS 5.5.1")
        header.append("2 FORM LINEAGE-LINKED")
        header.append("1 CHAR UTF-8")
        header.append("1 NOTE Merged genealogical data from multiple sources")
        header.append("2 CONT Includes Geni, Wikidata, and FTB data")
        header.append("2 CONT Processed with advanced deduplication")
        
        return '\n'.join(header) + '\n'
        
    def get_individual_gedcom_id(self, mongo_id: str) -> str:
        """Get or create GEDCOM ID for an individual"""
        if mongo_id not in self.individual_id_map:
            self.individual_id_map[mongo_id] = f"I{self.next_individual_id}"
            self.next_individual_id += 1
        return self.individual_id_map[mongo_id]
        
    def get_family_gedcom_id(self, mongo_id: str) -> str:
        """Get or create GEDCOM ID for a family"""
        if mongo_id not in self.family_id_map:
            self.family_id_map[mongo_id] = f"F{self.next_family_id}"
            self.next_family_id += 1
        return self.family_id_map[mongo_id]
        
    def format_individual_name(self, names: List[Dict]) -> str:
        """Format individual name for GEDCOM"""
        if not names:
            return "Unknown /Unknown/"
            
        # Use the first name entry, or find the most complete one
        best_name = names[0]
        for name in names:
            if name.get('given') and name.get('surname'):
                best_name = name
                break
                
        given = best_name.get('given', '')
        surname = best_name.get('surname', '')
        
        if surname:
            return f"{given} /{surname}/"
        elif given:
            return f"{given} //"
        else:
            return best_name.get('full', 'Unknown /Unknown/')
            
    def format_date(self, date_str: str) -> str:
        """Format date for GEDCOM"""
        if not date_str:
            return ""
            
        # Simple date formatting - would need more sophisticated parsing
        # GEDCOM prefers DD MMM YYYY format
        return date_str  # For now, pass through as-is
        
    def export_individual(self, individual: Dict) -> str:
        """Export individual record to GEDCOM format"""
        lines = []
        
        # Get GEDCOM ID
        gedcom_id = self.get_individual_gedcom_id(str(individual['_id']))
        lines.append(f"0 @{gedcom_id}@ INDI")
        
        # Name
        if individual.get('names'):
            name_line = self.format_individual_name(individual['names'])
            lines.append(f"1 NAME {name_line}")
            
            # Additional names
            all_names = individual.get('all_names', [])
            for alt_name in all_names[1:5]:  # Limit to 5 total names
                if alt_name != individual['names'][0].get('full', ''):
                    lines.append(f"1 NAME {alt_name}")
                    
        # Sex
        if individual.get('sex'):
            lines.append(f"1 SEX {individual['sex']}")
            
        # Birth
        birth_info = individual.get('dates', {}).get('birth', {})
        if birth_info:
            lines.append("1 BIRT")
            if birth_info.get('date'):
                formatted_date = self.format_date(birth_info['date'])
                if formatted_date:
                    lines.append(f"2 DATE {formatted_date}")
            if birth_info.get('place'):
                lines.append(f"2 PLAC {birth_info['place']}")
                
        # Death
        death_info = individual.get('dates', {}).get('death', {})
        if death_info:
            lines.append("1 DEAT")
            if death_info.get('date'):
                formatted_date = self.format_date(death_info['date'])
                if formatted_date:
                    lines.append(f"2 DATE {formatted_date}")
            if death_info.get('place'):
                lines.append(f"2 PLAC {death_info['place']}")
                
        # Geni IDs
        geni_ids = individual.get('all_geni_ids', [])
        if not geni_ids and individual.get('geni_id'):
            geni_ids = [individual['geni_id']]
        for geni_id in geni_ids:
            lines.append(f"1 REFN geni:{geni_id}")
            
        # Wikidata IDs
        wikidata_ids = individual.get('all_wikidata_ids', [])
        if not wikidata_ids and individual.get('wikidata_id'):
            wikidata_ids = [individual['wikidata_id']]
        for wikidata_id in wikidata_ids:
            lines.append(f"1 REFN wikidata:{wikidata_id}")
            
        # UID
        if individual.get('uid'):
            lines.append(f"1 _UID {individual['uid']}")
            
        # Notes
        notes_parts = []
        if individual.get('notes'):
            notes_parts.append(individual['notes'])
        if individual.get('merged_notes'):
            notes_parts.append("=== MERGED NOTES ===")
            notes_parts.append(individual['merged_notes'])
            
        if notes_parts:
            full_notes = '\n'.join(notes_parts)
            lines.append(f"1 NOTE {self.format_multiline_text(full_notes)}")
            
        # Family relationships
        for fam_id in individual.get('families_as_spouse', []):
            gedcom_fam_id = self.get_family_gedcom_id(fam_id)
            lines.append(f"1 FAMS @{gedcom_fam_id}@")
            
        for fam_id in individual.get('families_as_child', []):
            gedcom_fam_id = self.get_family_gedcom_id(fam_id)
            lines.append(f"1 FAMC @{gedcom_fam_id}@")
            
        # Source information
        if individual.get('source_file'):
            lines.append(f"1 NOTE Source: {individual['source_file']}")
            
        return '\n'.join(lines) + '\n'
        
    def format_multiline_text(self, text: str) -> str:
        """Format multiline text for GEDCOM"""
        lines = text.split('\n')
        if not lines:
            return ""
            
        # First line goes after NOTE
        result = lines[0] if lines else ""
        
        # Additional lines use CONT
        for line in lines[1:]:
            result += f"\n2 CONT {line}"
            
        return result
        
    def export_family(self, family: Dict) -> str:
        """Export family record to GEDCOM format"""
        lines = []
        
        # Get GEDCOM ID
        gedcom_id = self.get_family_gedcom_id(str(family['_id']))
        lines.append(f"0 @{gedcom_id}@ FAM")
        
        # Husband
        if family.get('husband_id'):
            husband_gedcom_id = self.get_individual_gedcom_id(family['husband_id'])
            lines.append(f"1 HUSB @{husband_gedcom_id}@")
            
        # Wife  
        if family.get('wife_id'):
            wife_gedcom_id = self.get_individual_gedcom_id(family['wife_id'])
            lines.append(f"1 WIFE @{wife_gedcom_id}@")
            
        # Children
        for child_id in family.get('children', []):
            child_gedcom_id = self.get_individual_gedcom_id(child_id)
            lines.append(f"1 CHIL @{child_gedcom_id}@")
            
        return '\n'.join(lines) + '\n'
        
    def export_to_gedcom(self, output_file: str, include_merged: bool = False):
        """Export the entire database to GEDCOM format"""
        logger.info(f"Starting GEDCOM export to {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write(self.generate_gedcom_header())
            
            # Export individuals
            individual_query = {}
            if not include_merged:
                individual_query['merged'] = {'$ne': True}
                
            individuals_exported = 0
            for individual in self.individuals.find(individual_query):
                gedcom_record = self.export_individual(individual)
                f.write(gedcom_record)
                individuals_exported += 1
                
                if individuals_exported % 1000 == 0:
                    logger.info(f"Exported {individuals_exported} individuals...")
                    
            # Export families
            families_exported = 0
            for family in self.families.find():
                gedcom_record = self.export_family(family)
                f.write(gedcom_record)
                families_exported += 1
                
            # Write trailer
            f.write("0 TRLR\n")
            
        logger.info(f"Export completed: {individuals_exported} individuals, {families_exported} families")
        
    def create_merge_report(self, output_file: str):
        """Create a report of the merge process"""
        logger.info("Creating merge report...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Genealogy Merge Report\n\n")
            f.write(f"Generated: {datetime.now()}\n\n")
            
            # Statistics
            total_individuals = self.individuals.count_documents({})
            merged_individuals = self.individuals.count_documents({'merged': True})
            active_individuals = self.individuals.count_documents({'merged': {'$ne': True}})
            
            f.write("## Statistics\n\n")
            f.write(f"- Total individuals in database: {total_individuals}\n")
            f.write(f"- Merged (duplicate) individuals: {merged_individuals}\n")
            f.write(f"- Active individuals: {active_individuals}\n")
            f.write(f"- Total families: {self.families.count_documents({})}\n\n")
            
            # Source breakdown
            f.write("## Source File Breakdown\n\n")
            for source in self.individuals.distinct('source_file'):
                count = self.individuals.count_documents({'source_file': source, 'merged': {'$ne': True}})
                f.write(f"- {source}: {count} active individuals\n")
                
            f.write("\n## Merge Process Summary\n\n")
            f.write("This merge process:\n")
            f.write("1. Imported GEDCOM files into MongoDB\n")
            f.write("2. Performed internal deduplication within source files\n") 
            f.write("3. Matched individuals across different source files\n")
            f.write("4. Merged duplicate records preserving all reference IDs\n")
            f.write("5. Exported clean, merged data back to GEDCOM format\n")
            
        logger.info(f"Merge report created: {output_file}")

if __name__ == "__main__":
    exporter = MongoToGedcomExporter()
    
    # Export merged data to GEDCOM
    exporter.export_to_gedcom("new_gedcoms/merged_genealogy.ged")
    
    # Create merge report
    exporter.create_merge_report("merge_report.md")
    
    logger.info("Export process completed")