#!/usr/bin/env python3
"""
Full FTB (Family Tree Builder) to GEDCOM converter with encoding fixes.
Handles problematic characters and data encoding issues.
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
        # Set text encoding to handle problematic characters
        self.conn.text_factory = lambda x: x.decode('utf-8', 'replace') if isinstance(x, bytes) else x
        
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            
    def safe_string(self, value):
        """Safely convert value to string, handling encoding issues"""
        if value is None:
            return ""
        try:
            if isinstance(value, bytes):
                return value.decode('utf-8', 'replace')
            else:
                return str(value).replace('\x00', '').replace('\n', ' ').replace('\r', ' ')
        except:
            return str(value).encode('ascii', 'replace').decode('ascii')
            
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
        """Get all facts for an individual with safe string handling"""
        cursor = self.conn.cursor()
        
        try:
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
            raw_facts = cursor.fetchall()
            
            # Process each fact to handle encoding issues
            safe_facts = []
            for fact in raw_facts:
                safe_fact = {
                    'fact_type': self.safe_string(fact['fact_type']),
                    'date': self.safe_string(fact['date']),
                    'age': self.safe_string(fact['age']),
                    'place': self.safe_string(fact['place']),
                    'header': self.safe_string(fact['header']),
                    'cause_of_death': self.safe_string(fact['cause_of_death'])
                }
                safe_facts.append(safe_fact)
                
            return safe_facts
            
        except Exception as e:
            logger.warning(f"Error getting facts for individual {individual_id}: {e}")
            return []
        
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
        """Get facts for a family with safe string handling"""
        cursor = self.conn.cursor()
        
        try:
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
            raw_facts = cursor.fetchall()
            
            # Process each fact safely
            safe_facts = []
            for fact in raw_facts:
                safe_fact = {
                    'fact_type': self.safe_string(fact['fact_type']),
                    'date': self.safe_string(fact['date']),
                    'spouse_age': self.safe_string(fact['spouse_age']),
                    'place': self.safe_string(fact['place']),
                    'header': self.safe_string(fact['header'])
                }
                safe_facts.append(safe_fact)
                
            return safe_facts
            
        except Exception as e:
            logger.warning(f"Error getting family facts for family {family_id}: {e}")
            return []
        
    def get_all_sources(self):
        """Get all source records with safe string handling"""
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
        raw_sources = cursor.fetchall()
        
        # Process sources safely
        safe_sources = []
        for source in raw_sources:
            safe_source = {
                'source_id': source['source_id'],
                'title': self.safe_string(source['title']),
                'abbreviation': self.safe_string(source['abbreviation']),
                'author': self.safe_string(source['author']),
                'publisher': self.safe_string(source['publisher']),
                'agency': self.safe_string(source['agency']),
                'text': self.safe_string(source['text']),
                'type': self.safe_string(source['type']),
                'media': self.safe_string(source['media'])
            }
            safe_sources.append(safe_source)
            
        logger.info(f"Retrieved {len(safe_sources)} sources")
        return safe_sources
        
    def format_name(self, individual):
        """Format individual name for GEDCOM"""
        name_parts = []
        
        prefix = self.safe_string(individual['prefix'])
        first_name = self.safe_string(individual['first_name'])
        last_name = self.safe_string(individual['last_name'])
        suffix = self.safe_string(individual['suffix'])
        
        if prefix:
            name_parts.append(prefix)
        if first_name:
            name_parts.append(first_name)
            
        given_name = ' '.join(name_parts) if name_parts else ''
        surname = last_name or ''
        
        name_line = f"{given_name} /{surname}/"
        if suffix:
            name_line += f" {suffix}"
            
        return name_line.strip()
        
    def map_fact_type(self, ftb_fact_type: str) -> str:
        """Map FTB fact types to GEDCOM tags"""
        if not ftb_fact_type:
            return 'EVEN'
            
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
                individual_count = 0
                for individual in individuals:
                    individual_count += 1
                    if individual_count % 1000 == 0:
                        logger.info(f"  Processed {individual_count} individuals...")
                        
                    f.write(f"0 @I{individual['individual_id']}@ INDI\n")
                    
                    # Name
                    name = self.format_name(individual)
                    if name.strip() and name != " //":
                        f.write(f"1 NAME {name}\n")
                        
                    # Additional names
                    nickname = self.safe_string(individual['nickname'])
                    religious_name = self.safe_string(individual['religious_name'])
                    former_name = self.safe_string(individual['former_name'])
                    married_surname = self.safe_string(individual['married_surname'])
                    alias_name = self.safe_string(individual['alias_name'])
                    aka = self.safe_string(individual['aka'])
                    
                    if nickname:
                        f.write(f"1 NAME {nickname}\n")
                        f.write("2 TYPE nickname\n")
                    if religious_name:
                        f.write(f"1 NAME {religious_name}\n")
                        f.write("2 TYPE religious\n")
                    if former_name:
                        f.write(f"1 NAME {former_name}\n")
                        f.write("2 TYPE former\n")
                    if married_surname:
                        f.write(f"1 NAME {married_surname}\n")
                        f.write("2 TYPE married\n")
                    if alias_name:
                        f.write(f"1 NAME {alias_name}\n")
                        f.write("2 TYPE alias\n")
                    if aka:
                        f.write(f"1 NAME {aka}\n")
                        f.write("2 TYPE aka\n")
                        
                    # Gender
                    gender = self.safe_string(individual['gender'])
                    if gender:
                        f.write(f"1 SEX {gender}\n")
                        
                    # GUID if available
                    guid = self.safe_string(individual['guid'])
                    if guid:
                        f.write(f"1 _UID {guid}\n")
                        
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
                family_count = 0
                for family in families:
                    family_count += 1
                    if family_count % 1000 == 0:
                        logger.info(f"  Processed {family_count} families...")
                        
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
                    guid = self.safe_string(family['guid'])
                    if guid:
                        f.write(f"1 _UID {guid}\n")
                        
                    f.write("\n")
                
                # Write sources
                logger.info("Writing sources...")
                source_count = 0
                for source in sources:
                    if source['title'] or source['author'] or source['text']:
                        source_count += 1
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
            logger.info(f"  Individuals: {individual_count}")
            logger.info(f"  Families: {family_count}")
            logger.info(f"  Sources: {source_count}")
            
        finally:
            self.close()

def main():
    ftb_file = "C:\\Users\\Immanuelle\\Documents\\Github\\Gaiad-Genealogy\\Gaiad with uncertain merging of the roman lines.ftb"
    output_file = "C:\\Users\\Immanuelle\\Documents\\Github\\Gaiad-Genealogy\\gaiad_full_ftb_converted.ged"
    
    if not os.path.exists(ftb_file):
        print(f"FTB file not found: {ftb_file}")
        return
        
    converter = FullFTBConverter(ftb_file, output_file)
    
    print("=== Full FTB to GEDCOM Converter (Fixed) ===")
    print(f"Input FTB: {ftb_file}")
    print(f"Size: {os.path.getsize(ftb_file) / (1024*1024):.1f} MB")
    print(f"Output GEDCOM: {output_file}")
    print()
    
    converter.convert_to_gedcom()
    
    if os.path.exists(output_file):
        print(f"Output file size: {os.path.getsize(output_file) / (1024*1024):.1f} MB")

if __name__ == "__main__":
    main()