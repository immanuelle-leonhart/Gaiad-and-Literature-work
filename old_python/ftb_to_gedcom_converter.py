#!/usr/bin/env python3
"""
Convert FTB (Family Tree Builder) SQLite database to GEDCOM format
"""

import sqlite3
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FTBToGedcomConverter:
    def __init__(self, ftb_file: str, output_gedcom: str):
        self.ftb_file = ftb_file
        self.output_gedcom = output_gedcom
        self.individuals = {}
        self.families = {}
        
    def get_sample_individuals(self, limit=10):
        """Get sample individuals from the database"""
        conn = sqlite3.connect(self.ftb_file)
        cursor = conn.cursor()
        
        query = """
        SELECT DISTINCT 
            i.individual_id,
            i.gender,
            i.is_alive,
            il.first_name,
            il.last_name,
            il.prefix,
            il.suffix
        FROM individual_main_data i
        LEFT JOIN individual_data_set ids ON i.individual_id = ids.individual_id
        LEFT JOIN individual_lang_data il ON ids.individual_data_set_id = il.individual_data_set_id
        WHERE i.delete_flag = 0 AND il.first_name IS NOT NULL
        LIMIT ?
        """
        
        cursor.execute(query, (limit,))
        results = cursor.fetchall()
        
        print(f"\nSample individuals from FTB database:")
        print("-" * 80)
        for row in results:
            individual_id, gender, is_alive, first_name, last_name, prefix, suffix = row
            print(f"ID: {individual_id}")
            print(f"  Name: {prefix or ''} {first_name or ''} {last_name or ''} {suffix or ''}".strip())
            print(f"  Gender: {gender}")
            print(f"  Alive: {'Yes' if is_alive else 'No'}")
            print()
            
        conn.close()
        return results
        
    def get_sample_facts(self, individual_id):
        """Get facts (birth, death, etc.) for an individual"""
        conn = sqlite3.connect(self.ftb_file)
        cursor = conn.cursor()
        
        query = """
        SELECT 
            if.fact_type,
            if.date,
            if.age,
            pl.place,
            ifl.header,
            ifl.cause_of_death
        FROM individual_fact_main_data if
        LEFT JOIN places_main_data pm ON if.place_id = pm.place_id
        LEFT JOIN places_lang_data pl ON pm.place_id = pl.place_id
        LEFT JOIN individual_fact_lang_data ifl ON if.individual_fact_id = ifl.individual_fact_id
        WHERE if.individual_id = ? AND if.delete_flag = 0
        ORDER BY if.sorted_date
        """
        
        cursor.execute(query, (individual_id,))
        results = cursor.fetchall()
        
        print(f"\nFacts for individual {individual_id}:")
        for row in results:
            fact_type, date, age, place, header, cause_of_death = row
            print(f"  {fact_type}: {date or ''} {place or ''}")
            if header:
                print(f"    Details: {header}")
            if cause_of_death:
                print(f"    Cause of death: {cause_of_death}")
                
        conn.close()
        return results
        
    def get_database_stats(self):
        """Get statistics about the database"""
        conn = sqlite3.connect(self.ftb_file)
        cursor = conn.cursor()
        
        stats = {}
        
        # Individuals count
        cursor.execute("SELECT COUNT(*) FROM individual_main_data WHERE delete_flag = 0")
        stats['individuals'] = cursor.fetchone()[0]
        
        # Families count  
        cursor.execute("SELECT COUNT(*) FROM family_main_data WHERE delete_flag = 0")
        stats['families'] = cursor.fetchone()[0]
        
        # Facts count
        cursor.execute("SELECT COUNT(*) FROM individual_fact_main_data WHERE delete_flag = 0")
        stats['individual_facts'] = cursor.fetchone()[0]
        
        # Family facts count
        cursor.execute("SELECT COUNT(*) FROM family_fact_main_data WHERE delete_flag = 0")
        stats['family_facts'] = cursor.fetchone()[0]
        
        # Media items count
        cursor.execute("SELECT COUNT(*) FROM media_item_main_data WHERE delete_flag = 0")
        stats['media_items'] = cursor.fetchone()[0]
        
        # Sources count
        cursor.execute("SELECT COUNT(*) FROM source_main_data WHERE delete_flag = 0")
        stats['sources'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
        
    def export_basic_gedcom(self, limit=100):
        """Export a basic GEDCOM file with limited individuals"""
        conn = sqlite3.connect(self.ftb_file)
        cursor = conn.cursor()
        
        # Get individuals with names
        query = """
        SELECT DISTINCT 
            i.individual_id,
            i.gender,
            i.is_alive,
            il.first_name,
            il.last_name,
            il.prefix,
            il.suffix
        FROM individual_main_data i
        LEFT JOIN individual_data_set ids ON i.individual_id = ids.individual_id
        LEFT JOIN individual_lang_data il ON ids.individual_data_set_id = il.individual_data_set_id
        WHERE i.delete_flag = 0 
        AND (il.first_name IS NOT NULL OR il.last_name IS NOT NULL)
        LIMIT ?
        """
        
        cursor.execute(query, (limit,))
        individuals = cursor.fetchall()
        
        # Start GEDCOM file
        gedcom_content = []
        gedcom_content.append("0 HEAD")
        gedcom_content.append("1 SOUR FTB_Converter")
        gedcom_content.append("2 NAME FTB to GEDCOM Converter")
        gedcom_content.append("1 GEDC")
        gedcom_content.append("2 VERS 5.5.1")
        gedcom_content.append("2 FORM LINEAGE-LINKED")
        gedcom_content.append("1 CHAR UTF-8")
        gedcom_content.append(f"1 DATE {datetime.now().strftime('%d %b %Y').upper()}")
        gedcom_content.append("")
        
        # Add individuals
        for row in individuals:
            individual_id, gender, is_alive, first_name, last_name, prefix, suffix = row
            
            gedcom_content.append(f"0 @I{individual_id}@ INDI")
            
            # Name
            name_parts = []
            if prefix: name_parts.append(prefix)
            if first_name: name_parts.append(first_name)
            name_line = f"1 NAME {' '.join(name_parts)} /{last_name or ''}/"
            if suffix:
                name_line += f" {suffix}"
            gedcom_content.append(name_line)
            
            # Gender
            if gender:
                gedcom_content.append(f"1 SEX {gender}")
                
            gedcom_content.append("")
            
        # End GEDCOM
        gedcom_content.append("0 TRLR")
        
        # Write file
        with open(self.output_gedcom, 'w', encoding='utf-8') as f:
            f.write('\n'.join(gedcom_content))
            
        conn.close()
        print(f"Basic GEDCOM exported to: {self.output_gedcom}")
        print(f"Exported {len(individuals)} individuals")

def main():
    ftb_file = "C:\\Users\\Immanuelle\\Documents\\Github\\Gaiad-Genealogy\\Gaiad with uncertain merging of the roman lines.ftb"
    output_file = "C:\\Users\\Immanuelle\\Documents\\Github\\Gaiad-Genealogy\\ftb_sample_export.ged"
    
    if not os.path.exists(ftb_file):
        print(f"FTB file not found: {ftb_file}")
        return
        
    converter = FTBToGedcomConverter(ftb_file, output_file)
    
    print("=== FTB Database Analysis ===")
    print(f"File: {ftb_file}")
    print(f"Size: {os.path.getsize(ftb_file) / (1024*1024):.1f} MB")
    print()
    
    # Get database statistics
    stats = converter.get_database_stats()
    print("Database Statistics:")
    print(f"  Individuals: {stats['individuals']:,}")
    print(f"  Families: {stats['families']:,}")
    print(f"  Individual Facts: {stats['individual_facts']:,}")
    print(f"  Family Facts: {stats['family_facts']:,}")
    print(f"  Media Items: {stats['media_items']:,}")
    print(f"  Sources: {stats['sources']:,}")
    print()
    
    # Get sample individuals
    sample_individuals = converter.get_sample_individuals(5)
    
    # Get facts for first individual
    if sample_individuals:
        first_individual_id = sample_individuals[0][0]
        converter.get_sample_facts(first_individual_id)
    
    # Export a sample GEDCOM
    print("\n=== Exporting Sample GEDCOM ===")
    converter.export_basic_gedcom(limit=50)

if __name__ == "__main__":
    main()