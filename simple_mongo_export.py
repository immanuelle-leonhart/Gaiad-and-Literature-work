#!/usr/bin/env python3
"""
Simple MongoDB to GEDCOM exporter - no complex merging
"""

import pymongo
from pymongo import MongoClient
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleMongoExporter:
    def __init__(self, db_name: str = "genealogy_merge"):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client[db_name]
        self.individuals = self.db.individuals
        self.families = self.db.families
        
        self.individual_id_map = {}
        self.family_id_map = {}
        self.next_individual_id = 1
        self.next_family_id = 1
        
    def get_individual_gedcom_id(self, gedcom_id: str, source_file: str) -> str:
        """Generate unique GEDCOM ID"""
        key = f"{source_file}_{gedcom_id}"
        if key not in self.individual_id_map:
            self.individual_id_map[key] = f"I{self.next_individual_id}"
            self.next_individual_id += 1
        return self.individual_id_map[key]
        
    def get_family_gedcom_id(self, gedcom_id: str, source_file: str) -> str:
        """Generate unique GEDCOM ID for family"""
        key = f"{source_file}_{gedcom_id}"
        if key not in self.family_id_map:
            self.family_id_map[key] = f"F{self.next_family_id}"
            self.next_family_id += 1
        return self.family_id_map[key]
        
    def export_individual(self, individual: dict) -> str:
        """Export individual to GEDCOM format"""
        lines = []
        
        gedcom_id = self.get_individual_gedcom_id(
            individual.get('gedcom_id', 'UNKNOWN'), 
            individual.get('source_file', 'UNKNOWN')
        )
        
        lines.append(f"0 @{gedcom_id}@ INDI")
        
        # Name
        if individual.get('names') and individual['names']:
            name = individual['names'][0].get('full', 'Unknown /Unknown/')
            lines.append(f"1 NAME {name}")
            
        # Sex
        if individual.get('sex'):
            lines.append(f"1 SEX {individual['sex']}")
            
        # Geni ID
        if individual.get('geni_id'):
            lines.append(f"1 REFN geni:{individual['geni_id']}")
            
        # Wikidata ID
        if individual.get('wikidata_id'):
            lines.append(f"1 REFN wikidata:{individual['wikidata_id']}")
            
        # UID
        if individual.get('uid'):
            lines.append(f"1 _UID {individual['uid']}")
            
        # Notes
        if individual.get('notes'):
            lines.append(f"1 NOTE {individual['notes']}")
            
        # Source
        lines.append(f"1 NOTE Source: {individual.get('source_file', 'Unknown')}")
        
        return '\n'.join(lines) + '\n'
        
    def export_to_gedcom(self, output_file: str):
        """Export all individuals to GEDCOM"""
        logger.info(f"Starting export to {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("0 HEAD\n")
            f.write("1 SOUR Combined_Genealogy\n")
            f.write("2 NAME Combined Genealogy Export\n")
            f.write(f"1 DATE {datetime.now().strftime('%d %b %Y').upper()}\n")
            f.write(f"1 FILE {output_file}\n")
            f.write("1 GEDC\n")
            f.write("2 VERS 5.5.1\n")
            f.write("2 FORM LINEAGE-LINKED\n")
            f.write("1 CHAR UTF-8\n")
            
            # Export individuals (skip merged ones if they exist)
            count = 0
            query = {'merged': {'$ne': True}}
            
            for individual in self.individuals.find(query):
                gedcom_record = self.export_individual(individual)
                f.write(gedcom_record)
                count += 1
                
                if count % 5000 == 0:
                    logger.info(f"Exported {count} individuals...")
                    
            # Trailer
            f.write("0 TRLR\n")
            
        logger.info(f"Export completed: {count} individuals")
        
        # Print statistics
        total = self.individuals.count_documents({})
        merged = self.individuals.count_documents({'merged': True})
        geni_wikidata = self.individuals.count_documents({'source_file': 'geni_wikidata', 'merged': {'$ne': True}})
        gaiad_ftb = self.individuals.count_documents({'source_file': 'gaiad_ftb', 'merged': {'$ne': True}})
        
        print(f"\n=== EXPORT STATISTICS ===")
        print(f"Total individuals in DB: {total}")
        print(f"Merged/duplicate individuals: {merged}")
        print(f"Exported individuals: {count}")
        print(f"From geni_wikidata source: {geni_wikidata}")
        print(f"From gaiad_ftb source: {gaiad_ftb}")

if __name__ == "__main__":
    exporter = SimpleMongoExporter()
    exporter.export_to_gedcom("new_gedcoms/combined_genealogy.ged")