#!/usr/bin/env python3
"""
Script to analyze and potentially extract data from FTB (Family Tree Builder) files.
FTB files are typically SQLite databases with a specific schema.
"""

import sqlite3
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FTBExtractor:
    def __init__(self, ftb_file: str):
        self.ftb_file = ftb_file
        
    def analyze_structure(self):
        """Analyze the FTB file structure (if it's an SQLite database)"""
        try:
            # FTB files are often SQLite databases
            conn = sqlite3.connect(self.ftb_file)
            cursor = conn.cursor()
            
            # Get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            print(f"Tables in FTB file:")
            for table in tables:
                table_name = table[0]
                print(f"  - {table_name}")
                
                # Get column info for each table
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                print(f"    Columns:")
                for col in columns:
                    print(f"      {col[1]} ({col[2]})")
                    
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"    Rows: {count}")
                print()
                
            conn.close()
            
        except sqlite3.Error as e:
            print(f"Error reading FTB file as SQLite: {e}")
            print("FTB file might be in a different format or encrypted.")
            
    def extract_basic_info(self):
        """Extract basic genealogical information if possible"""
        try:
            conn = sqlite3.connect(self.ftb_file)
            cursor = conn.cursor()
            
            # Common table names in FTB files
            possible_tables = ['Individuals', 'Persons', 'People', 'Names', 'Families']
            
            for table_name in possible_tables:
                try:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                    rows = cursor.fetchall()
                    if rows:
                        print(f"Sample data from {table_name}:")
                        for row in rows:
                            print(f"  {row}")
                        print()
                except sqlite3.Error:
                    continue
                    
            conn.close()
            
        except Exception as e:
            print(f"Error extracting data: {e}")

def main():
    ftb_file = "C:\\Users\\Immanuelle\\Documents\\Github\\Gaiad-Genealogy\\Gaiad with uncertain merging of the roman lines.ftb"
    
    if not os.path.exists(ftb_file):
        print(f"FTB file not found: {ftb_file}")
        return
        
    extractor = FTBExtractor(ftb_file)
    
    print("=== FTB File Analysis ===")
    print(f"File: {ftb_file}")
    print(f"Size: {os.path.getsize(ftb_file) / (1024*1024):.1f} MB")
    print()
    
    print("Analyzing structure...")
    extractor.analyze_structure()
    
    print("\nExtracting sample data...")
    extractor.extract_basic_info()

if __name__ == "__main__":
    main()