#!/usr/bin/env python3
"""
Yellow Emperor Relatives Importer from Wikidata
Imports descendants and relatives of the Yellow Emperor (Q29201) into a separate database
"""

import requests
import time
import logging
from typing import Dict, List, Set, Optional
import sqlite3
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class YellowEmperorImporter:
    def __init__(self, db_name: str = "yellow_emperor_genealogy.db"):
        self.db_name = db_name
        self.conn = None
        self.processed = set()
        self.queue = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'YellowEmperorGenealogy/1.0 (genealogy research)'
        })
        
    def setup_database(self):
        """Create database tables"""
        self.conn = sqlite3.connect(self.db_name)
        cursor = self.conn.cursor()
        
        # Create individuals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS individuals (
                qid TEXT PRIMARY KEY,
                name_en TEXT,
                name_zh TEXT,
                birth_date TEXT,
                death_date TEXT,
                description_en TEXT,
                description_zh TEXT,
                gender TEXT,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create relationships table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_qid TEXT,
                to_qid TEXT,
                relationship_type TEXT,
                property_id TEXT,
                FOREIGN KEY(from_qid) REFERENCES individuals(qid),
                FOREIGN KEY(to_qid) REFERENCES individuals(qid)
            )
        """)
        
        self.conn.commit()
        logger.info(f"Database initialized: {self.db_name}")
        
    def sparql_query(self, query: str, retries: int = 3) -> Optional[Dict]:
        """Execute SPARQL query with retries"""
        url = "https://query.wikidata.org/sparql"
        
        for attempt in range(retries):
            try:
                response = self.session.get(url, params={
                    'query': query,
                    'format': 'json'
                }, timeout=30)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limited
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"SPARQL query failed: {response.status_code}")
                    return None
                    
            except Exception as e:
                logger.error(f"SPARQL query error (attempt {attempt+1}): {e}")
                if attempt < retries - 1:
                    time.sleep(1)
                    
        return None
        
    def get_yellow_emperor_relatives(self, max_depth: int = 3) -> List[str]:
        """Get relatives of Yellow Emperor using family properties"""
        query = f"""
        SELECT DISTINCT ?person WHERE {{
          {{
            # Direct descendants (up to {max_depth} levels)
            wd:Q29201 (wdt:P40+) ?person .
          }} UNION {{
            # Parents, siblings, spouses
            {{ wd:Q29201 wdt:P22|wdt:P25 ?parent . ?parent wdt:P40 ?person . }}
            UNION {{ wd:Q29201 wdt:P26 ?person . }}
            UNION {{ ?person wdt:P26 wd:Q29201 . }}
          }} UNION {{
            # Ancestors
            ?person (wdt:P40+) wd:Q29201 .
          }} UNION {{
            # In-laws and extended family
            {{ wd:Q29201 wdt:P40 ?child . ?child wdt:P26 ?person . }}
            UNION {{ wd:Q29201 wdt:P26 ?spouse . ?spouse wdt:P22|wdt:P25 ?person . }}
          }}
          
          # Ensure it's a human
          ?person wdt:P31 wd:Q5 .
        }}
        LIMIT 5000
        """
        
        logger.info("Fetching Yellow Emperor relatives from Wikidata...")
        result = self.sparql_query(query)
        
        if not result:
            logger.error("Failed to fetch relatives")
            return []
            
        qids = []
        for binding in result.get('results', {}).get('bindings', []):
            qid = binding['person']['value'].split('/')[-1]
            qids.append(qid)
            
        logger.info(f"Found {len(qids)} relatives")
        return qids
        
    def get_individual_details(self, qid: str) -> Optional[Dict]:
        """Get detailed information for an individual"""
        query = f"""
        SELECT ?name_en ?name_zh ?birth ?death ?desc_en ?desc_zh ?gender WHERE {{
          wd:{qid} rdfs:label ?name_en .
          FILTER(LANG(?name_en) = "en")
          
          OPTIONAL {{ wd:{qid} rdfs:label ?name_zh . FILTER(LANG(?name_zh) = "zh") }}
          OPTIONAL {{ wd:{qid} schema:description ?desc_en . FILTER(LANG(?desc_en) = "en") }}
          OPTIONAL {{ wd:{qid} schema:description ?desc_zh . FILTER(LANG(?desc_zh) = "zh") }}
          OPTIONAL {{ wd:{qid} wdt:P569 ?birth . }}
          OPTIONAL {{ wd:{qid} wdt:P570 ?death . }}
          OPTIONAL {{ wd:{qid} wdt:P21 ?gender_item . }}
        }}
        """
        
        result = self.sparql_query(query)
        if not result:
            return None
            
        bindings = result.get('results', {}).get('bindings', [])
        if not bindings:
            return None
            
        binding = bindings[0]  # Take first result
        
        return {
            'qid': qid,
            'name_en': binding.get('name_en', {}).get('value', ''),
            'name_zh': binding.get('name_zh', {}).get('value', ''),
            'birth_date': binding.get('birth', {}).get('value', ''),
            'death_date': binding.get('death', {}).get('value', ''),
            'description_en': binding.get('desc_en', {}).get('value', ''),
            'description_zh': binding.get('desc_zh', {}).get('value', ''),
            'gender': binding.get('gender', {}).get('value', '')
        }
        
    def get_family_relationships(self, qid: str) -> List[Dict]:
        """Get family relationships for an individual"""
        query = f"""
        SELECT ?relation ?relationType ?relationLabel WHERE {{
          {{
            wd:{qid} wdt:P22 ?relation .
            BIND("father" AS ?relationType)
          }} UNION {{
            wd:{qid} wdt:P25 ?relation .
            BIND("mother" AS ?relationType)
          }} UNION {{
            wd:{qid} wdt:P26 ?relation .
            BIND("spouse" AS ?relationType)
          }} UNION {{
            wd:{qid} wdt:P40 ?relation .
            BIND("child" AS ?relationType)
          }} UNION {{
            ?relation wdt:P40 wd:{qid} .
            BIND("parent" AS ?relationType)
          }}
          
          ?relation wdt:P31 wd:Q5 .  # Ensure it's human
          ?relation rdfs:label ?relationLabel .
          FILTER(LANG(?relationLabel) = "en")
        }}
        """
        
        result = self.sparql_query(query)
        if not result:
            return []
            
        relationships = []
        for binding in result.get('results', {}).get('bindings', []):
            rel_qid = binding['relation']['value'].split('/')[-1]
            relationships.append({
                'to_qid': rel_qid,
                'relationship_type': binding['relationType']['value'],
                'name': binding.get('relationLabel', {}).get('value', '')
            })
            
        return relationships
        
    def save_individual(self, individual_data: Dict):
        """Save individual to database"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO individuals 
            (qid, name_en, name_zh, birth_date, death_date, description_en, description_zh, gender)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            individual_data['qid'],
            individual_data['name_en'],
            individual_data['name_zh'],
            individual_data['birth_date'],
            individual_data['death_date'],
            individual_data['description_en'],
            individual_data['description_zh'],
            individual_data['gender']
        ))
        self.conn.commit()
        
    def save_relationships(self, from_qid: str, relationships: List[Dict]):
        """Save relationships to database"""
        cursor = self.conn.cursor()
        
        for rel in relationships:
            cursor.execute("""
                INSERT OR IGNORE INTO relationships
                (from_qid, to_qid, relationship_type, property_id)
                VALUES (?, ?, ?, ?)
            """, (from_qid, rel['to_qid'], rel['relationship_type'], ''))
            
        self.conn.commit()
        
    def import_relatives(self):
        """Main import process"""
        logger.info("Starting Yellow Emperor genealogy import...")
        
        # Get initial list of relatives
        relatives = self.get_yellow_emperor_relatives()
        
        # Add Yellow Emperor himself
        relatives.insert(0, 'Q29201')
        
        total = len(relatives)
        processed = 0
        
        for qid in relatives:
            if qid in self.processed:
                continue
                
            processed += 1
            logger.info(f"Processing {processed}/{total}: {qid}")
            
            # Get individual details
            individual_data = self.get_individual_details(qid)
            if individual_data:
                self.save_individual(individual_data)
                logger.info(f"  Saved: {individual_data['name_en']} ({individual_data['name_zh']})")
            else:
                logger.warning(f"  Could not fetch details for {qid}")
                continue
                
            # Get relationships
            relationships = self.get_family_relationships(qid)
            if relationships:
                self.save_relationships(qid, relationships)
                logger.info(f"  Found {len(relationships)} relationships")
                
            self.processed.add(qid)
            
            # Rate limiting
            time.sleep(0.5)
            
        logger.info(f"Import completed! Processed {len(self.processed)} individuals")
        
    def generate_stats(self):
        """Generate statistics about the imported data"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM individuals")
        individual_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM relationships")
        relationship_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT relationship_type, COUNT(*) 
            FROM relationships 
            GROUP BY relationship_type 
            ORDER BY COUNT(*) DESC
        """)
        rel_types = cursor.fetchall()
        
        logger.info("=== YELLOW EMPEROR GENEALOGY STATS ===")
        logger.info(f"Total individuals: {individual_count}")
        logger.info(f"Total relationships: {relationship_count}")
        logger.info("Relationship types:")
        for rel_type, count in rel_types:
            logger.info(f"  {rel_type}: {count}")
            
    def export_to_gedcom(self, output_file: str):
        """Export the genealogy to GEDCOM format"""
        cursor = self.conn.cursor()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write("0 HEAD\n")
            f.write("1 SOUR Yellow_Emperor_Importer\n")
            f.write("2 NAME Yellow Emperor Genealogy from Wikidata\n")
            f.write("2 CORP Gaiad Genealogy Project\n")
            f.write(f"1 DATE {datetime.now().strftime('%d %b %Y')}\n")
            f.write(f"1 FILE {output_file}\n")
            f.write("1 GEDC\n")
            f.write("2 VERS 5.5.1\n")
            f.write("2 FORM LINEAGE-LINKED\n")
            f.write("1 CHAR UTF-8\n")
            f.write("1 NOTE Imported from Wikidata - Yellow Emperor (Q29201) and relatives\n")
            
            # Write individuals
            cursor.execute("SELECT * FROM individuals ORDER BY qid")
            individuals = cursor.fetchall()
            
            for ind in individuals:
                qid, name_en, name_zh, birth, death, desc_en, desc_zh, gender, fetched = ind
                
                f.write(f"0 @{qid}@ INDI\n")
                
                # Names
                if name_en:
                    f.write(f"1 NAME {name_en}\n")
                    f.write(f"2 GIVN {name_en}\n")
                if name_zh:
                    f.write(f"1 NAME {name_zh}\n")
                    f.write(f"2 GIVN {name_zh}\n")
                    
                # Gender
                if 'Q6581097' in gender:  # male
                    f.write("1 SEX M\n")
                elif 'Q6581072' in gender:  # female
                    f.write("1 SEX F\n")
                    
                # Birth
                if birth:
                    f.write("1 BIRT\n")
                    f.write(f"2 DATE {birth}\n")
                    
                # Death
                if death:
                    f.write("1 DEAT\n")
                    f.write(f"2 DATE {death}\n")
                    
                # Notes
                if desc_en:
                    f.write(f"1 NOTE {desc_en}\n")
                if desc_zh and desc_zh != desc_en:
                    f.write(f"1 NOTE {desc_zh}\n")
                    
                # Wikidata reference
                f.write(f"1 REFN {qid}\n")
                f.write(f"2 TYPE Wikidata\n")
                
            f.write("0 TRLR\n")
            
        logger.info(f"GEDCOM exported: {output_file}")

def main():
    importer = YellowEmperorImporter()
    importer.setup_database()
    importer.import_relatives()
    importer.generate_stats()
    importer.export_to_gedcom("yellow_emperor_genealogy.ged")

if __name__ == "__main__":
    main()