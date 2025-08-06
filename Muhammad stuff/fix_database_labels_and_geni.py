#!/usr/bin/env python3
"""
Fix Muhammad database:
1. Find entries without English labels
2. Fetch missing Geni IDs (P2600) from Wikidata
3. Update database with Geni IDs
4. Create JSON file for manual English label creation
"""

import json
import requests
import time
from typing import Dict, List, Set
from pymongo import MongoClient
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseFixer:
    def __init__(self):
        self.mongo_uri = "mongodb://127.0.0.1:27017"
        self.db_name = "Muhammad"
        self.coll_name = "persons"
        self.wikidata_api = "https://www.wikidata.org/w/api.php"
        
        self.client = MongoClient(self.mongo_uri)
        self.coll = self.client[self.db_name][self.coll_name]
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DatabaseFixer/1.0 (genealogy research)'
        })
        
        self.entries_without_english = []
        self.geni_updates_made = 0
        
    def find_entries_without_english_labels(self):
        """Find all database entries that don't have English labels"""
        logger.info("Finding entries without English labels...")
        
        total_count = self.coll.count_documents({})
        logger.info(f"Total entries in database: {total_count}")
        
        # Find entries where extracted.labels.en doesn't exist or is empty
        query = {
            "$or": [
                {"extracted.labels.en": {"$exists": False}},
                {"extracted.labels.en.value": {"$exists": False}},
                {"extracted.labels.en.value": ""}
            ]
        }
        
        cursor = self.coll.find(query, {"wikidata_id": 1, "extracted.labels": 1, "extracted.descriptions": 1})
        
        for doc in cursor:
            qid = doc["wikidata_id"]
            labels = doc.get("extracted", {}).get("labels", {})
            descriptions = doc.get("extracted", {}).get("descriptions", {})
            
            self.entries_without_english.append({
                "qid": qid,
                "labels": labels,
                "descriptions": descriptions
            })
        
        logger.info(f"Found {len(self.entries_without_english)} entries without English labels")
        
    def fetch_missing_data_from_wikidata(self):
        """Fetch missing Geni IDs and updated labels/descriptions from Wikidata"""
        logger.info("Fetching missing data from Wikidata...")
        
        # Get all QIDs from database
        all_qids = [doc["wikidata_id"] for doc in self.coll.find({}, {"wikidata_id": 1})]
        logger.info(f"Fetching data for {len(all_qids)} QIDs...")
        
        # Process in batches of 50
        batch_size = 50
        total_batches = (len(all_qids) + batch_size - 1) // batch_size
        
        for i in range(0, len(all_qids), batch_size):
            batch_num = i // batch_size + 1
            batch = all_qids[i:i + batch_size]
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} QIDs)")
            self._fetch_batch_data(batch)
            time.sleep(0.5)  # Be respectful to Wikidata API
            
            # Save progress every 20 batches
            if batch_num % 20 == 0:
                logger.info(f"Progress: {batch_num}/{total_batches} batches completed")
    
    def _fetch_batch_data(self, qids: List[str]):
        """Fetch updated data for a batch of QIDs"""
        entities = '|'.join(qids)
        
        params = {
            'action': 'wbgetentities',
            'ids': entities,
            'props': 'labels|descriptions|claims',
            'format': 'json'
        }
        
        try:
            response = self.session.get(self.wikidata_api, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'entities' in data:
                for qid, entity_data in data['entities'].items():
                    if 'missing' not in entity_data:
                        self._update_database_entry(qid, entity_data)
                    else:
                        logger.warning(f"Entity {qid} not found in Wikidata")
                        
        except Exception as e:
            logger.error(f"Error fetching batch {qids}: {e}")
    
    def _update_database_entry(self, qid: str, entity_data: dict):
        """Update database entry with fresh Wikidata data"""
        # Extract all labels and descriptions
        labels = entity_data.get('labels', {})
        descriptions = entity_data.get('descriptions', {})
        
        # Extract Geni profile ID (P2600)
        geni_id = None
        claims = entity_data.get('claims', {})
        if 'P2600' in claims:
            for claim in claims['P2600']:
                if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
                    geni_id = claim['mainsnak']['datavalue']['value']
                    break
        
        # Prepare update document
        update_doc = {
            "$set": {
                "extracted.labels": labels,
                "extracted.descriptions": descriptions,
                "last_updated": time.time()
            }
        }
        
        # Add Geni ID if found
        if geni_id:
            update_doc["$set"]["extracted.geni_profile_id"] = geni_id
            self.geni_updates_made += 1
            logger.debug(f"Found Geni ID for {qid}: {geni_id}")
        
        # Update the database entry
        result = self.coll.update_one(
            {"wikidata_id": qid},
            update_doc
        )
        
        if result.modified_count == 0:
            logger.warning(f"No database entry found for {qid}")
    
    def create_translation_json(self):
        """Create JSON file for manual English label creation"""
        logger.info("Creating translation JSON file...")
        
        # Re-scan for entries without English labels after updates
        self.entries_without_english = []
        query = {
            "$or": [
                {"extracted.labels.en": {"$exists": False}},
                {"extracted.labels.en.value": {"$exists": False}},
                {"extracted.labels.en.value": ""}
            ]
        }
        
        cursor = self.coll.find(query, {
            "wikidata_id": 1, 
            "extracted.labels": 1, 
            "extracted.descriptions": 1,
            "extracted.geni_profile_id": 1
        })
        
        translation_data = {}
        
        for doc in cursor:
            qid = doc["wikidata_id"]
            labels = doc.get("extracted", {}).get("labels", {})
            descriptions = doc.get("extracted", {}).get("descriptions", {})
            geni_id = doc.get("extracted", {}).get("geni_profile_id")
            
            # Convert labels format
            labels_dict = {}
            for lang, label_data in labels.items():
                if isinstance(label_data, dict) and 'value' in label_data:
                    labels_dict[lang] = label_data['value']
                elif isinstance(label_data, str):
                    labels_dict[lang] = label_data
            
            # Convert descriptions format
            descriptions_dict = {}
            for lang, desc_data in descriptions.items():
                if isinstance(desc_data, dict) and 'value' in desc_data:
                    descriptions_dict[lang] = desc_data['value']
                elif isinstance(desc_data, str):
                    descriptions_dict[lang] = desc_data
            
            translation_data[qid] = {
                "wikidata_url": f"https://www.wikidata.org/wiki/{qid}",
                "labels": labels_dict,
                "descriptions": descriptions_dict,
                "geni_profile_id": geni_id,
                "suggested_english_name": "[TO BE FILLED]"
            }
        
        # Save to JSON file
        output_file = "missing_english_labels.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(translation_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created translation file: {output_file}")
        logger.info(f"Entries needing English labels: {len(translation_data)}")
        
        # Also create a summary report
        with open("database_fix_summary.txt", 'w', encoding='utf-8') as f:
            f.write("DATABASE FIX SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            
            total_entries = self.coll.count_documents({})
            entries_with_geni = self.coll.count_documents({"extracted.geni_profile_id": {"$exists": True, "$ne": None}})
            entries_needing_labels = len(translation_data)
            
            f.write(f"Total entries in database: {total_entries}\n")
            f.write(f"Entries with Geni profile IDs: {entries_with_geni}\n")
            f.write(f"Geni IDs added in this run: {self.geni_updates_made}\n")
            f.write(f"Entries needing English labels: {entries_needing_labels}\n")
            f.write(f"Coverage: {((total_entries - entries_needing_labels)/total_entries*100):.1f}% have English labels\n\n")
            f.write(f"Translation file created: {output_file}\n")
            f.write("Review the JSON file and fill in English names for missing entries.\n")
        
        return len(translation_data)
    
    def run(self):
        """Run the complete database fixing process"""
        logger.info("Starting database fix process...")
        
        # Step 1: Find entries without English labels
        self.find_entries_without_english_labels()
        
        # Step 2: Fetch missing data from Wikidata
        self.fetch_missing_data_from_wikidata()
        
        # Step 3: Create translation JSON
        entries_needing_translation = self.create_translation_json()
        
        logger.info("Database fix completed!")
        logger.info(f"- Geni IDs added: {self.geni_updates_made}")
        logger.info(f"- Entries needing English labels: {entries_needing_translation}")
        logger.info("- Files created: missing_english_labels.json, database_fix_summary.txt")

if __name__ == "__main__":
    fixer = DatabaseFixer()
    fixer.run()