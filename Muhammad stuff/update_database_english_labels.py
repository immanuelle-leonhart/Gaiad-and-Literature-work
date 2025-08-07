#!/usr/bin/env python3
"""
Update Muhammad database with English labels from missing_english_labels_filled.json
"""

import json
import logging
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_database_with_english_labels():
    """Update database with filled English labels"""
    logger.info("Starting database English labels update...")
    
    # Connect to MongoDB
    client = MongoClient("mongodb://127.0.0.1:27017")
    coll = client["Muhammad"]["persons"]
    
    # Read the filled translations
    with open('missing_english_labels_filled.json', 'r', encoding='utf-8') as f:
        filled_data = json.load(f)
    
    logger.info(f"Loaded {len(filled_data)} entries with English names")
    
    updates_made = 0
    
    for qid, data in filled_data.items():
        english_name = data.get('suggested_english_name')
        
        if english_name and english_name != '[TO BE FILLED]':
            # Update the database entry
            result = coll.update_one(
                {"wikidata_id": qid},
                {
                    "$set": {
                        "extracted.labels.en": {
                            "language": "en",
                            "value": english_name
                        },
                        "english_label_updated": True
                    }
                }
            )
            
            if result.modified_count > 0:
                updates_made += 1
                logger.info(f"Updated {qid}: {english_name}")
            else:
                logger.warning(f"No database entry found for {qid}")
        else:
            logger.warning(f"No English name provided for {qid}")
    
    logger.info(f"Database update completed! Updated {updates_made} entries with English labels")

if __name__ == "__main__":
    update_database_with_english_labels()