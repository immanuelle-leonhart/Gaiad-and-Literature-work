#!/usr/bin/env python3
"""
FTB to GEDCOM Converter v3 - Fixed role mapping
Role 2 = HUSBAND, Role 3 = WIFE, Role 5 = CHILD
"""

import sqlite3
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FtbToGedcomV3:
    def __init__(self, ftb_file: str):
        self.ftb_file = ftb_file
        self.conn = None
        self.individuals = {}
        self.family_connections = {}
        
    def connect_database(self):
        try:
            self.conn = sqlite3.connect(self.ftb_file)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"Connected to FTB database: {self.ftb_file}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
            
    def extract_individuals(self):
        cursor = self.conn.cursor()
        
        query = """
        SELECT 
            imd.individual_id,
            imd.gender,
            imd.guid
        FROM individual_main_data imd
        WHERE imd.delete_flag = 0
        ORDER BY imd.individual_id
        """
        
        cursor.execute(query)
        individuals = cursor.fetchall()
        logger.info(f"Found {len(individuals)} individuals")
        
        for individual in individuals:
            individual_id = individual['individual_id']
            
            # Get name data
            name_query = """
            SELECT 
                ild.first_name,
                ild.last_name
            FROM individual_lang_data ild
            JOIN individual_data_set ids ON ild.individual_data_set_id = ids.individual_data_set_id
            WHERE ids.individual_id = ? AND ids.delete_flag = 0
            LIMIT 1
            """
            
            cursor.execute(name_query, (individual_id,))
            name_row = cursor.fetchone()
            
            first_name = name_row['first_name'] if name_row else ''
            last_name = name_row['last_name'] if name_row else ''
            
            self.individuals[individual_id] = {
                'individual_id': individual_id,
                'gender': individual['gender'] if individual['gender'] in ['M', 'F'] else 'U',
                'first_name': first_name or '',
                'last_name': last_name or '',
                'guid': individual['guid'] or '',
                'families_as_spouse': [],
                'families_as_child': []
            }
            
        logger.info(f"Extracted {len(self.individuals)} individuals with names")
        
    def extract_family_connections(self):
        cursor = self.conn.cursor()
        
        # Get all family connections
        query = """
        SELECT 
            fic.family_id,
            fic.individual_id,
            fic.individual_role_type
        FROM family_individual_connection fic
        WHERE fic.delete_flag = 0
        ORDER BY fic.family_id, fic.individual_role_type
        """
        
        cursor.execute(query)
        connections = cursor.fetchall()
        logger.info(f"Found {len(connections)} family connections")
        
        # Build family structure with CORRECTED role mapping
        for conn in connections:
            family_id = conn['family_id']
            individual_id = conn['individual_id']
            role_type = conn['individual_role_type']
            
            if family_id not in self.family_connections:
                self.family_connections[family_id] = {
                    'husband_id': None,
                    'wife_id': None, 
                    'children': []
                }
                
            family_conn = self.family_connections[family_id]
            
            # CORRECTED ROLE MAPPING:
            if role_type == 2:  # Role 2 = HUSBAND
                family_conn['husband_id'] = individual_id
                if individual_id in self.individuals:
                    self.individuals[individual_id]['families_as_spouse'].append(family_id)
            elif role_type == 3:  # Role 3 = WIFE  
                family_conn['wife_id'] = individual_id
                if individual_id in self.individuals:
                    self.individuals[individual_id]['families_as_spouse'].append(family_id)
            elif role_type == 5:  # Role 5 = CHILD
                family_conn['children'].append(individual_id)
                if individual_id in self.individuals:
                    self.individuals[individual_id]['families_as_child'].append(family_id)
            else:
                logger.warning(f"Unknown role type {role_type} for individual {individual_id} in family {family_id}")
                        
        # Remove empty families
        self.family_connections = {k: v for k, v in self.family_connections.items() 
                                 if v['husband_id'] or v['wife_id'] or v['children']}
                                 
        logger.info(f"Built {len(self.family_connections)} family structures")
        
        # Log statistics
        families_with_spouses = sum(1 for f in self.family_connections.values() 
                                  if f['husband_id'] or f['wife_id'])
        families_with_children = sum(1 for f in self.family_connections.values() 
                                   if f['children'])
        
        logger.info(f"  - {families_with_spouses} families with spouses")
        logger.info(f"  - {families_with_children} families with children")
        
    def write_gedcom(self, output_file: str):
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write("0 HEAD\n")
            f.write("1 SOUR FTB_to_GEDCOM_v3\n")
            f.write("2 NAME FTB to GEDCOM Converter v3 - Fixed Roles\n")
            f.write("2 CORP Gaiad Genealogy Project\n")
            f.write(f"1 DATE {datetime.now().strftime('%d %b %Y')}\n")
            f.write(f"1 FILE {output_file}\n")
            f.write("1 GEDC\n")
            f.write("2 VERS 5.5.1\n")
            f.write("2 FORM LINEAGE-LINKED\n")
            f.write("1 CHAR UTF-8\n")
            f.write(f"1 NOTE Converted from FTB: {self.ftb_file}\n")
            f.write(f"1 NOTE Fixed role mapping: Role 2=HUSBAND, Role 3=WIFE, Role 5=CHILD\n")
            
            # Write individuals
            for individual_id, individual in self.individuals.items():
                f.write(f"0 @I{individual_id}@ INDI\n")
                
                # Write name
                first_name = individual['first_name']
                last_name = individual['last_name']
                full_name = f"{first_name} /{last_name}/" if last_name else first_name
                
                f.write(f"1 NAME {full_name}\n")
                if first_name:
                    f.write(f"2 GIVN {first_name}\n")
                if last_name:
                    f.write(f"2 SURN {last_name}\n")
                    
                # Write gender
                f.write(f"1 SEX {individual['gender']}\n")
                
                # Write family references
                for family_id in individual['families_as_spouse']:
                    f.write(f"1 FAMS @F{family_id}@\n")
                for family_id in individual['families_as_child']:
                    f.write(f"1 FAMC @F{family_id}@\n")
                    
                # Write GUID as reference
                if individual['guid']:
                    f.write(f"1 REFN {individual['guid']}\n")
                    
            # Write families
            for family_id, family in self.family_connections.items():
                f.write(f"0 @F{family_id}@ FAM\n")
                
                if family['husband_id']:
                    f.write(f"1 HUSB @I{family['husband_id']}@\n")
                if family['wife_id']:
                    f.write(f"1 WIFE @I{family['wife_id']}@\n")
                    
                for child_id in family['children']:
                    f.write(f"1 CHIL @I{child_id}@\n")
                    
            f.write("0 TRLR\n")
            
        logger.info(f"GEDCOM written: {output_file}")
        logger.info(f"  Individuals: {len(self.individuals)}")
        logger.info(f"  Families: {len(self.family_connections)}")
        
        # Verify family linkages
        individuals_with_family_refs = sum(1 for i in self.individuals.values() 
                                         if i['families_as_spouse'] or i['families_as_child'])
        logger.info(f"  Individuals with family links: {individuals_with_family_refs}")
        
    def convert(self, output_file: str):
        logger.info("Starting FTB to GEDCOM conversion v3 (fixed roles)")
        
        self.connect_database()
        self.extract_individuals()
        self.extract_family_connections()
        self.write_gedcom(output_file)
        
        if self.conn:
            self.conn.close()
            
        logger.info("Conversion completed!")

def main():
    ftb_file = "new_gedcoms/Gaiad with uncertain merging of the roman lines.ftb"
    output_file = "new_gedcoms/gaiad_ftb_export_2.ged"
    
    converter = FtbToGedcomV3(ftb_file)
    converter.convert(output_file)

if __name__ == "__main__":
    main()