#!/usr/bin/env python3
"""
Comprehensive FTB (Family Tree Builder) to GEDCOM Converter
Extracts all genealogical data from FTB SQLite database and converts to proper GEDCOM format
"""

import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveFtbConverter:
    def __init__(self, ftb_file: str):
        self.ftb_file = ftb_file
        self.conn = None
        self.individuals = {}  # individual_id -> individual_data
        self.families = {}     # family_id -> family_data
        self.next_family_id = 1
        
    def connect_database(self):
        """Connect to the FTB SQLite database"""
        try:
            self.conn = sqlite3.connect(self.ftb_file)
            self.conn.row_factory = sqlite3.Row  # Enable column access by name
            logger.info(f"Connected to FTB database: {self.ftb_file}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
            
    def get_table_info(self):
        """Get information about all tables in the database"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        logger.info("Available tables:")
        for table in tables:
            table_name = table['name']
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            logger.info(f"  {table_name}: {len(columns)} columns")
            for col in columns:
                logger.info(f"    {col['name']} ({col['type']})")
                
        return tables
        
    def extract_individuals(self):
        """Extract all individuals from the database"""
        cursor = self.conn.cursor()
        
        # Get main individual data
        query = """
        SELECT 
            imd.individual_id,
            imd.gender,
            imd.privacy_level,
            imd.is_alive,
            imd.guid,
            imd.last_update,
            imd.create_timestamp
        FROM individual_main_data imd
        WHERE imd.delete_flag = 0
        ORDER BY imd.individual_id
        """
        
        cursor.execute(query)
        individuals = cursor.fetchall()
        logger.info(f"Found {len(individuals)} individuals")
        
        for individual in individuals:
            individual_id = individual['individual_id']
            
            # Get name data for this individual
            name_query = """
            SELECT 
                ild.first_name,
                ild.last_name,
                ild.prefix,
                ild.suffix,
                ild.nickname,
                ild.religious_name,
                ild.former_name,
                ild.married_surname,
                ild.alias_name,
                ild.aka
            FROM individual_lang_data ild
            JOIN individual_data_set ids ON ild.individual_data_set_id = ids.individual_data_set_id
            WHERE ids.individual_id = ? AND ids.delete_flag = 0
            ORDER BY ild.individual_lang_data_id
            """
            
            cursor.execute(name_query, (individual_id,))
            names = cursor.fetchall()
            
            # Build individual record
            individual_data = {
                'individual_id': individual_id,
                'gender': individual['gender'] if individual['gender'] in ['M', 'F'] else 'U',
                'privacy_level': individual['privacy_level'],
                'is_alive': individual['is_alive'],
                'guid': individual['guid'],
                'last_update': individual['last_update'],
                'names': [],
                'birth': None,
                'death': None,
                'events': [],
                'notes': [],
                'sources': [],
                'families_as_spouse': [],
                'families_as_child': []
            }
            
            # Process names
            for name in names:
                name_data = {
                    'first_name': name['first_name'] or '',
                    'last_name': name['last_name'] or '',
                    'prefix': name['prefix'] or '',
                    'suffix': name['suffix'] or '',
                    'nickname': name['nickname'] or '',
                    'religious_name': name['religious_name'] or '',
                    'former_name': name['former_name'] or '',
                    'married_surname': name['married_surname'] or '',
                    'alias_name': name['alias_name'] or '',
                    'aka': name['aka'] or ''
                }
                individual_data['names'].append(name_data)
                
            self.individuals[individual_id] = individual_data
            
        logger.info(f"Extracted {len(self.individuals)} individuals with name data")
        
    def extract_families(self):
        """Extract family relationships from the database"""
        cursor = self.conn.cursor()
        
        # Look for family-related tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%family%'")
        family_tables = cursor.fetchall()
        
        logger.info(f"Found family tables: {[t['name'] for t in family_tables]}")
        
        # Try to find family relationship data
        # Check for common family table names
        possible_family_queries = [
            "SELECT * FROM family_main_data WHERE delete_flag = 0",
            "SELECT * FROM families WHERE delete_flag = 0", 
            "SELECT * FROM family WHERE delete_flag = 0",
            "SELECT * FROM family_data WHERE delete_flag = 0"
        ]
        
        family_data_found = False
        
        for query in possible_family_queries:
            try:
                cursor.execute(query)
                families = cursor.fetchall()
                if families:
                    logger.info(f"Found {len(families)} families using query: {query}")
                    family_data_found = True
                    self.process_family_records(families, cursor)
                    break
            except sqlite3.OperationalError:
                continue
                
        if not family_data_found:
            logger.warning("No family table found, attempting to reconstruct from relationships")
            self.reconstruct_families_from_relationships(cursor)
            
    def process_family_records(self, families, cursor):
        """Process explicit family records"""
        for family in families:
            family_id = f"F{self.next_family_id}"
            self.next_family_id += 1
            
            family_data = {
                'family_id': family_id,
                'husband_id': None,
                'wife_id': None,
                'children': [],
                'marriage_date': None,
                'marriage_place': None,
                'events': []
            }
            
            # Extract family members based on available columns
            if 'husband_id' in family.keys():
                family_data['husband_id'] = family['husband_id']
            if 'wife_id' in family.keys():
                family_data['wife_id'] = family['wife_id']
                
            # Look for children
            if 'family_id' in family.keys():
                original_family_id = family['family_id']
                child_query = "SELECT individual_id FROM individual_family_child WHERE family_id = ?"
                try:
                    cursor.execute(child_query, (original_family_id,))
                    children = cursor.fetchall()
                    family_data['children'] = [child['individual_id'] for child in children]
                except sqlite3.OperationalError:
                    pass
                    
            self.families[family_id] = family_data
            
            # Update individual records with family references
            if family_data['husband_id'] and family_data['husband_id'] in self.individuals:
                self.individuals[family_data['husband_id']]['families_as_spouse'].append(family_id)
            if family_data['wife_id'] and family_data['wife_id'] in self.individuals:
                self.individuals[family_data['wife_id']]['families_as_spouse'].append(family_id)
                
            for child_id in family_data['children']:
                if child_id in self.individuals:
                    self.individuals[child_id]['families_as_child'].append(family_id)
                    
    def reconstruct_families_from_relationships(self, cursor):
        """Reconstruct family relationships from relationship tables"""
        logger.info("Attempting to reconstruct families from relationships...")
        
        # Look for relationship tables
        relationship_queries = [
            "SELECT * FROM individual_relationship WHERE delete_flag = 0",
            "SELECT * FROM relationships WHERE delete_flag = 0",
            "SELECT * FROM person_relationship WHERE delete_flag = 0"
        ]
        
        for query in relationship_queries:
            try:
                cursor.execute(query)
                relationships = cursor.fetchall()
                if relationships:
                    logger.info(f"Found {len(relationships)} relationships")
                    self.build_families_from_relationships(relationships)
                    return
            except sqlite3.OperationalError:
                continue
                
        logger.warning("No relationship data found - families may be incomplete")
        
    def build_families_from_relationships(self, relationships):
        """Build family structures from relationship records"""
        spouse_pairs = {}  # (person1, person2) -> family_data
        parent_child = {}  # parent_id -> [child_ids]
        
        for rel in relationships:
            if 'relationship_type' in rel.keys():
                rel_type = rel['relationship_type']
                person1 = rel.get('individual_id_1') or rel.get('person1_id')
                person2 = rel.get('individual_id_2') or rel.get('person2_id')
                
                if not person1 or not person2:
                    continue
                    
                # Handle spouse relationships
                if rel_type in ['spouse', 'husband', 'wife', 'married']:
                    pair_key = tuple(sorted([person1, person2]))
                    if pair_key not in spouse_pairs:
                        family_id = f"F{self.next_family_id}"
                        self.next_family_id += 1
                        
                        # Determine who is husband/wife
                        husband_id = None
                        wife_id = None
                        
                        if person1 in self.individuals and self.individuals[person1]['gender'] == 'M':
                            husband_id = person1
                        elif person2 in self.individuals and self.individuals[person2]['gender'] == 'M':
                            husband_id = person2
                            
                        if person1 in self.individuals and self.individuals[person1]['gender'] == 'F':
                            wife_id = person1
                        elif person2 in self.individuals and self.individuals[person2]['gender'] == 'F':
                            wife_id = person2
                            
                        spouse_pairs[pair_key] = {
                            'family_id': family_id,
                            'husband_id': husband_id,
                            'wife_id': wife_id,
                            'children': []
                        }
                        
                # Handle parent-child relationships
                elif rel_type in ['parent', 'father', 'mother', 'child', 'son', 'daughter']:
                    parent_id = person1 if rel_type in ['child', 'son', 'daughter'] else person1
                    child_id = person2 if rel_type in ['child', 'son', 'daughter'] else person2
                    
                    if parent_id not in parent_child:
                        parent_child[parent_id] = []
                    parent_child[parent_id].append(child_id)
                    
        # Merge spouse pairs with their children
        for pair_key, family_data in spouse_pairs.items():
            husband_id = family_data['husband_id']
            wife_id = family_data['wife_id']
            
            # Find children for this couple
            husband_children = parent_child.get(husband_id, [])
            wife_children = parent_child.get(wife_id, [])
            
            # Children should be in both lists for married couples
            common_children = list(set(husband_children) & set(wife_children))
            family_data['children'] = common_children
            
            self.families[family_data['family_id']] = family_data
            
        logger.info(f"Reconstructed {len(self.families)} families from relationships")
        
    def extract_events_and_facts(self):
        """Extract birth, death, and other events"""
        cursor = self.conn.cursor()
        
        # Look for event tables
        event_queries = [
            "SELECT * FROM individual_event WHERE delete_flag = 0",
            "SELECT * FROM events WHERE delete_flag = 0",
            "SELECT * FROM individual_fact WHERE delete_flag = 0",
            "SELECT * FROM facts WHERE delete_flag = 0"
        ]
        
        for query in event_queries:
            try:
                cursor.execute(query)
                events = cursor.fetchall()
                if events:
                    logger.info(f"Found {len(events)} events/facts")
                    self.process_events(events)
                    return
            except sqlite3.OperationalError:
                continue
                
        logger.warning("No event data found")
        
    def process_events(self, events):
        """Process event records and add to individuals"""
        for event in events:
            individual_id = event.get('individual_id')
            if not individual_id or individual_id not in self.individuals:
                continue
                
            event_type = event.get('event_type') or event.get('fact_type', '')
            event_date = event.get('event_date') or event.get('date', '')
            event_place = event.get('event_place') or event.get('place', '')
            
            event_data = {
                'type': event_type,
                'date': event_date,
                'place': event_place
            }
            
            # Special handling for birth and death
            if event_type.lower() in ['birth', 'born']:
                self.individuals[individual_id]['birth'] = event_data
            elif event_type.lower() in ['death', 'died', 'burial']:
                self.individuals[individual_id]['death'] = event_data
            else:
                self.individuals[individual_id]['events'].append(event_data)
                
    def write_gedcom(self, output_file: str):
        """Write the extracted data to GEDCOM format"""
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write("0 HEAD\n")
            f.write("1 SOUR Comprehensive_FTB_Converter\n")
            f.write("2 NAME Comprehensive FTB to GEDCOM Converter\n")
            f.write("2 CORP Gaiad Genealogy Project\n")
            f.write(f"1 DATE {datetime.now().strftime('%d %b %Y')}\n")
            f.write(f"1 FILE {output_file}\n")
            f.write("1 GEDC\n")
            f.write("2 VERS 5.5.1\n")
            f.write("2 FORM LINEAGE-LINKED\n")
            f.write("1 CHAR UTF-8\n")
            f.write(f"1 NOTE Converted from FTB file: {self.ftb_file}\n")
            
            # Write individuals
            for individual_id, individual in self.individuals.items():
                f.write(f"0 @I{individual_id}@ INDI\n")
                
                # Write names
                if individual['names']:
                    for name_idx, name in enumerate(individual['names']):
                        # Build full name
                        name_parts = []
                        if name['prefix']:
                            name_parts.append(name['prefix'])
                        if name['first_name']:
                            name_parts.append(name['first_name'])
                            
                        given_name = ' '.join(name_parts)
                        surname = name['last_name']
                        
                        full_name = f"{given_name} /{surname}/" if surname else given_name
                        
                        f.write(f"1 NAME {full_name}\n")
                        if given_name:
                            f.write(f"2 GIVN {given_name}\n")
                        if surname:
                            f.write(f"2 SURN {surname}\n")
                        if name['suffix']:
                            f.write(f"2 NSFX {name['suffix']}\n")
                        if name['nickname']:
                            f.write(f"2 NICK {name['nickname']}\n")
                            
                        # Only write primary name
                        if name_idx == 0:
                            break
                            
                # Write gender
                f.write(f"1 SEX {individual['gender']}\n")
                
                # Write birth
                if individual['birth']:
                    f.write("1 BIRT\n")
                    if individual['birth']['date']:
                        f.write(f"2 DATE {individual['birth']['date']}\n")
                    if individual['birth']['place']:
                        f.write(f"2 PLAC {individual['birth']['place']}\n")
                        
                # Write death
                if individual['death']:
                    f.write("1 DEAT\n")
                    if individual['death']['date']:
                        f.write(f"2 DATE {individual['death']['date']}\n")
                    if individual['death']['place']:
                        f.write(f"2 PLAC {individual['death']['place']}\n")
                        
                # Write family references
                for family_id in individual['families_as_spouse']:
                    f.write(f"1 FAMS @{family_id}@\n")
                for family_id in individual['families_as_child']:
                    f.write(f"1 FAMC @{family_id}@\n")
                    
                # Write GUID as reference number
                if individual['guid']:
                    f.write(f"1 REFN {individual['guid']}\n")
                    
            # Write families
            for family_id, family in self.families.items():
                f.write(f"0 @{family_id}@ FAM\n")
                
                if family['husband_id']:
                    f.write(f"1 HUSB @I{family['husband_id']}@\n")
                if family['wife_id']:
                    f.write(f"1 WIFE @I{family['wife_id']}@\n")
                    
                for child_id in family['children']:
                    f.write(f"1 CHIL @I{child_id}@\n")
                    
                # Write marriage event if available
                if family.get('marriage_date') or family.get('marriage_place'):
                    f.write("1 MARR\n")
                    if family.get('marriage_date'):
                        f.write(f"2 DATE {family['marriage_date']}\n")
                    if family.get('marriage_place'):
                        f.write(f"2 PLAC {family['marriage_place']}\n")
                        
            f.write("0 TRLR\n")
            
        logger.info(f"GEDCOM file written: {output_file}")
        logger.info(f"  Individuals: {len(self.individuals)}")
        logger.info(f"  Families: {len(self.families)}")
        
    def convert(self, output_file: str):
        """Main conversion method"""
        logger.info("Starting comprehensive FTB to GEDCOM conversion")
        
        self.connect_database()
        self.get_table_info()
        self.extract_individuals()
        self.extract_families()
        self.extract_events_and_facts()
        self.write_gedcom(output_file)
        
        if self.conn:
            self.conn.close()
            
        logger.info("Conversion completed successfully!")

def main():
    ftb_file = "Gaiad with uncertain merging of the roman lines.ftb"
    output_file = "new_gedcoms/comprehensive_gaiad_conversion.ged"
    
    converter = ComprehensiveFtbConverter(ftb_file)
    converter.convert(output_file)

if __name__ == "__main__":
    main()