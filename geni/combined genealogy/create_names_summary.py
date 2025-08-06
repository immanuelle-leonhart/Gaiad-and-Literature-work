#!/usr/bin/env python3
"""
Create a summary of Q-IDs used as names for manual review
"""

import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_names_summary():
    logger.info("Creating summary of Q-IDs used as names...")
    
    # Load the names.json file
    with open('names.json', 'r', encoding='utf-8') as f:
        wikidata_info = json.load(f)
    
    # Find Q-IDs used as names
    qids_as_names = []
    for qid, info in wikidata_info.items():
        if info.get('used_as_name', False):
            qids_as_names.append((qid, info))
    
    logger.info(f"Found {len(qids_as_names)} Q-IDs used as names")
    
    # Create summary file
    with open('names_for_manual_review.txt', 'w', encoding='utf-8') as f:
        f.write("Q-IDs USED AS NAMES - MANUAL REVIEW REQUIRED\n")
        f.write("=" * 60 + "\n\n")
        f.write("These Q-IDs appear in NAME fields and need proper English names.\n")
        f.write("Review all labels and descriptions to create appropriate anglicizations.\n\n")
        
        for qid, info in sorted(qids_as_names):
            f.write(f"Q-ID: {qid}\n")
            f.write(f"Wikidata: {info.get('wikidata_url', '')}\n")
            
            # Labels in all languages
            labels = info.get('labels', {})
            if labels:
                f.write("Labels:\n")
                for lang, label in sorted(labels.items()):
                    f.write(f"  {lang}: {label}\n")
            else:
                f.write("Labels: NONE FOUND\n")
            
            # Descriptions in all languages
            descriptions = info.get('descriptions', {})
            if descriptions:
                f.write("Descriptions:\n")
                for lang, desc in sorted(descriptions.items()):
                    f.write(f"  {lang}: {desc}\n")
            else:
                f.write("Descriptions: NONE FOUND\n")
            
            # Geni profile if available
            if info.get('geni_profile_id'):
                f.write(f"Geni Profile: https://www.geni.com/people/{info['geni_profile_id']}\n")
            
            f.write("\nSUGGESTED ENGLISH NAME: [TO BE FILLED]\n")
            f.write("-" * 60 + "\n\n")
    
    # Create JSON subset for easier processing
    names_subset = {qid: info for qid, info in qids_as_names}
    with open('names_needing_review.json', 'w', encoding='utf-8') as f:
        json.dump(names_subset, f, indent=2, ensure_ascii=False)
    
    logger.info("Summary files created:")
    logger.info("- names_for_manual_review.txt (human-readable)")
    logger.info("- names_needing_review.json (structured data)")

if __name__ == "__main__":
    create_names_summary()