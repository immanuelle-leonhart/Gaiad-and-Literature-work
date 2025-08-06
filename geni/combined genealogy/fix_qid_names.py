#!/usr/bin/env python3
"""
Focused script to fix entries with Q-ID names in wikidata_combined.ged
"""

import re
import json
import requests
import time
from typing import Dict, List
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_qid_name_entries(gedcom_file: str) -> List[Dict]:
    """Find all entries that have Q-ID as names"""
    logger.info("Finding entries with Q-ID names...")
    
    entries = []
    with open(gedcom_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all Q-ID names using regex
    pattern = r'1 NAME (Q\d+) //'
    matches = re.finditer(pattern, content)
    
    for match in matches:
        qid = match.group(1)
        line_start = content[:match.start()].count('\n') + 1
        entries.append({
            'qid': qid,
            'line_number': line_start,
            'original_line': f"1 NAME {qid} //"
        })
    
    logger.info(f"Found {len(entries)} entries with Q-ID names")
    return entries

def fetch_wikidata_info(qids: List[str]) -> Dict:
    """Fetch Wikidata info for Q-IDs"""
    logger.info(f"Fetching Wikidata info for {len(qids)} Q-IDs...")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'WikidataGedcomFixer/1.0 (genealogy research)'
    })
    
    api_url = "https://www.wikidata.org/w/api.php"
    results = {}
    
    # Process in batches of 50
    for i in range(0, len(qids), 50):
        batch = qids[i:i + 50]
        entities = '|'.join(batch)
        
        params = {
            'action': 'wbgetentities',
            'ids': entities,
            'props': 'labels|claims',
            'format': 'json'
        }
        
        try:
            logger.info(f"Fetching batch {i//50 + 1}/{(len(qids)-1)//50 + 1}")
            response = session.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'entities' in data:
                for qid, entity_data in data['entities'].items():
                    if 'missing' not in entity_data:
                        # Extract labels
                        labels = entity_data.get('labels', {})
                        
                        # Try to get English name first, then other languages
                        english_name = labels.get('en', {}).get('value')
                        if not english_name:
                            # Try other common languages in order of preference
                            for lang in ['en', 'ru', 'de', 'fr', 'es', 'it', 'hy', 'ar']:
                                if lang in labels:
                                    english_name = labels[lang]['value']
                                    break
                            
                            # If still no name, use first available label
                            if not english_name and labels:
                                first_lang = list(labels.keys())[0]
                                english_name = labels[first_lang]['value']
                            
                            # Final fallback to Q-ID
                            if not english_name:
                                english_name = qid
                        
                        # Extract Geni profile ID (P2600)
                        geni_id = None
                        claims = entity_data.get('claims', {})
                        if 'P2600' in claims:
                            for claim in claims['P2600']:
                                if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
                                    geni_id = claim['mainsnak']['datavalue']['value']
                                    break
                        
                        results[qid] = {
                            'english_name': english_name,
                            'all_labels': {lang: label['value'] for lang, label in labels.items()},
                            'geni_id': geni_id
                        }
                    else:
                        logger.warning(f"Entity {qid} not found")
                        results[qid] = {
                            'english_name': qid,
                            'all_labels': {},
                            'geni_id': None
                        }
            
            time.sleep(0.2)  # Be respectful
            
        except Exception as e:
            logger.error(f"Error fetching batch: {e}")
            for qid in batch:
                results[qid] = {
                    'english_name': qid,
                    'all_labels': {},
                    'geni_id': None
                }
    
    return results

def generate_report(qid_info: Dict, filename: str = "qid_names_report.txt"):
    """Generate a report of all Q-ID names and their labels"""
    logger.info(f"Generating report: {filename}")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("Q-ID NAMES REPORT\n")
        f.write("=" * 50 + "\n\n")
        
        for qid, info in sorted(qid_info.items()):
            f.write(f"Q-ID: {qid}\n")
            f.write(f"Suggested English Name: {info['english_name']}\n")
            
            if info['geni_id']:
                f.write(f"Geni Profile ID: {info['geni_id']}\n")
            
            if info['all_labels']:
                f.write("All Language Labels:\n")
                for lang, label in sorted(info['all_labels'].items()):
                    f.write(f"  {lang}: {label}\n")
            else:
                f.write("No labels found\n")
            
            f.write("\n" + "-" * 30 + "\n\n")

def update_gedcom_file(gedcom_file: str, entries: List[Dict], qid_info: Dict):
    """Update GEDCOM file with proper names"""
    logger.info("Updating GEDCOM file...")
    
    # Read the file
    with open(gedcom_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Create backup
    backup_file = gedcom_file.replace('.ged', '_qid_fixed_backup.ged')
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    # Update lines
    updates_made = 0
    for entry in entries:
        qid = entry['qid']
        if qid in qid_info:
            info = qid_info[qid]
            english_name = info['english_name']
            
            # Parse name into given and surname
            name_parts = english_name.split(' ', 1)
            given_name = name_parts[0]
            surname = name_parts[1] if len(name_parts) > 1 else ""
            
            # Find the line (adjust for 0-based indexing)
            line_idx = entry['line_number'] - 1
            if line_idx < len(lines):
                old_line = lines[line_idx].strip()
                if f"1 NAME {qid}" in old_line:
                    lines[line_idx] = f"1 NAME {given_name} /{surname}/\n"
                    updates_made += 1
                    logger.info(f"Updated {qid} -> {english_name}")
    
    # Write updated file
    with open(gedcom_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    logger.info(f"Updated {updates_made} entries. Backup saved as: {backup_file}")

def main():
    gedcom_file = "wikidata_combined.ged"
    
    # Find entries with Q-ID names
    entries = find_qid_name_entries(gedcom_file)
    
    if not entries:
        logger.info("No entries with Q-ID names found")
        return
    
    # Extract unique Q-IDs
    qids = list(set(entry['qid'] for entry in entries))
    
    # Fetch Wikidata info
    qid_info = fetch_wikidata_info(qids)
    
    # Generate report
    generate_report(qid_info)
    
    # Update GEDCOM
    update_gedcom_file(gedcom_file, entries, qid_info)
    
    logger.info("Processing completed!")
    logger.info(f"- Found {len(entries)} entries with Q-ID names")
    logger.info(f"- Fetched info for {len(qid_info)} Q-IDs")
    logger.info("- Report saved as: qid_names_report.txt")

if __name__ == "__main__":
    main()