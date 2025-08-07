#!/usr/bin/env python3
"""
Simple, fast FTB to GEDCOM converter focusing on essential data extraction
"""

import sqlite3
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def convert_ftb_to_gedcom(ftb_file: str, output_file: str):
    """Simple FTB to GEDCOM conversion"""
    
    logger.info(f"Converting FTB: {ftb_file}")
    logger.info(f"Output: {output_file}")
    
    # Connect to database
    conn = sqlite3.connect(ftb_file)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write GEDCOM header
        f.write("0 HEAD\n")
        f.write("1 SOUR FTB_Simple_Converter\n")
        f.write("2 NAME Simple FTB to GEDCOM Converter\n")
        f.write("1 GEDC\n")
        f.write("2 VERS 5.5.1\n")
        f.write("2 FORM LINEAGE-LINKED\n")
        f.write("1 CHAR UTF-8\n")
        f.write(f"1 DATE {datetime.now().strftime('%d %b %Y').upper()}\n")
        f.write(f"1 FILE {os.path.basename(output_file)}\n")
        f.write(f"1 NOTE Converted from FTB: {os.path.basename(ftb_file)}\n")
        f.write("\n")
        
        # Get and write individuals
        logger.info("Processing individuals...")
        cursor.execute("""
            SELECT DISTINCT 
                i.individual_id,
                i.gender,
                i.guid,
                il.first_name,
                il.last_name,
                il.prefix,
                il.suffix
            FROM individual_main_data i
            LEFT JOIN individual_data_set ids ON i.individual_id = ids.individual_id
            LEFT JOIN individual_lang_data il ON ids.individual_data_set_id = il.individual_data_set_id
            WHERE i.delete_flag = 0
            ORDER BY i.individual_id
        """)
        
        individuals = cursor.fetchall()
        logger.info(f"Writing {len(individuals)} individuals...")
        
        for i, individual in enumerate(individuals):
            if i % 5000 == 0:
                logger.info(f"  Processed {i} individuals...")
                
            f.write(f"0 @I{individual['individual_id']}@ INDI\n")
            
            # Build name
            name_parts = []
            if individual['prefix']:
                name_parts.append(str(individual['prefix']).strip())
            if individual['first_name']:
                name_parts.append(str(individual['first_name']).strip())
            
            given = ' '.join(name_parts) if name_parts else ''
            surname = str(individual['last_name']).strip() if individual['last_name'] else ''
            suffix = str(individual['suffix']).strip() if individual['suffix'] else ''
            
            name_line = f"{given} /{surname}/"
            if suffix:
                name_line += f" {suffix}"
            name_line = name_line.strip()
            
            if name_line and name_line != " //":
                f.write(f"1 NAME {name_line}\n")
            
            # Gender
            if individual['gender']:
                f.write(f"1 SEX {individual['gender']}\n")
            
            # GUID
            if individual['guid']:
                f.write(f"1 _UID {individual['guid']}\n")
            
            f.write("\n")
        
        # Get and write families
        logger.info("Processing families...")
        cursor.execute("""
            SELECT family_id, guid
            FROM family_main_data
            WHERE delete_flag = 0
            ORDER BY family_id
        """)
        
        families = cursor.fetchall()
        logger.info(f"Writing {len(families)} families...")
        
        for i, family in enumerate(families):
            if i % 2000 == 0:
                logger.info(f"  Processed {i} families...")
                
            f.write(f"0 @F{family['family_id']}@ FAM\n")
            
            # Get family connections
            cursor.execute("""
                SELECT individual_id, individual_role_type
                FROM family_individual_connection
                WHERE family_id = ? AND delete_flag = 0
                ORDER BY individual_role_type, child_order_in_family
            """, (family['family_id'],))
            
            connections = cursor.fetchall()
            for conn in connections:
                role = conn['individual_role_type']
                if role == 1:  # Husband
                    f.write(f"1 HUSB @I{conn['individual_id']}@\n")
                elif role == 2:  # Wife
                    f.write(f"1 WIFE @I{conn['individual_id']}@\n")
                elif role == 3:  # Child
                    f.write(f"1 CHIL @I{conn['individual_id']}@\n")
            
            # GUID
            if family['guid']:
                f.write(f"1 _UID {family['guid']}\n")
                
            f.write("\n")
        
        # Write trailer
        f.write("0 TRLR\n")
    
    cursor.close(); conn.close()
    logger.info("Conversion complete!")

def main():
    ftb_file = "C:\\Users\\Immanuelle\\Documents\\Github\\Gaiad-Genealogy\\Gaiad with uncertain merging of the roman lines.ftb"
    output_file = "C:\\Users\\Immanuelle\\Documents\\Github\\Gaiad-Genealogy\\gaiad_ftb_simple_conversion.ged"
    
    if not os.path.exists(ftb_file):
        print(f"FTB file not found: {ftb_file}")
        return
    
    print("=== Simple FTB to GEDCOM Converter ===")
    print(f"Input: {ftb_file}")
    print(f"Size: {os.path.getsize(ftb_file) / (1024*1024):.1f} MB")
    print(f"Output: {output_file}")
    print()
    
    convert_ftb_to_gedcom(ftb_file, output_file)
    
    if os.path.exists(output_file):
        print(f"Output size: {os.path.getsize(output_file) / (1024*1024):.1f} MB")

if __name__ == "__main__":
    main()