#!/usr/bin/env python3
"""
Full FTB (Family Tree Builder) to GEDCOM converter.
Extracts all individuals, families, facts, sources, and media from FTB SQLite database.
"""

import sqlite3
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FullFTBConverter:
    def __init__(self, ftb_file: str, output_gedcom: str):
        self.ftb_file = ftb_file
        self.output_gedcom = output_gedcom
        self.conn = None
        
    def connect(self):
        """Connect to FTB SQLite database"""
        self.conn = sqlite3.connect(self.ftb_file)
        self.conn.row_factory = sqlite3.Row  # Access columns by name
        
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            
    def get_all_individuals(self):
        """Get all individuals with their names"""
        cursor = self.conn.cursor()
        
        query = """
        SELECT DISTINCT 
            i.individual_id,
            i.gender,
            i.is_alive,
            i.guid,
            il.first_name,
            il.last_name,
            il.prefix,
            il.suffix,
            il.nickname,
            il.religious_name,
            il.former_name,
            il.married_surname,
            il.alias_name,
            il.aka
        FROM individual_main_data i
        LEFT JOIN individual_data_set ids ON i.individual_id = ids.individual_id
        LEFT JOIN individual_lang_data il ON ids.individual_data_set_id = il.individual_data_set_id
        WHERE i.delete_flag = 0
        ORDER BY i.individual_id
        """
        
        cursor.execute(query)
        individuals = cursor.fetchall()
        logger.info(f"Retrieved {len(individuals)} individuals")
        return individuals
        
    def get_individual_facts(self, individual_id: int):
        """Get all facts for an individual"""
        cursor = self.conn.cursor()
        
        query = """
        SELECT 
            if.fact_type,
            if.date,
            if.age,
            if.sorted_date,
            pl.place,
            ifl.header,
            ifl.cause_of_death
        FROM individual_fact_main_data if
        LEFT JOIN places_main_data pm ON if.place_id = pm.place_id
        LEFT JOIN places_lang_data pl ON pm.place_id = pl.place_id
        LEFT JOIN individual_fact_lang_data ifl ON if.individual_fact_id = ifl.individual_fact_id
        WHERE if.individual_id = ? AND if.delete_flag = 0
        ORDER BY if.sorted_date, if.individual_fact_id
        """
        
        cursor.execute(query, (individual_id,))
        return cursor.fetchall()
        
    def get_all_families(self):
        """Get all family records"""
        cursor = self.conn.cursor()
        
        query = """
        SELECT 
            f.family_id,
            f.status,
            f.guid
        FROM family_main_data f
        WHERE f.delete_flag = 0
        ORDER BY f.family_id
        """
        
        cursor.execute(query)
        families = cursor.fetchall()
        logger.info(f"Retrieved {len(families)} families")
        return families
        
    def get_family_members(self, family_id: int):
        """Get all members of a family"""
        cursor = self.conn.cursor()
        
        query = """
        SELECT 
            fc.individual_id,
            fc.individual_role_type,
            fc.child_order_in_family
        FROM family_individual_connection fc
        WHERE fc.family_id = ? AND fc.delete_flag = 0
        ORDER BY fc.individual_role_type, fc.child_order_in_family
        """
        
        cursor.execute(query, (family_id,))
        return cursor.fetchall()
        
    def get_family_facts(self, family_id: int):
        """Get facts for a family (marriages, etc.)"""
        cursor = self.conn.cursor()
        
        query = """
        SELECT 
            ff.fact_type,
            ff.date,
            ff.spouse_age,
            pl.place,
            ffl.header
        FROM family_fact_main_data ff
        LEFT JOIN places_main_data pm ON ff.place_id = pm.place_id
        LEFT JOIN places_lang_data pl ON pm.place_id = pl.place_id
        LEFT JOIN family_fact_lang_data ffl ON ff.family_fact_id = ffl.family_fact_id
        WHERE ff.family_id = ? AND ff.delete_flag = 0
        ORDER BY ff.sorted_date
        """
        
        cursor.execute(query, (family_id,))
        return cursor.fetchall()
        
    def get_all_sources(self):
        """Get all source records"""
        cursor = self.conn.cursor()
        
        query = """
        SELECT 
            s.source_id,
            sl.title,
            sl.abbreviation,
            sl.author,
            sl.publisher,
            sl.agency,
            sl.text,
            sl.type,
            sl.media
        FROM source_main_data s
        LEFT JOIN source_lang_data sl ON s.source_id = sl.source_id
        WHERE s.delete_flag = 0
        ORDER BY s.source_id
        """
        
        cursor.execute(query)
        sources = cursor.fetchall()
        logger.info(f"Retrieved {len(sources)} sources")
        return sources
        
    def format_name(self, individual):
        """Format individual name for GEDCOM"""
        name_parts = []
        
        if individual['prefix']:
            name_parts.append(individual['prefix'])
        if individual['first_name']:
            name_parts.append(individual['first_name'])
            
        given_name = ' '.join(name_parts) if name_parts else ''
        surname = individual['last_name'] or ''
        suffix = individual['suffix'] or ''
        
        name_line = f"{given_name} /{surname}/"
        if suffix:
            name_line += f" {suffix}"
            
        return name_line.strip()
        
    def map_fact_type(self, ftb_fact_type: str) -> str:
        """Map FTB fact types to GEDCOM tags"""
        mapping = {
            'Birth': 'BIRT',
            'Death': 'DEAT', 
            'Burial': 'BURI',
            'Baptism': 'BAPM',
            'Marriage': 'MARR',
            'Divorce': 'DIV',
            'Occupation': 'OCCU',
            'Residence': 'RESI',
            'Immigration': 'IMMI',
            'Emigration': 'EMIG',
            'Military': 'EVEN',
            'Education': 'EDUC',
            'Religion': 'RELI',
            'Census': 'CENS',
            'Graduation': 'GRAD',
            'Retirement': 'RETI',
        }
        return mapping.get(ftb_fact_type, 'EVEN')
        
    def convert_to_gedcom(self):
        """Convert FTB database to GEDCOM format"""
        logger.info("Starting FTB to GEDCOM conversion...")
        
        self.connect()
        
        try:
            # Get data
            individuals = self.get_all_individuals()
            families = self.get_all_families()
            sources = self.get_all_sources()
            
            # Write GEDCOM
            with open(self.output_gedcom, 'w', encoding='utf-8') as f:
                # Write header
                f.write("0 HEAD\n")
                f.write("1 SOUR FTB_Full_Converter\n")
                f.write("2 NAME Full FTB to GEDCOM Converter\n")
                f.write("2 VERS 1.0\n")
                f.write("1 DEST GEDCOM\n")
                f.write("1 GEDC\n")
                f.write("2 VERS 5.5.1\n")
                f.write("2 FORM LINEAGE-LINKED\n")
                f.write("1 CHAR UTF-8\n")
                f.write(f"1 DATE {datetime.now().strftime('%d %b %Y').upper()}\n")
                f.write(f"1 FILE {os.path.basename(self.output_gedcom)}\n")
                f.write(f"1 NOTE Converted from FTB file: {os.path.basename(self.ftb_file)}\n")
                f.write("\n")
                
                # Write individuals
                logger.info("Writing individuals...")
                for individual in individuals:
                    f.write(f"0 @I{individual['individual_id']}@ INDI\n")
                    
                    # Name
                    name = self.format_name(individual)
                    if name.strip():
                        f.write(f"1 NAME {name}\n")
                        
                    # Additional names
                    if individual['nickname']:
                        f.write(f"1 NAME {individual['nickname']}\n")
                        f.write("2 TYPE nickname\n")
                    if individual['religious_name']:
                        f.write(f"1 NAME {individual['religious_name']}\n")
                        f.write("2 TYPE religious\n")
                    if individual['former_name']:
                        f.write(f"1 NAME {individual['former_name']}\n")
                        f.write("2 TYPE former\n")
                    if individual['married_surname']:
                        f.write(f"1 NAME {individual['married_surname']}\n")
                        f.write("2 TYPE married\n")
                    if individual['alias_name']:
                        f.write(f"1 NAME {individual['alias_name']}\n")
                        f.write("2 TYPE alias\n")
                    if individual['aka']:
                        f.write(f"1 NAME {individual['aka']}\n")
                        f.write("2 TYPE aka\n")
                        
                    # Gender
                    if individual['gender']:
                        f.write(f"1 SEX {individual['gender']}\n")
                        
                    # GUID if available
                    if individual['guid']:
                        f.write(f"1 _UID {individual['guid']}\n")
                        
                    # Facts
                    facts = self.get_individual_facts(individual['individual_id'])
                    for fact in facts:
                        if fact['fact_type']:
                            gedcom_tag = self.map_fact_type(fact['fact_type'])
                            f.write(f"1 {gedcom_tag}\n")
                            
                            if fact['date']:
                                f.write(f"2 DATE {fact['date']}\n")
                            if fact['place']:
                                f.write(f"2 PLAC {fact['place']}\n")
                            if fact['header']:
                                f.write(f"2 NOTE {fact['header']}\n")
                            if fact['cause_of_death']:
                                f.write(f"2 CAUS {fact['cause_of_death']}\n")
                                
                    f.write("\n")
                
                # Write families
                logger.info("Writing families...")
                for family in families:
                    f.write(f"0 @F{family['family_id']}@ FAM\n")
                    
                    # Family members
                    members = self.get_family_members(family['family_id'])
                    for member in members:
                        role_type = member['individual_role_type']
                        individual_id = member['individual_id']
                        
                        # Role types: 1=Husband, 2=Wife, 3=Child
                        if role_type == 1:
                            f.write(f"1 HUSB @I{individual_id}@\n")
                        elif role_type == 2:
                            f.write(f"1 WIFE @I{individual_id}@\n")
                        elif role_type == 3:
                            f.write(f"1 CHIL @I{individual_id}@\n")
                            
                    # Family facts
                    family_facts = self.get_family_facts(family['family_id'])
                    for fact in family_facts:
                        if fact['fact_type']:
                            gedcom_tag = self.map_fact_type(fact['fact_type'])
                            f.write(f"1 {gedcom_tag}\n")
                            
                            if fact['date']:
                                f.write(f"2 DATE {fact['date']}\n")
                            if fact['place']:
                                f.write(f"2 PLAC {fact['place']}\n")
                            if fact['header']:
                                f.write(f"2 NOTE {fact['header']}\n")
                                
                    # GUID if available
                    if family['guid']:
                        f.write(f"1 _UID {family['guid']}\n")
                        
                    f.write("\n")
                
                # Write sources
                logger.info("Writing sources...")
                for source in sources:
                    if source['title'] or source['author'] or source['text']:
                        f.write(f"0 @S{source['source_id']}@ SOUR\n")
                        
                        if source['title']:
                            f.write(f"1 TITL {source['title']}\n")
                        if source['abbreviation']:
                            f.write(f"1 ABBR {source['abbreviation']}\n")
                        if source['author']:
                            f.write(f"1 AUTH {source['author']}\n")
                        if source['publisher']:
                            f.write(f"1 PUBL {source['publisher']}\n")
                        if source['text']:
                            f.write(f"1 TEXT {source['text']}\n")
                        if source['type']:
                            f.write(f"1 NOTE Type: {source['type']}\n")
                        if source['media']:
                            f.write(f"1 NOTE Media: {source['media']}\n")
                            
                        f.write("\n")
                
                # Write trailer
                f.write("0 TRLR\n")
                
            logger.info(f"Conversion complete!")
            logger.info(f"Output file: {self.output_gedcom}")
            logger.info(f"  Individuals: {len(individuals)}")
            logger.info(f"  Families: {len(families)}")
            logger.info(f"  Sources: {len([s for s in sources if s['title'] or s['author'] or s['text']])}")
            
        finally:
            self.close()

def main():
    ftb_file = "C:\\Users\\Immanuelle\\Documents\\Github\\Gaiad-Genealogy\\Gaiad with uncertain merging of the roman lines.ftb"
    output_file = "C:\\Users\\Immanuelle\\Documents\\Github\\Gaiad-Genealogy\\gaiad_full_ftb_converted.ged"
    
    if not os.path.exists(ftb_file):
        print(f"FTB file not found: {ftb_file}")
        return
        
    converter = FullFTBConverter(ftb_file, output_file)
    
    print("=== Full FTB to GEDCOM Converter ===")
    print(f"Input FTB: {ftb_file}")
    print(f"Size: {os.path.getsize(ftb_file) / (1024*1024):.1f} MB")
    print(f"Output GEDCOM: {output_file}")
    print()
    
    converter.convert_to_gedcom()
    
    if os.path.exists(output_file):
        print(f"Output file size: {os.path.getsize(output_file) / (1024*1024):.1f} MB")

if __name__ == "__main__":
    main()