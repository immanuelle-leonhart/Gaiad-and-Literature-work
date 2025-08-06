#!/usr/bin/env python3
"""
Extract ONLY Q-IDs that appear as names (1 NAME Q123456 //) - nothing else.
"""

import re
import json
import requests
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_qid_names_only():
    logger.info("Extracting ONLY Q-IDs used as names...")
    
    # Find Q-IDs in NAME lines only
    with open('wikidata_combined.ged', 'r', encoding='utf-8') as f:
        content = f.read()
    
    qid_names = re.findall(r'1 NAME (Q\d+) //', content)
    qid_names = list(set(qid_names))  # Remove duplicates
    
    logger.info(f"Found {len(qid_names)} Q-IDs used as names")
    
    # Fetch Wikidata info for ONLY these Q-IDs
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'QIDNamesExtractor/1.0 (genealogy research)'
    })
    
    api_url = "https://www.wikidata.org/w/api.php"
    qid_info = {}
    
    # Process in batches of 50
    for i in range(0, len(qid_names), 50):
        batch = qid_names[i:i + 50]
        entities = '|'.join(batch)
        
        params = {
            'action': 'wbgetentities',
            'ids': entities,
            'props': 'labels|descriptions|claims',
            'format': 'json'
        }
        
        try:
            logger.info(f"Fetching batch {i//50 + 1}/{(len(qid_names)-1)//50 + 1}")
            response = session.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'entities' in data:
                for qid, entity_data in data['entities'].items():
                    if 'missing' not in entity_data:
                        # Extract all labels
                        labels = entity_data.get('labels', {})
                        label_dict = {lang: label['value'] for lang, label in labels.items()}
                        
                        # Extract all descriptions
                        descriptions = entity_data.get('descriptions', {})
                        desc_dict = {lang: desc['value'] for lang, desc in descriptions.items()}
                        
                        # Extract Geni profile ID (P2600)
                        geni_id = None
                        claims = entity_data.get('claims', {})
                        if 'P2600' in claims:
                            for claim in claims['P2600']:
                                if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
                                    geni_id = claim['mainsnak']['datavalue']['value']
                                    break
                        
                        qid_info[qid] = {
                            'labels': label_dict,
                            'descriptions': desc_dict,
                            'geni_profile_id': geni_id,
                            'wikidata_url': f"https://www.wikidata.org/wiki/{qid}",
                            'has_english_label': 'en' in label_dict
                        }
                    else:
                        qid_info[qid] = {
                            'labels': {},
                            'descriptions': {},
                            'geni_profile_id': None,
                            'wikidata_url': f"https://www.wikidata.org/wiki/{qid}",
                            'has_english_label': False,
                            'missing': True
                        }
            
            time.sleep(0.2)  # Be respectful
            
        except Exception as e:
            logger.error(f"Error fetching batch: {e}")
    
    # Save to names.json
    with open('names.json', 'w', encoding='utf-8') as f:
        json.dump(qid_info, f, indent=2, ensure_ascii=False)
    
    # Statistics
    total = len(qid_info)
    with_english = sum(1 for info in qid_info.values() if info.get('has_english_label'))
    without_english = total - with_english
    with_geni = sum(1 for info in qid_info.values() if info.get('geni_profile_id'))
    
    logger.info(f"Results:")
    logger.info(f"- Total Q-IDs used as names: {total}")
    logger.info(f"- With English labels: {with_english}")
    logger.info(f"- WITHOUT English labels (need manual review): {without_english}")
    logger.info(f"- With Geni profiles: {with_geni}")
    
    # Create summary for manual review (only ones WITHOUT English labels)
    needs_review = {qid: info for qid, info in qid_info.items() 
                   if not info.get('has_english_label')}
    
    with open('names_for_manual_review.txt', 'w', encoding='utf-8') as f:
        f.write("Q-IDs USED AS NAMES WITHOUT ENGLISH LABELS - MANUAL REVIEW REQUIRED\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Processing {len(needs_review)} Q-IDs that need English names.\n")
        f.write("Review all labels and descriptions to create appropriate anglicizations.\n\n")
        
        for qid in sorted(needs_review.keys()):
            info = needs_review[qid]
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
            
            if info.get('geni_profile_id'):
                f.write(f"Geni Profile: https://www.geni.com/people/{info['geni_profile_id']}\n")
            
            f.write("\nSUGGESTED ENGLISH NAME: [TO BE FILLED]\n")
            f.write("-" * 60 + "\n\n")
    
    logger.info("Files created:")
    logger.info("- names.json (ALL Q-IDs used as names)")
    logger.info(f"- names_for_manual_review.txt (ONLY {len(needs_review)} without English labels)")

if __name__ == "__main__":
    extract_qid_names_only()